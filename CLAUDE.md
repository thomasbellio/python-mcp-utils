# mcp_utils — Python Implementation of mcp-utils-schema

## Project Overview

This is a Python (Pydantic v2) implementation of the CUE schemas defined in
`github.com/thomasbellio/mcp-utils-schema`. It is a foundational utility
library that other MCP server implementations will depend on.

## Critical References

- **CUE-to-Python Mapping Spec**: `./cue-to-python-mapping.md` — This is the
  authoritative specification for how CUE types map to Python types. Read this
  BEFORE writing any implementation code.
- **CUE Source Schemas**: https://github.com/thomasbellio/mcp-utils-schema —
  The source of truth for all type definitions. Use WebFetch to inspect
  specific files when needed. Also it may be available locally, check available directories for relevant 'mcp-utils-schema' path. 

## Architecture Role

You are acting as both the implementation agent and the architecture agent.
Before writing or modifying any code:

1. Consult `cue-to-python-mapping.md` for the correct type mapping
2. Ensure all Pydantic models use `McpUtilsBaseModel` as their base
3. Ensure snake_case fields have camelCase aliases where specified
4. Run `ruff check src/` and `mypy src/mcp_utils` after changes
5. Run `pytest tests/` to verify nothing breaks

## Package Structure
```
src/mcp_utils/
├── __init__.py           # Top-level re-exports
├── base/                 # Primitives and enums
├── core/                 # Error, progress, cancellation, operation state
├── mcp/                  # MCP notification types + optional rpc/ wrappers
└── _utils/               # Factory functions and transition helpers
```

## Code Standards

- **Formatter**: ruff format (2-space indent per pyproject.toml)
- **Linter**: ruff check
- **Type checker**: mypy (strict mode)
- **Tests**: pytest
- **All models are frozen** (immutable) — use `model_copy(update={...})`
- **All models serialize to camelCase** via aliases

## Commands

- `ruff check src/` — lint
- `ruff format --check src/` — format check
- `mypy src/mcp_utils` — type check
- `pytest tests/ -v` — run tests
- `./scripts/build.sh` — run all checks (same as CI)
