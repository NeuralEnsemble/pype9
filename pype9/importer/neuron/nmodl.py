from math import isnan, log10
import re
import regex
import operator
import quantities as pq
import os.path
import collections
from itertools import chain
from nineml.abstraction_layer.componentclass import Parameter
from nineml.abstraction_layer.dynamics import (
    TimeDerivative, StateAssignment, DynamicsClass)
from nineml.abstraction_layer.dynamics import Regime, StateVariable, OnEvent
from nineml.abstraction_layer.expressions import Alias
from nineml.abstraction_layer.ports import (
    AnalogReceivePort, AnalogSendPort, EventReceivePort)
import nineml.abstraction_layer.units as un
from nineml.user_layer import Definition
from nineml.document import Document
from nineml.user_layer import Dynamics
from nineml.abstraction_layer.expressions import Constant
from pype9.exceptions import Pype9RuntimeError

# from nineml.user_layer.dynamics import IonDynamics
from collections import defaultdict
from nineml.abstraction_layer import units
from nineml.abstraction_layer.expressions.piecewise import (Piecewise, Piece,
                                                            Otherwise)


# Compiled regular expressions
newline_re = re.compile(r" *[\n\r]+ *")
# An assignment not proceded by a greater or equals sign @IgnorePep8
assign_re = re.compile(r"(?<![\>\<]) *= *")
list_re = re.compile(r" *, *")
title_re = re.compile(r"TITLE (.*)")
comments_re = re.compile(r"COMMENT(.*)ENDCOMMENT")
whitespace_re = re.compile(r'\s')
getitem_re = re.compile(r'(\w+)\[(\d+)\]')
logstate_re = re.compile(r' *(\d+)? *(\w+)')  # For kinetics terms
notword_re = re.compile(r'\W')


class _Otherwise(object):
    """
    An object used to represent the "else/otherwise" condition of a piecewise
    function
    """

    def __init__(self, not_tests=[]):
        self.not_tests = not_tests

    def full_condition(self):
        return ' & '.join('!({})'.format(test) for test in self.not_tests)

    def __str__(self):
        return '__otherwise__'


_SI_to_dimension = {'m/s': un.conductance,
                    'kg*m**2/(s**3*A)': un.voltage,
                    'mol/m**3': un.concentration,
                    'A/m**2': un.currentDensity,
                    's': un.time,
                    'K': un.temperature,
                    'kg/(m**3*s)': un.flux,
                    '1/(s*A)': un.mass_per_charge,
                    'm': un.length,
                    's**3*A**2/(kg*m**4)': un.conductanceDensity,
                    'A': un.current,
                    'A/s': un.current_per_time,
                    's**3*A**2/(kg*m**2)': un.conductance,
                    '1/s': un.per_time,
                    's*A/m**3': un.charge_density,
                    'm**3/(s*mol)': un.per_time_per_concentration,
                    'mol/m**2': un.substance_per_area,
                    's*A': un.charge,
                    's**3*A/(kg*m**2)': un.per_voltage,
                    'kg*m**2/(s**2*K)': un.energy_per_temperature,
                    None: un.dimensionless}

# Create dict mapping nineml.Dimension and power to nineml.Unit
_SI_to_nineml_units = dict(((u.dimension, u.power), u)
                           for u in (getattr(un, uname) for uname in dir(un))
                           if isinstance(u, un.Unit))


class NMODLImporter(object):
    """
    Imports NMODL files into lib9ml structures
    """

    # This is used to differentiate a state assigment in a NET_RECEIVE block
    # from a regular alias
    StateAssignment = collections.namedtuple("StateAssignment", "variable")

    _inbuilt_constants = {'faraday': (96485.3365, 'coulomb'),
                          'k-mole': (8.3144621, 'J/K'),
                          'pi': (3.14159265359, 'dimensionless')}

    _function_substitutions = [('fabs', 'abs')]

    def __repr__(self):
        return ("NMODLImporter({}): {} parameters, {} ports, {} states,"
                " {} aliases").format(self.component_name,
                                      len(self.parameters),
                                      len(self.analog_ports),
                                      len(self._state_variables),
                                      len(self.aliases))

    def __init__(self, fname):
        # Read file
        with open(fname) as f:
            self.contents = f.read()
        # Parse file contents into blocks
        self._read_title()
        self._read_comments()
        self._read_blocks()
        # Initialise members
        self.used_units = ['degC', 'kelvin']
        self.functions = {}
        self.procedures = {}
        self.aliases = {}
        self.piecewises = {}
        self.constants = {}
        self.properties = {}
        self.valid_parameter_ranges = {}
        self.valid_state_ranges = {}
        self.dimensions = {}
        self._state_variables = {}
        self.state_variables_initial = {}
        self.stead_state_linear_equations = {}
        self.range_vars = set()
        self.globals = []  # Unused currently
        self.used_ions = {}
        self.breakpoint_solve_methods = {}
        self.initial_solve_methods = {}
        self.parameters = {}
        self.analog_ports = {}
        self.event_ports = {}
        self.regime_parts = []
        self.kinetics = {}
        self.on_event_parts = None
        # Extract declarations and expressions from blocks into members
        self._extract_neuron_block()
        self._extract_units_block()
        self._extract_procedure_and_function_blocks()
        self._extract_assigned_block()
        self._extract_parameter_and_constant_block()
        self._extract_initial_block()  # Done early so aliases can be overwrit.
        self._extract_state_block()  # Comes after state block to check dims.
        self._extract_linear_block()
        self._extract_kinetic_block()
        self._extract_derivative_block()
        self._extract_breakpoint_block()
        self._extract_netreceive_block()
        self._extract_independent_block()
        assert not self.blocks  # Check to see all blocks have been extracted
        # Create members from extracted information
        self._create_parameters_and_analog_ports()
        self._create_regimes()

    def get_component_class(self):
        comp_class = DynamicsClass(name=self.component_name + 'Class',
                                   parameters=self.parameters.values(),
                                   analog_ports=self.analog_ports.values(),
                                   event_ports=self.event_ports.values(),
                                   regimes=self._regimes,
                                   aliases=self.aliases.values(),
                                   piecewises=self.piecewises.values(),
                                   constants=self.constants.values(),
                                   state_variables=self._state_variables)
        return comp_class

    def get_component(self, class_path=None, hoc_properties={}):
        # Copy properties removing all properties that were added to the analog
        # ports
        properties = dict((n, (v, u))
                          for n, (v, u) in self.properties.iteritems()
                          if n not in self.analog_ports)
        # Update the parameters of the properties using the hoc set parameters
        # and the units specified in the NMODL file
        properties.update((n, (v, self.properties[n][1]))
                          for n, v in hoc_properties.iteritems())
        properties.update((n, (v, self._units2nineml_units(u)))
                          for n, (v, u) in properties.iteritems())
        context = Document()
        definition = Definition(self.component_name + 'Class', context,
                                url=os.path.normpath(class_path))
        comp = Dynamics(self.component_name, definition=definition,
                                 properties=properties)
        return comp

    def print_members(self):
        """
        Prints out a list of the aliases used in the component (primarily for
        debugging
        """
        print "\n\n------------------"
        print "     {}      ".format(self.component_name)
        print "------------------"
        print "\nParameters:"
        for p in self.parameters.itervalues():
            print '{}'.format(p.name)
        print "\nReceive Analog Ports:"
        for p in self.analog_ports.itervalues():
            if p.mode == 'recv':
                print '{}'.format(p.name)
        print "\nSend Analog Ports:"
        for p in self.analog_ports.itervalues():
            if p.mode == 'send':
                print '{}'.format(p.name)
        print "\nTime derivatives:"
        for r in self._regimes:
            for td in r.time_derivatives:
                print "{}' = {}".format(td.dependent_variable, td.rhs)
        print "\nAliases:"
        for a in self.aliases.itervalues():
            print '{} = {}'.format(a.lhs, a.rhs)
        print "\nConstants:"
        for c in self.constants.itervalues():
            print '{} = {} ({})'.format(c.name, c.value, c.units.name)
        print "\nPiecewises:"
        for p in self.piecewises.itervalues():
            print '{} =:'.format(p.name)
            for pc in p.pieces:
                print '    {},   {}'.format(*pc)
            print '    {},   otherwise'.format(str(p.otherwise))

    def all_expressions(self):
        """
        Create a list of all the expressions used in the NMODL file
        """
        td_rhs = []
        try:
            for regime in self._regimes.itervalues():
                td_rhs.extend([td.rhs for td in regime.time_derivatives])
        except AttributeError:
            for _, time_derivatives in self.regime_parts:
                td_rhs.extend(td.rhs for td in time_derivatives)
        # Get a list of all expressions used in the model
        simple_rhs = [a.rhs for a in self.aliases.values()
                      if isinstance(a.rhs, str)]
        piecewise_rhs = [[expr for expr, _ in a.rhs if isinstance(expr, str)]
                         for a in self.aliases.values()
                         if isinstance(a.rhs, list)]
        if piecewise_rhs:
            piecewise_rhs = reduce(operator.add, piecewise_rhs)
        piecewise_test = [[test for _, test in a.rhs
                           if not isinstance(test, _Otherwise)]
                          for a in self.aliases.values()
                          if isinstance(a.rhs, list)]
        if piecewise_test:
            piecewise_test = reduce(operator.add, piecewise_test)
        return td_rhs + simple_rhs + piecewise_rhs + piecewise_test

    def _create_parameters_and_analog_ports(self):
        # Add used ions to analog ports
        for name, (read, write, valence) in self.used_ions.iteritems():
            if valence:
                pass  # FIXME: Need to add aliases to scale up the current out.
            for n in read:
                # Check to see if ion property isn't specified as fixed in
                # mod file parameters
                if n not in self.properties or isnan(self.properties[n][0]):
                    if n.startswith('e'):
                        dimension = un.voltage
                    elif n.startswith('i'):
                        dimension = un.currentDensity
                    elif n.endswith('o') or n.endswith('i'):
                        dimension = un.concentration
                    else:
                        assert False, ("Unrecognised used ion element '{}'"
                                       .format(n))
                    self.analog_ports[n] = AnalogReceivePort(
                        n, dimension=dimension)
            for n in write:
                if n.startswith('i'):
                    dimension = un.currentDensity
                elif n.endswith('o') or n.endswith('i'):
                    dimension = un.concentration
                else:
                    assert False, ("Unrecognised used ion element '{}'"
                                   .format(n))
                self.analog_ports[n] = AnalogSendPort(
                    n, dimension=dimension)
        # Create parameters for each property
        for name, (_, units) in self.properties.iteritems():
            if name not in self.analog_ports:
                dimension = self._units2dimension(units)
                self.parameters[name] = Parameter(name, dimension=dimension)
        # Add ports/parameters for reserved NMODL keywords
        uses_celsius = uses_voltage = uses_diam = False
        for expr in self.all_expressions():
            if re.search(r'(\b)celsius(\b)', expr):
                uses_celsius = True
            if re.search(r'(\b)v(\b)', expr):
                uses_voltage = True
            if re.search(r'(\b)diam(\b)', expr):
                uses_diam = True
        if uses_voltage:
            self.analog_ports['v'] = AnalogReceivePort(
                'v', dimension=un.voltage)
        if uses_celsius and 'celsius' not in self.parameters:
            self.analog_ports['celsius'] = AnalogReceivePort(
                'celsius', dimension=un.temperature)
        if uses_diam:
            self.parameters['diam'] = Parameter('diam', dimension=un.length)

    def _create_regimes(self, expand_kinetics=True):
        self._regimes = []
        if self.on_event_parts:
            assert len(self.regime_parts) == 1
            regime = self.regime_parts[0]
            parameter, assignments, aliases = self.on_event_parts
            if parameter:
                port_name, dimension = parameter
                event_port_name = port_name + "_event"
                # Create an analog port from which to read the event weight
                # from. NB: this is just a hack for now until EventPorts
                # support parameters
                self.analog_ports.append(AnalogReceivePort(
                    name=port_name, dimension=dimension))
            else:
                event_port_name = port_name
            self.event_ports[event_port_name] = EventReceivePort(
                name=event_port_name)
            on_event = OnEvent(event_port_name,
                               state_assignments=[
                                   '{}={}'.format(a.lhs, a.rhs)
                                   for a in assignments.values()])
            self.aliases.update(aliases)
            self._regimes.append(Regime(name=regime[0],
                                       time_derivatives=regime[1],
                                       transitions=on_event))
        for name, (bidirectional, incoming, outgoing,
                   constraints, compartments) in self.kinetics.iteritems():
            if expand_kinetics:
                time_derivatives = self._expand_kinetics(bidirectional,
                                                         incoming, outgoing,
                                                         constraints,
                                                         compartments)
                self._regimes.append(Regime(name=name,
                                           time_derivatives=time_derivatives))
            else:
                # TODO: Haven't implemented explicit kinetics
                raise NotImplementedError("Haven't implemented explicit "
                                          "kinetics schemes")
        # Create Regimes from explicit time derivatives
        for name, time_derivatives in self.regime_parts:
            self._regimes.append(Regime(name=name,
                                       time_derivatives=time_derivatives))

    @classmethod
    def _expand_kinetics(cls, bidirectional, incoming, outgoing,
                         constraints, compartments):  # @UnusedVariable
        equations = defaultdict(str)
        # Sort terms into lhs variables multiplying by stoichiometric number
        for lhs_states, rhs_states, f_rate, b_rate in bidirectional:
            lhs_term = f_rate + '*' + cls._expand_kinetics_term(lhs_states)
            rhs_term = b_rate + '*' + cls._expand_kinetics_term(rhs_states)
            for s, p in lhs_states:
                pstr = (p + '*') if p else ''
                equations[s] += ' - ' + pstr + lhs_term
                equations[s] += ' + ' + pstr + rhs_term
            for s, p in rhs_states:
                pstr = (p + '*') if p else ''
                equations[s] += ' - ' + pstr + rhs_term
                equations[s] += ' + ' + pstr + lhs_term
        time_derivatives = []
        for state, rhs in equations.iteritems():
            rhs += ''.join(' + ' + str(r) for s, r in incoming if s == state)
            rhs += ''.join(' - ' + str(r) for s, r in outgoing if s == state)
            # Strip leading '+' if present
            if rhs.startswith(' + '):
                rhs = rhs[2:]
            time_derivatives.append(TimeDerivative(state, rhs))
        return time_derivatives

    @classmethod
    def _expand_kinetics_term(cls, states):
        return '*'.join('{}^{}'.format(s, p) if p else s
                        for s, p in states)

    # =========================================================================
    # Content readers
    # =========================================================================

    def _read_title(self):
        # Extract title and comments if present
        match = title_re.search(self.contents, re.MULTILINE)
        self.title = match.group(1) if match else ''

    def _read_comments(self):
        self.comments = []
        for cmt in comments_re.findall(self.contents,
                                       re.DOTALL | re.MULTILINE):
            self.comments.append(cmt)

    def _read_blocks(self):
        self.blocks = defaultdict(dict)
        line_iter = iter(self.contents.splitlines())
        for decl, contents, _ in self._matching_braces(line_iter,
                                                       multiline_pre=False):
            match = re.match(r" *(\w+)(.*)", decl)
            block_name = match.group(1).strip()
            if match.group(2).strip():
                if block_name == 'NET_RECEIVE':
                    self.blocks[block_name] = (match.group(2).strip()[1:-1],
                                               contents)
                else:
                    self.blocks[block_name][match.group(2).strip()] = contents
            else:
                if block_name == 'NET_RECEIVE':
                    self.blocks[block_name] = ('', contents)
                else:
                    self.blocks[block_name] = contents

    # =========================================================================
    # Block extractors
    # =========================================================================

    def _extract_procedure_and_function_blocks(self):
        # Read functions
        for blck_type, dct in (('FUNCTION', self.functions),
                                ('PROCEDURE', self.procedures)):
            for signature, block in self.blocks.pop(blck_type, {}).iteritems():
                # Strip function units from signature
                stripped = self._matching_parentheses(signature)
                output_units = signature[len(stripped):].strip()[1:-1]  # @UnusedVariable @IgnorePep8
                signature = stripped
                # Strip units statements from arguments (this may need to be
                # handled but hopefully it should be implicitly by the
                # dimension checking)
                for units in self.used_units:
                    signature = signature.replace('({})'.format(units), '')
                signature = signature.strip()
                match = re.match(r'(\w+) *\((.*)\)', signature)
                name = match.group(1).strip()
                arglist = match.group(2).strip()
                if arglist:
                    args = list_re.split(arglist)
                else:
                    args = []
                dct[name] = (args, block)

    def _extract_units_block(self):
        # Read the unit aliases
        for line in self._iterate_block(self.blocks.pop('UNITS')):
            match = re.match(r'\(?(\w+)\)? *= *\(([\w \/\*\-]+)\)'
                             r'(?: *\(([\w \d\/\*]+)\))?',
                             line)
            if match.group(3):
                name = match.group(1)
                inbuilt = match.group(2)
                declared_units = self._sanitize_units(match.group(3))
                value, units = self._inbuilt_constants[inbuilt]
                value *= float(pq.Quantity(1.0, units) /
                               pq.Quantity(1.0, declared_units))
                self.constants[name] = Constant(
                    name, value, units=self._units2nineml_units(units))
            else:
                alias = match.group(1)
                unitname = match.group(2)
                try:
                    pq.Quantity(1, alias)
                except:
                    try:
                        # Add alias to quantities object
                        unit = pq.Quantity(1, unitname)
                        unit.aliases.append(alias)
                    except:
                        raise Pype9RuntimeError("Unrecognised unit '{}'"
                                                .format(unitname))
                self.used_units.append(alias)

    def _extract_assigned_block(self):
        # Read the assigned block for analog out ports
        for line in self._iterate_block(self.blocks.pop('ASSIGNED', [])):
            parts = line.strip().split('(')
            if len(parts) == 1:
                var = parts[0]
                dimension = None
            elif len(parts) == 2:
                var, units = parts
                var = var.strip()
                units = units[:-1]  # remove parentheses
                dimension = self._units2dimension(units)
            else:
                raise Pype9RuntimeError(
                    "Three tokens found on line '{}', was expecting 1 or 2 "
                    "(var [units])".format(line))
            self.dimensions[var] = dimension

    def _extract_parameter_and_constant_block(self):
        # Read properties
        block = self.blocks.pop('PARAMETER') + self.blocks.pop('CONSTANT', [])
        for line in self._iterate_block(block):
            parts = assign_re.split(line)
            if len(parts) == 1:
                match = re.match(r'(\w+) +\(([\w\/\*\^]+)\)', line)
                name = match.group(1)
                units = match.group(2) if match.group(2) else 'dimensionless'
                # This is a bit of a hack to specify that this parameter
                # doesn't have a default value FIXME
                units = self._sanitize_units(units)
                if name not in ('celsius', 'v'):
                    self.properties[name] = (float('nan'), units)
            elif len(parts) == 2:
                name, rest = parts
                match = re.match(r'([\d\.e-]+)\s*(\([\d\w\.\*/]+\))?\s*'
                                 r'(<[\d\.e-]+,[\d\.e-]+>)?', rest)
                name = name.strip()
                value = float(match.group(1))
                units = match.group(2)
                if units:
                    units = units[1:-1]
                    units = self._sanitize_units(units)
                else:
                    units = 'dimensionless'
                # Check to see if quantity is really an inbuilt constant and
                # therefore shouldn't be a parameter
                quantity = pq.Quantity(value, units)
                is_constant = False
                for const in self._inbuilt_constants.itervalues():
                    const_quantity = pq.Quantity(*const)
                    try:
                        frac = (quantity - const_quantity) / const_quantity
                        if abs(frac) < 1e-4:
                            is_constant = True
                    except ValueError:
                        pass
                if is_constant:
                    self.constants[name] = Constant(name, value, units)
                else:
                    self.properties[name] = (value, units)
                    valid_range_str = match.group(3)
                    if valid_range_str:
                        vrange = [float(v)
                                  for v in valid_range_str[1:-1].split(',')]
                        self.valid_parameter_ranges[name] = vrange
            else:
                raise Pype9RuntimeError(
                    "More than one '=' found on parameter block line '{}'"
                    .format(line))

    def _extract_initial_block(self):
        reduced_block = []
        for line in self._iterate_block(self.blocks.pop('INITIAL', [])):
            if line.startswith('SOLVE'):
                match = re.match(r'SOLVE (\w+)'
                                 r' *(?:STEADYSTATE (\w+))?', line)
                if not match:
                    raise Pype9RuntimeError(
                        "Could not read solve statement '{}'".format(line))
                self.initial_solve_methods[match.group(1)] = match.group(2)
            else:
                reduced_block.append(line)
        # Read initial block
        self._initial_assign = self._extract_stmts_block(reduced_block)

    def _extract_state_block(self):
        # Read state variables
        block = self.blocks.pop('STATE', [])
        # Sometimes states can be written all on one line
        if len(block) == 1 and '(' not in block[0] and 'FROM' not in block[0]:
            block = block[0].split()
        for line in self._iterate_block(block):
            match = re.match(r'(\w+)(?: *\(([\w \/\*]+)\))?'
                             r'(?: *FROM *([\d\.\-]+) *TO *([\d\.\-]+))?',
                             line)
            var = match.group(1)
            # If Units are provided
            if match.group(2):
                units = match.group(2)
                dimension = self.dimensions[var] = self._units2dimension(units)
            else:
                try:
                    initial = self._initial_assign.pop(var)
                    dimension = self.dimensions[initial]
                except KeyError:
                    dimension = None
                self.dimensions[var] = dimension
            # If valid range is provided
            if match.group(3):
                self.valid_state_ranges[var] = (match.group(3), match.group(4))
            self._state_variables[var] = StateVariable(var, dimension=dimension)
        for lhs, rhs in self._initial_assign.iteritems():
            if lhs in self._state_variables:
                self.state_variables_initial[lhs] = self._escape_piecewise(lhs,
                                                                           rhs)
            else:
                self._set_alias_or_piecewise(lhs, rhs)

    def _extract_neuron_block(self):
        # Read the NEURON block
        self.component_name = None
        for line in self._iterate_block(self.blocks.pop('NEURON')):
            if line.startswith('SUFFIX'):
                self.component_name = line.split()[1]
            elif line.startswith('POINT_PROCESS'):
                self.component_name = line.split()[1]
            elif line.startswith('ARTIFICIAL_CELL'):
                self.component_name = line.split()[1]
            elif line.startswith('RANGE'):
                self.range_vars.update(list_re.split(line[6:]))
            elif line.startswith('USEION'):
                name = re.match(r'USEION (\w+)', line).group(1)
                match = re.match(r'.*READ ((?:\w+(?: *\, *)?)+)', line)
                read = list_re.split(match.group(1)) if match else []
                match = re.match(r'.*WRITE ((?:\w+(?: *\, *)?)+)', line)
                write = list_re.split(match.group(1)) if match else []
                match = re.match(r'.*VALENCE (\d+)', line)
                valence = match.group(1) if match else None
                self.used_ions[name] = (read, write, valence)
                for c in chain(read, write):
                    if c.startswith('i'):
                        if c.endswith('i') or c.endswith('o'):
                            raise Pype9RuntimeError(
                                "Amiguous usion element '{}' (elements "
                                "starting with 'i' are assumed to be currents "
                                "and elements ending with 'i' or 'o' are "
                                "assumed to be concentrations)".format(c))
                        self.dimensions[c] = 'membrane_current'
                    elif c.endswith('i') or c.endswith('o'):
                        self.dimensions[c] = 'concentration'
            elif line.startswith('NONSPECIFIC_CURRENT'):
                match = re.match(r'NONSPECIFIC_CURRENT (\w+)', line)
                write = match.group(1)
                self.used_ions['__nonspecific__'] = ([], [write], None)
                self.dimensions[write] = 'membrane_current'
            elif line.startswith('GLOBAL'):
                self.globals.extend(var for var in list_re.split(line[7:]))

    def _extract_derivative_block(self):
        # Read derivative
        named_blocks = self.blocks.pop('DERIVATIVE', {})
        for name, block in named_blocks.iteritems():
            time_derivatives = []
            # Extract aliases and states
            stmts = self._extract_stmts_block(block)
            # Detect state derivatives
            for lhs, rhs in stmts.iteritems():
                if lhs.endswith("'"):
                    if lhs[:-1] not in self._state_variables:
                        raise Pype9RuntimeError("Unrecognised variable '{}'"
                                                .format(lhs))
                    td = TimeDerivative(lhs[:-1],
                                        self._escape_piecewise(lhs, rhs))
                    time_derivatives.append(td)
                else:
                    self._set_alias_or_piecewise(lhs, rhs)
            self.regime_parts.append((name, time_derivatives))

    def _extract_breakpoint_block(self):
        reduced_block = []
        for line in self._iterate_block(self.blocks.pop('BREAKPOINT')):
            if line.startswith('SOLVE'):
                match = re.match(r'SOLVE (\w+) '
                                 r'METHOD (\w+)', line)
                if not match:
                    raise Pype9RuntimeError(
                        "Could not read solve statement '{}'".format(line))
                self.breakpoint_solve_methods[match.group(1)] = match.group(2)
            else:
                reduced_block.append(line)
        stmts = self._extract_stmts_block(reduced_block)
        for lhs, rhs in stmts.iteritems():
            self._set_alias_or_piecewise(lhs, rhs)

    def _extract_netreceive_block(self):
        arg_block = self.blocks.pop('NET_RECEIVE', None)
        if arg_block:
            arg_line, block = arg_block
            stmts = self._extract_stmts_block(block)
            match = re.match(r'(\w+) *\((\w+)\)', arg_line)
            if match:
                name = match.group(1)
                units = match.group(2)
                dimension = self._units2dimension(units)
                port = (name, dimension)
            else:
                port = None
            aliases = {}
            assignments = {}
            for lhs, rhs in stmts.iteritems():
                if isinstance(lhs, self.StateAssignment):
                    assignments[lhs.variable] = StateAssignment(lhs.variable,
                                                                rhs)
                else:
                    aliases[lhs] = Alias(lhs, rhs)
            self.on_event_parts = (port, assignments, aliases)

    def _extract_linear_block(self):
        named_blocks = self.blocks.pop('LINEAR', {})
        for name, block in named_blocks.iteritems():
            equations = []
            for line in self._iterate_block(block):
                match = re.match(r' *~ *(.*) *= *(.)', line)
                equations.append((match.group(1), match.group(2)))
            self.stead_state_linear_equations[name] = equations

    def _extract_kinetic_block(self):
        def split_states(states):
            return [tuple(reversed(logstate_re.match(s).groups()))
                    for s in states.split('+')]
        def process_rate(rate):  # @IgnorePep8
            rate = rate.strip()
            rate = self._extract_function_calls(rate, statements)
            if notword_re.search(rate):
                rate = '(' + rate + ')'
            return rate
        named_blocks = self.blocks.pop('KINETIC', {})
        for name, block in named_blocks.iteritems():
            bidirectional = []
            incoming = []
            outgoing = []
            constraints = []
            compartments = []
            statements = {}
            line_iter = self._iterate_block(block)
            try:
                line = next(line_iter)
            except StopIteration:
                continue
            while True:
                # Match the statement with the syntax variations
                match = re.match(r' *~ *([\w\d _\+\-]+) *\<\-\> '
                                 r'*([\w\d _\+\-]+) *'
                                 r'\( *([^,]+) *, *([^,]+) *\)', line)
                if match:
                    is_bidirectional = True
                else:
                    is_bidirectional = False
                    match = re.match(r' *~ *(.+) *\<\< *(.+)', line)
                    if match:
                        is_incoming = True
                    else:
                        is_incoming = False
                        match = re.match(r' *~ *(.+) *\-\> *(.+)', line)
                        if match:
                            is_outgoing = True
                        else:
                            is_outgoing = False
                if is_bidirectional:
                    s1, s2, r1, r2 = match.groups()
                    bidirectional.append(
                        (split_states(s1), split_states(s2), process_rate(r1),
                         process_rate(r2)))
                elif is_incoming:
                    s, r = match.groups()
                    incoming.append((s, process_rate(r)))
                elif is_outgoing:
                    s, r = match.groups()
                    outgoing.append((s, process_rate(r)))
                elif line.strip().startswith('CONSERVE'):
                    constraints.append(re.match(r' *CONSERVE (.+) *= *(.+)',
                                                line).groups())
                elif line.strip().startswith('COMPARTMENT'):
                    (pre, states, line) = next(self._matching_braces(
                        line_iter, line=line))
                    constraints.append((pre.split(), ' '.join(states).split()))
                    continue
                elif line:
                    stmts = self._extract_stmts_block([line])
                    # Get the index of last bidirectional equation in order to
                    # map the appropriate flux equation on to it.
                    try:
                        states1, states2, rate1, rate2 = bidirectional[-1]
                        # Create unique suffix
                        suffix = '_to_'.join('_'.join(''.join(s, p) if p else s
                                                      for s, p in states)
                                             for states in (states1, states2))
                        f_flux = 'f_flux_{}'.format(suffix)
                        b_flux = 'b_flux_{}'.format(suffix)
                        # Create aliases for the last-used flux terms
                        stmts[f_flux] = (rate1 + '*' +
                                         self._expand_kinetics_term(states1))
                        stmts[b_flux] = (rate2 + '*' +
                                         self._expand_kinetics_term(states2))
                        subs = [('f_flux', f_flux), ('b_flux', b_flux)]
                    except IndexError:
                        subs = []
                    for lhs, rhs in stmts.iteritems():
                        for old, new in subs:
                            rhs = self._subs_variable(old, new, rhs)
                    statements.update(stmts)
                try:
                    line = next(line_iter)
                except StopIteration:
                    break
            self.kinetics[name] = (bidirectional, incoming, outgoing,
                                   constraints, compartments)
            for lhs, rhs in statements.iteritems():
                self._set_alias_or_piecewise(lhs, rhs)

    def _extract_independent_block(self):
        self.blocks.pop('INDEPENDENT', None)
        # the Independent block is not actually required as it is always t

    # ---------------------------- #
    #  General extraction methods  #
    # ---------------------------- #

    def _extract_stmts_block(self, block, subs={}, suffix=''):
        """
        A workhorse function that extracts all expressions from a block of
        statements and returns them in a dictionary

        `block`  -- a block of text split into lines
        `subs`   -- a dict of substitutions of variables to be made (when
                    flattening functions into assignments for example).
        `suffix` -- suffix to append to LHS names
        """
        statements = {}
        line_iter = self._iterate_block(block)
        try:
            line = next(line_iter)
        except StopIteration:
            line = None
        while line:
            if line.startswith('TABLE'):
                while not re.match(r'TABLE\s+[\w\s\,_]+\s+FROM\s+[e\-\d\.]+\s+'
                                   r'TO\s+[e\-\d\.]+\s+WITH\s+[e\-\d\.]+',
                                   line):
                    try:
                        line += ' ' + next(line_iter)
                    except StopIteration:
                        raise Pype9RuntimeError(
                            "EOF while parsing table statement")
                line = next(line_iter)
                continue
            elif (line.startswith('LOCAL') or line in ('UNITSON', 'UNITSOFF')):
                try:
                    line = next(line_iter)
                except StopIteration:
                    if line.startswith('LOCAL'):
                        raise Pype9RuntimeError(
                            "LOCAL statements need to appear at the start of "
                            "the statement block")
                    else:
                        line = ''
                continue
            elif line.startswith('VERBATIM'):
                raise Pype9RuntimeError("Cannot parse VERBATIM block:\n\n{}"
                                        .format(block))
            # Escape all array indexing
            line = getitem_re.sub(r'\1__elem\2', line)
            # Split line into lhs and rhs (if '=' is present)
            parts = assign_re.split(line)
            # Either a conditional block or a procedure
            if len(parts) == 1 or '{' in line:
                expr = parts[0]
                match = re.match(r'(\w+) *\((.*)\)', expr)
                # If a procedure
                if not match:
                    raise Pype9RuntimeError(
                        "Unrecognised statement on line '{}'".format(line))
                if match.group(1) == 'if':
                    # Set the line that has been peeked at to the next line and
                    # continue to iterate through the lines
                    line = self._extract_conditional_block(line, statements,
                                                           line_iter, subs,
                                                           suffix)
                    continue
                elif match.group(1) in ('for', 'while'):
                    raise Pype9RuntimeError(
                        "Cannot represent '{}' statements in 9ML"
                        .format(match.group(1)))
                elif match.group(1) == 'state_discontinuity':
                    state, assignment = list_re.split(match.group(2))
                    l = '__state__ = {}'.format(assignment)
                    # Reuse the infrastructure for alias parsing for the
                    # state assignment (substitutes in functions and arguments)
                    expr = next(self._extract_stmts_block([l]).itervalues())
                    statements[self.StateAssignment(state)] = expr
                else:
                    proc_name = match.group(1)
                    try:
                        pargs, pbody = self.procedures[proc_name]
                    except KeyError:
                        raise Pype9RuntimeError("Unrecognised procedure '{}'"
                                                .format(proc_name))
                    argvals, _ = self._split_args(match.group(2))
                    argvals = [self._extract_function_calls(a, statements)
                               for a in argvals]
                    assert len(argvals) == len(pargs)
                    pstmts = self._extract_stmts_block(pbody,
                                                       subs=dict(zip(pargs,
                                                                     argvals)),
                                                       suffix=suffix)
                    # Add aliases from procedure to list of substitutions in
                    # order to append the suffixes
                    if suffix:
                        subs.update((lhs[:-len(suffix)], lhs)
                                    for lhs in pstmts.iterkeys())
                    statements.update(pstmts)
            elif len(parts) == 2:  # An to be an assignment expression
                self._extract_assignment(line, statements, subs, suffix)
            else:
                raise Pype9RuntimeError(
                    "More than one '=' found on line '{}'".format(line))
            try:
                line = next(line_iter)
            except StopIteration:
                line = ''
        return statements

    def _extract_assignment(self, line, statements, subs={}, suffix=''):
        lhs, rhs = assign_re.split(line)
        # Replace arguments with their values
        for old, new in subs.iteritems():
            rhs = self._subs_variable(old, new, rhs)
        rhs = self._extract_function_calls(rhs, statements)
        # Append the suffix to the left hand side
        lhs_w_suffix = lhs + suffix
        if is_builtin_symbol(lhs_w_suffix):
            lhs_w_suffix += '_'
        if suffix:
            subs[lhs] = lhs_w_suffix
        # If the same variable has been defined previously we need to
        # give it a new name so this statement doesn't override it.
        if lhs_w_suffix in statements:
            tmp_lhs = lhs_w_suffix + '__tmp'
            count = 0
            while tmp_lhs in statements:
                count += 1
                tmp_lhs = lhs_w_suffix + '__tmp' + str(count)
            statements[tmp_lhs] = statements[lhs_w_suffix]
            # Substitute the temporary lhs name into the rhs
            rhs = self._subs_variable(lhs_w_suffix, tmp_lhs, rhs)
            # Substitute the temporary lhs name into all previous rhss
            for l, r in statements.iteritems():
                if isinstance(r, list):
                    new_r = []
                    for expr, test in r:
                        new_expr = self._subs_variable(lhs_w_suffix, tmp_lhs,
                                                       expr)
                        new_test = self._subs_variable(lhs_w_suffix, tmp_lhs,
                                                       test)
                        new_r.append((new_expr, new_test))
                    statements[l] = new_r
                else:
                    statements[l] = self._subs_variable(lhs_w_suffix, tmp_lhs,
                                                        r)
        # Strip units statements (this may need to be handled but hopefully it
        # should be implicitly by the dimension checking)
        for units in self.used_units:
            rhs = rhs.replace('({})'.format(units), '')
        statements[lhs_w_suffix] = rhs

    def _extract_function_calls(self, expr, statements):
        # Expand function definitions, creating extra aliases for all
        # statements within the function body. Loop through all function
        # calls from right-to-left (so functions nested in argument-lists
        # are substituted first, updating the rhs as we go.
        found_user_function = True
        while found_user_function:
            # Find all functions in expression string
            matches = regex.findall(r"\b(\w+ *)\((.*)\)", expr,
                                    overlapped=True)
            if not matches:
                found_user_function = False
                break
            for match in matches:
                raw_name, arglist = match
                name = raw_name.strip()
                try:
                    params, body = self.functions[name]
                    argvals, raw_arglist = self._split_args(arglist)
                    argvals = [self._extract_function_calls(a, statements)
                               for a in argvals]
                    # Append a string of escaped argument values as an
                    # additional suffix
                    suffix = self._args_suffix(argvals)
                    stmts = self._extract_stmts_block(body, suffix=suffix,
                                                      subs=dict(zip(params,
                                                                    argvals)))
                    statements.update(stmts)
                    expr = expr.replace('{}({})'.format(raw_name, raw_arglist),
                                        name + suffix)
                    found_user_function = True
                    # The expression has been updated so need to break out of
                    # the matches loop and perform the regex search again
                    break
                except KeyError as e:
                    assert str(e) == "'{}'".format(name)
                    found_user_function = False
        return expr

    def _extract_conditional_block(self, line, statements, line_iter, subs={},
                                   suffix=''):
        conditional_stmts = []
        # Loop through all sub-blocks of the if/else-if/else statement
        previous_tests = []
        for pre, sblock, nline in self._matching_braces(line_iter, line=line):
            # Extract the test conditions for if and else if blocks
            match = re.search(r'\((.*)\)', pre)
            if match:
                test = match.group(1)
                # Replace arguments with their values into the test condition
                for old, new in subs.iteritems():
                    test = self._subs_variable(old, new, test)
                # Substitute in function calls
                test = self._extract_function_calls(test, statements)
                # Append any previous tests
                for prev_test in previous_tests:
                    test += ' & !({})'.format(prev_test)
                previous_tests.append(test)
            else:
                test = _Otherwise(previous_tests)
            # Extract the statements from the sub-block
            stmts = self._extract_stmts_block(sblock, subs, suffix)
            # Append the test and statements to a list for processing after all
            # blocks are processed.
            conditional_stmts.append((test, stmts))
            # Peek ahead at the next line and check to see whether there is an
            # 'else' on it, and if not stop the sub-block iteration
            try:
                while not nline.strip():
                    nline = next(line_iter)
            except StopIteration:
                line = ''
            if not re.search(r'(\b)else(\b)', nline):
                line = nline
                break
        # If the final block isn't an 'else' statement, the aliases should be
        # defined previously.
        no_otherwise_condition = not isinstance(test, _Otherwise)
        # Collate all the variables that are assigned in each sub-block
        common_lhss = reduce(set.intersection,
                             (set(s.keys())
                              for t, s in conditional_stmts))
        if len(conditional_stmts) > 2:
            # Create numbered versions of the helper statements in the sub-
            # blocks (i.e. that don't appear in all sub- blocks)
            for i, (test, stmts) in enumerate(conditional_stmts):
                branch_subs = {}
                # Get a list of substitutions to perform to unwrap the
                # conditional block
                for lhs, rhs in stmts.iteritems():
                    if lhs not in common_lhss:
                        new_lhs = ('{}__branch{}{}'
                                   .format(lhs[:-len(suffix)], i,
                                           suffix))
                        branch_subs[lhs] = new_lhs
                # Perform the substitutions on all the conditional statements
                for old, new in branch_subs.iteritems():
                    i = 1
                    # Substitute into the right-hand side equation
                    for lhs, rhs in stmts.iteritems():
                        stmts[lhs] = self._subs_variable(old, new, rhs)
                    # Substitute the left-hand side
                    rhs = stmts.pop(old)
                    stmts[new] = rhs
                # Copy all the "non-common lhs" statements, which have been
                # escaped into their separate branches to the general statement
                # block
                for _, new_lhs in branch_subs.iteritems():
                    rhs = stmts[new_lhs]
                    statements[new_lhs] = rhs
        else:
            for lhs, rhs in stmts.iteritems():
                if lhs not in common_lhss:
                    statements[lhs] = rhs
        # Loop through statements that are common to all conditions and create
        # a single piecewise statement for them
        for lhs in common_lhss:
            pieces = []
            for i, (test, stmts) in enumerate(conditional_stmts):
                self._unwrap_piecewise_stmt(stmts[lhs], test, pieces)
            if no_otherwise_condition:
                if lhs in statements:
                    rhs = statements[lhs]
                elif lhs in self.properties:
                    rhs = lhs
                    new_lhs = lhs + '_constrained'
                    subs[lhs] = new_lhs
                    lhs = new_lhs
                else:
                    raise Pype9RuntimeError(
                        "Could not find previous definition of '{}' to form "
                        "otherwise condition of conditional block".format(lhs))
                self._unwrap_piecewise_stmt(rhs,
                                            _Otherwise([t for _, t in pieces]),
                                            pieces)
            else:
                # If it does have an otherwise condition it shouldn't have been
                # defined previously
                # FIXME: possibily could have been though in strange NMODL
                # files
                assert lhs not in statements
            statements[lhs] = pieces
        # Add aliases from procedure to list of substitutions in order to
        # append the suffixes
        if suffix:
            subs.update((lhs[:-len(suffix)], lhs) for lhs in common_lhss)
        return line

    @classmethod
    def _unwrap_piecewise_stmt(cls, stmt, test, pieces):
        """
        Unwraps nested piecewise statements into a single piecewise statement
        """
        if isinstance(stmt, list):
            for s, t in stmt:
                if t == '__otherwise__':
                    combined_test = test
                else:
                    if isinstance(test, _Otherwise):
                        combined_test = ('{} & ({})'
                                         .format(test.full_condition(), t))
                    else:
                        combined_test = '({}) & ({})'.format(test, t)
                cls._unwrap_piecewise_stmt(s, combined_test, pieces)
        else:
            pieces.append((stmt, str(test)))

    # =========================================================================
    # Helper methods
    # =========================================================================

    def _subs_variable(self, old, new, expr):
        # If the new expression contains more than one "word" enclose it
        # in parentheses
        if notword_re.search(new):
            new = '(' + new + ')'
        expr = re.sub(r'\b({})\b'.format(re.escape(old)), new, expr)
        # Update dimensions tracking
        if old in self.dimensions:
            self.dimensions[new] = self.dimensions[old]
        return expr

    def _set_alias_or_piecewise(self, lhs, rhs):
        if isinstance(rhs, list):
            self._set_piecewise(lhs, rhs)
        else:
            self.aliases[lhs] = Alias(lhs, self._substitute_functions(rhs))

    def _set_piecewise(self, lhs, rhs):
        pieces = []
        otherwise = None
        for expr, test in rhs:
            expr = self._substitute_functions(expr)
            if test == '__otherwise__':
                assert otherwise is None, "Multiple otherwise statements"
                otherwise = Otherwise(expr)
            else:
                test = self._substitute_functions(test)
                pieces.append(Piece(expr, test))
        assert otherwise is not None, "No otherwise statement found"
        self.piecewises[lhs] = Piecewise(name=lhs, pieces=pieces,
                                         otherwise=otherwise)

    def _escape_piecewise(self, lhs, rhs):
        """
        If state variable initialisation or time derivative is set by a
        piecewise function create an alias for it and set the state variable
        initialisation to that
        """
        if isinstance(rhs, list):
            new_rhs = lhs + '__piecewise'
            self._set_piecewise(new_rhs, rhs)
            return new_rhs
        else:
            return self._substitute_functions(rhs)

    @classmethod
    def _substitute_functions(cls, rhs):
        new_rhs = rhs
        for old, new in cls._function_substitutions:
            new_rhs = re.sub(r'(?<!\w){}(?!\w)'.format(old), new, rhs)
        return new_rhs

    @classmethod
    def _split_args(cls, arglist):
        """
        Split arg list into groups based on ',', while respecting parentheses
        """
        argvals = []
        depth = 1
        start_token = 0
        end_of_arglist = len(arglist)
        for i, c in enumerate(arglist):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    end_of_arglist = i
                    break
            elif c == ',' and depth == 1:
                argvals.append(arglist[start_token:i].strip())
                start_token = i + 1
        arg = arglist[start_token:end_of_arglist].strip()
        if arg:
            argvals.append(arg)
        return argvals, arglist[:end_of_arglist]

    @classmethod
    def _units2SI(cls, units):
        if isinstance(units, pq.Quantity):
            units = units.units[4:]  # Strip leading '1.0 ' from units string
        units = units.strip()
        if units == '1' or units is None or units == 'dimensionless':
            return None, 0
        if units.startswith('/'):
            units = '1.0' + units
        units = cls._sanitize_units(units)
        si_units = pq.Quantity(1, units).simplified
        dimension = pq.Quantity(1, si_units._dimensionality)
        power = int(log10(si_units / dimension))
        return str(si_units._dimensionality), power

    @classmethod
    def _units2nineml_units(cls, units):
        dim_str, power = cls._units2SI(units)
        try:
            dim = _SI_to_dimension[dim_str]
        except KeyError:
            raise Pype9RuntimeError(
                "Unrecognised dimension from units '{}'('{}')"
                .format(units, dim_str))
        return _SI_to_nineml_units[(dim, power)]

    @classmethod
    def _units2dimension(cls, units):
        dim_str, _ = cls._units2SI(units)
        return _SI_to_dimension[dim_str]

    @classmethod
    def _sanitize_units(cls, units):
        if units == '1' or units == 1:
            return 'dimensionless'
        if units == 'mv':
            units = 'mV'
        units = units.strip()
        if units.startswith('/'):
            units = '1' + units
        units = re.sub(r'([a-zA-Z])([0-9\.]+)', r'\1^\2', units)
        if '-' in units:
            begin, end = units.split('-')
            units = "({})/{}".format(begin, end)
        units = re.sub(r'(?<=\d) +(?=\w)', r'*', units)
        return units

    @classmethod
    def _iterate_block(cls, block):
        for line in block:
            line = line.strip().split(':')[0]
            line = line.replace('\t', ' ')
            if line:
                yield line

    @classmethod
    def _matching_braces(cls, line_iter, line='', multiline_pre=True):
        depth = 0
        preamble = ''
        block = []
        while True:
            start_index = 0
            for j, c in enumerate(line):
                if c == '{':
                    if depth == 0:
                        start_index = j + 1
                        preamble += line[:j]
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        if line[start_index:j].strip():
                            block.append(line[start_index:j].strip())
                        line = line[j + 1:]
                        yield preamble, block, line
                        preamble = ''
                        block = []
                        continue
            if depth:
                if line[start_index:].strip():
                    block.append(line[start_index:].strip())
            elif line and multiline_pre:
                preamble += line + '\n'
            try:
                line = next(line_iter)
            except StopIteration:
                if depth:
                    raise Pype9RuntimeError(
                        "Block ended inside enclosing brace: \n{}"
                        .format(block))
                else:
                    raise StopIteration

    @classmethod
    def _matching_parentheses(cls, string):
        depth = 0
        for i, c in enumerate(string):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    output = string[:i + 1]
                    return output
        raise Pype9RuntimeError(
            "No matching ')' found for opening '(' in string " "'{}'"
            .format(string))

    @classmethod
    def _args_suffix(self, arg_vals):
        suffix = ''
        for a in arg_vals:
            a = re.sub(r' *\+ *', '__p__', a)
            a = re.sub(r' *\- *', '__m__', a)
            a = re.sub(r' *\* *', '__x__', a)
            a = re.sub(r' *\/ *', '__d__', a)
            a = re.sub(r' *\( *', '__o__', a)
            a = re.sub(r' *\) *', '__c__', a)
            a = re.sub(r'(?=\w)\[(.*)\]', '__elem\1', a)
            a = re.sub(r'[\. ]', '_', a)
            suffix += '_' + a
        return suffix
