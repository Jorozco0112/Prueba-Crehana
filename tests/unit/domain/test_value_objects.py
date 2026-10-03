from decimal import Decimal

import pytest

from app.domain.exceptions import InvalidFieldValue
from app.domain.value_objects import CompletionPercentage, Email, Priority


class TestPriority:
    def test_ranks_follow_the_order_of_importance(self):
        ranks = [priority.rank for priority in Priority]

        assert ranks == [0, 1, 2, 3]
        assert Priority.URGENT.rank > Priority.HIGH.rank > Priority.MEDIUM.rank

    @pytest.mark.parametrize("priority", list(Priority))
    def test_from_rank_is_the_inverse_of_rank(self, priority):
        assert Priority.from_rank(priority.rank) is priority

    def test_from_rank_rejects_an_unknown_rank(self):
        with pytest.raises(ValueError, match="Unknown priority rank"):
            Priority.from_rank(7)


class TestEmail:
    def test_normalizes_case_and_surrounding_spaces(self):
        assert Email("  Ana.Torres@Example.COM ").value == "ana.torres@example.com"

    def test_emails_that_differ_only_in_case_are_equal(self):
        assert Email("ANA@example.com") == Email("ana@example.com")
        assert hash(Email("ANA@example.com")) == hash(Email("ana@example.com"))

    def test_is_not_equal_to_a_plain_string(self):
        assert Email("ana@example.com") != "ana@example.com"

    @pytest.mark.parametrize(
        "value",
        ["", "no-at-sign", "@example.com", "ana@", "ana@localhost", "a@b@c.com"],
    )
    def test_rejects_invalid_addresses(self, value):
        with pytest.raises(InvalidFieldValue) as error:
            Email(value)

        assert error.value.field == "email"

    def test_rejects_addresses_longer_than_the_limit(self):
        with pytest.raises(InvalidFieldValue, match="at most 254"):
            Email("a" * 250 + "@example.com")

    def test_string_representations(self):
        email = Email("ana@example.com")

        assert str(email) == "ana@example.com"
        assert repr(email) == "Email('ana@example.com')"


class TestCompletionPercentage:
    def test_an_empty_list_is_at_zero_percent(self):
        completion = CompletionPercentage.from_counts(completed=0, total=0)

        assert completion.percentage == Decimal("0.00")
        assert completion.total == 0

    @pytest.mark.parametrize(
        ("completed", "total", "expected"),
        [
            (0, 4, "0.00"),
            (1, 3, "33.33"),
            (2, 3, "66.67"),
            (5, 12, "41.67"),
            (1, 8, "12.50"),
            (4, 4, "100.00"),
        ],
    )
    def test_rounds_to_two_decimals_half_up(self, completed, total, expected):
        completion = CompletionPercentage.from_counts(completed=completed, total=total)

        assert completion.percentage == Decimal(expected)

    @pytest.mark.parametrize(("completed", "total"), [(-1, 3), (1, -1), (4, 3)])
    def test_rejects_inconsistent_counts(self, completed, total):
        with pytest.raises(ValueError, match="Inconsistent task counts"):
            CompletionPercentage(completed=completed, total=total)

    def test_is_compared_by_value(self):
        assert CompletionPercentage(1, 2) == CompletionPercentage(1, 2)
        assert CompletionPercentage(1, 2) != CompletionPercentage(2, 4)
        assert CompletionPercentage(1, 2) != "50%"
        assert hash(CompletionPercentage(1, 2)) == hash(CompletionPercentage(1, 2))
        assert repr(CompletionPercentage(1, 2)) == "CompletionPercentage(1/2)"
