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
from builtins import next
import collections
from argparse import ArgumentParser
from nineml import units as un
from pype9.simulate.common.code_gen import BaseCodeGenerator
import quantities as pq
from pype9.utils.arguments import nineml_model
from pype9.utils.units import parse_units
from pype9.utils.logging import logger

RecordSpec = collections.namedtuple('RecordSpec', 'port fname t_start')


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
                        help="Time to run the simulation for (ms)")
    parser.add_argument('timestep', type=float,
                        help=("Timestep used to solve the differential "
                              "equations (ms)"))
    parser.add_argument('--prop', nargs=3, action='append',
                        metavar=('PARAM', 'VALUE', 'UNITS'), default=[],
                        help=("Set the property to the given value"))
    parser.add_argument('--init_regime', type=str, default=None,
                        help=("Initial regime for dynamics"))
    parser.add_argument('--init_value', nargs=3, default=[], action='append',
                        metavar=('STATE-VARIABLE', 'VALUE', 'UNITS'),
                        help=("Initial regime for dynamics"))
    parser.add_argument('--record', type=str, nargs='+', action='append',
                        default=[],
                        help=("Record the values from the send port or state "
                              "variable and the filename to save it into. "
                              "Each record option can have either 2 or 4 "
                              "arguments: PORT/STATE-VARIABLE FILENAME "
                              "[T_START T_START_UNITS]"))
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
    parser.add_argument('--min_delay', nargs=2, metavar=('DELAY', 'UNITS'),
                        default=None,
                        help=("The minimum delay of the model (only "
                              "applicable for single cell NEST simulations)"))
    parser.add_argument('--device_delay', nargs=2, metavar=('DELAY', 'UNITS'),
                        default=None,
                        help=("The delay applied to signals played into ports "
                              "of the model (only applicable for NEST "
                              "simulations)"))
    parser.add_argument('--build_mode', type=str, default='lazy',
                        help=("The strategy used to build and compile the "
                              "model. Can be one of '{}' (default %(default)s)"
                              .format("', '".join(
                                  BaseCodeGenerator.BUILD_MODE_OPTIONS))))
    parser.add_argument('--build_dir', default=None, type=str,
                        help=("Base build directory"))
    parser.add_argument('--build_version', type=str, default=None,
                        help=("Version to append to name to use when building "
                              "component classes"))
    return parser


def run(argv):
    """
    Runs the simulation script from the provided arguments
    """
    import nineml
    from pype9.exceptions import Pype9UsageError
    import neo.io

    args = argparser().parse_args(argv)

    time = args.time * un.ms
    timestep = args.timestep * un.ms

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

    min_delay = (float(args.min_delay[0]) *
                    parse_units(args.min_delay[1])
                    if args.min_delay is not None else 1.0 * un.ms)

    device_delay = (float(args.device_delay[0]) *
                    parse_units(args.device_delay[1])
                    if args.device_delay is not None else None)

    # Parse record specs
    record_specs = []
    for rec in args.record:
        if len(rec) == 4:
            rec_t_start = pq.Quantity(float(rec[2]), rec[3])
        elif len(rec) == 2:
            rec_t_start = None
        else:
            raise Pype9UsageError(
                "Record options can be passed either have 2 or 4 (provided {})"
                ": PORT/STATE-VARIABLE FILENAME [T_START T_START_UNITS]")
        record_specs.append(RecordSpec(rec[0], rec[1], rec_t_start))

    # Check for clashing record paths
    record_paths = [r.fname for r in record_specs]
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
        with Simulation(dt=timestep, seed=args.seed,
                        properties_seed=args.properties_seed,
                        device_delay=device_delay,
                        **model.delay_limits()) as sim:
            # Construct the network
            logger.info("Constructing network")
            network = Network(model, build_mode=args.build_mode,
                              build_base_dir=args.build_dir)
            logger.info("Finished constructing the '{}' network"
                        .format(model.name))
            for rspec in record_specs:
                pop_name, port_name = rspec.port.split('.')
                network.component_array(pop_name).record(port_name)
            logger.info("Running the simulation")
            sim.run(time)
        logger.info("Writing recorded data to file")
        for rspec in record_specs:
            pop_name, port_name = rspec.port.split('.')
            pop = network.component_array(pop_name)
            neo.PickleIO(rspec.fname).write(pop.recording(
                port_name, t_start=rspec.t_start))
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
        Cell = CellMetaClass(component_class,
                             build_mode=args.build_mode,
                             external_currents=external_currents,
                             build_version=args.build_version,
                             build_base_dir=args.build_dir)
        record_regime = False
        with Simulation(dt=timestep, seed=args.seed,
                        min_delay=min_delay,
                        device_delay=device_delay,
                        build_base_dir=args.build_dir) as sim:
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
                logger.info("Playing signal (t_start: {}, t_stop: {}, dt: {}) "
                            "into port '{}"
                            .format(signal.t_start, signal.t_stop,
                                    signal.sampling_period, port_name))
                # Input is an event train or analog signal
                cell.play(port_name, signal)
            # Set up recorders
            for rspec in record_specs:
                if (component_class.num_regimes > 1 and component_class.port(
                        rspec.port).communicates == 'analog'):
                    record_regime = True
                cell.record(rspec.port, t_start=rspec.t_start)
            if record_regime:
                cell.record_regime()
            # Run simulation
            sim.run(time)
        # Collect data into Neo Segments
        fnames = set(r.fname for r in record_specs)
        data_segs = {}
        for fname in fnames:
            data_segs[fname] = neo.Segment(
                description="Simulation of '{}' cell".format(model.name))
        for rspec in record_specs:
            data = cell.recording(rspec.port, t_start=rspec.t_start)
            if isinstance(data, neo.AnalogSignal):
                data_segs[rspec.fname].analogsignals.append(data)
            else:
                data_segs[rspec.fname].spiketrains.append(data)
            if record_regime:
                data_segs[rspec.fname].epochs.append(cell.regime_epochs())
        # Write data to file
        for fname, data_seg in data_segs.items():
            neo.io.PickleIO(fname).write(data_seg)
    logger.info("Finished simulation of '{}' for {}".format(model.name, time))
