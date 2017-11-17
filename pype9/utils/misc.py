
class classproperty(property):
    """Used to set a property of a class"""
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()
