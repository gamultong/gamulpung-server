class classproperty(property):
    def __get__(self, obj, cls=None):
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget(cls)
