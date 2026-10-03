"""Field limits and validation rules shared by the entities.

The HTTP schemas import these constants so each limit is defined only once (DEC-029).
"""

from app.domain.exceptions import InvalidFieldValue

TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 2000
LIST_NAME_MAX_LENGTH = 100
FULL_NAME_MAX_LENGTH = 100
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def require_text(field: str, value: str, max_length: int) -> str:
    """Return ``value`` stripped; reject it if it is blank or too long."""
    cleaned = value.strip()
    if not cleaned:
        raise InvalidFieldValue(field, "it cannot be empty.")
    if len(cleaned) > max_length:
        raise InvalidFieldValue(field, f"it must have at most {max_length} characters.")
    return cleaned


def optional_text(field: str, value: str | None, max_length: int) -> str | None:
    """Like :func:`require_text`, but blank values become ``None``."""
    if value is None or not value.strip():
        return None
    return require_text(field, value, max_length)


def validate_password(password: str) -> None:
    """Length over composition rules, as NIST SP 800-63B recommends (DEC-031)."""
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise InvalidFieldValue(
            "password",
            f"it must have between {PASSWORD_MIN_LENGTH} and "
            f"{PASSWORD_MAX_LENGTH} characters.",
        )
