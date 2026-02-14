"""Factory functions for generating IDs, timestamps, and cancellation tokens."""

import uuid
from datetime import UTC, datetime

from mcp_utils.base.primitives import OperationId, ProgressToken, Timestamp
from mcp_utils.core.cancellation_token import (
  CancellationReason,
  CancellationSource,
  CancellationToken,
)


def generate_uuid() -> str:
  """Generate a lowercase UUID v4 string."""
  return str(uuid.uuid4())


def generate_operation_id() -> OperationId:
  """Generate a properly formatted operation ID: 'op-{uuid}'."""
  return f"op-{generate_uuid()}"


def generate_progress_token() -> ProgressToken:
  """Generate a properly formatted progress token: 'pt-{uuid}'."""
  return f"pt-{generate_uuid()}"


def generate_timestamp() -> Timestamp:
  """Generate a UTC timestamp in ISO 8601 format matching the CUE schema."""
  return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_timestamp(ts: Timestamp) -> datetime:
  """Parse a CUE-format timestamp string into a datetime object."""
  return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def create_cancellation_token(
  *,
  cancelled: bool = False,
  reason: CancellationReason | None = None,
  source: CancellationSource | None = None,
) -> CancellationToken:
  """Create a CancellationToken with proper field enforcement."""
  if cancelled:
    if reason is None or source is None:
      raise ValueError("reason and source are required when cancelled=True")
    return CancellationToken(
      is_cancellation_requested=True,
      reason=reason,
      source=source,
      timestamp=generate_timestamp(),
    )
  return CancellationToken(is_cancellation_requested=False)


def create_active_cancellation_token() -> CancellationToken:
  """Create an uncancelled token (initial state)."""
  return CancellationToken(is_cancellation_requested=False)


def request_cancellation(
  token: CancellationToken,
  reason: CancellationReason,
  source: CancellationSource,
) -> CancellationToken:
  """Return a new CancellationToken with cancellation requested.

  Does not mutate the original (tokens are frozen).
  """
  return token.model_copy(
    update={
      "is_cancellation_requested": True,
      "reason": reason,
      "source": source,
      "timestamp": generate_timestamp(),
    }
  )
