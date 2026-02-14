"""Tests for base primitive types."""

import pytest
from pydantic import TypeAdapter, ValidationError

from mcp_utils.base.primitives import (
  UUID,
  OperationId,
  ProgressToken,
  Timestamp,
)


class TestUUID:
  ta = TypeAdapter(UUID)

  @pytest.mark.parametrize(
    "value",
    [
      "123e4567-e89b-12d3-a456-426614174000",
      "00000000-0000-0000-0000-000000000000",
      "abcdef01-2345-6789-abcd-ef0123456789",
    ],
  )
  def test_valid(self, value):
    assert self.ta.validate_python(value) == value

  @pytest.mark.parametrize(
    "value",
    [
      "not-a-uuid",
      "123E4567-E89B-12D3-A456-426614174000",  # uppercase
      "123e4567e89b12d3a456426614174000",  # no dashes
      "",
    ],
  )
  def test_invalid(self, value):
    with pytest.raises(ValidationError):
      self.ta.validate_python(value)


class TestTimestamp:
  ta = TypeAdapter(Timestamp)

  @pytest.mark.parametrize(
    "value",
    [
      "2025-01-15T10:30:00Z",
      "2025-01-15T10:30:00.000Z",
      "2025-01-15T10:30:00+05:30",
      "2025-01-15T10:30:00.000+05:30",
      "2025-01-15T10:30:00-08:00",
    ],
  )
  def test_valid(self, value):
    assert self.ta.validate_python(value) == value

  @pytest.mark.parametrize(
    "value",
    [
      "2025-01-15",
      "not-a-timestamp",
      "2025-01-15T10:30:00",  # no timezone
      "2025-01-15T10:30:00.00Z",  # 2 digit millis
      "",
    ],
  )
  def test_invalid(self, value):
    with pytest.raises(ValidationError):
      self.ta.validate_python(value)


class TestOperationId:
  ta = TypeAdapter(OperationId)

  def test_valid(self):
    value = "op-123e4567-e89b-12d3-a456-426614174000"
    assert self.ta.validate_python(value) == value

  @pytest.mark.parametrize(
    "value",
    [
      "123e4567-e89b-12d3-a456-426614174000",  # no prefix
      "pt-123e4567-e89b-12d3-a456-426614174000",  # wrong prefix
      "op-NOT-A-UUID",
      "",
    ],
  )
  def test_invalid(self, value):
    with pytest.raises(ValidationError):
      self.ta.validate_python(value)


class TestProgressToken:
  ta = TypeAdapter(ProgressToken)

  def test_valid(self):
    value = "pt-123e4567-e89b-12d3-a456-426614174000"
    assert self.ta.validate_python(value) == value

  @pytest.mark.parametrize(
    "value",
    [
      "123e4567-e89b-12d3-a456-426614174000",  # no prefix
      "op-123e4567-e89b-12d3-a456-426614174000",  # wrong prefix
      "",
    ],
  )
  def test_invalid(self, value):
    with pytest.raises(ValidationError):
      self.ta.validate_python(value)
