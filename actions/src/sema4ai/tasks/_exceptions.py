class RobocorpActionsError(RuntimeError):
    pass


class RobocorpTasksCollectError(RobocorpActionsError):
    """
    Exception given if there was some issue collecting actions.
    """


class InvalidArgumentsError(RobocorpActionsError):
    pass
