import os.path
import nineml
import ninemlcatalog
from argparse import ArgumentTypeError


def existing_file(fname):
    if not os.path.isfile(fname):
        raise ArgumentTypeError(
            "'{}' does not refer to an existing file".format(fname))
    return fname


def nineml_model(model_path):
    if model_path.startswith('//'):
        model = ninemlcatalog.load(model_path[2:])
    else:
        model = nineml.read(model_path)
        if isinstance(model, nineml.Document):
            model = model.as_network()
    return model
