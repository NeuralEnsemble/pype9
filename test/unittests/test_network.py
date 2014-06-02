# try:
#     import unittest2 as unittest
# except ImportError:
#     import unittest

import nineml.user_layer


# class TestNetworkRead(unittest.TestCase):

if __name__ == '__main__':
    model = nineml.user_layer.parse(
        '/home/tclose/kbrain/xml/9ml/networks/fabios_network.xml')
    net = model.groups['Network']
    gr = net.populations['Granules']
    gg = net.projections['Granules_Golgis']

    print "done"
