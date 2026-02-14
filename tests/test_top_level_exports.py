"""Tests for top-level exports and import ergonomics."""

from mcp_utils import (
  ErrorResponse,
  LifecycleStatus,
  ProgressMetrics,
  create_operation,
  generate_timestamp,
  transition_operation,
)


class TestTopLevelImports:
  def test_base_types(self):
    from mcp_utils import UUID, OperationId, ProgressToken, Timestamp

    assert UUID is not None
    assert Timestamp is not None
    assert OperationId is not None
    assert ProgressToken is not None

  def test_package_level_imports(self):
    from mcp_utils.base import Timestamp, VerbosityMode
    from mcp_utils.core import ErrorResponse, OperationState

    assert Timestamp is not None
    assert VerbosityMode is not None
    assert ErrorResponse is not None
    assert OperationState is not None

  def test_module_level_imports(self):
    from mcp_utils.base.primitives import Timestamp
    from mcp_utils.core.error_response import ErrorResponse

    assert Timestamp is not None
    assert ErrorResponse is not None

  def test_rpc_imports(self):
    from mcp_utils.mcp.rpc import JsonRpcProgressNotification

    assert JsonRpcProgressNotification is not None


class TestEndToEndWorkflow:
  def test_create_and_transition(self):
    state = create_operation("test_tool")
    assert state.status == LifecycleStatus.CREATED

    running = transition_operation(state, LifecycleStatus.RUNNING)
    assert running.status == LifecycleStatus.RUNNING

    progress = ProgressMetrics(current=100, total=100, percentage=100.0)
    completed = transition_operation(running, LifecycleStatus.COMPLETED, progress=progress)
    assert completed.status == LifecycleStatus.COMPLETED
    assert completed.end_time is not None
    assert completed.progress.percentage == 100.0

  def test_create_and_fail(self):
    state = create_operation("tool")
    running = transition_operation(state, LifecycleStatus.RUNNING)
    error = ErrorResponse(code=5001, message="failed", timestamp=generate_timestamp())
    failed = transition_operation(running, LifecycleStatus.FAILED, error=error)
    assert failed.status == LifecycleStatus.FAILED
    assert failed.error is not None
