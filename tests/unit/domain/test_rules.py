import pytest

from app.domain.exceptions import InvalidFieldValue
from app.domain.rules import optional_text, require_text, validate_password


def test_require_text_strips_surrounding_spaces():
    assert require_text("title", "  Buy milk  ", 20) == "Buy milk"


@pytest.mark.parametrize("value", ["", "   ", "\n\t"])
def test_require_text_rejects_blank_values(value):
    with pytest.raises(InvalidFieldValue, match="cannot be empty") as error:
        require_text("title", value, 20)

    assert error.value.field == "title"


def test_require_text_rejects_values_over_the_limit():
    with pytest.raises(InvalidFieldValue, match="at most 5 characters"):
        require_text("title", "abcdef", 5)


@pytest.mark.parametrize("value", [None, "", "   "])
def test_optional_text_turns_blank_values_into_none(value):
    assert optional_text("description", value, 20) is None


def test_optional_text_keeps_and_strips_real_values():
    assert optional_text("description", " Two liters ", 20) == "Two liters"


@pytest.mark.parametrize("password", ["a" * 8, "a" * 128])
def test_validate_password_accepts_the_limits(password):
    validate_password(password)


@pytest.mark.parametrize("password", ["a" * 7, "a" * 129])
def test_validate_password_rejects_lengths_out_of_range(password):
    with pytest.raises(InvalidFieldValue) as error:
        validate_password(password)

    assert error.value.field == "password"
