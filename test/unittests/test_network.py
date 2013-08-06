# try:
#     import unittest2 as unittest
# except ImportError:
#     import unittest

import nineml.user_layer


# class TestNetworkRead(unittest.TestCase):
    
if __name__ == '__main__':    
    nineml.user_layer.parse('/home/tclose/kbrain/xml/9ml/networks/fabios_network.xml')
    print "done"