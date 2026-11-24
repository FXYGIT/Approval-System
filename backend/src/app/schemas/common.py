from datetime import UTC, datetime
from typing import Annotated, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, StringConstraints
from pydantic.alias_generators import to_camel


class APIModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)


class InputModel(APIModel):
    model_config = ConfigDict(
        extra="forbid", populate_by_name=False, validate_by_name=False, validate_by_alias=True
    )


def utc_datetime(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


UTCTime = Annotated[datetime, BeforeValidator(utc_datetime)]
Username = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
T = TypeVar("T")


class Page[T](APIModel):
    items: list[T]
    total: int
    page: int
    page_size: int


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


ERROR_RESPONSES = {code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 409, 422, 500)}
