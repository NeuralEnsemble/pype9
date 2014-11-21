import sys
import re
import keyword
import os.path


def extract_tokens(rhs):
    tokens = list(t for t in re.split('[^\w\.\"\']+', rhs)
                  if t and (not t.startswith('"') and not t.endswith('"')))
    return tokens


def get_required_vars(filename):
    with open(filename) as f:
        contents = f.read()
    # Get list of used variables
    required_tokens = set(p for p in re.findall(r'{{ *([\w\.]+)', contents))
    for stmt in re.findall(r'{%\s*(.*)\s*%}', contents):
        stmt = stmt.strip()
        if stmt.startswith('for'):
            match = re.match(r'for *(\w+)(,\w+)* *in (.+) *', stmt)
            for var in ([match.group(1)] +
                        (list(match.group(2)) if match.group(2) else [])):
                required_tokens.discard(var)
            required_tokens.update(extract_tokens(match.group(3)))
        elif stmt.startswith('if'):
            match = re.match(r'if *(.+) *', stmt)
            required_tokens.update(extract_tokens(match.group(1)))
    required_tokens -= set(keyword.kwlist)
    required_vars = {}
    for tok in required_tokens:
        dct = required_vars
        for t in tok.split('.'):
            if t not in dct:
                dct[t] = {}
            dct = dct[t]
    return required_vars


def flatten_req_vars(required_vars, indent=''):
    s = ''
    for var, subvars in required_vars.iteritems():
        if not subvars:
            s += indent + str(var) + '\n'
        else:
            s += (indent + str(var) + ':\n' +
                  flatten_req_vars(subvars, indent=(indent + '  ')))
    return s


if __name__ == '__main__':
    if len(sys.argv) > 1:
        f = sys.argv[1]
    else:
        f = ('/home/tclose/git/nineline/nineline/cells/build/nest/'
                    'templates/NEST-dynamics.tmpl')
    templates_dir = os.path.join(os.getcwd(), 'templates')
    for f in os.listdir(templates_dir):
        if f.endswith('.tmpl'):
            required_vars = get_required_vars(os.path.join(templates_dir, f))
            print  '\n' + f[:-5] + '\n------------------'
            print flatten_req_vars(required_vars)
