"""Domain errors raised by business workflows, independent of HTTP handling."""


class DomainError(Exception):
    """Base class for expected business-rule failures."""


class ValidationError(DomainError):
    """Raised when supplied domain data is invalid."""


class ConflictError(DomainError):
    """Raised when a requested change conflicts with current state."""


class PermissionDeniedError(DomainError):
    """Raised when an actor cannot perform a domain action."""


class NotFoundError(DomainError):
    """Raised when a workflow target does not exist in the required scope."""


class LastAdministratorError(ConflictError):
    """Raised when a change would remove the final active administrator."""
