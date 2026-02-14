#!/bin/bash

set -e

echo "🔍 Running linting and formatting checks..."
ruff check .
ruff format --check .

echo "🔎 Running type checking..."
mypy src/mcp_utils

echo "🧪 Running tests..."
if [[ "$1" == "--with-coverage" ]]; then
  pytest --cov=src/mcp_utils --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=100
else
  pytest
fi

echo "✅ All checks passed!"
