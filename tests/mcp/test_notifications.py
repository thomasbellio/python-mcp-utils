"""Tests for MCP notification types."""

import pytest
from pydantic import ValidationError

from mcp_utils.core.cancellation_token import (
  CancellationReason,
  CancellationSource,
  CancellationToken,
)
from mcp_utils.core.error_response import ErrorResponse
from mcp_utils.core.operation_state import LifecycleStatus
from mcp_utils.mcp.notifications import (
  CancellationNotification,
  ErrorNotification,
  ProgressNotification,
  StateChangeNotification,
)

OP_ID = "op-123e4567-e89b-12d3-a456-426614174000"
TS = "2025-01-15T10:30:00.000Z"


class TestProgressNotificationReexport:
  def test_is_same_class(self):
    from mcp_utils.core.progress_metrics import (
      ProgressNotification as CorePN,
    )

    assert ProgressNotification is CorePN


class TestCancellationNotification:
  def test_valid(self):
    token = CancellationToken(
      is_cancellation_requested=True,
      reason=CancellationReason.USER_REQUESTED,
      source=CancellationSource.CLIENT,
      timestamp=TS,
    )
    n = CancellationNotification(
      operation_id=OP_ID,
      cancellation_token=token,
      timestamp=TS,
    )
    assert n.operation_id == OP_ID

  def test_aliases(self):
    token = CancellationToken(is_cancellation_requested=False)
    n = CancellationNotification(operation_id=OP_ID, cancellation_token=token, timestamp=TS)
    data = n.model_dump(by_alias=True)
    assert "operationId" in data
    assert "cancellationToken" in data

  def test_roundtrip(self):
    token = CancellationToken(is_cancellation_requested=False)
    n = CancellationNotification(operation_id=OP_ID, cancellation_token=token, timestamp=TS)
    data = n.model_dump(by_alias=True)
    n2 = CancellationNotification.model_validate(data)
    assert n == n2


class TestErrorNotification:
  def test_valid(self):
    error = ErrorResponse(code=5001, message="err", timestamp=TS)
    n = ErrorNotification(operation_id=OP_ID, error=error, timestamp=TS)
    assert n.error.code == 5001

  def test_alias(self):
    error = ErrorResponse(code=5001, message="err", timestamp=TS)
    n = ErrorNotification(operation_id=OP_ID, error=error, timestamp=TS)
    data = n.model_dump(by_alias=True)
    assert "operationId" in data


class TestStateChangeNotification:
  def test_valid_transition(self):
    n = StateChangeNotification(
      operation_id=OP_ID,
      old_state=LifecycleStatus.CREATED,
      new_state=LifecycleStatus.RUNNING,
      timestamp=TS,
    )
    assert n.old_state == LifecycleStatus.CREATED
    assert n.new_state == LifecycleStatus.RUNNING

  def test_invalid_transition(self):
    with pytest.raises(ValidationError):
      StateChangeNotification(
        operation_id=OP_ID,
        old_state=LifecycleStatus.CREATED,
        new_state=LifecycleStatus.COMPLETED,
        timestamp=TS,
      )

  def test_aliases(self):
    n = StateChangeNotification(
      operation_id=OP_ID,
      old_state=LifecycleStatus.RUNNING,
      new_state=LifecycleStatus.PAUSED,
      timestamp=TS,
    )
    data = n.model_dump(by_alias=True)
    assert "operationId" in data
    assert "oldState" in data
    assert "newState" in data

  def test_roundtrip(self):
    n = StateChangeNotification(
      operation_id=OP_ID,
      old_state=LifecycleStatus.RUNNING,
      new_state=LifecycleStatus.COMPLETED,
      timestamp=TS,
    )
    data = n.model_dump(by_alias=True)
    n2 = StateChangeNotification.model_validate(data)
    assert n == n2
