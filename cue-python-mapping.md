# CUE-to-Python Mapping Specification

## `mcp_utils` — Python Implementation of `mcp-utils-schema`

**Source Schema**: `github.com/thomasbellio/mcp-utils-schema`
**Target Library**: `mcp_utils` (Python, Pydantic v2)
**Generated From Template**: `thomasbellio/copier-template-python-library`

---

## 1. Design Decisions Record

These decisions are **binding** for the implementation and should not be revisited without updating this document.

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Python package name | `mcp_utils` | Clean, concise, matches ecosystem conventions |
| Field naming | snake_case with camelCase aliases | Pythonic API; Pydantic aliases preserve wire compatibility |
| Open structs (`{...}`) | `dict[str, Any]` with `model_config = ConfigDict(extra="allow")` where CUE uses `...` | Matches CUE open-struct semantics exactly |
| Generic result types | `TypeVar` + `Generic` on `OperationState`, `Checkpoint` | Enables typed results for consumers without losing flexibility |
| Validation library | Pydantic v2 (`pydantic >= 2.0`) | 1:1 mapping to CUE constraints; runtime validation; ubiquitous in MCP ecosystem |
| MCP notifications | Data models only (transport-agnostic); optional JSON-RPC wrappers in separate submodule | Avoids coupling to stdio/SSE/HTTP; lets official MCP SDK handle framing |
| Utility functions | Provided alongside data models; all models also exported directly | Convenience without forcing usage patterns |
| ErrorContext openness | `extra="allow"` | Matches CUE `{...}` semantics; consumers can add arbitrary fields |

---

## 2. Package Structure

### CUE Module → Python Package Mapping

```
CUE: schemas/base/          →  Python: src/mcp_utils/base/
CUE: schemas/core/          →  Python: src/mcp_utils/core/
CUE: schemas/mcp/           →  Python: src/mcp_utils/mcp/
(no CUE equivalent)         →  Python: src/mcp_utils/mcp/rpc/     (optional JSON-RPC wrappers)
```

### Full Python Package Layout

```
src/mcp_utils/
├── __init__.py              # Top-level re-exports of all public types + utilities
├── __about__.py             # Version info (from copier template)
├── py.typed                 # PEP 561 marker (from copier template)
│
├── base/
│   ├── __init__.py          # Re-exports: UUID, Timestamp, OperationId, ProgressToken, VerbosityMode
│   ├── primitives.py        # UUID, Timestamp, OperationId, ProgressToken
│   └── system_types.py      # VerbosityMode
│
├── core/
│   ├── __init__.py          # Re-exports all core types
│   ├── error_response.py    # ErrorCode, ErrorContext, ErrorResponse, ConnectionError, AuthError, QueryError
│   ├── progress_metrics.py  # ProgressMetrics, ProgressNotification
│   ├── cancellation_token.py # CancellationReason, CancellationSource, CancellationToken
│   └── operation_state.py   # LifecycleStatus, Checkpoint, ResumeCapability, OperationState
│
├── mcp/
│   ├── __init__.py          # Re-exports all MCP notification types
│   ├── notifications.py     # ProgressNotification (re-export), CancellationNotification, ErrorNotification, StateChangeNotification
│   └── rpc/
│       ├── __init__.py      # Re-exports JSON-RPC wrapper types
│       └── wrappers.py      # Optional JSON-RPC envelope models
│
└── _utils/
    ├── __init__.py          # Re-exports all utility functions
    ├── factories.py         # Factory functions: generate_operation_id(), generate_progress_token(), etc.
    └── transitions.py       # OperationState transition validation helpers
```

### Import Ergonomics

Consumers should be able to import at multiple levels:

```python
# Top-level (most common)
from mcp_utils import ErrorResponse, OperationState, CancellationToken

# Package-level (when you want to be explicit about origin)
from mcp_utils.core import ErrorResponse
from mcp_utils.base import Timestamp, OperationId

# Utilities
from mcp_utils import generate_operation_id, generate_progress_token

# Optional JSON-RPC wrappers (only for custom transport implementers)
from mcp_utils.mcp.rpc import JsonRpcProgressNotification
```

---

## 3. Global Conventions

### 3.1 Pydantic Model Configuration

All models in the library MUST use this base configuration pattern:

```python
from pydantic import BaseModel, ConfigDict

class McpUtilsBaseModel(BaseModel):
    """Base model for all mcp_utils types."""
    model_config = ConfigDict(
        populate_by_name=True,        # Allow both snake_case and camelCase
        serialize_by_alias=True,       # Serialize to camelCase by default (wire format)
        strict=False,                  # Allow coercion where sensible
        frozen=True,                   # Immutable by default — these are data transfer objects
    )
```

**Rationale for `frozen=True`**: These are schema-defined data transfer objects. Immutability prevents accidental mutation and makes them hashable. Consumers who need mutability can use `model_copy(update={...})`.

**Exception**: `CancellationToken` may warrant `frozen=False` if consumers need to flip `is_cancellation_requested` in-place. However, the recommended pattern is `token.model_copy(update={"is_cancellation_requested": True, ...})`. Decision: keep `frozen=True` for consistency; provide a utility method `CancellationToken.request_cancellation(reason, source)` that returns a new instance.

### 3.2 Field Alias Convention

Every field that differs between Python (snake_case) and CUE (camelCase) MUST declare an alias:

```python
from pydantic import Field

operation_id: OperationId = Field(..., alias="operationId")
```

This ensures:
- Python code uses `obj.operation_id` (Pythonic)
- JSON serialization produces `{"operationId": "..."}` (CUE-compatible)
- JSON deserialization accepts `{"operationId": "..."}` (CUE-compatible)
- JSON deserialization also accepts `{"operation_id": "..."}` (via `populate_by_name=True`)

### 3.3 Annotated Types Pattern

For constrained primitives (UUID, Timestamp, etc.), use `Annotated` with Pydantic validators:

```python
from typing import Annotated
from pydantic import Field
from pydantic.functional_validators import AfterValidator
# or
from annotated_types import Ge, Le  # for numeric constraints
```

---

## 4. Type Mapping Tables

### 4.1 Base Primitives (`schemas/base/primitives.cue` → `mcp_utils/base/primitives.py`)

| CUE Definition | CUE Type & Constraint | Python Type | Python Constraint | Notes |
|---|---|---|---|---|
| `#UUID` | `string & =~"^[a-f0-9]{8}-..."` | `Annotated[str, Field(pattern=UUID_PATTERN)]` | Regex pattern constant | Define `UUID_PATTERN` as a module-level constant |
| `#Timestamp` | `string & =~"^[0-9]{4}-..."` | `Annotated[str, Field(pattern=TIMESTAMP_PATTERN)]` | Regex pattern constant | ISO 8601 UTC only (ends in `Z`). Consider also accepting `datetime` and serializing to string — see design note below |
| `#OperationId` | `string & =~"^op-..."` | `Annotated[str, Field(pattern=OPERATION_ID_PATTERN)]` | Regex pattern constant | Format: `op-{uuid}` |
| `#ProgressToken` | `string & =~"^pt-..."` | `Annotated[str, Field(pattern=PROGRESS_TOKEN_PATTERN)]` | Regex pattern constant | Format: `pt-{uuid}` |

**Regex Pattern Constants** (define in `primitives.py`):

```python
UUID_PATTERN = r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
TIMESTAMP_PATTERN = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
OPERATION_ID_PATTERN = r"^op-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
PROGRESS_TOKEN_PATTERN = r"^pt-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
```

**Design Note on Timestamp**: The CUE schema requires a string in ISO 8601 format. The Python type should be a `str` constrained by regex to match the CUE spec exactly. However, the factory utility `generate_timestamp()` should produce these strings from `datetime.now(UTC)`, and a `parse_timestamp(ts: Timestamp) -> datetime` utility should be provided for consumers who want to work with `datetime` objects.

### 4.2 Base System Types (`schemas/base/system_types.cue` → `mcp_utils/base/system_types.py`)

| CUE Definition | CUE Values | Python Type | Python Implementation |
|---|---|---|---|
| `#VerbosityMode` | `"coarse" \| "normal" \| "fine" \| "debug"` | `VerbosityMode(StrEnum)` | `class VerbosityMode(StrEnum)` |

```python
from enum import StrEnum

class VerbosityMode(StrEnum):
    """Verbosity levels for progress notifications.

    - COARSE: Only major stage changes
    - NORMAL: Stage + percentage updates (default)
    - FINE: Detailed metrics + messages
    - DEBUG: Everything including metadata
    """
    COARSE = "coarse"
    NORMAL = "normal"
    FINE = "fine"
    DEBUG = "debug"
```

### 4.3 Core Error Types (`schemas/core/error_response.cue` → `mcp_utils/core/error_response.py`)

#### Error Code Types

| CUE Definition | CUE Constraint | Python Type | Python Constraint |
|---|---|---|---|
| `#ErrorCode` | `int & >=1000 & <=6999` | `Annotated[int, Field(ge=1000, le=6999)]` | Pydantic Field constraints |
| `#ConnectionErrorCode` | `int & >=1000 & <=1999` | `Annotated[int, Field(ge=1000, le=1999)]` | |
| `#AuthErrorCode` | `int & >=2000 & <=2999` | `Annotated[int, Field(ge=2000, le=2999)]` | |
| `#QueryErrorCode` | `int & >=3000 & <=3999` | `Annotated[int, Field(ge=3000, le=3999)]` | |
| `#DataErrorCode` | `int & >=4000 & <=4999` | `Annotated[int, Field(ge=4000, le=4999)]` | |
| `#SystemErrorCode` | `int & >=5000 & <=5999` | `Annotated[int, Field(ge=5000, le=5999)]` | |
| `#OperationErrorCode` | `int & >=6000 & <=6999` | `Annotated[int, Field(ge=6000, le=6999)]` | |

**Implementation approach**: Define these as `Annotated` type aliases, NOT as classes:

```python
from typing import Annotated
from pydantic import Field

ErrorCode = Annotated[int, Field(ge=1000, le=6999, description="Error code (1000-6999)")]
ConnectionErrorCode = Annotated[int, Field(ge=1000, le=1999, description="Connection error code (1000-1999)")]
AuthErrorCode = Annotated[int, Field(ge=2000, le=2999, description="Authentication error code (2000-2999)")]
QueryErrorCode = Annotated[int, Field(ge=3000, le=3999, description="Query error code (3000-3999)")]
DataErrorCode = Annotated[int, Field(ge=4000, le=4999, description="Data error code (4000-4999)")]
SystemErrorCode = Annotated[int, Field(ge=5000, le=5999, description="System error code (5000-5999)")]
OperationErrorCode = Annotated[int, Field(ge=6000, le=6999, description="Operation error code (6000-6999)")]
```

#### ErrorContext

| CUE Field | CUE Type | Python Field | Python Type | Required | Alias |
|---|---|---|---|---|---|
| `operation` | `string` | `operation` | `str \| None` | No | — |
| `stage` | `string` | `stage` | `str \| None` | No | — |
| `retriesAttempted` | `int & >=0` | `retries_attempted` | `Annotated[int, Field(ge=0)] \| None` | No | `retriesAttempted` |
| `...` (open) | any | — | — | — | `model_config = ConfigDict(extra="allow")` |

```python
class ErrorContext(McpUtilsBaseModel):
    """Context information about an error. Allows arbitrary additional fields."""
    model_config = ConfigDict(
        **McpUtilsBaseModel.model_config,  # inherit base config
        extra="allow",                      # CUE open struct: {...}
    )

    operation: str | None = None
    stage: str | None = None
    retries_attempted: Annotated[int, Field(ge=0)] | None = Field(
        default=None, alias="retriesAttempted"
    )
```

#### ErrorResponse

| CUE Field | CUE Type | Python Field | Python Type | Required | Alias |
|---|---|---|---|---|---|
| `code` | `#ErrorCode` | `code` | `ErrorCode` | **Yes** | — |
| `message` | `string & =~".+"` | `message` | `Annotated[str, Field(min_length=1)]` | **Yes** | — |
| `context` | `#ErrorContext` | `context` | `ErrorContext \| None` | No | — |
| `suggestion` | `string` | `suggestion` | `str \| None` | No | — |
| `trace` | `[...string]` | `trace` | `list[str] \| None` | No | — |
| `timestamp` | `base.#Timestamp` | `timestamp` | `Timestamp` | **Yes** | — |

**Conditional validation from CUE**: The CUE spec in `avante.md` states `if trace != _|_ { trace: len(trace) > 0 }` — if trace is provided, it must be non-empty. The actual `.cue` file uses `trace?: [...string]` without that constraint. **Follow the actual `.cue` file** but implement the non-empty check as a model validator since it's a sensible safety net:

```python
class ErrorResponse(McpUtilsBaseModel):
    code: ErrorCode
    message: Annotated[str, Field(min_length=1)]
    context: ErrorContext | None = None
    suggestion: str | None = None
    trace: list[str] | None = None
    timestamp: Timestamp

    @model_validator(mode="after")
    def validate_trace_non_empty(self) -> Self:
        if self.trace is not None and len(self.trace) == 0:
            raise ValueError("trace, if provided, must not be empty")
        return self
```

#### Specialized Error Types

These are subclasses with narrower code ranges and additional required fields:

| CUE Type | Python Class | Inherits | Code Type | Additional Required Fields |
|---|---|---|---|---|
| `#ConnectionError` | `ConnectionError_` | `ErrorResponse` | `ConnectionErrorCode` | `context.operation` must be present |
| `#AuthError` | `AuthError` | `ErrorResponse` | `AuthErrorCode` | `suggestion` must be present (not None) |
| `#QueryError` | `QueryError` | `ErrorResponse` | `QueryErrorCode` | `context.operation` must be present |

**Naming note**: `ConnectionError` shadows the Python built-in. Use `ConnectionError_` as the class name but export it as `ConnectionError` via `__all__` with a note in documentation. Alternatively, name it `McpConnectionError`. **Decision: use `McpConnectionError`** to avoid any shadowing issues.

```python
class McpConnectionError(ErrorResponse):
    """Connection error — requires operation in context."""
    code: ConnectionErrorCode
    context: ErrorContext  # Required (not Optional)

    @model_validator(mode="after")
    def validate_operation_required(self) -> Self:
        if self.context.operation is None:
            raise ValueError("ConnectionError requires context.operation")
        return self

class AuthError(ErrorResponse):
    """Authentication error — must include suggestion."""
    code: AuthErrorCode
    suggestion: str  # Required (not Optional)

class QueryError(ErrorResponse):
    """Query error — requires operation in context."""
    code: QueryErrorCode
    context: ErrorContext  # Required (not Optional)

    @model_validator(mode="after")
    def validate_operation_required(self) -> Self:
        if self.context.operation is None:
            raise ValueError("QueryError requires context.operation")
        return self
```

### 4.4 Core Progress Types (`schemas/core/progress_metrics.cue` → `mcp_utils/core/progress_metrics.py`)

#### ProgressMetrics

| CUE Field | CUE Type | Python Field | Python Type | Required | Alias | Default |
|---|---|---|---|---|---|---|
| `current` | `int & >=0` | `current` | `Annotated[int, Field(ge=0)]` | **Yes** | — | — |
| `total` | `int \| *null` | `total` | `int \| None` | No | — | `None` |
| `unit` | `string \| *"items"` | `unit` | `str` | No | — | `"items"` |
| `percentage` | `float & >=0 & <=100` | `percentage` | `Annotated[float, Field(ge=0.0, le=100.0)]` | **Yes** | — | — |

**CUE conditional validation**: "if total is known and > 0, percentage must match current/total * 100 within 0.01 tolerance"

```python
class ProgressMetrics(McpUtilsBaseModel):
    current: Annotated[int, Field(ge=0)]
    total: int | None = None
    unit: str = "items"
    percentage: Annotated[float, Field(ge=0.0, le=100.0)]

    @model_validator(mode="after")
    def validate_percentage_consistency(self) -> Self:
        if self.total is not None and self.total > 0:
            expected = (self.current / self.total) * 100
            if abs(self.percentage - expected) > 0.01:
                raise ValueError(
                    f"percentage ({self.percentage}) inconsistent with "
                    f"current/total ({self.current}/{self.total} = {expected:.2f})"
                )
        return self
```

#### ProgressNotification

| CUE Field | CUE Type | Python Field | Python Type | Required | Alias |
|---|---|---|---|---|---|
| `operationId` | `base.#OperationId` | `operation_id` | `OperationId` | **Yes** | `operationId` |
| `progressToken` | `base.#ProgressToken` | `progress_token` | `ProgressToken` | **Yes** | `progressToken` |
| `stage` | `string` | `stage` | `str` | **Yes** | — |
| `progress` | `#ProgressMetrics` | `progress` | `ProgressMetrics` | **Yes** | — |
| `message` | `string` | `message` | `str \| None` | No | — |
| `metadata` | `{...}` | `metadata` | `dict[str, Any] \| None` | No | — |
| `timestamp` | `base.#Timestamp` | `timestamp` | `Timestamp` | **Yes** | — |

### 4.5 Core Cancellation Types (`schemas/core/cancellation_token.cue` → `mcp_utils/core/cancellation_token.py`)

#### Enums

| CUE Definition | CUE Values | Python Type |
|---|---|---|
| `#CancellationReason` | `"user_requested" \| "timeout" \| "resource_limit" \| "error_threshold"` | `CancellationReason(StrEnum)` |
| `#CancellationSource` | `"client" \| "server"` | `CancellationSource(StrEnum)` |

```python
class CancellationReason(StrEnum):
    USER_REQUESTED = "user_requested"
    TIMEOUT = "timeout"
    RESOURCE_LIMIT = "resource_limit"
    ERROR_THRESHOLD = "error_threshold"

class CancellationSource(StrEnum):
    CLIENT = "client"
    SERVER = "server"
```

#### CancellationToken

| CUE Field | CUE Type | Python Field | Python Type | Required | Alias |
|---|---|---|---|---|---|
| `isCancellationRequested` | `bool` | `is_cancellation_requested` | `bool` | **Yes** | `isCancellationRequested` |
| `reason` | `#CancellationReason` | `reason` | `CancellationReason \| None` | Conditional | — |
| `source` | `#CancellationSource` | `source` | `CancellationSource \| None` | Conditional | — |
| `timestamp` | `base.#Timestamp` | `timestamp` | `Timestamp \| None` | Conditional | — |

**CUE conditional**: "if `isCancellationRequested == true`, then `reason`, `source`, and `timestamp` are all required"

```python
class CancellationToken(McpUtilsBaseModel):
    is_cancellation_requested: bool = Field(..., alias="isCancellationRequested")
    reason: CancellationReason | None = None
    source: CancellationSource | None = None
    timestamp: Timestamp | None = None

    @model_validator(mode="after")
    def validate_cancellation_fields(self) -> Self:
        if self.is_cancellation_requested:
            missing = []
            if self.reason is None:
                missing.append("reason")
            if self.source is None:
                missing.append("source")
            if self.timestamp is None:
                missing.append("timestamp")
            if missing:
                raise ValueError(
                    f"When cancellation is requested, these fields are required: {', '.join(missing)}"
                )
        return self
```

### 4.6 Core Operation State Types (`schemas/core/operation_state.cue` → `mcp_utils/core/operation_state.py`)

#### Enums

| CUE Definition | CUE Values | Python Type |
|---|---|---|
| `#LifecycleStatus` | `"created" \| "running" \| "paused" \| "completed" \| "failed" \| "cancelled"` | `LifecycleStatus(StrEnum)` |

```python
class LifecycleStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

**Valid state transitions** (from architecture diagram):

```python
VALID_TRANSITIONS: dict[LifecycleStatus, set[LifecycleStatus]] = {
    LifecycleStatus.CREATED: {LifecycleStatus.RUNNING},
    LifecycleStatus.RUNNING: {
        LifecycleStatus.PAUSED,
        LifecycleStatus.COMPLETED,
        LifecycleStatus.FAILED,
        LifecycleStatus.CANCELLED,
    },
    LifecycleStatus.PAUSED: {LifecycleStatus.RUNNING},
    LifecycleStatus.COMPLETED: set(),   # terminal
    LifecycleStatus.FAILED: set(),       # terminal
    LifecycleStatus.CANCELLED: set(),    # terminal
}
```

This transition map should live in `mcp_utils/_utils/transitions.py` and be used by utility functions.

#### Generic Type Variables

```python
from typing import TypeVar, Generic, Any

TResult = TypeVar("TResult", default=dict[str, Any])
TCheckpointData = TypeVar("TCheckpointData", default=dict[str, Any])
TPartialResult = TypeVar("TPartialResult", default=dict[str, Any])
```

**Note on TypeVar defaults**: `TypeVar` defaults require Python 3.13+ or `typing_extensions`. Since the copier template targets `min_python_version: "3.14"`, native `TypeVar` defaults are available. If broader compatibility is needed later, use `typing_extensions.TypeVar`.

#### Checkpoint

| CUE Field | CUE Type | Python Field | Python Type | Required | Alias |
|---|---|---|---|---|---|
| `data` | `{...}` | `data` | `TCheckpointData` | **Yes** | — |
| `timestamp` | `base.#Timestamp` | `timestamp` | `Timestamp` | **Yes** | — |
| `stage` | `string` | `stage` | `str` | **Yes** | — |

```python
class Checkpoint(McpUtilsBaseModel, Generic[TCheckpointData]):
    data: TCheckpointData
    timestamp: Timestamp
    stage: str
```

#### ResumeCapability

| CUE Field | CUE Type | Python Field | Python Type | Required | Alias |
|---|---|---|---|---|---|
| `checkpoint` | `#Checkpoint` | `checkpoint` | `Checkpoint[TCheckpointData]` | **Yes** | — |
| `resumableOperations` | `[...string]` | `resumable_operations` | `list[str]` | **Yes** | `resumableOperations` |

```python
class ResumeCapability(McpUtilsBaseModel, Generic[TCheckpointData]):
    checkpoint: Checkpoint[TCheckpointData]
    resumable_operations: list[str] = Field(..., alias="resumableOperations")
```

#### OperationState

| CUE Field | CUE Type | Python Field | Python Type | Required | Alias |
|---|---|---|---|---|---|
| `operationId` | `base.#OperationId` | `operation_id` | `OperationId` | **Yes** | `operationId` |
| `toolName` | `string` | `tool_name` | `str` | **Yes** | `toolName` |
| `status` | `#LifecycleStatus` | `status` | `LifecycleStatus` | **Yes** | — |
| `startTime` | `base.#Timestamp` | `start_time` | `Timestamp` | **Yes** | `startTime` |
| `endTime` | `base.#Timestamp` | `end_time` | `Timestamp \| None` | Conditional | `endTime` |
| `progress` | `#ProgressMetrics` | `progress` | `ProgressMetrics` | **Yes** | — |
| `result` | `{...}` | `result` | `TResult \| None` | Conditional | — |
| `error` | `#ErrorResponse` | `error` | `ErrorResponse \| None` | Conditional | — |
| `partialResults` | `{...}` | `partial_results` | `TPartialResult \| None` | Conditional | `partialResults` |

**CUE conditional validations** (from `avante.md` spec — the actual `.cue` file defers these to runtime):

1. Terminal states (`completed`, `failed`, `cancelled`) → `end_time` required
2. `failed` → `error` required
3. `cancelled` → `partial_results` required

```python
class OperationState(McpUtilsBaseModel, Generic[TResult, TPartialResult]):
    operation_id: OperationId = Field(..., alias="operationId")
    tool_name: str = Field(..., alias="toolName")
    status: LifecycleStatus
    start_time: Timestamp = Field(..., alias="startTime")
    end_time: Timestamp | None = Field(default=None, alias="endTime")
    progress: ProgressMetrics
    result: TResult | None = None
    error: ErrorResponse | None = None
    partial_results: TPartialResult | None = Field(default=None, alias="partialResults")

    @model_validator(mode="after")
    def validate_status_constraints(self) -> Self:
        terminal = {LifecycleStatus.COMPLETED, LifecycleStatus.FAILED, LifecycleStatus.CANCELLED}
        if self.status in terminal and self.end_time is None:
            raise ValueError(f"end_time is required when status is '{self.status}'")
        if self.status == LifecycleStatus.FAILED and self.error is None:
            raise ValueError("error is required when status is 'failed'")
        if self.status == LifecycleStatus.CANCELLED and self.partial_results is None:
            raise ValueError("partial_results is required when status is 'cancelled'")
        return self
```

### 4.7 MCP Notification Types (`schemas/mcp/notifications.cue` → `mcp_utils/mcp/notifications.py`)

These are the **transport-agnostic data models** — the payloads, not the envelopes.

| CUE Type | Python Class | Fields |
|---|---|---|
| `#ProgressNotification` | Re-export of `core.ProgressNotification` | (same as core) |
| `#CancellationNotification` | `CancellationNotification` | `operation_id`, `cancellation_token`, `timestamp` |
| `#ErrorNotification` | `ErrorNotification` | `operation_id`, `error`, `timestamp` |
| `#StateChangeNotification` | `StateChangeNotification` | `operation_id`, `old_state`, `new_state`, `timestamp` |

```python
# mcp_utils/mcp/notifications.py

from mcp_utils.core.progress_metrics import ProgressNotification  # re-export

class CancellationNotification(McpUtilsBaseModel):
    operation_id: OperationId = Field(..., alias="operationId")
    cancellation_token: CancellationToken = Field(..., alias="cancellationToken")
    timestamp: Timestamp

class ErrorNotification(McpUtilsBaseModel):
    operation_id: OperationId = Field(..., alias="operationId")
    error: ErrorResponse
    timestamp: Timestamp

class StateChangeNotification(McpUtilsBaseModel):
    operation_id: OperationId = Field(..., alias="operationId")
    old_state: LifecycleStatus = Field(..., alias="oldState")
    new_state: LifecycleStatus = Field(..., alias="newState")
    timestamp: Timestamp

    @model_validator(mode="after")
    def validate_transition(self) -> Self:
        valid = VALID_TRANSITIONS.get(self.old_state, set())
        if self.new_state not in valid:
            raise ValueError(
                f"Invalid state transition: '{self.old_state}' → '{self.new_state}'"
            )
        return self
```

### 4.8 Optional JSON-RPC Wrappers (`mcp_utils/mcp/rpc/wrappers.py`)

These wrap the notification payloads in JSON-RPC envelope format. **Only needed by consumers implementing custom transports.**

```python
# mcp_utils/mcp/rpc/wrappers.py

from typing import Literal

class JsonRpcNotification(McpUtilsBaseModel):
    """Base JSON-RPC 2.0 notification (no id, no response expected)."""
    jsonrpc: Literal["2.0"] = "2.0"
    method: str
    params: dict[str, Any] | None = None

class JsonRpcProgressNotification(JsonRpcNotification):
    method: Literal["notifications/progress"] = "notifications/progress"
    params: ProgressNotification

class JsonRpcCancellationNotification(JsonRpcNotification):
    method: Literal["notifications/cancelled"] = "notifications/cancelled"
    params: CancellationNotification

class JsonRpcErrorNotification(JsonRpcNotification):
    method: Literal["notifications/error"] = "notifications/error"
    params: ErrorNotification

class JsonRpcStateChangeNotification(JsonRpcNotification):
    method: Literal["notifications/state_change"] = "notifications/state_change"
    params: StateChangeNotification
```

---

## 5. Utility Functions

### 5.1 Factories (`mcp_utils/_utils/factories.py`)

```python
import uuid
from datetime import datetime, UTC

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
```

### 5.2 CancellationToken Convenience Methods (`mcp_utils/_utils/factories.py`)

```python
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
    return token.model_copy(update={
        "is_cancellation_requested": True,
        "reason": reason,
        "source": source,
        "timestamp": generate_timestamp(),
    })
```

### 5.3 OperationState Transitions (`mcp_utils/_utils/transitions.py`)

```python
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
    end_time: Timestamp | None = None,
    result: TResult | None = None,
    error: ErrorResponse | None = None,
    partial_results: TPartialResult | None = None,
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
) -> OperationState:
    """Create a new OperationState in 'created' status."""
    return OperationState(
        operation_id=generate_operation_id(),
        tool_name=tool_name,
        status=LifecycleStatus.CREATED,
        start_time=generate_timestamp(),
        progress=progress or ProgressMetrics(current=0, percentage=0.0),
    )
```

---

## 6. Top-Level Exports (`src/mcp_utils/__init__.py`)

The top-level `__init__.py` should re-export everything a consumer needs for typical usage:

```python
# Types
from mcp_utils.base.primitives import UUID, Timestamp, OperationId, ProgressToken
from mcp_utils.base.system_types import VerbosityMode
from mcp_utils.core.error_response import (
    ErrorCode, ConnectionErrorCode, AuthErrorCode, QueryErrorCode,
    DataErrorCode, SystemErrorCode, OperationErrorCode,
    ErrorContext, ErrorResponse, McpConnectionError, AuthError, QueryError,
)
from mcp_utils.core.progress_metrics import ProgressMetrics, ProgressNotification
from mcp_utils.core.cancellation_token import (
    CancellationReason, CancellationSource, CancellationToken,
)
from mcp_utils.core.operation_state import (
    LifecycleStatus, Checkpoint, ResumeCapability, OperationState,
)
from mcp_utils.mcp.notifications import (
    CancellationNotification, ErrorNotification, StateChangeNotification,
)

# Utilities
from mcp_utils._utils.factories import (
    generate_uuid, generate_operation_id, generate_progress_token,
    generate_timestamp, parse_timestamp,
    create_cancellation_token, create_active_cancellation_token,
    request_cancellation,
)
from mcp_utils._utils.transitions import (
    VALID_TRANSITIONS, validate_transition, transition_operation, create_operation,
)
```

---

## 7. Dependencies

### Required (add to `pyproject.toml` under `[tool.poetry.dependencies]`):

```toml
pydantic = "^2.0"
```

### No Additional Dependencies Required

- `StrEnum` is built-in (Python 3.11+)
- `TypeVar` defaults are built-in (Python 3.13+)
- `Annotated` is built-in (Python 3.9+)
- `uuid`, `datetime` are stdlib

---

## 8. Testing Strategy Notes

This section provides guidance for the test agent. Tests should be organized to mirror the source:

```
tests/
├── base/
│   ├── test_primitives.py       # Regex validation, valid/invalid patterns
│   └── test_system_types.py     # Enum membership
├── core/
│   ├── test_error_response.py   # Code ranges, required fields, specialized errors
│   ├── test_progress_metrics.py # Percentage consistency, boundary values
│   ├── test_cancellation_token.py # Conditional required fields
│   └── test_operation_state.py  # Status-dependent validations, generics
├── mcp/
│   ├── test_notifications.py    # All four notification types
│   └── rpc/
│       └── test_wrappers.py     # JSON-RPC envelope structure
└── utils/
    ├── test_factories.py        # ID generation format, timestamp format
    └── test_transitions.py      # Valid/invalid transitions, create_operation
```

### Key Test Categories Per Type

For each Pydantic model, tests should cover:

1. **Happy path**: Valid data matching CUE test fixtures (from `test/validation/`)
2. **Constraint violations**: Values outside ranges, empty strings, missing required fields
3. **Conditional validation**: Status-dependent required fields
4. **Serialization round-trip**: `model.model_dump(by_alias=True)` produces camelCase JSON → `Model.model_validate(json)` reconstructs the object
5. **Alias acceptance**: Both `{"operationId": "..."}` and `{"operation_id": "..."}` deserialize correctly

### Reference Fixtures (from CUE `test/validation/`)

The CUE repository contains validation fixtures that should be translated to Python test data:

```python
# From test/validation/error_response.cue
VALID_CONNECTION_ERROR = {
    "code": 1001,
    "message": "Failed to connect to database",
    "context": {"operation": "connect", "retriesAttempted": 3},
    "suggestion": "Check that the database server is running and accessible",
    "timestamp": "2025-01-15T10:30:00Z",
}

VALID_AUTH_ERROR = {
    "code": 2001,
    "message": "Invalid credentials provided",
    "suggestion": "Verify your username and password are correct",
    "timestamp": "2025-01-15T10:30:00Z",
}
```

---

## 9. Architecture Agent Checklist

The architecture agent should verify these properties on every review pass:

### Structural Compliance
- [ ] Package layout matches Section 2 exactly
- [ ] Every CUE type has a corresponding Python type
- [ ] No Python types exist that don't trace back to a CUE definition (except `McpUtilsBaseModel`, utilities, and JSON-RPC wrappers)
- [ ] Import paths work at all three levels (top-level, package, module)

### Field Compliance
- [ ] Every CUE field maps to the correct Python field with proper alias
- [ ] All snake_case ↔ camelCase aliases are declared
- [ ] Required fields in CUE are required (no default) in Python
- [ ] Optional fields in CUE are `| None = None` in Python
- [ ] Default values match (`unit: *"items"` → `unit: str = "items"`)

### Constraint Compliance
- [ ] All regex patterns match CUE exactly
- [ ] All numeric ranges match CUE exactly (`ge`, `le` vs `>=`, `<=`)
- [ ] All enum values match CUE exactly
- [ ] Conditional validations are implemented as `@model_validator`

### Serialization Compliance
- [ ] `model_dump(by_alias=True)` produces CUE-compatible JSON
- [ ] `model_validate(cue_compatible_json)` succeeds
- [ ] Round-trip: `Model.model_validate(model.model_dump(by_alias=True))` preserves all data

### Tooling Compliance
- [ ] `ruff check src/` passes
- [ ] `ruff format --check src/` passes
- [ ] `mypy src/mcp_utils` passes (strict mode)
- [ ] `pytest tests/` passes
- [ ] All public types are in `__all__` or re-exported
