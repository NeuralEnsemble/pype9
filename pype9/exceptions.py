

class Pype9RuntimeError(Exception):
    pass


class Pype9TypeError(TypeError):
    pass


class Pype9IrreducibleMorphException(Exception):
    pass


class Pype9BuildError(Exception):
    pass


class ProjectionToCloneNotCreatedYetException(Exception):

    def __init__(self, orig_proj_id=None):
        self.orig_proj_id = orig_proj_id
