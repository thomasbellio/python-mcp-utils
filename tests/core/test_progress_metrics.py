"""Tests for core progress types."""

import pytest
from pydantic import ValidationError

from mcp_utils.core.progress_metrics import ProgressMetrics, ProgressNotification

# CUE test fixture
VALID_PROGRESS_NOTIFICATION = {
  "operationId": "op-123e4567-e89b-12d3-a456-426614174000",
  "progressToken": "pt-123e4567-e89b-12d3-a456-426614174001",
  "stage": "discovering_entities",
  "progress": {
    "current": 50,
    "total": 100,
    "unit": "entities",
    "percentage": 50.0,
  },
  "message": "Discovered 50 out of 100 entities",
  "timestamp": "2025-01-15T10:30:00.000Z",
}


class TestProgressMetrics:
  def test_valid(self):
    pm = ProgressMetrics(current=50, total=100, percentage=50.0)
    assert pm.current == 50
    assert pm.unit == "items"

  def test_current_non_negative(self):
    with pytest.raises(ValidationError):
      ProgressMetrics(current=-1, percentage=0.0)

  def test_percentage_bounds(self):
    ProgressMetrics(current=0, percentage=0.0)
    ProgressMetrics(current=100, percentage=100.0)

    with pytest.raises(ValidationError):
      ProgressMetrics(current=0, percentage=-0.1)
    with pytest.raises(ValidationError):
      ProgressMetrics(current=0, percentage=100.1)

  def test_percentage_consistency(self):
    # Valid: matches current/total
    ProgressMetrics(current=25, total=100, percentage=25.0)

    # Invalid: doesn't match
    with pytest.raises(ValidationError):
      ProgressMetrics(current=25, total=100, percentage=50.0)

  def test_no_total_skips_consistency(self):
    # When total is None, percentage can be anything valid
    ProgressMetrics(current=50, percentage=75.0)

  def test_unit_default(self):
    pm = ProgressMetrics(current=0, percentage=0.0)
    assert pm.unit == "items"


class TestProgressNotification:
  def test_fixture_roundtrip(self):
    pn = ProgressNotification.model_validate(VALID_PROGRESS_NOTIFICATION)
    assert pn.stage == "discovering_entities"
    assert pn.progress.current == 50
    assert pn.message == "Discovered 50 out of 100 entities"
    data = pn.model_dump(by_alias=True)
    pn2 = ProgressNotification.model_validate(data)
    assert pn == pn2

  def test_aliases(self):
    pn = ProgressNotification.model_validate(VALID_PROGRESS_NOTIFICATION)
    data = pn.model_dump(by_alias=True)
    assert "operationId" in data
    assert "progressToken" in data

  def test_snake_case_input(self):
    pn = ProgressNotification(
      operation_id="op-123e4567-e89b-12d3-a456-426614174000",
      progress_token="pt-123e4567-e89b-12d3-a456-426614174001",
      stage="test",
      progress=ProgressMetrics(current=0, percentage=0.0),
      timestamp="2025-01-15T10:30:00Z",
    )
    assert pn.operation_id == "op-123e4567-e89b-12d3-a456-426614174000"

  def test_optional_fields(self):
    pn = ProgressNotification(
      operation_id="op-123e4567-e89b-12d3-a456-426614174000",
      progress_token="pt-123e4567-e89b-12d3-a456-426614174001",
      stage="test",
      progress=ProgressMetrics(current=0, percentage=0.0),
      timestamp="2025-01-15T10:30:00Z",
    )
    assert pn.message is None
    assert pn.metadata is None
