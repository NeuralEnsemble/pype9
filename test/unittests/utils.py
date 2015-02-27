from os.path import dirname, join

test_data_dir = join(dirname(__file__), '..', 'data')


class DummyTestCase(object):

    def __init__(self):
        try:
            self.setUp()
        except AttributeError:
            pass

    def __del__(self):
        try:
            self.tearDown()
        except AttributeError:
            pass

    def assertEqual(self, first, second):
        print '{} and {} are{} equal'.format(repr(first), repr(second),
                                             ' not' if first != second else '')
