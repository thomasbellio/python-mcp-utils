"""Optional JSON-RPC 2.0 notification wrappers."""

from typing import Any, Literal

from pydantic import Field

from mcp_utils._base_model import McpUtilsBaseModel
from mcp_utils.core.progress_metrics import ProgressNotification
from mcp_utils.mcp.notifications import (
  CancellationNotification,
  ErrorNotification,
  StateChangeNotification,
)


class JsonRpcNotification(McpUtilsBaseModel):
  """Base JSON-RPC 2.0 notification (no id, no response expected)."""

  jsonrpc: Literal["2.0"] = "2.0"
  method: str
  params: dict[str, Any] | None = None


class JsonRpcProgressNotification(McpUtilsBaseModel):
  """JSON-RPC wrapper for progress notifications."""

  jsonrpc: Literal["2.0"] = "2.0"
  method: Literal["notifications/progress"] = Field(default="notifications/progress")
  params: ProgressNotification


class JsonRpcCancellationNotification(McpUtilsBaseModel):
  """JSON-RPC wrapper for cancellation notifications."""

  jsonrpc: Literal["2.0"] = "2.0"
  method: Literal["notifications/cancelled"] = Field(default="notifications/cancelled")
  params: CancellationNotification


class JsonRpcErrorNotification(McpUtilsBaseModel):
  """JSON-RPC wrapper for error notifications."""

  jsonrpc: Literal["2.0"] = "2.0"
  method: Literal["notifications/error"] = Field(default="notifications/error")
  params: ErrorNotification


class JsonRpcStateChangeNotification(McpUtilsBaseModel):
  """JSON-RPC wrapper for state change notifications."""

  jsonrpc: Literal["2.0"] = "2.0"
  method: Literal["notifications/state_change"] = Field(default="notifications/state_change")
  params: StateChangeNotification
