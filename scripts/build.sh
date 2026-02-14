#!/bin/bash

set -e

echo "🔍 Running linting and formatting checks..."
ruff check .
ruff format --check .

echo "🔎 Running type checking..."
mypy src/mcp_utils

echo "🧪 Running tests..."
pytest

echo "✅ All checks passed!"
