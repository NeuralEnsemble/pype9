import time

try:
    from mpy4py import MPI
    comm = MPI.COMM_WORLD  # The MPI communicator object
    rank = comm.Get_rank()  # The ID of the current process
    num_processes = comm.Get_size()
except ImportError:
    num_processes = 1
    rank = 0


def inputpath(arg):
    return str(arg)


def outputpath(arg):
    return str(arg)


class randomseed(int):

    counter = 0

    def __new__(cls, arg=None, mirror_mpi=False):
        """
        `arg`        -- An existing seed to use
        `mirror_mpi` -- flags whether the seeds should be the same on different
                        MPI nodes or not
        """
        if arg is None or arg == 'None' or int(arg) == 0:
            seed = int(time.time() * 256) + cls.counter
            cls.counter += 1
        else:
            seed = int(arg)
        # Ensure a different seed gets used on each MPI node
        if not mirror_mpi:
            seed = seed * num_processes + rank
        return cls(seed)
