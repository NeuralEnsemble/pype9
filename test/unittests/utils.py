from os.path import dirname, join

test_data_dir = join(dirname(__file__), '..', 'data')


class DummyTestCase(object):

    def __init__(self):
        self.setUp()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def __del__(self):
        self.tearDown()

    def assertEqual(self, first, second, message=None):
        if first != second:
            if message is None:
                message = '{} and {} are not equal'.format(repr(first),
                                                           repr(second))
            print message

    def assertAlmostEqual(self, first, second, message=None):
        if first != second:
            if message is None:
                message = '{} and {} are not equal'.format(repr(first),
                                                           repr(second))
            print message

    def assertLess(self, first, second, message=None):
        if first >= second:
            if message is None:
                message = '{} is not less than {}'.format(repr(first),
                                                          repr(second))
            print message
