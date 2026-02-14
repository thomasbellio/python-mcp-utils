"""Core operation state types: LifecycleStatus, Checkpoint, ResumeCapability, OperationState."""

from enum import StrEnum
from typing import Any, Generic, Self, TypeVar

from pydantic import Field, model_validator

from mcp_utils._base_model import McpUtilsBaseModel
from mcp_utils.base.primitives import OperationId, Timestamp
from mcp_utils.core.error_response import ErrorResponse
from mcp_utils.core.progress_metrics import ProgressMetrics


class LifecycleStatus(StrEnum):
  """Lifecycle status of an operation."""

  CREATED = "created"
  RUNNING = "running"
  PAUSED = "paused"
  COMPLETED = "completed"
  FAILED = "failed"
  CANCELLED = "cancelled"


TResult = TypeVar("TResult", default=dict[str, Any])
TCheckpointData = TypeVar("TCheckpointData", default=dict[str, Any])
TPartialResult = TypeVar("TPartialResult", default=dict[str, Any])


class Checkpoint(McpUtilsBaseModel, Generic[TCheckpointData]):
  """Savepoint for resuming operations."""

  data: TCheckpointData
  timestamp: Timestamp
  stage: str


class ResumeCapability(McpUtilsBaseModel, Generic[TCheckpointData]):
  """Whether an operation can be resumed."""

  checkpoint: Checkpoint[TCheckpointData]
  resumable_operations: list[str] = Field(..., alias="resumableOperations")


class OperationState(McpUtilsBaseModel, Generic[TResult, TPartialResult]):
  """Current state of an operation."""

  operation_id: OperationId = Field(..., alias="operationId")
  tool_name: str = Field(..., alias="toolName")
  status: LifecycleStatus
  start_time: Timestamp = Field(..., alias="startTime")
  end_time: Timestamp | None = Field(default=None, alias="endTime")
  progress: ProgressMetrics
  result: TResult | None = None
  error: ErrorResponse | None = None
  partial_results: TPartialResult | None = Field(default=None, alias="partialResults")

  @model_validator(mode="after")
  def validate_status_constraints(self) -> Self:
    terminal = {LifecycleStatus.COMPLETED, LifecycleStatus.FAILED, LifecycleStatus.CANCELLED}
    if self.status in terminal and self.end_time is None:
      raise ValueError(f"end_time is required when status is '{self.status}'")
    if self.status == LifecycleStatus.FAILED and self.error is None:
      raise ValueError("error is required when status is 'failed'")
    if self.status == LifecycleStatus.CANCELLED and self.partial_results is None:
      raise ValueError("partial_results is required when status is 'cancelled'")
    return self
