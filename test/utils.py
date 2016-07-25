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

    def assertEqual(self, first, second, msg=None):
        if first != second:
            if msg is None:
                msg = '{} and {} are not equal'.format(repr(first),
                                                       repr(second))
            print msg

    def assertAlmostEqual(self, first, second, places=None, msg=None):
        if places is None:
            places = 7
        if abs(first - second) > 10 ** -places:
            if msg is None:
                msg = '{} and {} are not equal'.format(repr(first),
                                                       repr(second))
            print msg

    def assertLess(self, first, second, msg=None):
        if first >= second:
            if msg is None:
                msg = '{} is not less than {}'.format(repr(first),
                                                      repr(second))
            print msg

    def assertLessEqual(self, first, second, msg=None):
        if first > second:
            if msg is None:
                msg = '{} is not less than or equal to {}'.format(
                    repr(first), repr(second))
            print msg
