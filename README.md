# mcp_utils

A Python (Pydantic v2) implementation of the [mcp-utils-schema](https://github.com/thomasbellio/mcp-utils-schema) CUE schemas. This foundational library provides type-safe data models for error handling, progress tracking, cancellation, and operation lifecycle management that downstream MCP server implementations depend on.

[![Tests](https://github.com/thomasbellio/python-mcp-utils/actions/workflows/push.yml/badge.svg?branch=master)](https://github.com/thomasbellio/python-mcp-utils/actions/workflows/push.yml)

## Features

- **Error taxonomy** -- Structured error responses with code ranges (connection, auth, query, data, system, operation)
- **Progress tracking** -- Metrics with percentage consistency validation and verbosity levels
- **Cancellation tokens** -- Cooperative cancellation with reason/source tracking
- **Operation state** -- Full lifecycle management (created, running, paused, completed, failed, cancelled) with validated transitions
- **MCP notifications** -- Transport-agnostic notification models with optional JSON-RPC wrappers
- **Immutable models** -- All types are frozen Pydantic models, serializing to camelCase for wire compatibility

## Installation

```bash
pip install mcp_utils
```

Requires Python 3.14+.

## Quick Start

```python
from mcp_utils import create_operation, transition_operation, LifecycleStatus

# Create and transition an operation
op = create_operation("my_tool")
op = transition_operation(op, LifecycleStatus.RUNNING)
op = transition_operation(op, LifecycleStatus.COMPLETED)
```

For detailed usage, see [USAGE.md](USAGE.md).

## Development

This project uses [uv](https://github.com/astral-sh/uv) for environment management and [Poetry](https://python-poetry.org/) for dependency management.

### Setup

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a virtual environment and install dependencies:
```bash
uv venv
uv sync
```

### Development Tools

This project uses the following development tools:

- **ruff**: Linting and formatting
- **mypy**: Type checking (with pydantic plugin)
- **pytest**: Testing
- **lefthook**: Git hooks for pre-commit checks

Install lefthook:
```bash
# On macOS
brew install lefthook

# On Linux
curl -1sLf 'https://dl.cloudsmith.io/public/evilmartians/lefthook/setup.rpm.sh' | sudo -E bash
sudo yum install lefthook

# Or using go
go install github.com/evilmartians/lefthook@latest
```

Initialize git hooks:
```bash
lefthook install
```

### Running Tests

```bash
pytest
```

### Running Linting and Type Checks

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check
mypy src/mcp_utils
```

Or run all checks at once:
```bash
./scripts/build.sh
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
