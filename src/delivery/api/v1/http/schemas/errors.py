from pydantic import BaseModel, ConfigDict


class ValidationFieldError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: list[str | int]
    message: str


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    request_id: str
    fields: list[ValidationFieldError] | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorBody
