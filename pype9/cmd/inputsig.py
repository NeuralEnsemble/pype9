"""
Creates a range of basic input signals for input into model simulations
"""
from argparse import ArgumentParser

input_types = ('step', 'constant_freq')

parser = ArgumentParser(description=__doc__)
parser.add_argument('output_file', type=str,
                    help=("Output file"))
parser.add_argument('input_type', type=str, choices=input_types,
                    help=("Type of signal to create. Can be one of '{}'."
                          .format("', '".join(input_types))))
parser.add_argument('duration', type=float,
                    help=("Duration of the input signal"))
parser.add_argument('--delay', type=float, default=0.0,
                    help=("Start time of the input when input_type is 'step'"))
parser.add_argument('--amplitude', type=float,
                    help=("Amplitude of the step when input_type is 'step'"))
parser.add_argument('--freq', type=float, default=None,
                    help=("Frequency of the input events"))
parser.add_argument('--dt', type=float, default=None,
                    help=("Time step of the analog signal generated"))


def run(argv):
    import numpy
    import quantities as pq
    import neo
    args = parser.parse_args(argv)

    segment = neo.Segment()
    if args.input_type == 'step':
        num_preceding = int(numpy.floor(args.delay / args.dt))
        num_remaining = int(numpy.ceil((args.duration - args.delay) / args.dt))
        amplitude = float(pq.Quantity(args.amplitude, 'nA'))
        signal = neo.AnalogSignal(
            numpy.concatenate((numpy.zeros(num_preceding),
                               numpy.ones(num_remaining) * amplitude)),
            sampling_period=args.dt * pq.ms, units='nA', time_units='ms')
        segment.analogsignals.append(signal)
    elif args.input_type == 'constant_freq':
        isi = 1 / float(pq.Quantity(args.freq, 'kHz'))
        offset = args.delay if args.delay is not None else isi
        train = neo.SpikeTrain(
            numpy.arange(offset, args.duration, isi),
            units='ms', t_stop=args.duration * pq.ms)
        segment.spiketrains.append(train)
    # Write segment to file
    neo.PickleIO(args.output_file).write(segment)
