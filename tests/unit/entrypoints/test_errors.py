from http import HTTPStatus

import pytest

from app.domain.exceptions import (
    AssigneeNotFound,
    DomainError,
    EmailAlreadyRegistered,
    InvalidCredentials,
    NotTaskOwner,
    TaskNotFound,
)
from app.entrypoints.api.errors import status_for
from tests.factories import make_user


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (TaskNotFound(make_user().id), HTTPStatus.NOT_FOUND),
        (NotTaskOwner(make_user().id), HTTPStatus.FORBIDDEN),
        (EmailAlreadyRegistered("ana@example.com"), HTTPStatus.CONFLICT),
        (AssigneeNotFound("x@example.com"), HTTPStatus.UNPROCESSABLE_CONTENT),
        (InvalidCredentials(), HTTPStatus.UNAUTHORIZED),
    ],
)
def test_each_category_maps_to_its_status_code(error, expected):
    assert status_for(error) == expected


def test_an_error_without_category_is_a_server_error():
    assert status_for(DomainError("bug")) == HTTPStatus.INTERNAL_SERVER_ERROR
