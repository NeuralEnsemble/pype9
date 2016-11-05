"""
Runs a simulation described by an Experiment layer 9ML file
"""
from argparse import ArgumentParser
from ._utils import nineml_model


parser = ArgumentParser(prog='pype9 simulate',
                        description=__doc__)
parser.add_argument('model', type=nineml_model,
                    help=("Path to nineml model file which to simulate. "
                          "It can be a relative path, absolute path, URL or "
                          "if the path starts with '//' it will be interpreted"
                          "as a ninemlcatalog path. For files with multiple "
                          "components, the name of component to simulated must"
                          " be appended after a #, "
                          "e.g. //neuron/izhikevich#izhikevich"))
parser.add_argument('simulator', choices=('neuron', 'nest'), type=str,
                    help="Which simulator backend to use")
parser.add_argument('time', type=float,
                    help="Time to run the simulation for")
parser.add_argument('timestep', type=float,
                    help="Timestep used to solve the differential equations")
parser.add_argument('--prop', nargs=3, action='append',
                    metavar=('PARAM', 'VALUE', 'UNITS'), default=[],
                    help=("Set the property to the given value"))
parser.add_argument('--init_regime', type=str, default=None,
                    help=("Initial regime for dynamics"))
parser.add_argument('--init_value', nargs=3, default=[], action='append',
                    metavar=('STATE-VARIABLE', 'VALUE', 'UNITS'),
                    help=("Initial regime for dynamics"))
parser.add_argument('--record', type=str, nargs=3, action='append', default=[],
                    metavar=('PORT/STATE-VARIABLE', 'FILENAME', 'SAVENAME'),
                    help=("Record the values from the send port or state "
                          "variable and the filename to save it into"))
parser.add_argument('--play', type=str, nargs=3, action='append',
                    metavar=('PORT', 'FILENAME', 'NAME'), default=[],
                    help=("Name of receive port and filename with signal to "
                          "play it into"))
parser.add_argument('--play_prop', nargs=4, action='append',
                    metavar=('PORT', 'PARAM', 'VALUE', 'UNITS'), default=[],
                    help=("Set the property to the given value"))
parser.add_argument('--play_init_regime', nargs=2, type=str, default=None,
                    metavar=('PORT', 'REGIME-NAME'),
                    help=("Initial regime for dynamics"))
parser.add_argument('--play_init_value', nargs=4, default=[],
                    action='append',
                    metavar=('PORT', 'STATE-VARIALBE', 'VALUE', 'UNITS'),
                    help=("Initial regime for dynamics"))
parser.add_argument('--seed', type=int, default=None,
                    help="Random seed used to create network and properties")


def run(argv):
    """
    Runs the simulation script from the provided arguments
    """
    import nineml
    from nineml import units as un
    from pype9.exceptions import Pype9UsageError
    import neo.io
    import time

    args = parser.parse_args(argv)

    seed = time.time() if args.seed is None else args.seed

    if args.simulator == 'neuron':
        from pype9.neuron import Network, CellMetaClass, simulation_controller  # @UnusedImport @IgnorePep8
    elif args.simulator == 'nest':
        from pype9.nest import Network, CellMetaClass, simulation_controller  # @Reimport @IgnorePep8
    else:
        raise Pype9UsageError(
            "Unrecognised simulator '{}', (available 'neuron' or 'nest')"
            .format(args.simulator))

    if isinstance(args.model, nineml.Document):
        min_delay = 0.1  # FIXME: Should add as method to Network class
        max_delay = 10.0
    else:
        min_delay = args.timestep
        max_delay = args.timestep * 2

    if isinstance(args.model, nineml.Network):
        if args.simulator == 'neuron':
            from pyNN.neuron import run, setup  # @UnusedImport
        else:
            from pyNN.nest import run, setup  # @Reimport

        # Reset the simulator
        setup(min_delay=min_delay, max_delay=max_delay,
              timestep=args.timestep, rng_seeds_seed=seed)
        # Construct the network
        print "Constructing '{}' network".format(args.model.name)
        network = Network(args.model, build_mode=args.build_mode)
        print "Finished constructing the '{}' network".format(args.model.name)
        for record_name, _, _ in args.record:
            pop_name, port_name = record_name.split('.')
            network[pop_name].record(port_name)
        print "Running the simulation".format()
        run(args.simtime)
        for record_name, filename, name in args.record:
            pop_name, port_name = record_name.split('.')
            seg = network[pop_name].get_data().segments[0]
            data[filename] = seg  # FIXME: not implemented
    else:
        assert isinstance(args.model, (nineml.DynamicsProperties,
                                       nineml.Dynamics))
        if args.prop:
            props = dict((parm, float(val), getattr(un, unts))
                         for parm, val, unts in args.prop)
            model = nineml.DynamicsProperties(
                args.model.name + '_props', args.model, props)
        if not isinstance(args.model, nineml.DynamicsProperties):
            raise Pype9UsageError(
                "Specified model {} is not a dynamics properties object"
                .format(args.model))
        component_class = args.model.component_class
        init_regime = args.init_regime
        if init_regime is None:
            if component_class.num_regimes == 1:
                init_regime = next(component_class.regimes)
            else:
                raise Pype9UsageError(
                    "Need to specify initial regime as dynamics has more than "
                    "one '{}'".format("', '".join(
                        r.name for r in component_class.regimes)))
        # Build cell class
        Cell = CellMetaClass(args.model.component_class, name=args.model.name,
                             init_regime=init_regime)
        # Create cell
        cell = Cell(args.model)
        init_state = dict((sv, float(val), getattr(un, units))
                          for sv, val, units in args.init_value)
        if set(cell.state_variable_names) != set(init_state.iterkeys()):
            raise Pype9UsageError(
                "Need to specify an initial value for each state in the model,"
                " missing '{}'".format(
                    "', '".join(set(cell.state_variable_names) -
                                set(init_state.iterkeys()))))
        cell.update_state(init_state)
        # Play inputs
        for port_name, fname, _ in args.play:
            data_seg = neo.io.PickleIO(filename=fname).read_segment()
            port = component_class.receive_port(port_name)
            # FIXME: Should look up name of spiketrain or analogsignals
            if port.communicates == 'event':
                cell.play(port_name, data_seg.spiketrains[0])
            else:
                cell.play(port_name, data_seg.analogsignals[0])
        # Set up recorders
        for port_name, _, _ in args.record:
            cell.record(port_name)
        # Run simulation
        simulation_controller.run(args.time)
        # Collect data into Neo Segments
        fnames = set(r[2] for r in args.record)
        data_segs = {}
        for fname in fnames:
            data_segs[fname] = neo.Segment(
                description="Simulation of '{}' cell".format(args.model.name))
        for port_name, fname, _ in args.record:
            data = cell.recording(port_name)
            if isinstance(data, neo.AnalogSignal):
                data_segs[fname].analogsignals.append(data)
            else:
                data_segs[fname].spiketrains.append(data)
        # Write data to file
        for fname, data_seg in data_segs.iteritems():
            neo.io.PickleIO(fname).write(data_seg)
    print "Simulated '{}' for {} ms".format(args.model.name, args.time)
