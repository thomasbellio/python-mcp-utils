"""Tests for operation state transition utilities."""

import pytest

from mcp_utils._utils.transitions import (
  VALID_TRANSITIONS,
  create_operation,
  transition_operation,
  validate_transition,
)
from mcp_utils.core.error_response import ErrorResponse
from mcp_utils.core.operation_state import LifecycleStatus
from mcp_utils.core.progress_metrics import ProgressMetrics


class TestValidTransitions:
  def test_created_can_only_go_to_running(self):
    assert VALID_TRANSITIONS[LifecycleStatus.CREATED] == {LifecycleStatus.RUNNING}

  def test_running_has_four_targets(self):
    assert len(VALID_TRANSITIONS[LifecycleStatus.RUNNING]) == 4

  def test_terminal_states_have_no_transitions(self):
    for status in [LifecycleStatus.COMPLETED, LifecycleStatus.FAILED, LifecycleStatus.CANCELLED]:
      assert VALID_TRANSITIONS[status] == set()

  def test_paused_can_resume(self):
    assert VALID_TRANSITIONS[LifecycleStatus.PAUSED] == {LifecycleStatus.RUNNING}


class TestValidateTransition:
  def test_valid(self):
    assert validate_transition(LifecycleStatus.CREATED, LifecycleStatus.RUNNING) is True

  def test_invalid(self):
    assert validate_transition(LifecycleStatus.CREATED, LifecycleStatus.COMPLETED) is False

  def test_terminal(self):
    assert validate_transition(LifecycleStatus.COMPLETED, LifecycleStatus.RUNNING) is False


class TestCreateOperation:
  def test_creates_in_created_status(self):
    state = create_operation("my_tool")
    assert state.status == LifecycleStatus.CREATED
    assert state.tool_name == "my_tool"
    assert state.operation_id.startswith("op-")
    assert state.progress.current == 0
    assert state.progress.percentage == 0.0

  def test_custom_progress(self):
    progress = ProgressMetrics(current=5, total=10, percentage=50.0)
    state = create_operation("tool", progress=progress)
    assert state.progress.current == 5


class TestTransitionOperation:
  def test_valid_transition(self):
    state = create_operation("tool")
    running = transition_operation(state, LifecycleStatus.RUNNING)
    assert running.status == LifecycleStatus.RUNNING
    assert running.operation_id == state.operation_id

  def test_invalid_transition_raises(self):
    state = create_operation("tool")
    with pytest.raises(ValueError, match="Invalid transition"):
      transition_operation(state, LifecycleStatus.COMPLETED)

  def test_terminal_gets_end_time(self):
    state = create_operation("tool")
    running = transition_operation(state, LifecycleStatus.RUNNING)
    completed = transition_operation(running, LifecycleStatus.COMPLETED)
    assert completed.end_time is not None

  def test_failed_with_error(self):
    state = create_operation("tool")
    running = transition_operation(state, LifecycleStatus.RUNNING)
    error = ErrorResponse(code=5001, message="failed", timestamp="2025-01-15T10:30:00Z")
    failed = transition_operation(running, LifecycleStatus.FAILED, error=error)
    assert failed.status == LifecycleStatus.FAILED
    assert failed.error is not None

  def test_cancelled_with_partial_results(self):
    state = create_operation("tool")
    running = transition_operation(state, LifecycleStatus.RUNNING)
    cancelled = transition_operation(
      running, LifecycleStatus.CANCELLED, partial_results={"items": [1]}
    )
    assert cancelled.status == LifecycleStatus.CANCELLED
    assert cancelled.partial_results == {"items": [1]}

  def test_progress_update(self):
    state = create_operation("tool")
    running = transition_operation(state, LifecycleStatus.RUNNING)
    progress = ProgressMetrics(current=50, total=100, percentage=50.0)
    updated = transition_operation(running, LifecycleStatus.COMPLETED, progress=progress)
    assert updated.progress.current == 50

  def test_immutable_original(self):
    state = create_operation("tool")
    transition_operation(state, LifecycleStatus.RUNNING)
    assert state.status == LifecycleStatus.CREATED
