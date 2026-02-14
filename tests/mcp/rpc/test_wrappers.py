"""Tests for JSON-RPC notification wrappers."""

from mcp_utils.core.cancellation_token import (
  CancellationToken,
)
from mcp_utils.core.error_response import ErrorResponse
from mcp_utils.core.operation_state import LifecycleStatus
from mcp_utils.core.progress_metrics import ProgressMetrics, ProgressNotification
from mcp_utils.mcp.notifications import (
  CancellationNotification,
  ErrorNotification,
  StateChangeNotification,
)
from mcp_utils.mcp.rpc.wrappers import (
  JsonRpcCancellationNotification,
  JsonRpcErrorNotification,
  JsonRpcNotification,
  JsonRpcProgressNotification,
  JsonRpcStateChangeNotification,
)

OP_ID = "op-123e4567-e89b-12d3-a456-426614174000"
PT_ID = "pt-123e4567-e89b-12d3-a456-426614174001"
TS = "2025-01-15T10:30:00.000Z"


class TestJsonRpcNotification:
  def test_base(self):
    n = JsonRpcNotification(method="test/method")
    assert n.jsonrpc == "2.0"
    assert n.method == "test/method"
    assert n.params is None


class TestJsonRpcProgressNotification:
  def test_valid(self):
    params = ProgressNotification(
      operation_id=OP_ID,
      progress_token=PT_ID,
      stage="test",
      progress=ProgressMetrics(current=0, percentage=0.0),
      timestamp=TS,
    )
    n = JsonRpcProgressNotification(params=params)
    assert n.jsonrpc == "2.0"
    assert n.method == "notifications/progress"
    data = n.model_dump(by_alias=True)
    assert data["jsonrpc"] == "2.0"
    assert data["method"] == "notifications/progress"


class TestJsonRpcCancellationNotification:
  def test_valid(self):
    token = CancellationToken(is_cancellation_requested=False)
    params = CancellationNotification(operation_id=OP_ID, cancellation_token=token, timestamp=TS)
    n = JsonRpcCancellationNotification(params=params)
    assert n.method == "notifications/cancelled"


class TestJsonRpcErrorNotification:
  def test_valid(self):
    error = ErrorResponse(code=5001, message="err", timestamp=TS)
    params = ErrorNotification(operation_id=OP_ID, error=error, timestamp=TS)
    n = JsonRpcErrorNotification(params=params)
    assert n.method == "notifications/error"


class TestJsonRpcStateChangeNotification:
  def test_valid(self):
    params = StateChangeNotification(
      operation_id=OP_ID,
      old_state=LifecycleStatus.CREATED,
      new_state=LifecycleStatus.RUNNING,
      timestamp=TS,
    )
    n = JsonRpcStateChangeNotification(params=params)
    assert n.method == "notifications/state_change"
    data = n.model_dump(by_alias=True)
    assert data["params"]["oldState"] == "created"
    assert data["params"]["newState"] == "running"
