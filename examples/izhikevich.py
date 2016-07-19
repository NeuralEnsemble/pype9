import os.path
from argparse import ArgumentParser
import ninemlcatalog
import quantities as pq
import numpy as np
import neo
import matplotlib

device_delay = 0.1
dt = 0.001


def construct_reference(input_signal):
    params = {
        'C_m': 1.0,
        'a': 0.2,
        'alpha': 0.04,
        'b': 0.025,
        'beta': 5.0,
        'c': -75.0,
        'd': 0.2,
        'theta': -50.0,
        'zeta': 140.0,
        'U': -1.625,
        'V': -70.0}
    cell = nest.Create('izhikevich', 1, params)
    generator = nest.Create(
        'step_current_generator', 1,
        {'amplitude_values': pq.Quantity(input_signal, 'pA'),
         'amplitude_times': (pq.Quantity(input_signal.times, 'ms') -
                             device_delay * pq.ms),
         'start': float(pq.Quantity(input_signal.t_start, 'ms')),
         'stop': float(pq.Quantity(input_signal.t_stop, 'ms'))})
    nest.Connect(generator, cell, syn_spec={'delay': device_delay})
    multimeter = nest.Create('multimeter', 1, {"interval": dt})
    nest.SetStatus(multimeter, {'record_from': ['V_m']})
    nest.Connect(multimeter, cell)
    return (cell, multimeter, generator)


def input_step(port_name, amplitude, start_time, duration, dt):
    num_preceding = int(np.floor(start_time / dt))
    num_remaining = int(np.ceil((duration - start_time) / dt))
    amplitude = float(pq.Quantity(amplitude, 'nA'))
    signal = neo.AnalogSignal(
        np.concatenate((np.zeros(num_preceding),
                        np.ones(num_remaining) * amplitude)),
        sampling_period=dt * pq.ms, units='nA', time_units='ms')
    return (port_name, signal)


parser = ArgumentParser()
parser.add_argument('--fast_spiking', action='store_true', default=False,
                    help=("Whether to use the \"fast-spiking\" version of the "
                          "Izhikevich neuron or not"))
parser.add_argument('--reference', action='store_true', default=False,
                    help=("Plot the trace of "))
parser.add_argument('--simtime', type=float, default=100.0,
                    help="The length of the simulation in ms")
parser.add_argument('--timestep', type=float, default=0.001,
                    help="Simulation timestep")
parser.add_argument('--simulators', type=str, nargs='+',
                    default=['neuron', 'nest'],
                    help="Which simulators to simulate the 9ML network")
parser.add_argument('--plot_start', type=float, default=0.0,
                    help=("The time to start plotting from"))
parser.add_argument('--build_mode', type=str, default='lazy',
                    help=("The build mode with which to construct the network."
                          " 'lazy' will only regenerate and compile the "
                          "source files if the network has changed, whereas "
                          "'force' will always rebuild the network"))
parser.add_argument('--seed', type=int, default=None,
                    help="Random seed passed to the simulators")
parser.add_argument('--reference', action='store_true', default=False,
                    help="Plot a reference NEST implementation alongside")
parser.add_argument('--save_fig', type=str, default=None,
                    help=("Location to save the generated figures"))
parser.add_argument('--figsize', nargs=2, type=float, default=(10, 15),
                    help="The size of the figures")
args = parser.parse_args()


if __name__ == "__main__":

    if args.save_fig is not None:
        matplotlib.use('pdf')
        save_path = os.path.abspath(args.save_fig)
        if not os.path.exists(save_path):
            os.mkdir(save_path)
    else:
        save_path = None
    # Needs to be imported after the args.save_fig argument is parsed to
    # allow the backend to be set
    from matplotlib import pyplot as plt  # @IgnorePep8

    pyNN_module = {}
    pype9_metaclass = {}
    pype9_controller = {}
    if 'neuron' in args.simulators:
        import pyNN.neuron  # @IgnorePep8
        from pype9.neuron import (CellMetaClass as CellMetaClassNEURON,
                                  simulation_controller as controllerNEURON)
        pyNN_module['neuron'] = pyNN.neuron
        pype9_controller['neuron'] = controllerNEURON
        pype9_metaclass['neuron'] = CellMetaClassNEURON
    if 'nest' in args.simulators or args.reference:
        import nest  # @IgnorePep8
        import pyNN.nest  # @IgnorePep8
        from pype9.nest import (CellMetaClass as CellMetaClassNEST,
                                simulation_controller as controllerNEST)
        pyNN_module['nest'] = pyNN.nest
        pype9_controller['nest'] = controllerNEST
        pype9_metaclass['nest'] = CellMetaClassNEST

    if args.fast_spiking:
        model = ninemlcatalog.load('neuron/Izhikevich',
                                   'IzhikevichFastSpiking')
        properties = ninemlcatalog.load('neuron/Izhikevich',
                                        'SampleIzhikevichFastSpiking')
        initial_regime = 'subVb'
        initial_states = {'U': -1.625 * pq.pA, 'V': -65.0 * pq.mV}
        input_signal = input_step('Isyn', 0.02, 50, 100, dt)
    else:
        model = ninemlcatalog.load('neuron/Izhikevich', 'Izhikevich')
        properties = ninemlcatalog.load('neuron/Izhikevich',
                                        'SampleIzhikevich')
        input_signal = input_step('iSyn', 100 * pq.pA, 25.0, 100, dt)
        initial_regime = 'default'
        initial_states = {'U': -14.0 * pq.mV / pq.ms, 'V': -65.0 * pq.mV}

    cells = {}
    for simulator in args.simulators:
        cells[simulator] = pype9_metaclass[simulator](
            model, name=model.name, default_properties=properties,
            initial_regime=initial_regime)()
        if not args.fast_spiking:
            cells[simulator].play(input_signal)
        cells[simulator].record('V')
        cells[simulator].update_state(initial_states)

    # Set of simulators to run
    simulator_to_run = set(args.simulators)

    if args.reference:
        ref_cell, ref_multi, ref_generator = construct_reference(input_signal)
        simulator_to_run.add('nest')

    # Run the simulation(s)
    for simulator in simulator_to_run:
        pyNN_module[simulator].run(args.simtime)

    # Plot the results
    print "Plotting the results"
    plt.figure(figsize=args.figsize)
    plt.title("Izhikevich{}".format(' Fast Spiking'
                                    if args.fast_spiking else ''), fontsize=14)
    legend = []
    for simulator in args.simulators:
        v = cells[simulator].recording('V')
        inds = v.times > args.plot_start
        plt.plot(v.times[inds], v[inds])
        legend.append(simulator.upper())
    if args.reference:
        events, interval = nest.GetStatus(
            ref_multi['V_m'], ["events", 'interval'])[0]
        t, v = np.asarray(events['times']), np.asarray(events['V_m'])
        inds = t > args.plot_start
        plt.plot(t[inds], v[inds])
        legend.append('Ref. NEST')
    plt.xlabel('Time (ms)')
    plt.ylabel('Membrane Voltage (mV)')
    plt.legend(legend)
    if save_path is not None:
        plt.savefig(save_path)
    else:
        plt.show()
    print "done"
