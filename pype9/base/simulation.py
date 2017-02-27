from abc import ABCMeta, abstractmethod
import weakref
from pype9.exceptions import Pype9RuntimeError


class BaseSimulation(object):

    __metaclass__ = ABCMeta

    def __init__(self):
        if self.instance_counter:
            raise Pype9RuntimeError(
                "Cannot instantiate more than one instance of Simulation")
        self.instance_counter += 1
        self.running = False
        self.registered_cells = []

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    def initialize(self):
        self.reset()
        self.running = True

    def reset_cells(self):
        for cell_ref in reversed(self.registered_cells):
            if cell_ref():
                cell_ref().initialize()
                cell_ref().reset_recordings()
            else:
                # If the cell has been deleted remove the weak reference to it
                self.registered_cells.remove(cell_ref)

    @abstractmethod
    def run(self, simulation_time, **kwargs):
        pass

    def register_cell(self, cell):
        self.registered_cells.append(weakref.ref(cell))

    def deregister_cell(self, cell):
        for cell_ref in reversed(self.registered_cells):
            if cell is cell_ref() or not cell_ref():
                self.registered_cells.remove(cell_ref)
