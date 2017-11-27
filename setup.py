#!/usr/bin/env python
import os
import sys
from setuptools import find_packages  # @UnresolvedImport
from distutils.core import setup


# Generate the package data
package_name = 'pype9'
package_dir = os.path.join(os.path.dirname(__file__), package_name)
package_data = []
prefix_len = len(package_dir) + 1
for path, dirs, files in os.walk(package_dir, topdown=True):
    package_data.extend(
        (os.path.join(path, f)[prefix_len:] for f in files
         if os.path.splitext(f)[1] in ('.tmpl', '.cpp') or f == 'Makefile'))

# Filter unittests from packages
packages = [p for p in find_packages() if not p.startswith('test.')]

sys.path.insert(0, package_dir)
from version import __version__  # @IgnorePep8 @UnresolvedImport
sys.path.pop(0)

setup(
    name=package_name,
    version=__version__,
    package_data={package_name: package_data},
    scripts=[os.path.join('scripts', 'pype9')],
    packages=packages,
    author="The PyPe9 Team (see AUTHORS)",
    author_email="tom.g.close@gmail.com",
    description=(
        "PYthon PipelinEs for 9ML (Pype9) is a collection of Python pipelines "
        "for simulating networks of neuron models described in 9ML with various "
        "simulator backends."),
    long_description=open("README.rst").read(),
    license="MIT",
    keywords=("NineML pipeline computational neuroscience modeling "
              "interoperability XML YAML JSON HDF5 9ML neuron nest"),
    url="http://readthedocs.io/pype9",
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: MIT License',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Topic :: Scientific/Engineering'],
    install_requires=[
        'nineml>=1.0',
        'ninemlcatalog>=0.1',
        'sympy>=1.1',
        'Jinja2>=2.6',
        'docutils>=0.10',
        'mock>=1.0',
        'numpy>=1.5',
        'quantities>=0.11.1',
        'neo>=0.5.1',
        'mpi4py>=1.3.1',
        'pyNN>=0.9.1',
        'lazyarray>=0.2.7',
        'diophantine>=0.2.0',
        'PyYAML>=3.11',
        'h5py>=2.7.0',
        'future>=0.16'],
     extras_require={
         'plot': 'matplotlib>=2.0'},
     tests_require=['nose'],
     python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4'
)
