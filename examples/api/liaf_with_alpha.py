#!/usr/bin/env python
"""
Constructs a leaky integrate and fire model with an alpha synapse and connects
it to an input source that fires spikes at a constant rate
"""
from __future__ import division
import sys
from argparse import ArgumentParser
from nineml import units as un, MultiDynamics, Property
from pype9.simulate.common.cells import WithSynapses, ConnectionParameterSet
import ninemlcatalog
from pype9.plot import plot
import pype9.utils.logger_handlers.sysout_info  # @UnusedImport


def argparser():
    parser = ArgumentParser(__doc__)
    parser.add_argument('--simulator', type=str, default='nest',
                        help=("The simulator used to run the simulation "
                              "(either 'nest' or (neuron')."))
    parser.add_argument('--timestep', type=float, default=0.01,
                        help=("Timestep of the simulation"))
    parser.add_argument('--weight', type=float, default=750.0,
                        help=("Weight of the synapse (nA)"))
    parser.add_argument('--threshold', type=float, default=20.0,
                        help="The voltage threshold (mV) for spike output")
    parser.add_argument('--rate', type=float, default=40.0,
                        help=("Rate of the input spike train (Hz)"))
    parser.add_argument('--tau', type=float, default=75,
                        help=("Tau parameter of the LIAF model (ms)"))
    parser.add_argument('--delay', type=float, default=1.0,
                        help=("The delay betweeen the input and cell (ms)"))
    parser.add_argument('--simtime', type=float, default=200.0,
                        help=("Simulation time (ms)"))
    parser.add_argument('--build_mode', type=str, default='lazy',
                        help=("The build mode to apply when creating the cell "
                              "class"))
    parser.add_argument('--connection_weight', action='store_true',
                        default=False,
                        help=("Whether weight should be a parameter of the "
                              "cell or passed as a weight"))
    parser.add_argument('--save_fig', type=str, default=None,
                        help=("Location to save the generated figures"))
    return parser


def run(argv):
    args = argparser().parse_args(argv)

    delay = args.delay * un.ms

    # Import of nest needs to be after arguments have been passed as it kills
    # them before the SLI interpreter tries to read them.
    if args.simulator == 'nest':
        from pype9.simulate.nest import CellMetaClass, Simulation  # @IgnorePep8 @UnusedImport
    elif args.simulator == 'neuron':
        from pype9.simulate.neuron import CellMetaClass, Simulation  # @IgnorePep8 @Reimport
    else:
        raise Exception("Unrecognised simulator '{}' (can be either 'nest' or "
                        "'neuron')".format(args.simulator))

    # Get and combine 9ML models
    input_model = ninemlcatalog.load(
        'input/ConstantRate', 'ConstantRate')
    liaf_model = ninemlcatalog.load(
        'neuron/LeakyIntegrateAndFire', 'LeakyIntegrateAndFire')
    alpha_model = ninemlcatalog.load(
        'postsynapticresponse/Alpha', 'Alpha')
    weight_model = ninemlcatalog.load(
        'plasticity/Static', 'Static')
    multi_model = MultiDynamics(
        name="test_alpha_syn",
        sub_components={'cell': liaf_model, 'psr': alpha_model,
                        'pls': weight_model},
        port_connections=[('psr', 'i_synaptic', 'cell', 'i_synaptic'),
                          ('pls', 'fixed_weight', 'psr', 'weight')],
        port_exposures=[('psr', 'input_spike'), ('cell', 'spike_output')])
    # Add connection weight
    conn_params = []
    if args.connection_weight:
        conn_params.append(ConnectionParameterSet(
            'input_spike__psr', [multi_model.parameter('weight__pls')]))

    # Reinterpret the multi-component model as one containing synapses that can
    # be set by connection weights
    w_syn_model = WithSynapses.wrap(multi_model,
                                    connection_parameter_sets=conn_params)
    # Generate Pype9 classes
    Input = CellMetaClass(input_model, build_mode=args.build_mode)
    Cell = CellMetaClass(w_syn_model, build_mode=args.build_mode)
    # Create instances
    rate = args.rate * un.Hz
    weight = args.weight * un.nA
    cell_params = {
        'tau__cell': args.tau * un.ms,
        'R__cell': 1.5 * un.Mohm,
        'refractory_period__cell': 2.0 * un.ms,
        'v_threshold__cell': args.threshold * un.mV,
        'v_reset__cell': 0.0 * un.mV,
        'tau__psr': 0.5 * un.ms,
        'regime_': 'subthreshold___sole___sole',
        'b__psr': 0.0 * un.nA,
        'a__psr': 0.0 * un.nA,
        'v__cell': 0.0 * un.mV,
        'refractory_end__cell': 0.0 * un.ms}
    # If PSR weight is part of the cell dynamics (as opposed to the connection)
    if args.connection_weight:
        conn_properties = [Property('weight__pls', weight)]
    else:
        cell_params['weight__pls'] = weight
        conn_properties = []
    with Simulation(args.timestep * un.ms, min_delay=delay) as sim:
        input = Input(rate=rate, t_next=(1 * un.unitless) / rate)  # @ReservedAssignment @IgnorePep8
        cell = Cell(**cell_params)
        # Connect cells together
        cell.connect(input, 'spike_output', 'input_spike__psr',
                     delay, properties=conn_properties)
        # Set up recorders
        cell.record('spike_output__cell')
        cell.record_regime()
        cell.record('v__cell')
        # Run simulation
        sim.run(args.simtime * un.ms)
    # Plot recordings
    plot(cell.recordings(), save=args.save_fig, show=(not args.save_fig),
         title='Leaky Integrate and Fire with Alpha Synapse')
    print("Finished simulation.")


if __name__ == '__main__':
    run(sys.argv[1:])
