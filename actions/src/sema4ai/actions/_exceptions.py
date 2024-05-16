class ActionsError(RuntimeError):
    pass


class ActionsCollectError(ActionsError):
    """
    Exception given if there was some issue collecting actions.
    """


class InvalidArgumentsError(ActionsError):
    pass
