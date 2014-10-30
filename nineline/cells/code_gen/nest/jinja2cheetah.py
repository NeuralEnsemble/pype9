import sys
import re
if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = ('/home/tclose/git/nineline/nineline/cells/build/nest/templates'
                '/NEST-nodes.tmpl')
with open(filename) as f:
    contents = f.read()
contents = contents.replace('$', '\$')
contents = contents.replace('#', '\#')
contents = contents.replace('{% endfor %}', '#end for')
contents = contents.replace('{% endif %}', '#end if')
contents = re.sub(r'{{([\w\.\, \(\)\'\"]+)}}', r'$\1', contents)
contents = re.sub(r'{% *(?:if) *(\w+)', r'#if $\1', contents)
contents = re.sub(r'{% *for +([\w\, ]+) +in (\w+)', r'#for \1 in $\2',
                  contents)
contents = contents.replace(' %}', '')
contents = contents.replace('\n\n#', '\n#')
contents = re.sub(r'\$attr\( *([\w\.]+) *\, *([^\)]+) *\)',
                  r'$\1[\2]', contents)
requires = set(p[1:] for p in re.findall(r'\$\w+', contents))
contents = ('#*\nThis template requires the following parameters:\n' +
            '\n'.join('  - ' + r for r in requires) +
            '\n*#' + contents)
# contents = re.sub(r'\n\s*\n', '\n', contents, re.MULTILINE)
if len(sys.argv) > 2:
    with open(sys.argv[2], 'w') as f:
        f.write(contents)
else:
    print contents
