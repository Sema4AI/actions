"""
Exceptions for work items.

Based on robocorp-workitems (Apache 2.0 License).
"""


class EmptyQueue(Exception):
    """Raised when attempting to get an item from an empty queue."""

    pass


class WorkItemException(Exception):
    """Base exception for work item processing errors."""

    def __init__(
        self,
        message: str = "",
        code: str = "",
    ):
        super().__init__(message)
        self.message = message
        self.code = code


class BusinessException(WorkItemException):
    """
    Exception for expected business logic failures.

    These exceptions indicate that the work item cannot be processed
    due to a business rule violation or invalid data. The work item
    should not be retried.
    """

    pass


class ApplicationException(WorkItemException):
    """
    Exception for unexpected application failures.

    These exceptions indicate a transient or recoverable error
    in the application. The work item may be retried.
    """

    pass
