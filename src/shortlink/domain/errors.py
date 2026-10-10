class DomainError(Exception):
    """Base class for errors the API turns into a 4xx response."""

    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFound(DomainError):
    status_code = 404
    code = "NOT_FOUND"

    def __init__(self, what: str):
        super().__init__(f"{what} not found")


class LinkGone(DomainError):
    status_code = 410
    code = "LINK_GONE"

    def __init__(self, reason: str):
        super().__init__(f"This link is {reason}")


class Unauthorized(DomainError):
    status_code = 401
    code = "UNAUTHORIZED"


class InvalidUrl(DomainError):
    status_code = 422
    code = "INVALID_URL"


class InvalidAlias(DomainError):
    status_code = 422
    code = "INVALID_ALIAS"


class AliasTaken(DomainError):
    status_code = 409
    code = "ALIAS_TAKEN"

    def __init__(self, alias: str):
        super().__init__(f"The alias '{alias}' is already in use")


class InvalidExpiry(DomainError):
    status_code = 422
    code = "INVALID_EXPIRY"
