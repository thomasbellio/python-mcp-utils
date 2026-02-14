"""Core progress types: ProgressMetrics and ProgressNotification."""

from typing import Annotated, Any, Self

from pydantic import Field, model_validator

from mcp_utils._base_model import McpUtilsBaseModel
from mcp_utils.base.primitives import OperationId, ProgressToken, Timestamp


class ProgressMetrics(McpUtilsBaseModel):
  """Progress tracking metrics."""

  current: Annotated[int, Field(ge=0)]
  total: int | None = None
  unit: str = "items"
  percentage: Annotated[float, Field(ge=0.0, le=100.0)]

  @model_validator(mode="after")
  def validate_percentage_consistency(self) -> Self:
    if self.total is not None and self.total > 0:
      expected = (self.current / self.total) * 100
      if abs(self.percentage - expected) > 0.01:
        raise ValueError(
          f"percentage ({self.percentage}) inconsistent with "
          f"current/total ({self.current}/{self.total} = {expected:.2f})"
        )
    return self


class ProgressNotification(McpUtilsBaseModel):
  """Progress update notification."""

  operation_id: OperationId = Field(..., alias="operationId")
  progress_token: ProgressToken = Field(..., alias="progressToken")
  stage: str
  progress: ProgressMetrics
  message: str | None = None
  metadata: dict[str, Any] | None = None
  timestamp: Timestamp
