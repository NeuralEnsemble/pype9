"""
Simulates a single cell defined by a 9ML Dynamics or DynamicsProperties, or a
complete 9ML network, using either Neuron_ or NEST_ as the simulator backend.

Send ports and state-variables of the simulation can be recorded and saved to
file in Neo_ format using the '--record' option, e.g.::

    $ pype9 simulate my_cell.xml nest 100.0 0.01 \\
      --record my_event_port ~/my_even_port.neo.pkl

For single-cell simulations, analog and event inputs stored in Neo_ format
can be "played" into ports of the Dynamics class using the '--play' option
e.g.::

    $ pype9 simulate my_cell.xml nest 100.0 0.01 \\
      --record my_event_port data-dir/my_even_port.neo.pkl \\
      --play my_analog_receive_port data-dir/my_input_current.neo.pkl


Properties, initial values and the initial regime (for single cells) can be
overridden with the '--prop', '--initial_value' and '--initial_regime'
respectively and must be provided for every parameter/state-variable if they
are not in the model description file.
"""
from argparse import ArgumentParser
from nineml import units as un
from pype9.simulate.common.cells.code_gen import BaseCodeGenerator
from ._utils import nineml_model, parse_units, logger


def argparser():
    parser = ArgumentParser(prog='pype9 simulate',
                            description=__doc__)
    parser.add_argument('model', type=nineml_model,
                        help=("Path to nineml model file which to simulate. "
                              "It can be a relative path, absolute path, URL "
                              "or if the path starts with '//' it will be "
                              "interpreted as a ninemlcatalog path. For files "
                              "with multiple components, the name of component"
                              " to simulated must be appended after a #, "
                              "e.g. //neuron/izhikevich#izhikevich"))
    parser.add_argument('simulator', choices=('neuron', 'nest'), type=str,
                        help="Which simulator backend to use")
    parser.add_argument('time', type=float,
                        help="Time to run the simulation for")
    parser.add_argument('timestep', type=float,
                        help=("Timestep used to solve the differential "
                              "equations"))
    parser.add_argument('--prop', nargs=3, action='append',
                        metavar=('PARAM', 'VALUE', 'UNITS'), default=[],
                        help=("Set the property to the given value"))
    parser.add_argument('--build_name', type=str, default=None,
                        help="Name to use when building component classes")
    parser.add_argument('--init_regime', type=str, default=None,
                        help=("Initial regime for dynamics"))
    parser.add_argument('--init_value', nargs=3, default=[], action='append',
                        metavar=('STATE-VARIABLE', 'VALUE', 'UNITS'),
                        help=("Initial regime for dynamics"))
    parser.add_argument('--record', type=str, nargs=2, action='append',
                        default=[],
                        metavar=('PORT/STATE-VARIABLE', 'FILENAME'),
                        help=("Record the values from the send port or state "
                              "variable and the filename to save it into"))
    parser.add_argument('--play', type=str, nargs=2, action='append',
                        metavar=('PORT', 'FILENAME'), default=[],
                        help=("Name of receive port and filename with signal "
                              "to play it into"))
    parser.add_argument('--seed', type=int, default=None,
                        help=("Random seed used to create network and "
                              "properties"))
    parser.add_argument('--properties_seed', type=int, default=None,
                        help=("Random seed used to create network connections "
                              "and properties. If not provided it is generated"
                              " from the '--seed' option."))
    parser.add_argument('--build_mode', type=str, default='lazy',
                        help=("The strategy used to build and compile the "
                              "model. Can be one of '{}' (default %(default)s)"
                              .format("', '".join(
                                  BaseCodeGenerator.BUILD_MODE_OPTIONS))))
    return parser


def run(argv):
    """
    Runs the simulation script from the provided arguments
    """
    import nineml
    from pype9.exceptions import Pype9UsageError
    import neo.io

    args = argparser().parse_args(argv)

    if args.simulator == 'neuron':
        from pype9.simulate.neuron import Network, CellMetaClass, Simulation  # @UnusedImport @IgnorePep8
    elif args.simulator == 'nest':
        from pype9.simulate.nest import Network, CellMetaClass, Simulation  # @Reimport @IgnorePep8
    else:
        assert False

    if not args.record:
        raise Pype9UsageError(
            "No recorders set, please specify at least one with the '--record'"
            " option")

    # Check for clashing record paths
    record_paths = [fname for _, fname in args.record]
    for pth in record_paths:
        if record_paths.count(pth) > 1:
            raise Pype9UsageError(
                "Duplicate record paths '{}' given to separate '--record' "
                "options".format(pth))

    # For convenience
    model = args.model

    if isinstance(model, nineml.Network) and not model.num_projections:
        raise Pype9UsageError(
            "Provided network model '{}' (may have been implicitly created "
            "from complete document) does not contain any projections"
            .format(model))

    if isinstance(model, nineml.Network):
        with Simulation(dt=args.timestep * un.ms, seed=args.seed,
                        properties_seed=args.properties_seed,
                        **model.delay_limits()) as sim:
            # Construct the network
            logger.info("Constructing network")
            network = Network(model, build_mode=args.build_mode)
            logger.info("Finished constructing the '{}' network"
                        .format(model.name))
            for record_name, _ in args.record:
                pop_name, port_name = record_name.split('.')
                network.component_array(pop_name).record(port_name)
            logger.info("Running the simulation")
            sim.run(args.time * un.ms)
        logger.info("Writing recorded data to file")
        for record_name, fname in args.record:
            pop_name, port_name = record_name.split('.')
            pop = network.component_array(pop_name)
            neo.PickleIO(fname).write(pop.recording(port_name))
    else:
        assert isinstance(model, (nineml.DynamicsProperties, nineml.Dynamics))
        # Override properties passed as options
        if args.prop:
            props_dict = dict((parm, float(val) * parse_units(unts))
                              for parm, val, unts in args.prop)
            props = nineml.DynamicsProperties(
                model.name + '_props', model, props_dict)
            component_class = model
        elif isinstance(model, nineml.DynamicsProperties):
            props = model
            component_class = model.component_class
        else:
            raise Pype9UsageError(
                "Specified model {} is not a dynamics properties object and "
                "no properties supplied to simulate command via --prop option"
                .format(model))
        # Get the initial state
        init_state = dict((sv, float(val) * parse_units(units))
                          for sv, val, units in args.init_value)
        # Get the init_regime
        init_regime = args.init_regime
        if init_regime is None:
            if component_class.num_regimes == 1:
                # If there is only one regime it doesn't need to be specified
                init_regime = next(component_class.regimes).name
            else:
                raise Pype9UsageError(
                    "Need to specify initial regime as dynamics has more than "
                    "one '{}'".format("', '".join(
                        r.name for r in component_class.regimes)))
        # FIXME: A bit of a hack until better detection of input currents is
        #        implemented in neuron code gen.
        external_currents = []
        for port_name, _ in args.play:
            if component_class.port(port_name).dimension == un.current:
                external_currents.append(port_name)
        # Build cell class
        Cell = CellMetaClass(component_class, name=args.build_name,
                             build_mode=args.build_mode,
                             external_currents=external_currents)
        record_regime = False
        with Simulation(dt=args.timestep * un.ms, seed=args.seed) as sim:
            # Create cell
            cell = Cell(props, regime_=init_regime, **init_state)
            # Play inputs
            for port_name, fname in args.play:
                port = component_class.receive_port(port_name)
                seg = neo.io.PickleIO(filename=fname).read()[0]
                if port.communicates == 'event':
                    signal = seg.spiketrains[0]
                else:
                    signal = seg.analogsignals[0]
                # Input is an event train or analog signal
                cell.play(port_name, signal)
            # Set up recorders
            for port_name, _ in args.record:
                if (component_class.num_regimes > 1 and component_class.port(
                        port_name).communicates == 'analog'):
                    record_regime = True
                cell.record(port_name)
            if record_regime:
                cell.record_regime()
            # Run simulation
            sim.run(args.time * un.ms)
        # Collect data into Neo Segments
        fnames = set(r[1] for r in args.record)
        data_segs = {}
        for fname in fnames:
            data_segs[fname] = neo.Segment(
                description="Simulation of '{}' cell".format(model.name))
        for port_name, fname in args.record:
            data = cell.recording(port_name)
            if isinstance(data, neo.AnalogSignal):
                data_segs[fname].analogsignals.append(data)
            else:
                data_segs[fname].spiketrains.append(data)
            if record_regime:
                data_segs[fname].epocharrays.append(cell.regime_epochs())
        # Write data to file
        for fname, data_seg in data_segs.iteritems():
            neo.io.PickleIO(fname).write(data_seg)
    logger.info("Finished simulation of '{}' for {} ms".format(model.name,
                                                               args.time))
