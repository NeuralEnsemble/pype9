

class Pype9RuntimeError(Exception):
    pass


class Pype9TypeError(TypeError):
    pass


class Pype9IrreducibleMorphException(Exception):
    pass


class Pype9BuildError(Exception):
    pass


class Pype9CouldNotGuessFromDimensionException(Exception):
    pass


class Pype9NoMatchingElementException(Exception):
    pass


class Pype9MemberNameClashException(Exception):
    pass


class Pype9ProjToCloneNotCreatedException(Exception):

    def __init__(self, orig_proj_id=None):
        self.orig_proj_id = orig_proj_id
