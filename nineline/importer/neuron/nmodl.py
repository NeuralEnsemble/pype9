

def import_from_nmodl(fname):
    with open(fname) as f:
        data = f.read()

if __name__ == '__main__':
    import sys
    import_from_nmodl(sys.argv[1])