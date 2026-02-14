"""MCP notification types (transport-agnostic data models)."""

from typing import Self

from pydantic import Field, model_validator

from mcp_utils._base_model import McpUtilsBaseModel
from mcp_utils._utils.transitions import VALID_TRANSITIONS
from mcp_utils.base.primitives import OperationId, Timestamp
from mcp_utils.core.cancellation_token import CancellationToken
from mcp_utils.core.error_response import ErrorResponse
from mcp_utils.core.operation_state import LifecycleStatus
from mcp_utils.core.progress_metrics import ProgressNotification

# Re-export ProgressNotification from core
__all__ = [
  "ProgressNotification",
  "CancellationNotification",
  "ErrorNotification",
  "StateChangeNotification",
]


class CancellationNotification(McpUtilsBaseModel):
  """MCP cancellation notification."""

  operation_id: OperationId = Field(..., alias="operationId")
  cancellation_token: CancellationToken = Field(..., alias="cancellationToken")
  timestamp: Timestamp


class ErrorNotification(McpUtilsBaseModel):
  """MCP error notification."""

  operation_id: OperationId = Field(..., alias="operationId")
  error: ErrorResponse
  timestamp: Timestamp


class StateChangeNotification(McpUtilsBaseModel):
  """MCP operation state change notification."""

  operation_id: OperationId = Field(..., alias="operationId")
  old_state: LifecycleStatus = Field(..., alias="oldState")
  new_state: LifecycleStatus = Field(..., alias="newState")
  timestamp: Timestamp

  @model_validator(mode="after")
  def validate_transition(self) -> Self:
    valid = VALID_TRANSITIONS.get(self.old_state, set())
    if self.new_state not in valid:
      raise ValueError(f"Invalid state transition: '{self.old_state}' → '{self.new_state}'")
    return self
