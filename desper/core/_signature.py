import inspect


class LooseSignature(inspect.Signature):
    """Loose implementation of a :class:`inspect.Signature`.

    This implementation will ignore the parameter names.
    """

    def __eq__(self, value):
        return len(self.parameters) == len(value.parameters)
