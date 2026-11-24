from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from app.schemas.common import APIModel, InputModel, Username, UTCTime


class RegisterInput(InputModel):
    username: Username
    password: str = Field(min_length=8, max_length=128, repr=False)
    display_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]


class LoginInput(InputModel):
    username: Username
    password: str = Field(min_length=1, max_length=128, repr=False)


class UserSummary(APIModel):
    id: UUID
    username: str
    display_name: str


class UserPublic(UserSummary):
    created_at: UTCTime


class TokenResponse(APIModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int
