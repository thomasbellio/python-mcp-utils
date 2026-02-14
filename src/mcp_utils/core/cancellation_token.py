"""Core cancellation types: CancellationReason, CancellationSource, CancellationToken."""

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from mcp_utils._base_model import McpUtilsBaseModel
from mcp_utils.base.primitives import Timestamp


class CancellationReason(StrEnum):
  """Why an operation was cancelled."""

  USER_REQUESTED = "user_requested"
  TIMEOUT = "timeout"
  RESOURCE_LIMIT = "resource_limit"
  ERROR_THRESHOLD = "error_threshold"


class CancellationSource(StrEnum):
  """Who initiated the cancellation."""

  CLIENT = "client"
  SERVER = "server"


class CancellationToken(McpUtilsBaseModel):
  """Cancellation request token."""

  is_cancellation_requested: bool = Field(..., alias="isCancellationRequested")
  reason: CancellationReason | None = None
  source: CancellationSource | None = None
  timestamp: Timestamp | None = None

  @model_validator(mode="after")
  def validate_cancellation_fields(self) -> Self:
    if self.is_cancellation_requested:
      missing = []
      if self.reason is None:
        missing.append("reason")
      if self.source is None:
        missing.append("source")
      if self.timestamp is None:
        missing.append("timestamp")
      if missing:
        raise ValueError(
          f"When cancellation is requested, these fields are required: {', '.join(missing)}"
        )
    return self
