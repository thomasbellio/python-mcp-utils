"""Core error types: ErrorCode, ErrorContext, ErrorResponse, and specialized errors."""

from typing import Annotated, Self

from pydantic import ConfigDict, Field, model_validator

from mcp_utils._base_model import McpUtilsBaseModel
from mcp_utils.base.primitives import Timestamp

# Error code type aliases
ErrorCode = Annotated[int, Field(ge=1000, le=6999)]
ConnectionErrorCode = Annotated[int, Field(ge=1000, le=1999)]
AuthErrorCode = Annotated[int, Field(ge=2000, le=2999)]
QueryErrorCode = Annotated[int, Field(ge=3000, le=3999)]
DataErrorCode = Annotated[int, Field(ge=4000, le=4999)]
SystemErrorCode = Annotated[int, Field(ge=5000, le=5999)]
OperationErrorCode = Annotated[int, Field(ge=6000, le=6999)]


class ErrorContext(McpUtilsBaseModel):
  """Context information about an error. Allows arbitrary additional fields."""

  model_config = ConfigDict(
    populate_by_name=True,
    serialize_by_alias=True,
    strict=False,
    frozen=True,
    extra="allow",
  )

  operation: str | None = None
  stage: str | None = None
  retries_attempted: Annotated[int, Field(ge=0)] | None = Field(
    default=None, alias="retriesAttempted"
  )


class ErrorResponse(McpUtilsBaseModel):
  """Structured error response."""

  code: ErrorCode
  message: Annotated[str, Field(min_length=1)]
  context: ErrorContext | None = None
  suggestion: str | None = None
  trace: list[str] | None = None
  timestamp: Timestamp

  @model_validator(mode="after")
  def validate_trace_non_empty(self) -> Self:
    if self.trace is not None and len(self.trace) == 0:
      raise ValueError("trace, if provided, must not be empty")
    return self


class McpConnectionError(ErrorResponse):
  """Connection error — requires operation in context."""

  code: ConnectionErrorCode
  context: ErrorContext

  @model_validator(mode="after")
  def validate_operation_required(self) -> Self:
    if self.context.operation is None:
      raise ValueError("ConnectionError requires context.operation")
    return self


class AuthError(ErrorResponse):
  """Authentication error — must include suggestion."""

  code: AuthErrorCode
  suggestion: str


class QueryError(ErrorResponse):
  """Query error — requires operation in context."""

  code: QueryErrorCode
  context: ErrorContext

  @model_validator(mode="after")
  def validate_operation_required(self) -> Self:
    if self.context.operation is None:
      raise ValueError("QueryError requires context.operation")
    return self
