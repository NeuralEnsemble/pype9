#!/usr/bin/env python

from setuptools import setup, find_packages  # @UnresolvedImport

setup(
    name="PyPe9",
    version="0.1",
    package_data={'pype9': ['pype9', 'pype9/*.py', 'pype9/cells',
                            'pype9/cells/code_gen', 'pype9/cells/build',
                            'pype9/importer', 'pype9/pyNN', 'pype9/hpc',
                            'pype9/test', 'pype9/test/unittests',
                            'pype9/morphology']},
    packages=find_packages(),
    author="Thomas G. Close",
    # add your name here if you contribute to the code
    author_email="tom.g.close@gmail.com",
    description=("Python PipelinEs for 9ML (PyPe9) for reading and simulating "
                 "neurons and neuron networks models described in 9ML."),
    long_description=open("README.md").read(),
    license="The MIT License (MIT)",
    keywords=("Python pipeline NineML computational neuroscience modeling "
              "interoperability XML"),
    url="http://github.com/CNS-OIST/PyPe9",
    classifiers=['Development Status :: initial stages',
                 'Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: MIT',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2',
                 'Topic :: Scientific/Engineering'],
    install_requires=['nineml', 'pyNN', 'lxml'],
    tests_require=['nose', 'ninemlcatalog']
)
