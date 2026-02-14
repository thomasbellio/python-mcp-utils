"""Base model for all mcp_utils types."""

from pydantic import BaseModel, ConfigDict


class McpUtilsBaseModel(BaseModel):
  """Base model for all mcp_utils types.

  All models are frozen (immutable), serialize to camelCase by default,
  and accept both camelCase and snake_case on input.
  """

  model_config = ConfigDict(
    populate_by_name=True,
    serialize_by_alias=True,
    strict=False,
    frozen=True,
  )
