"""Tests for core operation state types."""

import pytest
from pydantic import ValidationError

from mcp_utils.core.error_response import ErrorResponse
from mcp_utils.core.operation_state import (
  Checkpoint,
  LifecycleStatus,
  OperationState,
  ResumeCapability,
)
from mcp_utils.core.progress_metrics import ProgressMetrics


class TestLifecycleStatus:
  def test_members(self):
    assert set(LifecycleStatus) == {
      LifecycleStatus.CREATED,
      LifecycleStatus.RUNNING,
      LifecycleStatus.PAUSED,
      LifecycleStatus.COMPLETED,
      LifecycleStatus.FAILED,
      LifecycleStatus.CANCELLED,
    }

  def test_values(self):
    assert LifecycleStatus.CREATED == "created"
    assert LifecycleStatus.CANCELLED == "cancelled"


class TestCheckpoint:
  def test_valid(self):
    cp = Checkpoint(
      data={"key": "value"},
      timestamp="2025-01-15T10:30:00Z",
      stage="stage1",
    )
    assert cp.data == {"key": "value"}
    assert cp.stage == "stage1"

  def test_generic_type(self):
    """Checkpoint with typed data."""
    cp = Checkpoint[dict[str, str]](
      data={"key": "value"},
      timestamp="2025-01-15T10:30:00Z",
      stage="stage1",
    )
    assert cp.data["key"] == "value"


class TestResumeCapability:
  def test_valid(self):
    rc = ResumeCapability(
      checkpoint=Checkpoint(
        data={"step": 5},
        timestamp="2025-01-15T10:30:00Z",
        stage="processing",
      ),
      resumable_operations=["op1", "op2"],
    )
    assert rc.resumable_operations == ["op1", "op2"]

  def test_alias(self):
    rc = ResumeCapability.model_validate(
      {
        "checkpoint": {
          "data": {},
          "timestamp": "2025-01-15T10:30:00Z",
          "stage": "s",
        },
        "resumableOperations": ["a"],
      }
    )
    assert rc.resumable_operations == ["a"]
    data = rc.model_dump(by_alias=True)
    assert "resumableOperations" in data


PROGRESS_ZERO = ProgressMetrics(current=0, percentage=0.0)


class TestOperationState:
  def test_created_state(self):
    state = OperationState(
      operation_id="op-123e4567-e89b-12d3-a456-426614174000",
      tool_name="test_tool",
      status=LifecycleStatus.CREATED,
      start_time="2025-01-15T10:30:00Z",
      progress=PROGRESS_ZERO,
    )
    assert state.status == LifecycleStatus.CREATED
    assert state.end_time is None

  def test_completed_requires_end_time(self):
    with pytest.raises(ValidationError):
      OperationState(
        operation_id="op-123e4567-e89b-12d3-a456-426614174000",
        tool_name="test",
        status=LifecycleStatus.COMPLETED,
        start_time="2025-01-15T10:30:00Z",
        progress=PROGRESS_ZERO,
      )

  def test_completed_with_end_time(self):
    state = OperationState(
      operation_id="op-123e4567-e89b-12d3-a456-426614174000",
      tool_name="test",
      status=LifecycleStatus.COMPLETED,
      start_time="2025-01-15T10:30:00Z",
      end_time="2025-01-15T10:31:00Z",
      progress=PROGRESS_ZERO,
    )
    assert state.end_time == "2025-01-15T10:31:00Z"

  def test_failed_requires_error(self):
    with pytest.raises(ValidationError):
      OperationState(
        operation_id="op-123e4567-e89b-12d3-a456-426614174000",
        tool_name="test",
        status=LifecycleStatus.FAILED,
        start_time="2025-01-15T10:30:00Z",
        end_time="2025-01-15T10:31:00Z",
        progress=PROGRESS_ZERO,
      )

  def test_failed_with_error(self):
    error = ErrorResponse(code=5001, message="system error", timestamp="2025-01-15T10:30:00Z")
    state = OperationState(
      operation_id="op-123e4567-e89b-12d3-a456-426614174000",
      tool_name="test",
      status=LifecycleStatus.FAILED,
      start_time="2025-01-15T10:30:00Z",
      end_time="2025-01-15T10:31:00Z",
      progress=PROGRESS_ZERO,
      error=error,
    )
    assert state.error is not None

  def test_cancelled_requires_partial_results(self):
    with pytest.raises(ValidationError):
      OperationState(
        operation_id="op-123e4567-e89b-12d3-a456-426614174000",
        tool_name="test",
        status=LifecycleStatus.CANCELLED,
        start_time="2025-01-15T10:30:00Z",
        end_time="2025-01-15T10:31:00Z",
        progress=PROGRESS_ZERO,
      )

  def test_cancelled_with_partial_results(self):
    state = OperationState(
      operation_id="op-123e4567-e89b-12d3-a456-426614174000",
      tool_name="test",
      status=LifecycleStatus.CANCELLED,
      start_time="2025-01-15T10:30:00Z",
      end_time="2025-01-15T10:31:00Z",
      progress=PROGRESS_ZERO,
      partial_results={"items": [1, 2]},
    )
    assert state.partial_results == {"items": [1, 2]}

  def test_aliases(self):
    state = OperationState(
      operation_id="op-123e4567-e89b-12d3-a456-426614174000",
      tool_name="test",
      status=LifecycleStatus.CREATED,
      start_time="2025-01-15T10:30:00Z",
      progress=PROGRESS_ZERO,
    )
    data = state.model_dump(by_alias=True)
    assert "operationId" in data
    assert "toolName" in data
    assert "startTime" in data

  def test_roundtrip(self):
    state = OperationState(
      operation_id="op-123e4567-e89b-12d3-a456-426614174000",
      tool_name="test",
      status=LifecycleStatus.RUNNING,
      start_time="2025-01-15T10:30:00Z",
      progress=ProgressMetrics(current=10, total=100, percentage=10.0),
    )
    data = state.model_dump(by_alias=True)
    state2 = OperationState.model_validate(data)
    assert state == state2
