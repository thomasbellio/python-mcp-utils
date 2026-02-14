"""A Python library that houses several utilities that are useful for implementing mcp servers"""

from mcp_utils.__about__ import __version__
from mcp_utils._utils.factories import (
  create_active_cancellation_token,
  create_cancellation_token,
  generate_operation_id,
  generate_progress_token,
  generate_timestamp,
  generate_uuid,
  parse_timestamp,
  request_cancellation,
)
from mcp_utils._utils.transitions import (
  VALID_TRANSITIONS,
  create_operation,
  transition_operation,
  validate_transition,
)
from mcp_utils.base.primitives import UUID, OperationId, ProgressToken, Timestamp
from mcp_utils.base.system_types import VerbosityMode
from mcp_utils.core.cancellation_token import (
  CancellationReason,
  CancellationSource,
  CancellationToken,
)
from mcp_utils.core.error_response import (
  AuthError,
  AuthErrorCode,
  ConnectionErrorCode,
  DataErrorCode,
  ErrorCode,
  ErrorContext,
  ErrorResponse,
  McpConnectionError,
  OperationErrorCode,
  QueryError,
  QueryErrorCode,
  SystemErrorCode,
)
from mcp_utils.core.operation_state import (
  Checkpoint,
  LifecycleStatus,
  OperationState,
  ResumeCapability,
)
from mcp_utils.core.progress_metrics import ProgressMetrics, ProgressNotification
from mcp_utils.mcp.notifications import (
  CancellationNotification,
  ErrorNotification,
  StateChangeNotification,
)

__all__ = [
  "__version__",
  # Base types
  "UUID",
  "Timestamp",
  "OperationId",
  "ProgressToken",
  "VerbosityMode",
  # Error types
  "ErrorCode",
  "ConnectionErrorCode",
  "AuthErrorCode",
  "QueryErrorCode",
  "DataErrorCode",
  "SystemErrorCode",
  "OperationErrorCode",
  "ErrorContext",
  "ErrorResponse",
  "McpConnectionError",
  "AuthError",
  "QueryError",
  # Progress types
  "ProgressMetrics",
  "ProgressNotification",
  # Cancellation types
  "CancellationReason",
  "CancellationSource",
  "CancellationToken",
  # Operation state types
  "LifecycleStatus",
  "Checkpoint",
  "ResumeCapability",
  "OperationState",
  # MCP notifications
  "CancellationNotification",
  "ErrorNotification",
  "StateChangeNotification",
  # Utilities
  "generate_uuid",
  "generate_operation_id",
  "generate_progress_token",
  "generate_timestamp",
  "parse_timestamp",
  "create_cancellation_token",
  "create_active_cancellation_token",
  "request_cancellation",
  "VALID_TRANSITIONS",
  "validate_transition",
  "transition_operation",
  "create_operation",
]
