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


def run(argv):
    import numpy
    import quantities as pq
    import neo
    args = parser.parse_args(argv)

    segment = neo.Segment()
    if args.input_type == 'step':
        num_preceding = int(numpy.floor(start_time / dt))
        num_remaining = int(numpy.ceil((duration - start_time) / dt))
        amplitude = float(pq.Quantity(amplitude, 'nA'))
        signal = neo.AnalogSignal(
            numpy.concatenate((numpy.zeros(num_preceding),
                               numpy.ones(num_remaining) * amplitude)),
            sampling_period=dt * pq.ms, units='nA', time_units='ms')
        segment.analogsignals.append(signal)
    elif args.input_type == 'constant_freq':
        isi = 1 / float(pq.Quantity(freq, 'kHz'))
        if offset is None:
            isi = offset
        train = neo.SpikeTrain(
            numpy.arange(offset, duration, isi),
            units='ms', t_stop=duration * pq.ms)
        segment.spiketrains.append(train)
    # Write segment to file
    neo.PickleIO(args.output_file).write(segment)
