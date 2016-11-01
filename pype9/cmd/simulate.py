"""
Runs a simulation described by an Experiment layer 9ML file
"""
from argparse import ArgumentParser
from ._utils import existing_file


parser = ArgumentParser(description=__doc__)
parser.add_argument('model_file', type=existing_file,
                    help=("Path to nineml model file which to simulate. "
                          "It can be a relative path, absolute path, URL or "
                          "if the path starts with '//' it will be interpreted"
                          "as a ninemlcatalog path"))
parser.add_argument('simulator', choices=('neuron', 'nest'), type=str,
                    help="Which simulator backend to use")
parser.add_argument('time', type=float,
                    help="Time to run the simulation for")
parser.add_argument('--name', type=str, default=None,
                    help="Name of the model to run from the model file")
parser.add_argument('--prop', type=(str, float, str), nargs=3, action='append',
                    metavar=('PARAM', 'VALUE', 'UNITS'), default=[],
                    help=("Set the property to the given value"))
parser.add_argument('--initial_regime', type=str, default=None,
                    help=("Initial regime for dynamics"))
parser.add_argument('--initial_value', nargs=3, default=[], action='append',
                    metavar=('STATE-VARIALBE', 'VALUE', 'UNITS'),
                    help=("Initial regime for dynamics"))
parser.add_argument('--record', type=str, nargs=3, action='append', default=[],
                    metavar=('PORT/STATE-VARIABLE', 'FILENAME'),
                    help=("Record the values from the send port or state "
                          "variable and the filename to save it into"))
parser.add_argument('--play', type=str, nargs=3, action='append',
                    metavar=('PORT', 'FILENAME', 'NAME'), default=[],
                    help=("Name of receive port and filename with signal to "
                          "play it into"))
parser.add_argument('--play_prop', nargs=4, action='append',
                    metavar=('PORT', 'PARAM', 'VALUE', 'UNITS'), default=[],
                    help=("Set the property to the given value"))
parser.add_argument('--play_initial_regime', nargs=2, type=str, default=None,
                    metavar=('PORT', 'REGIME-NAME'),
                    help=("Initial regime for dynamics"))
parser.add_argument('--play_initial_value', nargs=4, default=[],
                    action='append',
                    metavar=('PORT', 'STATE-VARIALBE', 'VALUE', 'UNITS'),
                    help=("Initial regime for dynamics"))


def run(argv):
    """
    Runs the simulation script from the provided arguments
    """
    import nineml
    import ninemlcatalog
    from nineml import units as un
    from pype9.exceptions import Pype9UsageError
    import neo.io

    args = parser.parse_args(argv)

    if args.simulator == 'neuron':
        from pype9.neuron import Network, CellMetaClass, simulation_controller  # @UnusedImport @IgnorePep8
    elif args.simulator == 'nest':
        from pype9.nest import Network, CellMetaClass, simulation_controller  # @Reimport @IgnorePep8
    else:
        raise Pype9UsageError(
            "Unrecognised simulator '{}', (available 'neuron' or 'nest')"
            .format(args.simulator))

    # Load the model from the provided arguments
    if args.model_file.startswith('//'):
        doc = ninemlcatalog.load(args.model_file[2:])
    else:
        doc = nineml.read(args.model_file)
    if args.dynamics is not None:
        # Simulate a dynamics object instead of a network
        model = doc[args.name]
    else:
        if len(list(doc.network_structures)):
            model = doc.as_network()
        else:
            dyn_props = [p for p in doc.components
                         if isinstance(p, nineml.DynamicsProperties)]
            if len(dyn_props) == 1:
                model = dyn_props[0]
            elif len(dyn_props) >= 2:
                raise Pype9UsageError(
                    "No network structures (i.e. Population, Projection, "
                    "Selection) and more than one dynamics properties found "
                    "in '{}' document, please specify one with the '--model' "
                    "argument.".format(args.model_file))
            else:
                dyns = [d for d in doc.component_classes
                        if isinstance(d, nineml.Dynamics)]
                if len(dyns) == 1:
                    model = dyns[0]
                elif len(dyns) >= 2:
                    raise Pype9UsageError(
                        "No network structures (i.e. Population, Projection, "
                        "Selection) or dynamics properties and more than one "
                        "dynamics found in '{}' document, please specify one "
                        "with the '--model' argument."
                        .format(args.model_file))
                else:
                    raise Pype9UsageError(
                        "No network structures (i.e. Population, Projection, "
                        "Selection) dynamics or dynamics properties found in "
                        "'{}' docuemnt.".format(args.model_file))

    if isinstance(model, nineml.Network):
        pass
    else:
        assert isinstance(model, (nineml.DynamicsProperties,
                                  nineml.Dynamics))
        if args.prop:
            props = dict((parm, float(val), getattr(un, unts))
                         for parm, val, unts in args.prop)
            model = nineml.DynamicsProperties(
                model.name + '_props', model, props)
        if not isinstance(model, nineml.DynamicsProperties):
            raise Pype9UsageError(
                "Specified model {} is not a dynamics properties object"
                .format(model))
        component_class = model.component_class
        initial_regime = args.initial_regime
        if initial_regime is None:
            if component_class.num_regimes == 1:
                initial_regime = next(component_class.regimes)
            else:
                raise Pype9UsageError(
                    "Need to specify initial regime as dynamics has more than "
                    "one '{}'".format("', '".join(
                        r.name for r in component_class.regimes)))
        # Build cell class
        Cell = CellMetaClass(model.component_class, name=model.name,
                                  initial_regime=initial_regime)
        # Create cell
        cell = Cell(model)
        initial_state = dict((sv, float(val), getattr(un, units))
                              for sv, val, units in args.initial_value)
        if set(cell.state_variable_names) != set(initial_state.iterkeys()):
            raise Pype9UsageError(
                "Need to specify an initial value for each state in the model,"
                " missing '{}'".format(
                    "', '".join(set(cell.state_variable_names) -
                                set(initial_state.iterkeys()))))
        cell.update_state(initial_state)
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
                description="Simulation of '{}' cell".format(model.name))
        for port_name, fname, _ in args.record:
            data = cell.recording(port_name)
            if isinstance(data, neo.AnalogSignal):
                data_segs[fname].analogsignals.append(data)
            else:
                data_segs[fname].spiketrains.append(data)
        # Write data to file
        for fname, data_seg in data_segs.iteritems():
            neo.io.PickleIO(fname).write(data_seg)
        print "Simulated '{}' for {} ms".format(model.name, args.time)
