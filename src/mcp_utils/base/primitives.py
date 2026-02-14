"""Base primitive types: UUID, Timestamp, OperationId, ProgressToken."""

from typing import Annotated

from pydantic import Field

# Regex pattern constants (match CUE source schemas exactly)
UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
TIMESTAMP_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?(Z|[+-]\d{2}:\d{2})$"
OPERATION_ID_PATTERN = r"^op-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
PROGRESS_TOKEN_PATTERN = r"^pt-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

# Annotated type aliases
UUID = Annotated[str, Field(pattern=UUID_PATTERN)]
Timestamp = Annotated[str, Field(pattern=TIMESTAMP_PATTERN)]
OperationId = Annotated[str, Field(pattern=OPERATION_ID_PATTERN)]
ProgressToken = Annotated[str, Field(pattern=PROGRESS_TOKEN_PATTERN)]
