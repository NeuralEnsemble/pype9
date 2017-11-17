class DummyMPICom(object):

    rank = 0
    size = 1

    def barrier(self):
        pass

try:
    from mpi4py import MPI  # @UnusedImport @IgnorePep8 This is imported before NEURON to avoid a bug in NEURON
except ImportError:
    mpi_comm = DummyMPICom()
else:
    mpi_comm = MPI.COMM_WORLD

MPI_ROOT = 0


def is_mpi_master():
    return (mpi_comm.rank == MPI_ROOT)
