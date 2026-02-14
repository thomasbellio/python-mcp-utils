"""Tests for utility factory functions."""

import re
from datetime import UTC

import pytest

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
from mcp_utils.base.primitives import (
  OPERATION_ID_PATTERN,
  PROGRESS_TOKEN_PATTERN,
  TIMESTAMP_PATTERN,
  UUID_PATTERN,
)
from mcp_utils.core.cancellation_token import (
  CancellationReason,
  CancellationSource,
)


class TestGenerateUUID:
  def test_format(self):
    result = generate_uuid()
    assert re.match(UUID_PATTERN, result)

  def test_uniqueness(self):
    ids = {generate_uuid() for _ in range(100)}
    assert len(ids) == 100


class TestGenerateOperationId:
  def test_format(self):
    result = generate_operation_id()
    assert re.match(OPERATION_ID_PATTERN, result)
    assert result.startswith("op-")

  def test_uniqueness(self):
    ids = {generate_operation_id() for _ in range(50)}
    assert len(ids) == 50


class TestGenerateProgressToken:
  def test_format(self):
    result = generate_progress_token()
    assert re.match(PROGRESS_TOKEN_PATTERN, result)
    assert result.startswith("pt-")


class TestGenerateTimestamp:
  def test_format(self):
    result = generate_timestamp()
    assert re.match(TIMESTAMP_PATTERN, result)
    assert result.endswith("Z")


class TestParseTimestamp:
  def test_utc(self):
    dt = parse_timestamp("2025-01-15T10:30:00Z")
    assert dt.year == 2025
    assert dt.month == 1
    assert dt.day == 15
    assert dt.hour == 10
    assert dt.minute == 30
    assert dt.tzinfo == UTC

  def test_with_millis(self):
    dt = parse_timestamp("2025-01-15T10:30:00.000Z")
    assert dt.hour == 10

  def test_with_offset(self):
    dt = parse_timestamp("2025-01-15T10:30:00+05:30")
    assert dt.tzinfo == UTC.__class__ or dt.utcoffset() is not None


class TestCreateCancellationToken:
  def test_uncancelled(self):
    token = create_cancellation_token()
    assert token.is_cancellation_requested is False
    assert token.reason is None

  def test_cancelled(self):
    token = create_cancellation_token(
      cancelled=True,
      reason=CancellationReason.TIMEOUT,
      source=CancellationSource.SERVER,
    )
    assert token.is_cancellation_requested is True
    assert token.reason == CancellationReason.TIMEOUT
    assert token.timestamp is not None

  def test_cancelled_missing_reason(self):
    with pytest.raises(ValueError):
      create_cancellation_token(cancelled=True, source=CancellationSource.CLIENT)

  def test_cancelled_missing_source(self):
    with pytest.raises(ValueError):
      create_cancellation_token(cancelled=True, reason=CancellationReason.TIMEOUT)


class TestCreateActiveCancellationToken:
  def test_creates_uncancelled(self):
    token = create_active_cancellation_token()
    assert token.is_cancellation_requested is False


class TestRequestCancellation:
  def test_returns_new_token(self):
    original = create_active_cancellation_token()
    cancelled = request_cancellation(
      original,
      CancellationReason.USER_REQUESTED,
      CancellationSource.CLIENT,
    )
    assert original.is_cancellation_requested is False
    assert cancelled.is_cancellation_requested is True
    assert cancelled.reason == CancellationReason.USER_REQUESTED
    assert cancelled.source == CancellationSource.CLIENT
    assert cancelled.timestamp is not None
