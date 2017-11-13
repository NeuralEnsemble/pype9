class Pype9Exception(Exception):
    pass


class Pype9Unsupported9MLException(Pype9Exception):
    pass


class Pype9RuntimeError(Pype9Exception):
    pass


class Pype9DimensionError(Pype9RuntimeError):
    pass


class Pype9UnitStrError(Pype9RuntimeError):
    pass


class Pype9TypeError(TypeError, Pype9RuntimeError):
    pass


class Pype9NameError(KeyError, Pype9RuntimeError):
    pass


class Pype9ImportError(Pype9RuntimeError):
    pass


class Pype9AttributeError(AttributeError, Pype9RuntimeError):
    pass


class Pype9IrreducibleMorphException(Pype9RuntimeError):
    pass


class Pype9BuildError(Pype9RuntimeError):
    pass


class Pype9UnflattenableSynapseException(Exception):
    pass


class Pype9CouldNotGuessFromDimensionException(Pype9RuntimeError):
    pass


class Pype9NoMatchingElementException(Pype9RuntimeError):
    pass


class Pype9MemberNameClashException(Pype9RuntimeError):
    pass


class Pype9BuildMismatchError(Pype9BuildError):
    pass


class Pype9ProjToCloneNotCreatedException(Pype9RuntimeError):

    def __init__(self, orig_proj_id=None):
        self.orig_proj_id = orig_proj_id


class Pype9UsageError(Pype9RuntimeError):
    pass


class Pype9NoActiveSimulationError(Pype9RuntimeError):
    pass


class Pype9RegimeTransitionsNotRecordedError(Pype9UsageError):
    pass


class Pype9CommandNotFoundError(Pype9BuildError):
    pass
