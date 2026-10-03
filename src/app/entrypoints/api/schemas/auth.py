from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, EmailStr, Field

from app.domain.rules import (
    FULL_NAME_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
)
from app.entrypoints.api.schemas.common import RequestModel, ResponseModel


class RegisterRequest(RequestModel):
    email: EmailStr
    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )
    full_name: str = Field(min_length=1, max_length=FULL_NAME_MAX_LENGTH)


class UserResponse(ResponseModel):
    id: UUID
    email: Annotated[str, BeforeValidator(str)]
    full_name: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
