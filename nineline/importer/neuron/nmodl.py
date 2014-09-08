import re
import operator
import quantities as pq
import collections
from nineml.abstraction_layer.components.interface import Parameter
from nineml.abstraction_layer.dynamics.component import ComponentClass
from nineml.abstraction_layer.dynamics import Regime, StateVariable
from nineml.abstraction_layer.dynamics.component.expressions import (Alias,
                                                                TimeDerivative)
from nineml.abstraction_layer.dynamics.component.ports import AnalogPort
from collections import defaultdict


newline_re = re.compile(r" *[\n\r]+ *")
assign_re = re.compile(r" *= *")
list_re = re.compile(r" *, *")
celsius_re = re.compile(r'(\W|^)celsius(\W|$)')
title_re = re.compile(r"TITLE (.*)")
comments_re = re.compile(r"COMMENT(.*)ENDCOMMENT")
whitespace_re = re.compile(r'\s')
getitem_re = re.compile(r'(\w+)\[(\d+)\]')

_SI_to_dimension = {'m/s': 'conductance',
                    'kg*m**2/(s**3*A)': 'voltage',
                    'mol/m**3': 'concentration',
                    'A/m**2': 'membrane_current',
                    's': 'time',
                    'K': 'absolute_temperature',
                    'kg/(m**3*s)': 'flux',
                    '1/(s*A)': 'mass_per_charge',
                    'm': 'length',
                    's**3*A**2/(kg*m**4)': 'membrane_conductance',
                    'A': 'current',
                    'A/s': 'change_in_current',
                    's**3*A**2/(kg*m**2)': 'conductance',
                    '1/s': 'frequency',
                    None: None}


def units2dimension(units):
    if units == '1':
        return None
    units = re.sub(r'([a-zA-Z])([0-9\.]+)', r'\1^\2', units)
    si_units = str(pq.Quantity(1, units).simplified._dimensionality)
    return _SI_to_dimension[si_units]


class NMODLImporter(object):
    """
    Imports NMODL files into lib9ml structures
    """

    # This is used to differentiate a state assigment in a NET_RECEIVE block
    # from a regular alias
    StateAssignment = collections.namedtuple("StateAssignment", "variable")

    class NonOverwriteDict(dict):

        def __setitem__(self, key, val):
            assert key not in self or val.rhs == self[key].rhs, \
                                               "Attempting to overwrite alias"
            super(NMODLImporter.NonOverwriteDict, self).__setitem__(key, val)

    def __init__(self, fname):
        # Read file
        with open(fname) as f:
            self.contents = f.read()
        # Parse file contents into blocks
        self._read_title()
        self._read_comments()
        self._read_blocks()
        # Initialise members
        self.functions = {}
        self.procedures = {}
        self.aliases = self.NonOverwriteDict()
        self.parameters = {}
        self.dimensions = {}
        self.state_variables = {}
        self.used_ions = {}
        self.solve_methods = {}
        self.analog_ports = []
        self.regimes = []
        self.on_trigger = None
        # Extract declarations and expressions from blocks into members
        self._extract_units_block()
        self._extract_procedure_and_function_blocks()
        self._extract_assigned_block()
        self._extract_parameter_block()
        self._extract_initial_block()
        self._extract_state_block()
        self._extract_neuron_block()
        self._extract_derivative_block()
        self._extract_breakpoint_block()
        self._extract_netreceive_block()
        self._create_analog_ports()

    def get_component(self):
        return ComponentClass(name=self.component_name,
                              parameters=self.parameters.values(),
                              analog_ports=self.analog_ports,
                              regimes=self.regimes,
                              aliases=self.aliases.values(),
                              state_variables=self.state_variables)
        print "Title: {}\nComments: {}\nBlocks: {}".format(self.title,
                                                           self.comments)

    def _read_title(self):
        # Extract title and comments if present
        match = title_re.search(self.contents, re.MULTILINE)
        self.title = match.group(1) if match else ''

    def _read_comments(self):
        self.comments = []
        for cmt in comments_re.findall(self.contents, re.DOTALL | re.MULTILINE):
            self.comments.append(cmt)

    def _read_blocks(self):
        self.blocks = defaultdict(dict)
        line_iter = iter(self.contents.splitlines())
        for decl, contents, _ in self._matching_braces(line_iter,
                                                       multiline_pre=False):
            match = re.match(r" *([a-zA-Z_]+)([a-zA-Z_ \(\)0-9]*)",
                             decl)
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

    def _extract_procedure_and_function_blocks(self):
        # Read functions
        for blck_type, dct in (('FUNCTION', self.functions),
                                ('PROCEDURE', self.procedures)):
            for signature, block in self.blocks.get(blck_type, {}).iteritems():
                i = signature.find('(')
                name = signature[:i].strip()
                args = [a.split('(')[0]
                        for a in list_re.split(signature[i + 1:-1])]
                dct[name] = (args, block)

    def _extract_units_block(self):
        # Read the unit aliases
        for line in self.iterate_block(self.blocks['UNITS']):
            if line.strip():
                alias, unitname = (s.strip()[1:-1]
                                   for s in assign_re.split(line))
                try:
                    pq.Quantity(1, alias)
                except:
                    try:
                        # Add alias to quantities object
                        unit = pq.Quantity(1, unitname)
                        unit.aliases.append(alias)
                    except:
                        raise Exception("Unrecognised unit '{}'"
                                        .format(unitname))

    def _extract_assigned_block(self):
        # Read the assigned block for analog out ports
        for line in self.iterate_block(self.blocks['ASSIGNED']):
            parts = line.strip().split('(')
            if len(parts) == 1:
                var = parts[0]
                dimension = None
            elif len(parts) == 2:
                var, units = parts
                var = var.strip()
                units = units[:-1]  # remove parentheses
                dimension = units2dimension(units)
            else:
                raise Exception("Three tokens found on line '{}', was "
                                "expecting 1 or 2 (var [units])".format(line))
            self.dimensions[var] = dimension

    def _extract_parameter_block(self):
        # Read parameters
        for line in self.iterate_block(self.blocks['PARAMETER']):
            name, rest = assign_re.split(line)
            match = re.match(r'([\d\.e-]+)\s*(\([\d\w\.\*/]+\))?\s*'
                             r'(<[\d\.e-]+,[\d\.e-]+>)?', rest)
            default_value = float(match.group(1))
            units_str = match.group(2)
            valid_range_str = match.group(3)
            if units_str:
                dimension = units2dimension(units_str[1:-1])
                self.dimensions[name] = dimension
            else:
                dimension = None
            if valid_range_str:
                valid_range = [float(v)
                               for v in valid_range_str[1:-1].split(',')]
            else:
                valid_range = None
            name = name.strip()
            self.parameters[name] = Parameter(name, dimension=dimension,
                                              default_value=default_value,
                                              valid_range=valid_range)

    def _extract_initial_block(self):
        # Read initial block
        self._raw_initial = self._extract_stmts_block(self.blocks['INITIAL'])

    def _extract_state_block(self):
        # Read state variables
        for line in self.iterate_block(self.blocks['STATE']):
            var = line.strip()
            parts = var.split('(')
            if len(parts) == 2:
                var, units = parts
                var = var.strip()
                units = units[:-1]  # remove parentheses
                dimension = self.dimensions[var] = units2dimension(units)
                initial = self._raw_initial.pop(var)
            else:
                initial = self._raw_initial.pop(var)
                if len(initial.split()) != 1:
                    raise Exception("Cannot currently handle expression "
                                    "initialisation of states ({} = {})"
                                    .format(var, initial))
                dimension = self.dimensions[var] = self.dimensions[initial]
            self.state_variables[var] = StateVariable(var, dimension=dimension,
                                                      initial=initial)
        self.aliases.update((lhs, Alias(lhs, rhs))
                            for lhs, rhs in self._raw_initial.iteritems())

    def _extract_neuron_block(self):
        # Read the NEURON block
        self.component_name = None
        for line in self.iterate_block(self.blocks['NEURON']):
            if line.startswith('SUFFIX'):
                self.component_name = line.split()[1]
            elif line.startswith('POINT_PROCESS'):
                self.component_name = line.split()[1]
            elif line.startswith('ARTIFICIAL_CELL'):
                self.component_name = line.split()[1]
            elif line.startswith('RANGE'):
                self.range_vars = list_re.split(line[6:])
            elif line.startswith('USEION'):
                name = re.match(r'USEION ([a-zA-Z0-9_]+)', line).group(1)
                match = re.match(r'.*READ ([a-zA-Z0-9_]+)', line)
                read = list_re.split(match.group(1)) if match else []
                match = re.match(r'.*WRITE ([a-zA-Z0-9_]+)', line)
                write = list_re.split(match.group(1)) if match else []
                match = re.match(r'.*VALENCE ([0-9]+)', line)
                valence = match.group(1) if match else None
                self.used_ions[name] = (read, write, valence)
                for conc in read:
                    self.dimensions[conc] = 'concentration'
                for curr in write:
                    self.dimensions[curr] = 'membrane_current'
            elif line.startswith('NONSPECIFIC_CURRENT'):
                match = re.match(r'NONSPECIFIC_CURRENT ([a-zA-Z0-9_]+)', line)
                write = match.group(1)
                self.used_ions['__nonspecific__'] = ([], [write], None)
                self.dimensions[write] = 'membrane_current'
            elif line.startswith('GLOBAL'):
                self.globals = [var for var in list_re.split(line[7:])]

    def _extract_derivative_block(self):
        # Read derivative
        for name, block in self.blocks['DERIVATIVE'].iteritems():
            time_derivatives = []
            # Extract aliases and states
            stmts = self._extract_stmts_block(block)
            # Detect state derivatives
            for lhs, rhs in stmts.iteritems():
                if lhs.endswith("'"):
                    if lhs[:-1] not in self.state_variables:
                        raise Exception("Unrecognised variable '{}'"
                                        .format(lhs))
                    time_derivatives.append(TimeDerivative(lhs[:-1], rhs))
                else:
                    self.aliases[lhs] = Alias(lhs, rhs)
            regime = Regime(name=name, time_derivatives=time_derivatives)
            self.regimes.append(regime)

    def _extract_breakpoint_block(self):
        reduced_block = []
        for line in self.iterate_block(self.blocks['BREAKPOINT']):
            if line.startswith('SOLVE'):
                match = re.match(r'SOLVE (\w+) '
                                 r'METHOD (\w+)', line)
                if not match:
                    raise Exception("Could not read solve statement '{}'"
                                    .format(line))
                self.solve_methods[match.group(1)] = match.group(2)
            else:
                reduced_block.append(line)
        stmts = self._extract_stmts_block(reduced_block)
        self.aliases.update((lhs, Alias(lhs, rhs))
                            for lhs, rhs in stmts.iteritems())

    def _extract_netreceive_block(self):
        if self.blocks['NET_RECEIVE']:
            arg_line, block = self.blocks['NET_RECEIVE']
            stmts = self._extract_stmts_block(block)
            match = re.match(r'(\w+) *\((\w+)\)', arg_line)
            if match:
                arg = (match.group(1), match.group(2))
            else:
                arg = None
            aliases = {}
            assignments = {}
            for lhs, rhs in stmts.iteritems():
                if isinstance(lhs, self.StateAssignment):
                    assignments[lhs.variable] = rhs
                else:
                    aliases[lhs] = Alias(lhs, rhs)
            self.on_trigger = (arg, assignments, aliases)

    def _create_analog_ports(self):
        # Add range variables to analog ports
        ion_vars = reduce(operator.add,
                          [r + w for r, w, _ in self.used_ions.itervalues()])
        for var in self.range_vars:
            if var not in self.parameters and var not in ion_vars:
                if self.component_name and var == 'e' + self.component_name:
                    mode = 'recv'
                    dimension = 'voltage'
                else:
                    mode = 'send'
                try:
                    dimension = self.dimensions[var]
                except KeyError:
                    dimension = None
                self.analog_ports.append(AnalogPort(var, mode=mode,
                                                    dimension=dimension))
        # Add used ions to analog ports
        for name, (read, write, _) in self.used_ions.iteritems():
            for n in read:
                if n == 'e' + name:
                    dimension = 'voltage'
                else:
                    dimension = 'concentration'
                self.analog_ports.append(AnalogPort(n, mode='recv',
                                                    dimension=dimension))
            for n in write:
                self.analog_ports.append(AnalogPort(n, mode='send',
                                                 dimension='membrane_current'))
        uses_celsius = False
        uses_voltage = False
        # If 'celsius' or 'v' appears anywhere in the file add them to the
        # receive ports
        simple_rhs = [a.rhs for a in self.aliases.values()
                    if isinstance(a.rhs, str)]
        piecewise_rhs = [[expr for expr, _ in a.rhs]
                         for a in self.aliases.values()
                         if isinstance(a.rhs, list)]
        if piecewise_rhs:
            piecewise_rhs = reduce(operator.add, piecewise_rhs)
        all_rhs = simple_rhs + piecewise_rhs
        for rhs in all_rhs:
            if re.search(r'(?:^|[^a-zA-Z0-9_])celsius(?:[^a-zA-Z0-9_]|$)',
                         rhs):
                uses_celsius = True
            if re.search(r'(?:^|[^a-zA-Z0-9_])v(?:[^a-zA-Z0-9_]|$)',
                         rhs):
                uses_voltage = True
        if uses_voltage:
            self.analog_ports.append(AnalogPort('v', mode='recv',
                                        dimension='voltage'))
        if uses_celsius:
            self.analog_ports.append(AnalogPort('celsius', mode='recv',
                                         dimension='absolute_temperature'))

    @classmethod
    def iterate_block(cls, block):
        for line in block:
            line = line.strip().split(':')[0]
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
                        if line[:j].strip():
                            block.append(line[:j].strip())
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
                    raise Exception("Block ended inside enclosing brace: \n{}"
                                    .format(block))
                else:
                    raise StopIteration

    @classmethod
    def _args_suffix(self, arg_vals):
        return '_' + '_'.join(re.sub(r'\-\.', '_', a) for a in arg_vals)

    def _extract_stmts_block(self, block, subs=[], suffix=''):
        """
        A workhorse function that extracts all expressions from a block of
        statements and returns them in a dictionary

        `block`  -- a block of text split into lines
        `subs`   -- substitutions of variables to be made (when flattening
                    functions into assignments for example)
        `suffix` -- suffix to append to LHS names
        """
        statements = {}
        line_iter = self.iterate_block(block)
        try:
            line = next(line_iter)
        except StopIteration:
            line = None
        while line:
            if line.startswith('TABLE') or line.startswith('LOCAL'):
                try:
                    line = next(line_iter)
                except StopIteration:
                    raise Exception("TABLE statements need to appear at the "
                                    "start of the statement block")
                continue  # TODO: Do I need to do something with this?
            # Escape all array indexing
            line = getitem_re.sub(r'\1__elem\2', line)
            # Split line into lhs and rhs (if '=' is present)
            parts = assign_re.split(line)
            if len(parts) == 1:
                expr = parts[0]
                match = re.match(r'(\w+) *\((.*)\)', expr)
                # If a procedure
                if not match:
                    raise Exception("Unrecognised statement on line '{}'"
                                    .format(line))
                if match.group(1) == 'if':
                    conditional_stmts = []
                    # Loop through all sub-blocks of the if/else-if/else
                    # statement
                    for pre, sblock, nline in self._matching_braces(line_iter,
                                                                    line=line):
                        # Extract the test conditions for if and else if
                        # blocks
                        match = re.match(r'.*\((.*)\)', pre)
                        if match:
                            test = match.group(1)
                        else:
                            test = 'otherwise'
                        # Extract the statements from the sub-block
                        stmts = self._extract_stmts_block(sblock, subs, suffix)
                        # Append the test and statements to a list for
                        # processing after all blocks are processed.
                        conditional_stmts.append((test, stmts))
                        # Peek ahead at the next line and check to see whether
                        # there is an 'else' on it, and if not stop the
                        # sub-block iteration
                        try:
                            while not nline.strip():
                                nline = next(line_iter)
                        except StopIteration:
                            line = ''
                        if not re.search(r'(\W|^)else(\W|$)', nline):
                            break
                    # Collate all the variables that are assigned in each
                    # sub-block
                    common_lhss = reduce(set.intersection,
                                         (set(s.keys())
                                          for t, s in conditional_stmts))
                    # Create numbered versions of the helper statements in the
                    # sub- blocks (i.e. that don't appear in all sub-blocks)
                    for i, (test, stmts) in enumerate(conditional_stmts):
                        statements.update(('{}__{}'.format(lhs, i), rhs)
                                          for lhs, rhs in stmts.iteritems()
                                          if lhs not in common_lhss)
                    # Loop through statements that are common to all conditions
                    # and create a single piecewise statement for them
                    for lhs in common_lhss:
                        pieces = []
                        for i, (test, stmts) in enumerate(conditional_stmts):
                            rhs = stmts[lhs]
                            # Substitute in the numbered versions of the
                            # helper aliases
                            for l in stmts.iterkeys():
                                if l not in common_lhss:
                                    rhs = self._subs_variable(l,
                                                         '{}__{}'.format(l, i),
                                                         rhs)
                            pieces.append((rhs, test))
                        statements[lhs] = pieces
                    # Set the line that has been peeked at to the next line and
                    # continue to iterate through the lines
                    line = nline
                    continue
                elif match.group(1) in ('for', 'while'):
                    raise Exception("Cannot represent '{}' statements in 9ML"
                                    .format(match.group(1)))
                elif match.group(1) == 'state_discontinuity':
                    state, assignment = list_re.split(match.group(2))
                    l = '__state__ = {}'.format(assignment)
                    # Reuse the infrastructure for alias parsing for the
                    # assignment
                    expr = next(self._extract_stmts_block([l]).itervalues())
                    statements[self.StateAssignment(state)] = expr
                else:
                    try:
                        pargs, pbody = self.procedures[match.group(1)]
                    except KeyError:
                        raise Exception("Unrecognised procedure '{}'"
                                        .format(match.group(1)))
                    argvals = list_re.split(match.group(2))
                    psuffix = suffix + self._args_suffix(argvals)
                    pstmts = self._extract_stmts_block(pbody,
                                                      subs=zip(pargs, argvals),
                                                      suffix=psuffix)
                    # Add aliases from procedure to list of substitutions in
                    # order to append the suffixes
                    subs = subs + [(lhs[:-len(psuffix)], lhs)
                                   for lhs in pstmts.iterkeys()]
                    statements.update(pstmts)
            elif len(parts) == 2:  # Assume to be an assignment expression
                lhs, rhs = parts
                # Replace arguments with their values
                for old, new in subs:
                    rhs = self._subs_variable(old, new, rhs)
                # Expand function definitions, creating extra aliases for all
                # statements within the function body
                for fname, (fargs, fbody) in self.functions.iteritems():
                    for match in re.findall("({} *)\((.*)\)".format(fname),
                                            rhs):
                        argvals = list_re.split(match[1])
                        fsuffix = suffix + self._args_suffix(argvals)
                        fstmts = self._extract_stmts_block(fbody,
                                                           subs=zip(fargs,
                                                                    argvals),
                                                           suffix=fsuffix)
                        statements.update(fstmts)
                        rhs = rhs.replace('{}({})'.format(*match),
                                          fname + fsuffix)
                # Append the suffix to the left hand side
                lhs_suff = lhs + suffix
                # If the same variable has been defined previously we need to
                # give it a new name so this statement doesn't override it.
                if lhs_suff in statements:
                    tmp_lhs = lhs_suff + '__tmp'
                    count = 0
                    while tmp_lhs in statements:
                        count += 1
                        tmp_lhs = lhs_suff + '__tmp' + str(count)
                    statements[tmp_lhs] = statements[lhs_suff]
                    rhs = self._subs_variable(lhs, tmp_lhs, rhs)
                statements[lhs_suff] = rhs
            else:
                raise Exception("More than one '=' found on line '{}'"
                                .format(line))
            try:
                line = next(line_iter)
            except StopIteration:
                line = ''
        return statements

    def _subs_variable(self, old, new, expr):
        # Pad with spaces so as to avoid missed matches due to begin/end of
        # string
        expr = ' ' + expr + ' '
        expr = re.sub(r'(?<=[^a-zA-Z0-9_]){}(?=[^a-zA-Z0-9_])'.format(old),
                      new, expr)
        # Update dimensions tracking
        if old in self.dimensions:
            self.dimensions[new] = self.dimensions[old]
        return expr.strip()
