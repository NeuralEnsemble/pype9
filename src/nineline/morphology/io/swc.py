import numpy

class SWCTree:
    
    class Section:
        def __init__(self, section_id, coord, radius, parent):
            self.id = section_id
            self.coord = coord
            self.parent = parent
            self.radius = radius
            self.children = list()
            if parent:
                parent.children.append(self)

        def has_child(self):
            return len(self.children)

        def is_branch_start(self):
            return len(self.parent.children) > 1

        def is_branch_end(self):
            return not len(self.children)

        def is_fork(self):
            return len(self.children) > 1

        def endpoints(self):
            if self.is_branch_start():
                start = self.parent.coord
            else:
                start = (self.parent.coord + self.coord) / 2.0
            if self.is_fork() or self.is_branch_end():
                end = self.coord
            else:
                end = (self.coord + self.children[0].coord) / 2.0
            return (start, end)

        def length(self):
            epoints = self.endpoints()
            return numpy.sqrt(numpy.sum(numpy.square(epoints[1] - epoints[0])))

        def volume(self):
            return self.length() * numpy.pi * (self.radius * self.radius)


    def __init__(self, filename=None, skip_axon=True):
        self.start = None
        ## Stores all the sections of the tree in a dictionary indexed by the SWC ID
        self.dendrite_sections = dict()
        self.axon_sections = dict()
        self.soma_sections = dict()
        self.min_bounds = numpy.ones(3) * float('inf')
        self.max_bounds = numpy.ones(3) * float('-inf')
        if filename:
            self.load(filename, skip_axon=skip_axon)

    def load(self, filename, skip_axon=True, verbose=True):
        with open(filename, 'r') as f:
            self.dendrite_sections = dict()
            self.axon_sections = dict()
            self.soma_sections = dict()
            line_count = 0
            while True:
                line = f.readline()
                if not line:
                    break
                if line[0] != '#':
                    line_count = line_count + 1
                    contents = line.split()
                    if len(contents) != 7:
                        raise Exception ('Incorrect number of values (%d) on line %d' % 
                                         (len(contents), line_count))
                    section_id = int(contents[0])
                    section_type = int(contents[1])
                    coord = numpy.array(contents[2:5], dtype=float)
                    radius = float(contents[5])
                    parent_id = int(contents[6])
                    if section_type == 1:
                        # If section is part of soma add it to list so that the dendritic sections 
                        # can Note that the "radius" of soma sections is not relevant as it does not 
                        # correspond to the radius of the actual soma
                        self.soma_sections[section_id] = SWCTree.Section(section_id, coord,
                                                                         float('NaN'), None)
                    elif section_type == 2 or section_type == 3:
                        if skip_axon and section_type == 2:
                            if verbose:
                                print "Skipped axon on line %d" % line_count
                        else:
                            if section_type == 2:
                                section_dict = self.axon_sections
                            else:
                                section_dict = self.dendrite_sections
                            # Save the minimum and maximum bounds of the dendritic tree
                            for d in xrange(3):
                                if coord[d] < self.min_bounds[d]:
                                    self.min_bounds[d] = coord[d]
                                if coord[d] > self.max_bounds[d]:
                                    self.max_bounds[d] = coord[d]
                            if parent_id == -1:
                                self.start = SWCTree.Section(section_id, coord, float('NaN'), None)
                                parent = self.start
                            elif parent_id in self.soma_sections.keys():
                                self.start = self.soma_sections[parent_id]
                                parent = self.start
                            else:
                                parent = section_dict[parent_id]
                            section_dict[section_id] = SWCTree.Section(section_id, coord, radius, 
                                                                       parent)    
                    else:
                        raise Exception('Unrecognised section type (%d)' % section_type)
            print 'Loaded %d sections (%d) from file: %s' % (line_count, 
                                                             len(self.dendrite_sections), filename)


    def save_NeurolucidaXML(self, filename):
        """
        Saves the SWC tree into the Neurolucida XML file format
        
        @param filename [str]: The path of the file to save the xml to
        """
        print "Writing dendritic tree to xml file '{}'...".format(filename)
        # Define helper function 'write_branch_xml' used in recursive loop
        def write_branch_xml(f, branch, indent):
            if numpy.isnan(branch.radius):
                diam = branch.children[0].radius * 2.0
            else:
                diam = branch.radius * 2.0
            f.write('{indent}<point x="{coord[0]}" y="{coord[1]}" z="{coord[2]}" d="{diam}" />\n'
                    .format(indent=indent, coord=branch.coord, diam=diam))
            if branch.is_fork():
                f.write('{indent}<branch>\n'.format(indent=indent))
                for child in branch.children:
                    write_branch_xml(f, child, indent + '    ')
                f.write('{indent}</branch>\n'.format(indent=indent))
            elif not branch.is_branch_end():
                write_branch_xml(f, branch.children[0], indent)
        # Open up the file and write all the branches
        with open(filename, 'w') as f:
            f.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n'
                    '<mbf version="4.0" xmlns="http://www.mbfbioscience.com/2007/neurolucida" '
                    'xmlns:nl="http://www.mbfbioscience.com/2007/neurolucida" appname="Neurolucida" '
                    'appversion="10.40 (64-bit)">\n')
            f.write("<!-- Generated xml file from '{}' SWC file -->\n".format(filename))
            f.write('<tree  type="Dendrite" leaf="Normal">\n')
            write_branch_xml(f, self.start, '    ')
            f.write("</tree>\n</mbf>\n")
        print "Finished writing tree"
        
        
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', type=str, help="Input filename (swc format)")
    parser.add_argument('output_file', type=str, help="Output filename (neurolucida XML format)")
    args = parser.parse_args()
    tree = SWCTree(args.input_file, skip_axon=False)
    tree.save_NeurolucidaXML(args.output_file)
    print "Converted '{}' from SWC format to '{}' in NeurolucidaXML format".format(args.input_file,
                                                                                   args.output_file)
