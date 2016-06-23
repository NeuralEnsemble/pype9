"""
Command that compares a 9ML model with an existing version in NEURON and/or
NEST
"""
import argparse
import pyNN.neuron  # @UnusedImport - imports PyNN mechanisms
try:
    import pylab as plt
except ImportError:
    plt = None
import neo
import nineml
from pype9.exceptions import Pype9RuntimeError
from pype9.testing import Comparer


parser = argparse.ArgumentParser(__doc__)
parser.add_argument('nineml', type=str, nargs="*", default=None,
                    help=("The 9ML model to compare plus the simulators to"
                          " simulate it in (path, simulator1, "
                          "simulator2...)"))
parser.add_argument('--model_name', type=str, default=None,
                    help="The name of the model to select within the file")
parser.add_argument('--nest_ref', type=str, default=None,
                    help="The name of the nest model to compare against")
parser.add_argument('--neuron_ref', type=str, default=None,
                    help="The name of the NEURON model to compare against")
parser.add_argument('--dt', type=float, default=0.01,
                    help="The simulation timestep (ms)")
parser.add_argument('--state_variable', type=str, default='v',
                    help="The variable to compare")
parser.add_argument('--plot', action='store_true',
                    help="Plot the simulations")
parser.add_argument('--parameter', '-p', nargs=2, action='append',
                    help="A parameter name/value pair",
                    metavar=('NAME', 'VALUE'), default=[])
parser.add_argument('--initial_state', '-i', nargs=2, action='append',
                    help="An initial state name/value pair",
                    metavar=('NAME', 'VALUE'), default=[])
parser.add_argument('--duration', type=float, default=100.0,
                    help="Duration of the simulation (ms)")
parser.add_argument('--nest_trans', '-s', nargs=3, action='append',
                    help=("A translation for a parameter or state to the "
                          "name/scale used in the nest model"),
                    metavar=('OLD', 'NEW', 'SCALE'), default=[])
parser.add_argument('--neuron_trans', '-u', nargs=3, action='append',
                    help=("A translation for a parameter or state to the "
                          "name/scale used in the neuron model"),
                    metavar=('OLD', 'NEW', 'SCALE'), default=[])
parser.add_argument('--input_signal', type=str, nargs=2, default=None,
                    help=("Port name and path to the analog signal to "
                          "inject"), metavar=('PORT', 'NEO_FILE'))
parser.add_argument('--input_train', type=str, nargs=2, default=None,
                    help=("Port name and path to the event train to "
                          "inject"), metavar=('PORT', 'NEO_FILE'))
parser.add_argument('--input_step', type=str, nargs=3, default=None,
                    help=("Instead of a input signal, specify a simple "
                          "step function (port_name, start, amplitude)"),
                    metavar=('PORT', 'START_TIME', 'AMPLITUDE'))
parser.add_argument('--input_freq', type=str, nargs=2, default=None,
                    help=("Instead of a input train, specify a simple "
                          "input event frequency (port_name, frequency)"),
                    metavar=('PORT', 'FREQUENCY'))
parser.add_argument('--build_arg', '-b', nargs=3, action='append',
                    default=[], metavar=('SIMULATOR', 'NAME', 'VALUE'),
                    help=("Any build arg that should be passed to the 9ML"
                          "metaclass (simulator, name, value)"))
parser.add_argument('--min_delay', type=float, default=0.2,
                    help="Minimum delay used for the simulation")
parser.add_argument('--max_delay', type=float, default=10.0,
                    help="Minimum delay used for the simulation")
args = parser.parse_args()

if args.nineml is None and args.neuron is None and args.nest is None:
    raise Pype9RuntimeError("No simulations specified")
if args.nineml is not None:
    nineml_file = args.nineml[0]
    simulators = args.nineml[1:]
    nineml_doc = nineml.read(nineml_file)
    if args.model_name:
        nineml_model = nineml_doc[args.model_name]
    else:
        # Guess the desired nineml component from the file (if there is
        # only one component in the file)
        components = list(nineml_doc.components)
        if len(components) == 1:
            nineml_model = components[0]
        elif len(components) == 0:
            component_classes = list(nineml_doc.component_classes)
            if len(component_classes) == 1:
                nineml_model = component_classes[0]
            else:
                raise Pype9RuntimeError(
                    "Multiple component classes found in '{}' file, need to "
                    "specify the --model_name parameter")
        else:
            raise Pype9RuntimeError(
                "Multiple components found in '{}' file, need to specify the "
                "--model_name parameter")
else:
    # If the user only wants to run the reference model
    nineml_model = None
    simulators = []
parameters = dict((k, float(v)) for k, v in args.parameter)
initial_states = dict((k, float(v)) for k, v in args.initial_state)
nest_translations = dict((o, ((n if n != '__none__' else None), float(s)))
                         for o, n, s in args.nest_trans)
neuron_translations = dict((o, ((n if n != '__none__' else None), float(s)))
                           for o, n, s in args.neuron_trans)
neuron_build_args = dict((k, v) for s, k, v in args.build_arg
                         if s.lower() == 'neuron')
nest_build_args = dict((k, v) for s, k, v in args.build_arg
                         if s.lower() == 'nest')
if args.input_signal is not None:
    if args.input_step is not None:
        raise Pype9RuntimeError(
            "Cannot use '--input_signal' and '--input_step' simultaneously")
    port_name, fpath = args.input_signal
    block = neo.PickleIO(fpath).read()
    input_signal = (port_name, block[0])
elif args.input_step is not None:
    port_name, start_time, amplitude = args.input_step
    input_signal = Comparer.input_step(port_name, amplitude, start_time,
                                       args.duration, args.dt)
else:
    input_signal = None
if args.input_train is not None:
    if args.input_freq is not None:
        raise Pype9RuntimeError(
            "Cannot use '--input_train' and '--input_freq' simultaneously")
    port_name, fpath = args.input_train
    block = neo.PickleIO(fpath).read()
    input_train = (port_name, block[0])
elif args.input_freq is not None:
    train = Comparer.input_train(*args.input_freq)
else:
    input_train = None
comparer = Comparer(nineml_model=nineml_model, parameters=parameters,
                    state_variable=args.state_variable,
                    simulators=simulators, dt=args.dt,
                    initial_states=initial_states,
                    neuron_ref=args.neuron_ref, nest_ref=args.nest_ref,
                    input_signal=input_signal, input_train=input_train,
                    nest_translations=nest_translations,
                    neuron_translations=neuron_translations,
                    neuron_build_args=neuron_build_args,
                    nest_build_args=nest_build_args,
                    min_delay=args.min_delay, max_delay=args.max_delay)
comparer.simulate(args.duration)
for (name1, name2), diff in comparer.compare().iteritems():
    print "Average error between {} and {}: {}".format(name1, name2, diff)
if args.plot:
    comparer.plot()
