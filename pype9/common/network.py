"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from pype9 import DEFAULT_V_INIT
import os.path
from pyNN.random import NumpyRNG
import pyNN.standardmodels
import nineml
import quantities as pq
from pype9.exceptions import Pype9ProjToCloneNotCreatedException

_REQUIRED_SIM_PARAMS = ['timestep', 'min_delay', 'max_delay', 'temperature']


class Network(object):

    def __init__(self, filename, network_name=None, build_mode='lazy',
                 verbose=False, timestep=None, min_delay=None, max_delay=None,   # @UnusedVariable @IgnorePep8
                 temperature=None, silent_build=False, flags=[],  # @UnusedVariable @IgnorePep8
                 rng=None, solver_name='cvode'):
        parsed_nineml = nineml.read(filename)
        if network_name:
            try:
                self.nineml_model = parsed_nineml.groups[network_name]
            except KeyError:
                raise Exception("Nineml file '{}' does not contain network "
                                "named '{}'" .format(filename, network_name))
        else:
            try:
                self.nineml_model = parsed_nineml.groups.values()[0]
            except IndexError:
                raise Exception("No network objects loaded from NineMl file "
                                 "'{}'".format(filename))
        self._set_simulation_params(timestep=timestep, min_delay=min_delay,
                                    max_delay=max_delay,
                                    temperature=temperature)
        self.dirname = os.path.dirname(filename)
        self.label = self.nineml_model.name
        self._rng = rng if rng else NumpyRNG()
        self._populations = {}
        PopulationClass = self._PopulationClass
        for name, model in self.nineml_model.populations.iteritems():
            self._populations[name] = PopulationClass(model, self._rng,
                                                      build_mode, silent_build,
                                                      solver_name=solver_name)
        if build_mode not in ('build_only', 'compile_only'):
            self._projections = {}
            ProjectionClass = self._ProjectionClass
            projection_models = self.nineml_model.projections.values()
            num_projections = len(projection_models)
            for model in projection_models:
                try:
                    self._projections[model.name] = ProjectionClass(
                        self._populations[model.source.population.name],
                        self._populations[model.target.population.name],
                        model, rng=self._rng)
                except Pype9ProjToCloneNotCreatedException as e:
                    if e.orig_proj_id in self.nineml_model.projections.keys():
                        projection_models.append(model)
                        # I think this is the theoretical limit for the number
                        # of iterations this loop will have to make for the
                        # worst ordering of cloned projections
                        if ((len(projection_models) - num_projections) >
                                (num_projections * (num_projections + 1) / 2)):
                            raise Exception("Projections using 'Clone' pattern"
                                            "form a circular reference")
                    else:
                        raise Exception("Projection '{}' attempted to clone "
                                        "connectivity patterns from '{}', "
                                        "which was not found in network."
                                        .format(name, e.orig_proj_id))
            self._finalise_construction()

    def _finalise_construction(self):
        """
        Can be overriden by deriving classes to do any simulator-specific
        finalisation that is required
        """
        pass

    @property
    def populations(self):
        return self._populations

    @property
    def projections(self):
        return self._projections

    def describe(self):
        """
        Describes all populations and projections within the network
        """
        print "Populations:"
        for pop in self.populations.itervalues():
            print pop.describe()

        print "Projections:"
        for proj in self.projections.itervalues():
            print proj.describe()

    def save_connections(self, output_dir):
        """
        Saves generated connections to output directory

        @param output_dir:
        """
        for proj in self.projections.itervalues():
            if isinstance(proj.synapse_type,
                          pyNN.standardmodels.synapses.ElectricalSynapse):
                attributes = 'weight'
            else:
                attributes = 'all'
            proj.save(attributes, os.path.join(
                output_dir, proj.label + '.proj'), format='list', gather=True)

    def save_positions(self, output_dir):
        """
        Saves generated cell positions to output directory

        @param output_dir:
        """
        for pop in self.populations.itervalues():
            pop.save_positions(os.path.join(output_dir, pop.label) + '.pop')

    def record(self, variable):
        """
        Record variable from complete network
        """
        for pop in self.populations.itervalues():
            pop.record(variable)

    def write_data(self, file_prefix, **kwargs):
        """
        Record all spikes generated in the network

        @param filename: The prefix for every population files before the
                         popluation name. The suffix '.spikes' will be
                         appended to the filenames as well.
        """
        # Add a dot to separate the prefix from the population label if it
        # doesn't already have one and isn't a directory
        if (not os.path.isdir(file_prefix) and not file_prefix.endswith('.')
                and not file_prefix.endswith(os.path.sep)):
            file_prefix += '.'
        for pop in self.populations.itervalues():
            # @UndefinedVariable
            pop.write_data(file_prefix + pop.label + '.pkl', **kwargs)

    def _get_simulation_params(self, **params):
        sim_params = dict([(p.name, pq.Quantity(p.value, p.unit))
                           for p in self.nineml_model.parameters.values()])
        for key in _REQUIRED_SIM_PARAMS:
            if key in params and params[key]:
                sim_params[key] = params[key]
            elif key not in sim_params or not sim_params[key]:
                raise Exception("'{}' parameter was not specified either in "
                                "Network initialisation or NetworkML "
                                "specification".format(key))
        return sim_params


class PyNNCellWrapper(object):

    """
    A base cell object for PyNNCellWrapper cell classes.
    """

    @classmethod
    def get_parameter_names(cls):
        """
        Returns a list of parameters that can be set for the Cell class.

        @return [list(str)]: The list of parameter names in the class
        """
        return cls.parameter_names


class PyNNCellWrapperMetaClass(type):

    """
    Metaclass for building NineMLCellType subclasses
    Called by nineml_celltype_from_model
    """

    def __new__(cls, celltype_id, bases, dct):  # @NoSelf
        # Retrieved parsed model (it is placed in dct to conform with
        # with the standard structure for the "__new__" function of
        # metaclasses).
        nineml_model = dct['model'].nineml_model
        (dct["default_parameters"],
         dct["default_initial_values"]) = cls._construct_default_parameters(
             nineml_model)
        dct["receptor_types"] = cls._construct_receptor_types(nineml_model)
        dct['recordable'] = cls._construct_recordable(nineml_model)
        dct["injectable"] = True
        dct["conductance_based"] = True
        dct["model_name"] = celltype_id
        dct["weight_variables"] = cls._construct_weight_variables()
        dct["parameter_names"] = dct['default_parameters'].keys()
        return super(PyNNCellWrapperMetaClass, cls).__new__(
            cls, celltype_id + 'PyNN', bases, dct)

    def __init__(self, celltype_name, nineml_model, build_mode='lazy',
                 silent=False, solver_name=None, standalone=False):
        """
        Not required, but since I have changed the signature of the new method
        it otherwise complains
        """
        pass

    @classmethod
    def _construct_default_parameters(cls, nineml_model):  # @UnusedVariable
        """
        Constructs the default parameters of the 9ML class from the nineml
        model
        """
        default_params = {}
        initial_values = {}
        for p in nineml_model.parameters:
            if p.componentclass:
                component = nineml_model.biophysics.components[
                    p.componentclass]
            else:
                component = nineml_model.biophysics.components[
                    '__NO_COMPONENT__']
            try:
                reference = cls._basic_nineml_translations[p.reference]
            except KeyError:
                reference = p.reference
            if p.reference == 'Voltage':
                parameter = DEFAULT_V_INIT
            else:
                parameter = component.parameters[reference].value
            default_params[p.name] = parameter
            if p.type == 'initialState':
                initial_values[p.name] = parameter
        return default_params, initial_values

    @classmethod
    def _construct_receptor_types(cls, nineml_model):
        """
        Constructs the dictionary of recordable parameters from the NineML
        model
        """
        receptors = []
        for mapping in nineml_model.mappings:
            for comp_name in mapping.components:
                component = nineml_model.biophysics.components[comp_name]
                if component.type == 'post-synaptic-conductance':
                    clsfctn = nineml_model.morphology.classifications[
                        mapping.segments.classification]
                    for seg_cls in mapping.segments:
                        for member in clsfctn[seg_cls]:
                            receptors.append(
                                '{' + str(member) + '}' + component.name)
        return receptors

    @classmethod
    def _construct_recordable(cls, nineml_model):
        """
        Constructs the dictionary of recordable parameters from the NineML
        model
        """
        # TODO: Make selected componentclass variables also recordable
        return ['spikes', 'v'] + \
            ['{' + seg + '}v'
             for seg in nineml_model.morphology.segments.keys()]

    @classmethod
    def _construct_weight_variables(cls):
        """
        Constructs the dictionary of weight variables from the NineML model
        """
        # TODO: When weights are included into the NineML model, they should be
        # added to the list here
        return {}
