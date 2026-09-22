"""Framework-independent errors raised by Expedia Lite controllers."""


class RecordNotFoundError(LookupError):
    """Raised when a requested user, trip, or booking does not exist."""

    def __init__(self, resource: str, identifier: str) -> None:
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource.capitalize()} {identifier} was not found.")


class BookingValidationError(ValueError):
    """Raised when a booking operation contains an unsupported value."""


class SearchValidationError(ValueError):
    """Raised when a hotel search query is not usable."""


class AccountValidationError(ValueError):
    """Raised when new account data does not meet the documented contract."""


class DuplicateUsernameError(ValueError):
    """Raised when an account username is already present."""


class AuthenticationError(ValueError):
    """Raised when supplied credentials do not authenticate an account."""


class PostcodeNotFoundError(LookupError):
    """Raised when Geoapify returns no acceptable U.S. postcode result."""

    def __init__(self, postcode: str) -> None:
        self.postcode = postcode
        super().__init__(f"U.S. postcode {postcode} could not be resolved.")


class GeoapifyRequestError(RuntimeError):
    """Raised when Geoapify cannot provide a usable response."""


class GeoapifyConfigurationError(RuntimeError):
    """Raised when the backend has no usable Geoapify API key."""
