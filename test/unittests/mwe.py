import nest
import quantities as pq
import neo
import matplotlib.pyplot as plt


nest.SetKernelStatus({'resolution': 0.02})
cell = nest.Create('izhikevich', 1,
                   {'a': 0.02, 'c': -65.0, 'b': 0.2, 'd': 2.0})
iclamp = nest.Create(
    'dc_generator', 1,
    {'start': float(5),
     'stop': float(10),
     'amplitude': float(20.0)})
nest.Connect(iclamp, cell)
multimeter = nest.Create('multimeter', 1,
                         {"interval": 0.02})
nest.SetStatus(multimeter,
               {'record_from': ['V_m']})
nest.Connect(multimeter, cell)
nest.SetStatus(cell, {'V_m': float(65.0), 'U_m': 14.0})
nest.Simulate(10)
signal = neo.AnalogSignal(nest.GetStatus(multimeter, 'events')[0]['V_m'],
                          sampling_period=0.02 * pq.ms, units='mV')
plt.plot(pq.Quantity(signal.times, 'ms'), pq.Quantity(signal, 'mV'))
plt.show()
