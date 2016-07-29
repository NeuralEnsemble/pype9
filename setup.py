#!/usr/bin/env python
import os.path
from setuptools import setup, find_packages  # @UnresolvedImport

# Generate the package data
package_name = 'pype9'
package_dir = os.path.join(os.path.dirname(__file__), package_name)
package_data = []
prefix_len = len(package_dir) + 1
for path, dirs, files in os.walk(package_dir, topdown=True):
    package_data.extend(
        (os.path.join(path, f)[prefix_len:] for f in files
         if os.path.splitext(f)[1] in ('.tmpl', '.cpp') or f == 'Makefile'))

packages = [p for p in find_packages() if p != 'test']

setup(
    name="pype9",
    version="0.1a",
    package_data={package_name: package_data},
    packages=packages,
    author="Thomas G. Close",
    # add your name here if you contribute to the code
    author_email="tom.g.close@gmail.com",
    description=("\"Python PipelinEs for 9ML (PyPe9)\" to simulate neuron and "
                 "neuron network models described in 9ML in the NEURON and "
                 "NEST simulators."),
    long_description=open("README.rst").read(),
    license="The MIT License (MIT)",
    keywords=("Python pipeline NineML computational neuroscience modeling "
              "interoperability XML 9ML NEURON NEST"),
    url="http://github.com/CNS-OIST/PyPe9",
    classifiers=['Development Status :: 3 - Alpha',
                 'Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: MIT',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2',
                 'Topic :: Scientific/Engineering'],
    install_requires=['pyNN'],  # 'nineml',
    tests_require=['nose', 'ninemlcatalog']
)
