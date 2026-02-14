"""Tests for McpUtilsBaseModel."""

import pytest
from pydantic import Field, ValidationError

from mcp_utils._base_model import McpUtilsBaseModel


class SampleModel(McpUtilsBaseModel):
  """Test model with a camelCase alias."""

  my_field: str = Field(..., alias="myField")
  simple: int = 0


class TestMcpUtilsBaseModel:
  def test_frozen(self):
    m = SampleModel(my_field="hello")
    with pytest.raises(ValidationError):
      m.my_field = "world"  # type: ignore[misc]

  def test_populate_by_name(self):
    m = SampleModel(my_field="hello")
    assert m.my_field == "hello"

  def test_populate_by_alias(self):
    m = SampleModel.model_validate({"myField": "hello"})
    assert m.my_field == "hello"

  def test_serialize_by_alias(self):
    m = SampleModel(my_field="hello")
    data = m.model_dump(by_alias=True)
    assert "myField" in data
    assert "my_field" not in data

  def test_serialize_default_uses_alias(self):
    m = SampleModel(my_field="hello")
    data = m.model_dump()
    assert "myField" in data

  def test_roundtrip(self):
    m = SampleModel(my_field="hello", simple=42)
    data = m.model_dump(by_alias=True)
    m2 = SampleModel.model_validate(data)
    assert m == m2

  def test_model_copy(self):
    m = SampleModel(my_field="hello", simple=1)
    m2 = m.model_copy(update={"simple": 2})
    assert m.simple == 1
    assert m2.simple == 2
