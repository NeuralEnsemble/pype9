import re
import operator
import quantities as pq
import collections
from copy import copy
from nineml.abstraction_layer.components.interface import Parameter
from nineml.abstraction_layer.dynamics.component import ComponentClass
from nineml.abstraction_layer.dynamics import Regime, StateVariable, OnEvent
from nineml.abstraction_layer.dynamics.component.expressions import (
                                        Alias, TimeDerivative, StateAssignment)
from nineml.abstraction_layer.dynamics.component.ports import (AnalogPort,
                                                               EventPort)
from collections import defaultdict


newline_re = re.compile(r" *[\n\r]+ *")
assign_re = re.compile(r" *= *")
list_re = re.compile(r" *, *")
celsius_re = re.compile(r'(\W|^)celsius(\W|$)')
title_re = re.compile(r"TITLE (.*)")
comments_re = re.compile(r"COMMENT(.*)ENDCOMMENT")
whitespace_re = re.compile(r'\s')
getitem_re = re.compile(r'(\w+)\[(\d+)\]')


class NMODLImporter(object):
    """
    Imports NMODL files into lib9ml structures
    """

    # This is used to differentiate a state assigment in a NET_RECEIVE block
    # from a regular alias
    StateAssignment = collections.namedtuple("StateAssignment", "variable")

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

    class NoOverwriteDict(dict):
        """
        A dictionary that doesn't allow overwriting previously written values.
        Used for aliases dictonary to prevent accidental overwriting during the
        import process
        """

        def __setitem__(self, key, val):
            assert key not in self or val.rhs == self[key].rhs, \
                                               "Attempting to overwrite alias"
            super(NMODLImporter.NoOverwriteDict, self).__setitem__(key, val)

#         def update(self, d):
#             assert all(k not in self for k in d.iterkeys()), \
#                                                 "Attempting to overwrite alias"
#             super(NMODLImporter.NoOverwriteDict, self).update(d)

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
        self.aliases = self.NoOverwriteDict()  # This is done for safety
        self.constants = {}
        self.valid_parameter_ranges = {}
        self.dimensions = {}
        self.state_variables = {}
        self.used_ions = {}
        self.solve_methods = {}
        self.parameters = {}
        self.analog_ports = []
        self.event_ports = []
        self.regime_parts = []
        self.on_event_parts = None
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
        self._create_parameters_and_analog_ports()
        self._create_regimes()

    def get_component(self):
        self.print_members()
        return ComponentClass(name=self.component_name,
                              parameters=self.parameters.values(),
                              analog_ports=self.analog_ports,
                              regimes=self.regimes,
                              aliases=(self.aliases.values() +
                                       [Alias(k, v)
                                        for k, v in self.constants.items()
                                        if k not in self.parameters]),
                              state_variables=self.state_variables)

    def print_members(self):
        """
        Prints out a list of the aliases used in the component (primarily for
        debugging
        """
        print "\n\n------------------"
        print "     {}      ".format(self.component_name)
        print "------------------"
        print "\nParameters:"
        for p in self.parameters.values():
            print '{}'.format(p.name)
        print "\nReceive Analog Ports:"
        for p in self.analog_ports:
            if p.mode == 'recv':
                print '{}'.format(p.name)
        print "\nTime derivatives:"
        for r in self.regimes:
            for td in r.time_derivatives:
                print "{}' = {}".format(td.dependent_variable, td.rhs)
        print "\nAliases:"
        for a in self.aliases.itervalues():
            print '{} = {}'.format(a.lhs, a.rhs)

    def _create_regimes(self):
        if self.on_event_parts:
            assert len(self.regime_parts) == 1
            regime = self.regime_parts[0]
            parameter, assignments, aliases = self.on_event_parts  #TODO: EventPorts may need a dimension attribute(s) for incoming associated variables @IgnorePep8 @UnusedVariable
            if parameter:
                port_name, dimension = parameter
                event_port_name = port_name + "_event"
                # Create an analog port from which to read the event weight
                # from. NB: this is just a hack for now until EventPorts
                # support parameters
                self.analog_ports.append(AnalogPort(name=port_name,
                                                    mode='recv',
                                                    dimension=dimension))
            else:
                event_port_name = port_name
            self.event_ports.append(EventPort(name=event_port_name,
                                              mode='recv'))
            on_event = OnEvent(event_port_name,
                               state_assignments=['{}={}'
                                                  .format(a.lhs, a.rhs)
                                                for a in assignments.values()])
            self.aliases.update(aliases)
            self.regimes = [Regime(name=regime[0], time_derivatives=regime[1],
                                   transitions=on_event)]
        else:
            self.regimes = []
            for name, td in self.regime_parts:
                self.regimes.append(Regime(name=name, time_derivatives=td))

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
            match = re.match(r" *(\w+)([a-zA-Z_ \(\)0-9]*)",
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
                dimension = self._units2dimension(units)
            else:
                raise Exception("Three tokens found on line '{}', was "
                                "expecting 1 or 2 (var [units])".format(line))
            self.dimensions[var] = dimension

    def _extract_parameter_block(self):
        # Read constants
        for line in self.iterate_block(self.blocks['PARAMETER']):
            name, rest = assign_re.split(line)
            match = re.match(r'([\d\.e-]+)\s*(\([\d\w\.\*/]+\))?\s*'
                             r'(<[\d\.e-]+,[\d\.e-]+>)?', rest)
            name = name.strip()
            value = float(match.group(1))
            units = match.group(2)
            if units:
                units = units[1:-1]
                units = self._sanitize_units(units)
                quantity = pq.Quantity(value, units)
            else:
                quantity = pq.Quantity(value, 'dimensionless')
            self.constants[name] = quantity
            valid_range_str = match.group(3)
            if valid_range_str:
                vrange = [float(v) for v in valid_range_str[1:-1].split(',')]
                self.valid_parameter_ranges[name] = vrange

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
                dimension = self.dimensions[var] = self._units2dimension(units)
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
                name = re.match(r'USEION (\w+)', line).group(1)
                match = re.match(r'.*READ ((?:\w+(?: *\, *)?)+)', line)
                read = list_re.split(match.group(1)) if match else []
                match = re.match(r'.*WRITE ((?:\w+(?: *\, *)?)+)', line)
                write = list_re.split(match.group(1)) if match else []
                match = re.match(r'.*VALENCE (\d+)', line)
                valence = match.group(1) if match else None
                self.used_ions[name] = (read, write, valence)
                for conc in read:
                    self.dimensions[conc] = 'concentration'
                for curr in write:
                    self.dimensions[curr] = 'membrane_current'
            elif line.startswith('NONSPECIFIC_CURRENT'):
                match = re.match(r'NONSPECIFIC_CURRENT (\w+)', line)
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
            self.regime_parts.append((name, time_derivatives))

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

    def _create_parameters_and_analog_ports(self):
        # Add range variables to analog ports
        ion_vars = reduce(operator.add,
                          [r + w for r, w, _ in self.used_ions.itervalues()])
        for var in self.range_vars:
            if var in self.constants:
                constant = self.constants[var]
                dimension = self._units2dimension(str(constant.dimensionality))
                valid_range = self.valid_parameter_ranges.get(var, None)
                self.parameters[var] = Parameter(var, dimension=dimension,
                                                 valid_range=valid_range)
            elif var not in ion_vars:
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
        piecewise_rhs = [[expr for expr, _ in a.rhs if isinstance(expr, str)]
                         for a in self.aliases.values()
                         if isinstance(a.rhs, list)]
        if piecewise_rhs:
            piecewise_rhs = reduce(operator.add, piecewise_rhs)
        all_rhs = simple_rhs + piecewise_rhs
        for rhs in all_rhs:
            if re.search(r'(\b)celsius(\b)',
                         rhs):
                uses_celsius = True
            if re.search(r'(\b)v(\b)',
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
                    functions into assignments for example). A list of
                    (old, new) tuples.
        `suffix` -- suffix to append to LHS names
        """
        statements = {}
        # Get a copy of the substitutions to avoid adding to calling function
        subs = copy(subs)
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
                    raise Exception("TABLE and LOCAL statements need to appear"
                                    " at the start of the statement block")
                continue
            elif line.startswith('VERBATIM'):
                raise Exception("Cannot parse VERBATIM block:\n\n{}"
                                .format(block))
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
                        if not re.search(r'(\b)else(\b)', nline):
                            break
                    # If the final block isn't an 'else' statement, the aliases
                    # should be defined previously.
                    defined_previously = test != 'otherwise'
                    # Collate all the variables that are assigned in each
                    # sub-block
                    common_lhss = reduce(set.intersection,
                                         (set(s.keys())
                                          for t, s in conditional_stmts))
                    if len(conditional_stmts) > 2:
                        # Create numbered versions of the helper statements in
                        # the sub- blocks (i.e. that don't appear in all sub-
                        # blocks)
                        for i, (test, stmts) in enumerate(conditional_stmts):
                            branch_subs = []
                            # Get a list of substitutions to perform to unwrap
                            # the conditional block
                            for lhs, rhs in stmts.iteritems():
                                if lhs not in common_lhss:
                                    new_lhs = ('{}__branch{}{}'
                                               .format(lhs[:-len(suffix)], i,
                                                       suffix))
                                    branch_subs.append((lhs, new_lhs))
                            # Perform the substitutions on all the conditional
                            # statements
                            for old, new in branch_subs:
                                i = 1
                                # Substitute into the right-hand side equation
                                for lhs, rhs in stmts.iteritems():
                                    stmts[lhs] = self._subs_variable(old, new,
                                                                     rhs)
                                # Substitute the left-hand side
                                rhs = stmts.pop(old)
                                stmts[new] = rhs
                            # Copy all the "non-common lhs" statements, which
                            # have been escaped into their separate branches to
                            # the general statement block
                            for _, new_lhs in branch_subs:
                                rhs = stmts[new_lhs]
                                statements[new_lhs] = rhs
                    else:
                        for lhs, rhs in stmts.iteritems():
                            if lhs not in common_lhss:
                                statements[lhs] = rhs
                    # Loop through statements that are common to all conditions
                    # and create a single piecewise statement for them
                    for lhs in common_lhss:
                        pieces = []
                        for i, (test, stmts) in enumerate(conditional_stmts):
                            rhs = stmts[lhs]
#                             # Substitute in the numbered versions of the
#                             # helper aliases
#                             for l in stmts.iterkeys():
#                                 if l not in common_lhss:
#                                     rhs = self._subs_variable(l,
#                                                        '{}__{}'.format(l, i),
#                                                          rhs)
                            pieces.append((rhs, test))
                        if defined_previously:
                            if lhs in statements:
                                rhs = statements[lhs]
                            elif lhs in self.constants:
                                rhs = lhs
                                new_lhs = lhs + '_constrained'
                                subs.append((lhs, new_lhs))
                                lhs = new_lhs
                            else:
                                raise Exception("Could not find previous "
                                                "definition of '{}' to form "
                                                "otherwise condition of "
                                                "conditional block"
                                                .format(lhs))
                            pieces.append((rhs, 'otherwise'))
                        else:
                            assert lhs not in statements
                        statements[lhs] = pieces
                    # Add aliases from procedure to list of substitutions in
                    # order to append the suffixes
                    if suffix:
                        subs = subs + [(lhs[:-len(suffix)], lhs)
                                       for lhs in common_lhss]
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
                    # state assignment (substitutes in functions and arguments)
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
                    if psuffix:
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
                lhs_w_suffix = lhs + suffix
                if suffix:
                    subs.append((lhs, lhs_w_suffix))
                # If the same variable has been defined previously we need to
                # give it a new name so this statement doesn't override it.
                if lhs_w_suffix in statements:
                    tmp_lhs = lhs_w_suffix + '__tmp'
                    count = 0
                    while tmp_lhs in statements:
                        count += 1
                        tmp_lhs = lhs_w_suffix + '__tmp' + str(count)
                    statements[tmp_lhs] = statements[lhs_w_suffix]
                    rhs = self._subs_variable(lhs_w_suffix, tmp_lhs, rhs)
                statements[lhs_w_suffix] = rhs
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
        expr = re.sub(r'\b({})\b'.format(old), new, expr)
        # Update dimensions tracking
        if old in self.dimensions:
            self.dimensions[new] = self.dimensions[old]
        return expr.strip()

    @classmethod
    def _units2dimension(cls, units):
        if units == '1' or units is None or units == 'dimensionless':
            return None
        units = cls._sanitize_units(units)
        si_units = str(pq.Quantity(1, units).simplified._dimensionality)
        return cls._SI_to_dimension[si_units]

    @classmethod
    def _sanitize_units(cls, units):
        return re.sub(r'([a-zA-Z])([0-9\.]+)', r'\1^\2', units)
