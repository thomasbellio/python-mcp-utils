# Usage Guide

This guide shows how to use `mcp_utils` when building an MCP server implementation.

## Importing

You can import at three levels depending on your preference:

```python
# Top-level (most common)
from mcp_utils import ErrorResponse, OperationState, CancellationToken

# Package-level (explicit about origin)
from mcp_utils.core import ErrorResponse
from mcp_utils.base import Timestamp, OperationId

# Module-level (most specific)
from mcp_utils.core.error_response import ErrorResponse
```

## Operation Lifecycle

The core workflow for long-running MCP tool operations:

```python
from mcp_utils import (
    create_operation,
    transition_operation,
    LifecycleStatus,
    ProgressMetrics,
    ErrorResponse,
    generate_timestamp,
)

# 1. Create an operation when a tool is invoked
state = create_operation("query_database")
# state.status == "created", state.operation_id == "op-..."

# 2. Transition to running
state = transition_operation(state, LifecycleStatus.RUNNING)

# 3. Update progress as work proceeds
progress = ProgressMetrics(current=50, total=100, unit="rows", percentage=50.0)
state = transition_operation(
    state,
    LifecycleStatus.RUNNING,  # stays running, but see note below
    progress=progress,
)
```

**Note:** `transition_operation` validates that the transition is legal. For example, you cannot go from `CREATED` directly to `COMPLETED` -- you must go through `RUNNING` first.

### Completing an operation

```python
# Success
state = transition_operation(
    state,
    LifecycleStatus.COMPLETED,
    result={"rows_processed": 100},
)
# state.end_time is automatically set

# Failure
error = ErrorResponse(
    code=5001,
    message="Database connection lost",
    timestamp=generate_timestamp(),
)
state = transition_operation(state, LifecycleStatus.FAILED, error=error)

# Cancellation
state = transition_operation(
    state,
    LifecycleStatus.CANCELLED,
    partial_results={"rows_processed": 42},
)
```

### Valid state transitions

```
created  --> running
running  --> paused | completed | failed | cancelled
paused   --> running
```

Terminal states (`completed`, `failed`, `cancelled`) have no outgoing transitions. You can check validity programmatically:

```python
from mcp_utils import validate_transition, VALID_TRANSITIONS, LifecycleStatus

validate_transition(LifecycleStatus.RUNNING, LifecycleStatus.COMPLETED)  # True
validate_transition(LifecycleStatus.CREATED, LifecycleStatus.FAILED)     # False
```

## Error Handling

Use the error taxonomy to create structured errors with appropriate code ranges:

```python
from mcp_utils import (
    ErrorResponse,
    McpConnectionError,
    AuthError,
    QueryError,
    ErrorContext,
    generate_timestamp,
)

# General error (code 1000-6999)
error = ErrorResponse(
    code=5001,
    message="Internal server error",
    timestamp=generate_timestamp(),
)

# Connection error (code 1000-1999) -- requires context.operation
error = McpConnectionError(
    code=1001,
    message="Failed to connect to database",
    context=ErrorContext(operation="connect", retries_attempted=3),
    suggestion="Check that the database server is running",
    timestamp=generate_timestamp(),
)

# Auth error (code 2000-2999) -- requires suggestion
error = AuthError(
    code=2001,
    message="Invalid credentials",
    suggestion="Verify your username and password",
    timestamp=generate_timestamp(),
)

# Query error (code 3000-3999) -- requires context.operation
error = QueryError(
    code=3001,
    message="SQL syntax error",
    context=ErrorContext(operation="executeQuery", stage="parsing"),
    timestamp=generate_timestamp(),
)
```

### Error code ranges

| Range | Type | Use case |
|-------|------|----------|
| 1000-1999 | `McpConnectionError` | Network/connection failures |
| 2000-2999 | `AuthError` | Authentication/authorization |
| 3000-3999 | `QueryError` | Query/request errors |
| 4000-4999 | Data errors | Data format/integrity |
| 5000-5999 | System errors | Internal server errors |
| 6000-6999 | Operation errors | Lifecycle/operation failures |

### ErrorContext extras

`ErrorContext` accepts arbitrary additional fields (CUE open struct):

```python
ctx = ErrorContext(
    operation="query",
    stage="execution",
    retries_attempted=2,
    # Any extra fields are allowed
    query_id="q-123",
    table="users",
)
```

## Progress Tracking

Report progress during long-running operations:

```python
from mcp_utils import ProgressMetrics, ProgressNotification, generate_timestamp

# Create metrics
metrics = ProgressMetrics(
    current=50,
    total=100,
    unit="entities",
    percentage=50.0,  # must be consistent with current/total when total is set
)

# Create a notification to send to the client
notification = ProgressNotification(
    operation_id="op-123e4567-e89b-12d3-a456-426614174000",
    progress_token="pt-123e4567-e89b-12d3-a456-426614174001",
    stage="discovering_entities",
    progress=metrics,
    message="Discovered 50 out of 100 entities",
    timestamp=generate_timestamp(),
)
```

**Note:** When `total` is provided and greater than zero, `percentage` must match `current / total * 100` within a 0.01 tolerance. This is validated automatically.

## Cancellation

Implement cooperative cancellation for long-running tools:

```python
from mcp_utils import (
    create_active_cancellation_token,
    request_cancellation,
    CancellationReason,
    CancellationSource,
)

# Create an uncancelled token at the start of an operation
token = create_active_cancellation_token()

# When cancellation is requested, create a new token (tokens are immutable)
cancelled_token = request_cancellation(
    token,
    reason=CancellationReason.USER_REQUESTED,
    source=CancellationSource.CLIENT,
)

# Check in your processing loop
if cancelled_token.is_cancellation_requested:
    # Clean up and transition to cancelled state
    ...
```

## MCP Notifications

Send notifications to MCP clients about operation state changes:

```python
from mcp_utils.mcp import (
    CancellationNotification,
    ErrorNotification,
    StateChangeNotification,
)

# State change (validates the transition is legal)
notification = StateChangeNotification(
    operation_id="op-123e4567-e89b-12d3-a456-426614174000",
    old_state=LifecycleStatus.RUNNING,
    new_state=LifecycleStatus.COMPLETED,
    timestamp=generate_timestamp(),
)
```

### JSON-RPC Wrappers

If you're implementing a custom transport, use the JSON-RPC wrappers:

```python
from mcp_utils.mcp.rpc import JsonRpcProgressNotification

rpc_message = JsonRpcProgressNotification(params=notification)
# rpc_message.jsonrpc == "2.0"
# rpc_message.method == "notifications/progress"

wire_data = rpc_message.model_dump(by_alias=True)
# Ready to serialize to JSON and send over the wire
```

## Serialization

All models serialize to camelCase by default (matching the CUE wire format):

```python
from mcp_utils import ErrorResponse, generate_timestamp

error = ErrorResponse(
    code=1001,
    message="Connection failed",
    timestamp=generate_timestamp(),
)

# Serialize to camelCase JSON (default)
data = error.model_dump(by_alias=True)
# {"code": 1001, "message": "Connection failed", "timestamp": "..."}

# Deserialize from camelCase
error2 = ErrorResponse.model_validate(data)

# snake_case input is also accepted
error3 = ErrorResponse.model_validate({
    "code": 1001,
    "message": "Connection failed",
    "timestamp": "2025-01-15T10:30:00Z",
})
```

## Immutability

All models are frozen. Use `model_copy` to create modified instances:

```python
error = ErrorResponse(
    code=1001,
    message="Original message",
    timestamp=generate_timestamp(),
)

# This raises an error:
# error.message = "New message"

# Instead, create a copy with updates:
updated = error.model_copy(update={"message": "Updated message"})
```

## ID and Timestamp Generation

Utility functions for generating properly formatted identifiers:

```python
from mcp_utils import (
    generate_uuid,
    generate_operation_id,
    generate_progress_token,
    generate_timestamp,
    parse_timestamp,
)

generate_uuid()            # "a1b2c3d4-e5f6-7890-abcd-ef0123456789"
generate_operation_id()    # "op-a1b2c3d4-e5f6-7890-abcd-ef0123456789"
generate_progress_token()  # "pt-a1b2c3d4-e5f6-7890-abcd-ef0123456789"
generate_timestamp()       # "2025-01-15T10:30:00Z"

dt = parse_timestamp("2025-01-15T10:30:00Z")  # datetime object (UTC)
```
