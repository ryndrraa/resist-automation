class RESISTAutomationError(Exception):
    """Base exception with a user-facing message."""


class RSXError(RESISTAutomationError):
    pass


class InvalidRSXError(RSXError):
    pass


class MissingRSXElementError(RSXError):
    pass


class WorkbookError(RESISTAutomationError):
    pass


class InvalidWorkbookError(WorkbookError):
    pass


class MappingError(WorkbookError):
    pass


class ExportError(WorkbookError):
    pass


class OutputExistsError(ExportError):
    pass


class SessionError(RESISTAutomationError):
    pass


class UnsupportedSessionVersionError(SessionError):
    pass
