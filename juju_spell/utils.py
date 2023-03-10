__all__ = ["Namespace"]


class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
