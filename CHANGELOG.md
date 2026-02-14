# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-14

### Added
- Pydantic v2 models implementing the mcp-utils-schema CUE definitions
- Base primitive types (UUID, Timestamp, OperationId, ProgressToken) with regex validation
- VerbosityMode enum for progress notification detail levels
- Error taxonomy with structured ErrorResponse and specialized error types (McpConnectionError, AuthError, QueryError) covering code ranges 1000-6999
- Progress tracking with ProgressMetrics and ProgressNotification, including percentage consistency validation
- Cooperative cancellation via CancellationToken with conditional field validation
- Operation lifecycle management with OperationState, validated state transitions, and generic result types
- MCP notification models (progress, cancellation, error, state change) with transition validation
- Optional JSON-RPC 2.0 wrappers for custom transport implementations
- Utility functions for ID generation, timestamp handling, cancellation token management, and operation state transitions
- McpUtilsBaseModel base class providing frozen models with camelCase serialization
- Pydantic mypy plugin configuration for full type-checking support
