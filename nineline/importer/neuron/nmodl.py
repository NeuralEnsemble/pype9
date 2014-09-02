import re
import operator
import quantities as pq
from nineml.abstraction_layer.components.interface import Parameter
from nineml.abstraction_layer.dynamics.component import ComponentClass
from nineml.abstraction_layer.dynamics import Regime, StateVariable
from nineml.abstraction_layer.dynamics.component.expressions import (Alias,
                                                                TimeDerivative)
from nineml.abstraction_layer.dynamics.component.ports import AnalogPort


newline_re = re.compile(r" *[\n\r]+ *")
assign_re = re.compile(r" *= *")
list_re = re.compile(r" *, *")
celsius_re = re.compile(r'[^a-zA-Z0-9]celsius[^a-zA-Z0-9]')

_SI_to_dimension = {'m/s': 'conductance', None: None,
                    'kg*m**2/(s**3*A)': 'voltage',
                    'mol/m**3': 'concentration',
                    'A/m**2': 'membrane_current', 's': 'time',
                    'K': 'absolute_temperature'}


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
        match = re.search(r"TITLE (.*)", self.contents, re.MULTILINE)
        self.title = match.group(1) if match else ''

    def _read_comments(self):
        match = re.search(r"COMMENT(.*)ENDCOMMENT", self.contents, re.DOTALL)
        self.comments = match.group(1) if match else ''

    def _read_blocks(self):
        self.blocks = {}
            # Read code blocks
        match = re.findall(r"([a-zA-Z_]+)([a-zA-Z_ \(\)0-9]*){(.*?)}",
                           self.contents, re.DOTALL)
        for btype, bname, bcontents in match:
            # If block has a name associated with it create a dictionary for
            # this block type
            if bname.strip():
                self.blocks[btype] = self.blocks.get(btype, {})
                self.blocks[btype][bname.strip()] = bcontents
            else:
                self.blocks[btype] = bcontents
        stripargs_re = re.compile('\(.*')
        self.procedure_names = [stripargs_re.sub('', s)
                                for s in self.blocks['PROCEDURE'].keys()]

    def _extract_expr(self, line):
        parts = assign_re.split(line)
        if len(parts) == 2:
            var, expr = parts
        elif len(parts) == 1:
            var = None
            expr = parts[0].strip()
            match = re.match(r'([a-zA-Z][a-zA-Z0-9]*) *\((.*)\)', expr)
            if match:
                if match.group(1) not in self.procedure_names:
                    raise Exception("Unrecognised procedure '{}'"
                                    .format(match.group(1)))
                else:
                    print "need to process args ({})".format(match.group(2))
            else:
                raise Exception("Cannot process line '{}'".format(line))
        else:
            raise Exception("More than one '=' found on line '{}'"
                            .format(line))
        for funcname, (func_args,
                       func_aliases, out) in self.functions.iteritems():
            match = re.search("{} *\((.*)\)".format(funcname), expr)
            if match:
                arg_vals = list_re.split(match.group(1))
                for al_var, al_expr in func_aliases:
                    for arg_var, arg_val in zip(func_args, arg_vals):
                        al_expr = al_expr.replace(arg_var, arg_val)
                    self.aliases[al_var] = Alias(al_var, al_expr)
                self.aliases[funcname] = Alias(funcname, out)
                expr = expr.replace(match.group(0), funcname)
        if var and re.search(r'([^a-zA-z0-9]|^){}([^a-zA-z0-9]|$)'.format(var),
                            expr):
            if var not in self.aliases:
                raise Exception("Assignment references itself but hasn't been "
                                "previously defined '{}' = '{}'"
                                .format(var, expr))
            expr = re.sub(r'([^a-zA-z0-9]|^){}([^a-zA-z0-9]|$)'.format(var),
                          r'\1({})\2'.format(self.aliases[var].rhs), expr)
        expr = expr.strip()
        return var, expr

    def _extract_procedure_and_function_blocks(self):
        # Read functions
        self.functions = {}
        for blck_type, dct in (('FUNCTION', self.functions),
                                ('PROCEDURE', self.procedures)):
            for signature, block in self.blocks.get(blck_type, {}).iteritems():
                i = signature.find('(')
                name = signature[:i].strip()
                args = list_re.split(signature[i + 1:-1])
                dct[name] = (args, block)

    def _extract_expr_block(self, block, subs={}, suffix=''):
        expressions = {}
        for line in self.iterate_block(block):
            if line.startswith('TABLE'):
                continue  # TODO: Do I need to do something with this?
            parts = assign_re.split(line)
            if len(parts) == 1:
                expr = parts[0]
                match = re.match(r'([a-zA-Z][a-zA-Z0-9]*) *\((.*)\)', expr)
                # If a procedure
                if match:
                    try:
                        pargs, pbody = self.procedures[match.group(1)]
                    except KeyError:
                        raise Exception("Unrecognised procedure '{}'"
                                        .format(match.group(1)))
                    arg_vals = list_re.split(match.group(2))
                    psuffix = self._args_suffix(arg_vals)
                    pexprs = self._extract_expr_block(
                                                     self.iterate_block(pbody),
                                                     subs=zip(pargs, arg_vals),
                                                     suffix=psuffix)
                    expressions.extend(pexprs)
                else:
                    if re.search(r'[^a-zA-Z0-9]if[^a-zA-Z0-9]', expr):
                        raise NotImplementedError
                    elif (re.search(r'[^a-zA-Z0-9]for[^a-zA-Z0-9]', expr) or
                          re.search(r'[^a-zA-Z0-9]while[^a-zA-Z0-9]', expr)):
                        raise Exception("Cannot convert 'for' or 'while' "
                                        "statements ({})".format(line))
                    else:
                        raise Exception("Unrecognised statement on line '{}'"
                                        .format(line))
            elif len(parts) == 2:  # Assume to be an assignment expression
                lhs, rhs = parts
                # Replace arguments with their values
                for old, new in subs:
                    rhs = re.sub(r'[^a-zA-Z0-9]{}[^a-zA-Z0-9]'.format(old),
                                 r'\1{}\2'.format(new), rhs)
                # Expand function definitions, creating extra aliases for all
                # expressions within the function body
                for fname, (fargs, fbody) in self.functions.iteritems():
                    for match in re.findall("{} *\((.*)\)".format(fname), rhs):
                        arg_vals = list_re.split(match[1])
                        fsuffix = self._args_suffix(arg_vals)
                        fexprs = self._extract_expr_block(
                                                     self.iterate_block(fbody),
                                                     subs=zip(fargs, arg_vals),
                                                     suffix=fsuffix)
                        expressions.extend(fexprs)
                        rhs = rhs.replace(match[0], fname + fsuffix)
                expressions[lhs + suffix] = rhs
            else:
                raise Exception("More than one '=' found on line '{}'"
                                .format(line))
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
            var, units = line.strip().split()
            units = units[1:-1]  # remove parentheses
            if units == '1':
                dimension = None
            else:
                dimension = units2dimension(units)
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
        self.initial_states = self._extract_expr_block(self.blocks['INITIAL'])

    def _extract_state_block(self):
        # Read state variables
        self.state_variables = {}
        for line in self.iterate_block(self.blocks['STATE']):
            var = line.strip()
            initial = self.initial_states.pop(var)
            if len(initial.split()) != 1:  # Can't remember why this would be
                raise Exception("Cannot currently handle expression "
                                "initialisation of states ({} = {})"
                                .format(var, initial))
            dimension = self.dimensions[var] = self.dimensions[initial]
        self.state_variables[var] = StateVariable(var, dimension=dimension,
                                                  initial=initial)
        # Treat the rest of the initial block as aliases
        for var, expr in self.initial_states.iteritems():
            self.aliases[var] = Alias(var, expr)

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
            aliases = self._extract_expr_block(block)
            # Detect state derivatives
            for var, expr in aliases:
                if var.endswith("'"):
                    if var not in self.state_variables:
                        raise Exception("Unrecognised variable '{}'"
                                        .format(var))
                    time_derivatives.append(TimeDerivative(var[:-1], expr))
            # Remove time derivatives from aliases and append to aliases dict
            for td in time_derivatives:
                del aliases[td.name]
            self.aliases.update(aliases)
        regime = Regime(name=name, time_derivatives=time_derivatives)
        self.regimes.append(regime)

    def _extract_breakpoint_block(self):
        # Read Breakpoint
        bpoint_aliases = self._extract_expr_block(self.blocks['BREAKPOINT'])
        self.aliases.extend(bpoint_aliases)

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
            if re.search(r'(?:^|[^a-zA-Z0-9])celsius(?:[^a-zA-Z0-9]|$)',
                         alias.rhs):
                uses_celsius = True
            if re.search(r'(?:^|[^a-zA-Z0-9])v(?:[^a-zA-Z0-9]|$)', alias.rhs):
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
