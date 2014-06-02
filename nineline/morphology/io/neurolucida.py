
import collections
import xml.sax
from ...__init__ import XMLHandler


class NeurolucidaTreeXMLHandler(XMLHandler):

    """
    An XML handler to extract dendrite locates from Neurolucida XML format
    """
    # Create named tuples (sort of light-weight classes with no methods, like a struct in C/C++) to
    # store the extracted NeurolucidaTreeXMLHandler data.
    Point = collections.namedtuple('Point', 'x y z diam')
    Branch = collections.namedtuple('Branch', 'points sub_branches')

    def __init__(self):
        """
        Initialises the handler, saving the cell name and creating the lists to hold the _point_data
        and segment groups.
        """
        XMLHandler.__init__(self)
        self.roots = []
        self.open_branches = []

    def startElement(self, tag_name, attrs):
        """
        Overrides function in xml.sax.handler to parse all MorphML tag openings. Creates
        corresponding segment and segment-group tuples in the handler object.
        """
        if self._opening(tag_name, attrs, 'tree', required_attrs=[('type', 'Dendrite')]):
            self.open_branches.append(self.Branch([], []))
        elif self._opening(tag_name, attrs, 'branch', parents=[('tree', 'branch')]):
            branch = self.Branch([], [])
            self.open_branches[-1].sub_branches.append(branch)
            self.open_branches.append(branch)
        elif self._opening(tag_name, attrs, 'point', parents=[('tree', 'branch')]):
            self.open_branches[-1].points.append(self.Point(float(attrs['x']), float(attrs['y']),
                                                            float(attrs['z']), float(attrs['d'])))

    def endElement(self, tag_name):
        if self._closing(tag_name, 'tree', required_attrs=[('type', 'Dendrite')]):
            assert(len(self.open_branches) == 1)
            self.roots.append(self.open_branches.pop())
        elif self._closing(tag_name, 'branch', parents=[('tree', 'branch')]):
            self.open_branches.pop()
        XMLHandler.endElement(self, tag_name)


class NeurolucidaSomaXMLHandler(XMLHandler):

    """
    An XML handler to extract dendrite locates from Neurolucida XML format
    """
    # Create named tuples (sort of light-weight classes with no methods, like a struct in C/C++) to
    # store the extracted NeurolucidaTreeXMLHandler data.
    Soma = collections.namedtuple('Soma', 'index contours')
    Contour = collections.namedtuple('Contour', 'points')
    Point = collections.namedtuple('Point', 'x y z diam')

    def __init__(self):
        """
        Initialises the handler, saving the cell name and creating the lists to hold the _point_data
        and segment groups.
        """
        XMLHandler.__init__(self)
        self.somas = {}
        self.soma_count = 0

    def startElement(self, tag_name, attrs):
        """
        Overrides function in xml.sax.handler to parse all MorphML tag openings. Creates
        corresponding segment and segment-group tuples in the handler object.
        """
        if self._opening(tag_name, attrs, 'contour'):
            contour_name = attrs['name']
            if contour_name not in self.somas:
                self.somas[contour_name] = self.Soma(self.soma_count, [])
                self.soma_count += 1
            self.current_contour = self.Contour([])
            self.somas[contour_name].contours.append(self.current_contour)
        elif self._opening(tag_name, attrs, 'point', parents=[('contour')]):
            self.current_contour.points.append(self.Point(attrs['x'], attrs['y'], attrs['z'],
                                                          attrs['d']))


def read_NeurolucidaTreeXML(filename):
    parser = xml.sax.make_parser()
    handler = NeurolucidaTreeXMLHandler()
    parser.setContentHandler(handler)
    parser.parse(filename)
    return handler.roots


def read_NeurolucidaSomaXML(filename):
    parser = xml.sax.make_parser()
    handler = NeurolucidaSomaXMLHandler()
    parser.setContentHandler(handler)
    parser.parse(filename)
    return handler.somas
