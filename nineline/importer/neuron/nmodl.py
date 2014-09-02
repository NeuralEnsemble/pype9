import re
import operator
import quantities as pq
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
celsius_re = re.compile(r'[^a-zA-Z0-9_]celsius[^a-zA-Z0-9_]')
title_re = re.compile(r"TITLE (.*)")
comments_re = re.compile(r"COMMENT(.*)ENDCOMMENT")

_SI_to_dimension = {'m/s': 'conductance',
                    'kg*m**2/(s**3*A)': 'voltage',
                    'mol/m**3': 'concentration',
                    'A/m**2': 'membrane_current',
                    's': 'time',
                    'K': 'absolute_temperature',
                    None: None}


def units2dimension(units):
    units = re.sub(r'([a-zA-Z])([0-9\.]+)', r'\1^\2', units)
    si_units = str(pq.Quantity(1, units).simplified).split()[1]
    return _SI_to_dimension[si_units]


class Importer(object):
    """
    Imports NMODL files into lib9ml structures
    """

    def __init__(self, fname):
        with open(fname) as f:
            self.contents = f.read()
        self._read_title()
        self._read_comments()
        self._read_blocks()
        self.aliases = {}
        self._extract_units_block()
        self._extract_procedure_and_function_blocks()
        self._extract_assigned_block()
        self._extract_parameter_block()
        self._extract_initial_block()
        self._extract_state_block()
        self._extract_neuron_block()
        self._extract_derivative_block()
        self._extract_breakpoint_block()
        self._create_ports_for_reserved_keywords()

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
        match = comments_re.search(self.contents, re.DOTALL)
        self.comments = match.group(1) if match else ''

    def _read_blocks(self):
        self.blocks = defaultdict(dict)
        for decl, contents, _ in self._matching_braces(iter(self.contents),
                                                     multiline_preamble=False):
            match = re.match(r" *([a-zA-Z_]+)([a-zA-Z_ \(\)0-9]*){(.*?)}",
                             decl)
            if match.group(2):
                self.blocks[match.group(1)][match.group(2)] = contents
            else:
                self.blocks[match.group(1)] = contents
#         # Read code blocks
#         match = re.findall(r"([a-zA-Z_]+)([a-zA-Z_ \(\)0-9]*){(.*?)}",
#                            self.contents, re.DOTALL)
#         for btype, bname, bcontents in match:
#             # If block has a name associated with it create a dictionary for
#             # this block type
#             if bname.strip():
#                 self.blocks[btype] = self.blocks.get(btype, {})
#                 self.blocks[btype][bname.strip()] = bcontents
#             else:
#                 self.blocks[btype] = bcontents
#         stripargs_re = re.compile('\(.*')
#         self.procedure_names = [stripargs_re.sub('', s)
#                                 for s in self.blocks['PROCEDURE'].keys()]

    @classmethod
    def _matching_braces(cls, line_iter, line='', multiline_preamble=True):
        depth = 0
        block = []
        preamble = ''
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
                        block.append(line[:j])
                        line = line[j + 1:]
                        yield preamble, block, line
                        continue
            if depth:
                if len(line) > start_index:
                    block.append(line[start_index:])
            elif line and multiline_preamble:
                preamble += line + '\n'
            try:
                line = next(line_iter)
            except StopIteration:
                if depth:
                    raise Exception("Block ended inside enclosing brace: \n{}"
                                    .format(block))
                else:
                    raise StopIteration

    def _extract_procedure_and_function_blocks(self):
        # Read functions
        self.functions = {}
        self.procedures = {}
        for blck_type, dct in (('FUNCTION', self.functions),
                                ('PROCEDURE', self.procedures)):
            for signature, block in self.blocks.get(blck_type, {}).iteritems():
                i = signature.find('(')
                name = signature[:i].strip()
                args = [a.split('(')[0]
                        for a in list_re.split(signature[i + 1:-1])]
                dct[name] = (args, block)

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

    def _extract_expr_block(self, block, subs=[], suffix=''):
        expressions = {}
        line_iter = self.iterate_block(block)
        try:
            line = next(line_iter)
        except StopIteration:
            line = None
        while line:
            if line.startswith('TABLE'):
                line = next(line_iter)
                continue  # TODO: Do I need to do something with this?
            parts = assign_re.split(line)
            if len(parts) == 1:
                expr = parts[0]
                match = re.match(r'([a-zA-Z][a-zA-Z0-9]*) *\((.*)\)', expr)
                # If a procedure
                if not match:
                    raise Exception("Unrecognised statement on line '{}'"
                                    .format(line))
                if match.group(1) == 'if':
                    test = match.group(2)
                    subblock, next_line = self._until_matching_brace(line,
                                                                     line_iter)
                    while not next_line.strip():
                        next_line = next(line_iter)
                    if re.search(r'(^|[^a-zA-Z0-9])else($|[^a-zA-Z0-9])',
                                 next_line):
                        match = re.search(r'else +if +\((.*)\)'. next_line)
                        if match:
                            pass
                elif match.group(1) in ('for', 'while'):
                    raise Exception("Cannot represent '{}' statements in 9ML"
                                    .format(match.group(1)))
                else:
                    try:
                        pargs, pbody = self.procedures[match.group(1)]
                    except KeyError:
                        raise Exception("Unrecognised procedure '{}'"
                                        .format(match.group(1)))
                    argvals = list_re.split(match.group(2))
                    psuffix = suffix + self._args_suffix(argvals)
                    pexprs = self._extract_expr_block(pbody,
                                                      subs=zip(pargs, argvals),
                                                      suffix=psuffix)
                    # Add aliases from procedure to list of substitutions in
                    # order to append the suffixes
                    subs = subs + [(lhs[:-len(psuffix)], lhs)
                                   for lhs in pexprs.iterkeys()]
                    expressions.update(pexprs)
            elif len(parts) == 2:  # Assume to be an assignment expression
                lhs, rhs = parts
                # Replace arguments with their values
                for old, new in subs:
                    rhs = self._subs_variable(old, new, rhs)
                # Expand function definitions, creating extra aliases for all
                # expressions within the function body
                for fname, (fargs, fbody) in self.functions.iteritems():
                    for match in re.findall("({} *)\((.*)\)".format(fname),
                                            rhs):
                        argvals = list_re.split(match[1])
                        fsuffix = suffix + self._args_suffix(argvals)
                        fexprs = self._extract_expr_block(fbody,
                                                          subs=zip(fargs,
                                                                   argvals),
                                                          suffix=fsuffix)
                        expressions.update(fexprs)
                        rhs = rhs.replace('{}({})'.format(*match),
                                          fname + fsuffix)
                if lhs + suffix in expressions:
                    rhs = self._subs_variable(lhs, '(' +
                                              expressions[lhs + suffix] + ')',
                                              rhs)
                expressions[lhs + suffix] = rhs
            else:
                raise Exception("More than one '=' found on line '{}'"
                                .format(line))
            line = next(line_iter)
        return expressions

    @classmethod
    def _args_suffix(self, arg_vals):
        return '_' + '_'.join(re.sub(r'\-\.', '_', a) for a in arg_vals)

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
        self.dimensions = {}
        for line in self.iterate_block(self.blocks['ASSIGNED']):
            parts = line.strip().split()
            if len(parts) == 1:
                var = parts[0]
                dimension = None
            elif len(parts) == 2:
                var, units = parts
                units = units[1:-1]  # remove parentheses
                if units == '1':
                    dimension = None
                else:
                    dimension = units2dimension(units)
            else:
                raise Exception("Three tokens found on line '{}', was "
                                "expecting 1 or 2 (var [units])".format(line))
            self.dimensions[var] = dimension

    def _extract_parameter_block(self):
        # Read parameters
        self.parameters = {}
        for line in self.iterate_block(self.blocks['PARAMETER']):
            name, val = assign_re.split(line)
            if ' ' in val:
                val, units = val.split()
                dimension = units2dimension(units)
                self.dimensions[name] = dimension
            else:
                val = float(val)
                dimension = None
            name = name.strip()
            self.parameters[name] = Parameter(name, dimension=dimension)

    def _extract_initial_block(self):
        # Read initial block
        self._raw_initial = self._extract_expr_block(self.blocks['INITIAL'])

    def _extract_state_block(self):
        # Read state variables
        self.state_variables = {}
        for line in self.iterate_block(self.blocks['STATE']):
            var = line.strip()
            initial = self._raw_initial.pop(var)
            if len(initial.split()) != 1:  # Can't remember why this would be
                raise Exception("Cannot currently handle expression "
                                "initialisation of states ({} = {})"
                                .format(var, initial))
            dimension = self.dimensions[var] = self.dimensions[initial]
            self.state_variables[var] = StateVariable(var, dimension=dimension,
                                                      initial=initial)
        self.aliases.update((lhs, Alias(lhs, rhs))
                            for lhs, rhs in self._raw_initial.iteritems())

    def _extract_neuron_block(self):
        self.used_ions = {}
        # Read the NEURON block
        for line in self.iterate_block(self.blocks['NEURON']):
            if line.startswith('SUFFIX'):
                self.component_name = line.split()[1]
            elif line.startswith('RANGE'):
                self.analog_ports = [AnalogPort(var, mode='send',
                                                dimension=self.dimensions[var])
                                     for var in list_re.split(line[6:])]
            elif line.startswith('USEION'):
                name = re.match('USEION (.*) READ', line).group(1)
                match = re.match('.*READ (.*) WRITE.*', line)
                read = list_re.split(match.group(1)) if match else []
                match = re.match('.*WRITE (.*)', line)
                write = list_re.split(match.group(1)) if match else []
                self.used_ions[name] = (read, write)
            elif line.startswith('GLOBAL'):
                self.globals = [var for var in list_re.split(line[7:])]
        ion_vars = reduce(operator.add,
                          [r + w for r, w in self.used_ions.itervalues()])
        # Filter out not actual range variables
        self.analog_ports = [p for p in self.analog_ports
                             if (p.name not in self.parameters and
                                 p.name not in ion_vars)]
        # Add used ions to analog ports
        for read, write in self.used_ions.itervalues():
            for n in read:
                self.analog_ports.append(AnalogPort(n, mode='recv',
                                                    dimension='concentration'))
            for n in write:
                self.analog_ports.append(AnalogPort(n, mode='send',
                                                 dimension='membrane_current'))

    def _extract_derivative_block(self):
        self.regimes = []
        # Read derivative
        for name, block in self.blocks['DERIVATIVE'].iteritems():
            time_derivatives = []
            # Extract aliases and states
            expressions = self._extract_expr_block(block)
            # Detect state derivatives
            for lhs, rhs in expressions.iteritems():
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
        self.solve_methods = {}
        reduced_block = ''
        for line in self.iterate_block(self.blocks['BREAKPOINT']):
            if line.startswith('SOLVE'):
                match = re.match(r'SOLVE ([a-zA-Z0-9_]+) '
                                 r'METHOD ([a-zA-Z0-9_]+)', line)
                if not match:
                    raise Exception("Could not read solve statement '{}'"
                                    .format(line))
                self.solve_methods[match.group(1)] = match.group(2)
            else:
                reduced_block += line + '\n'
        expressions = self._extract_expr_block(reduced_block)
        self.aliases.update((lhs, Alias(lhs, rhs))
                            for lhs, rhs in expressions.iteritems())

    @classmethod
    def iterate_block(cls, block):
        for line in newline_re.split(block):
            line = line.strip().split(':')[0]
            if line:
                yield line

    def _create_ports_for_reserved_keywords(self):
        uses_celsius = False
        uses_voltage = False
        # If 'celsius' or 'v' appears anywhere in the file add them to the
        # receive ports
        for alias in self.aliases.itervalues():
            if re.search(r'(?:^|[^a-zA-Z0-9_])celsius(?:[^a-zA-Z0-9_]|$)',
                         alias.rhs):
                uses_celsius = True
            if re.search(r'(?:^|[^a-zA-Z0-9_])v(?:[^a-zA-Z0-9_]|$)',
                         alias.rhs):
                uses_voltage = True
        if uses_voltage:
            self.analog_ports.append(AnalogPort('v', mode='recv',
                                        dimension='concentration'))
        if uses_celsius:
            self.analog_ports.append(AnalogPort('celsius', mode='recv',
                                         dimension='absolute_temperature'))


if __name__ == '__main__':
    import sys
    componentclass = Importer(sys.argv[1]).get_component()
    componentclass.write(sys.argv[2])
    print componentclass
