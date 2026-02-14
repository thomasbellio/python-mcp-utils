"""Tests for core cancellation types."""

import pytest
from pydantic import ValidationError

from mcp_utils.core.cancellation_token import (
  CancellationReason,
  CancellationSource,
  CancellationToken,
)


class TestCancellationReason:
  def test_members(self):
    assert set(CancellationReason) == {
      CancellationReason.USER_REQUESTED,
      CancellationReason.TIMEOUT,
      CancellationReason.RESOURCE_LIMIT,
      CancellationReason.ERROR_THRESHOLD,
    }

  def test_values(self):
    assert CancellationReason.USER_REQUESTED == "user_requested"
    assert CancellationReason.TIMEOUT == "timeout"


class TestCancellationSource:
  def test_members(self):
    assert set(CancellationSource) == {
      CancellationSource.CLIENT,
      CancellationSource.SERVER,
    }


class TestCancellationToken:
  def test_not_cancelled(self):
    token = CancellationToken(is_cancellation_requested=False)
    assert token.is_cancellation_requested is False
    assert token.reason is None
    assert token.source is None
    assert token.timestamp is None

  def test_cancelled_with_all_fields(self):
    token = CancellationToken(
      is_cancellation_requested=True,
      reason=CancellationReason.USER_REQUESTED,
      source=CancellationSource.CLIENT,
      timestamp="2025-01-15T10:30:00Z",
    )
    assert token.is_cancellation_requested is True
    assert token.reason == CancellationReason.USER_REQUESTED

  def test_cancelled_missing_reason(self):
    with pytest.raises(ValidationError):
      CancellationToken(
        is_cancellation_requested=True,
        source=CancellationSource.CLIENT,
        timestamp="2025-01-15T10:30:00Z",
      )

  def test_cancelled_missing_source(self):
    with pytest.raises(ValidationError):
      CancellationToken(
        is_cancellation_requested=True,
        reason=CancellationReason.TIMEOUT,
        timestamp="2025-01-15T10:30:00Z",
      )

  def test_cancelled_missing_timestamp(self):
    with pytest.raises(ValidationError):
      CancellationToken(
        is_cancellation_requested=True,
        reason=CancellationReason.TIMEOUT,
        source=CancellationSource.SERVER,
      )

  def test_alias_input(self):
    token = CancellationToken.model_validate({"isCancellationRequested": False})
    assert token.is_cancellation_requested is False

  def test_alias_output(self):
    token = CancellationToken(is_cancellation_requested=False)
    data = token.model_dump(by_alias=True)
    assert "isCancellationRequested" in data

  def test_roundtrip(self):
    token = CancellationToken(
      is_cancellation_requested=True,
      reason=CancellationReason.RESOURCE_LIMIT,
      source=CancellationSource.SERVER,
      timestamp="2025-01-15T10:30:00.000Z",
    )
    data = token.model_dump(by_alias=True)
    token2 = CancellationToken.model_validate(data)
    assert token == token2
