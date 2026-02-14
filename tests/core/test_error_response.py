"""Tests for core error types."""

import pytest
from pydantic import ValidationError

from mcp_utils.core.error_response import (
  AuthError,
  ErrorContext,
  ErrorResponse,
  McpConnectionError,
  QueryError,
)

# CUE test fixtures
VALID_CONNECTION_ERROR = {
  "code": 1001,
  "message": "Failed to connect to database",
  "context": {"operation": "connect", "retriesAttempted": 3},
  "suggestion": "Check that the database server is running and accessible",
  "timestamp": "2025-01-15T10:30:00.000Z",
}

VALID_AUTH_ERROR = {
  "code": 2001,
  "message": "Invalid credentials provided",
  "suggestion": "Verify your username and password are correct",
  "timestamp": "2025-01-15T10:30:00.000Z",
}

VALID_QUERY_ERROR = {
  "code": 3001,
  "message": "SQL syntax error in query",
  "context": {"operation": "executeQuery", "stage": "parsing"},
  "suggestion": "Check your SQL syntax",
  "timestamp": "2025-01-15T10:30:00.000Z",
}


class TestErrorCode:
  def test_valid_range(self):
    er = ErrorResponse(code=1000, message="test", timestamp="2025-01-15T10:30:00Z")
    assert er.code == 1000

  def test_max_range(self):
    er = ErrorResponse(code=6999, message="test", timestamp="2025-01-15T10:30:00Z")
    assert er.code == 6999

  @pytest.mark.parametrize("code", [999, 7000, 0, -1])
  def test_out_of_range(self, code):
    with pytest.raises(ValidationError):
      ErrorResponse(code=code, message="test", timestamp="2025-01-15T10:30:00Z")


class TestErrorContext:
  def test_all_optional(self):
    ctx = ErrorContext()
    assert ctx.operation is None
    assert ctx.stage is None
    assert ctx.retries_attempted is None

  def test_extra_fields_allowed(self):
    ctx = ErrorContext.model_validate({"custom_field": "value", "another": 42})
    assert ctx.model_extra is not None
    assert ctx.model_extra["custom_field"] == "value"

  def test_retries_alias(self):
    ctx = ErrorContext.model_validate({"retriesAttempted": 3})
    assert ctx.retries_attempted == 3

  def test_retries_non_negative(self):
    with pytest.raises(ValidationError):
      ErrorContext(retries_attempted=-1)

  def test_serialize_alias(self):
    ctx = ErrorContext(retries_attempted=5)
    data = ctx.model_dump(by_alias=True)
    assert "retriesAttempted" in data


class TestErrorResponse:
  def test_valid(self):
    er = ErrorResponse(code=1001, message="error", timestamp="2025-01-15T10:30:00Z")
    assert er.code == 1001

  def test_empty_message_rejected(self):
    with pytest.raises(ValidationError):
      ErrorResponse(code=1001, message="", timestamp="2025-01-15T10:30:00Z")

  def test_trace_non_empty_when_provided(self):
    with pytest.raises(ValidationError):
      ErrorResponse(code=1001, message="err", timestamp="2025-01-15T10:30:00Z", trace=[])

  def test_trace_allowed_when_populated(self):
    er = ErrorResponse(code=1001, message="err", timestamp="2025-01-15T10:30:00Z", trace=["frame1"])
    assert er.trace == ["frame1"]

  def test_frozen(self):
    er = ErrorResponse(code=1001, message="err", timestamp="2025-01-15T10:30:00Z")
    with pytest.raises(ValidationError):
      er.code = 2000  # type: ignore[misc]

  def test_roundtrip(self):
    er = ErrorResponse(
      code=1001,
      message="err",
      context=ErrorContext(operation="test"),
      timestamp="2025-01-15T10:30:00Z",
    )
    data = er.model_dump(by_alias=True)
    er2 = ErrorResponse.model_validate(data)
    assert er == er2


class TestMcpConnectionError:
  def test_fixture_roundtrip(self):
    err = McpConnectionError.model_validate(VALID_CONNECTION_ERROR)
    assert err.code == 1001
    assert err.context.operation == "connect"
    assert err.context.retries_attempted == 3
    data = err.model_dump(by_alias=True)
    err2 = McpConnectionError.model_validate(data)
    assert err == err2

  def test_code_range(self):
    with pytest.raises(ValidationError):
      McpConnectionError(
        code=2000,
        message="err",
        context=ErrorContext(operation="test"),
        timestamp="2025-01-15T10:30:00Z",
      )

  def test_context_operation_required(self):
    with pytest.raises(ValidationError):
      McpConnectionError(
        code=1001,
        message="err",
        context=ErrorContext(),
        timestamp="2025-01-15T10:30:00Z",
      )


class TestAuthError:
  def test_fixture_roundtrip(self):
    err = AuthError.model_validate(VALID_AUTH_ERROR)
    assert err.code == 2001
    assert err.suggestion == "Verify your username and password are correct"
    data = err.model_dump(by_alias=True)
    err2 = AuthError.model_validate(data)
    assert err == err2

  def test_code_range(self):
    with pytest.raises(ValidationError):
      AuthError(
        code=1000,
        message="err",
        suggestion="try again",
        timestamp="2025-01-15T10:30:00Z",
      )

  def test_suggestion_required(self):
    with pytest.raises(ValidationError):
      AuthError.model_validate(
        {
          "code": 2001,
          "message": "err",
          "timestamp": "2025-01-15T10:30:00Z",
        }
      )


class TestQueryError:
  def test_fixture_roundtrip(self):
    err = QueryError.model_validate(VALID_QUERY_ERROR)
    assert err.code == 3001
    assert err.context.operation == "executeQuery"
    data = err.model_dump(by_alias=True)
    err2 = QueryError.model_validate(data)
    assert err == err2

  def test_context_operation_required(self):
    with pytest.raises(ValidationError):
      QueryError(
        code=3001,
        message="err",
        context=ErrorContext(),
        timestamp="2025-01-15T10:30:00Z",
      )
