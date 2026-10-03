from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.application.use_cases.auth.log_in import LogIn
from app.application.use_cases.auth.register_user import RegisterUser
from app.entrypoints.api.dependencies import get_log_in, get_register_user
from app.entrypoints.api.schemas.auth import (
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.entrypoints.api.schemas.common import ProblemDetails

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ProblemDetails, "description": "Email already used"}},
)
def register(
    body: RegisterRequest,
    use_case: Annotated[RegisterUser, Depends(get_register_user)],
) -> UserResponse:
    user = use_case.execute(
        email=body.email, password=body.password, full_name=body.full_name
    )
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    responses={401: {"model": ProblemDetails, "description": "Invalid credentials"}},
)
def log_in(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    use_case: Annotated[LogIn, Depends(get_log_in)],
) -> TokenResponse:
    """OAuth2 password form, so Swagger's "Authorize" button works (DEC-030).

    ``username`` receives the user's email.
    """
    token = use_case.execute(email=form.username, password=form.password)
    return TokenResponse(access_token=token.access_token, expires_in=token.expires_in)
