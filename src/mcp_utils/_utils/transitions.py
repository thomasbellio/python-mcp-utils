"""OperationState transition validation helpers."""

from typing import Any

from mcp_utils._utils.factories import generate_operation_id, generate_timestamp
from mcp_utils.core.error_response import ErrorResponse
from mcp_utils.core.operation_state import (
  LifecycleStatus,
  OperationState,
  TPartialResult,
  TResult,
)
from mcp_utils.core.progress_metrics import ProgressMetrics

VALID_TRANSITIONS: dict[LifecycleStatus, set[LifecycleStatus]] = {
  LifecycleStatus.CREATED: {LifecycleStatus.RUNNING},
  LifecycleStatus.RUNNING: {
    LifecycleStatus.PAUSED,
    LifecycleStatus.COMPLETED,
    LifecycleStatus.FAILED,
    LifecycleStatus.CANCELLED,
  },
  LifecycleStatus.PAUSED: {LifecycleStatus.RUNNING},
  LifecycleStatus.COMPLETED: set(),
  LifecycleStatus.FAILED: set(),
  LifecycleStatus.CANCELLED: set(),
}


def validate_transition(
  current: LifecycleStatus,
  target: LifecycleStatus,
) -> bool:
  """Check whether a state transition is valid."""
  return target in VALID_TRANSITIONS.get(current, set())


def transition_operation(
  state: OperationState[TResult, TPartialResult],
  new_status: LifecycleStatus,
  *,
  end_time: str | None = None,
  result: Any | None = None,
  error: ErrorResponse | None = None,
  partial_results: Any | None = None,
  progress: ProgressMetrics | None = None,
) -> OperationState[TResult, TPartialResult]:
  """Transition an OperationState to a new status with validation.

  Returns a new OperationState instance (immutable pattern).
  Raises ValueError if the transition is invalid.
  """
  if not validate_transition(state.status, new_status):
    raise ValueError(
      f"Invalid transition: '{state.status}' → '{new_status}'. "
      f"Valid targets: {VALID_TRANSITIONS.get(state.status, set())}"
    )

  terminal = {LifecycleStatus.COMPLETED, LifecycleStatus.FAILED, LifecycleStatus.CANCELLED}
  effective_end_time = end_time if new_status in terminal else None
  if new_status in terminal and effective_end_time is None:
    effective_end_time = generate_timestamp()

  updates: dict[str, Any] = {"status": new_status}
  if effective_end_time is not None:
    updates["end_time"] = effective_end_time
  if result is not None:
    updates["result"] = result
  if error is not None:
    updates["error"] = error
  if partial_results is not None:
    updates["partial_results"] = partial_results
  if progress is not None:
    updates["progress"] = progress

  return state.model_copy(update=updates)


def create_operation(
  tool_name: str,
  *,
  progress: ProgressMetrics | None = None,
) -> OperationState[dict[str, Any], dict[str, Any]]:
  """Create a new OperationState in 'created' status."""
  return OperationState(
    operation_id=generate_operation_id(),
    tool_name=tool_name,
    status=LifecycleStatus.CREATED,
    start_time=generate_timestamp(),
    progress=progress or ProgressMetrics(current=0, percentage=0.0),
  )
