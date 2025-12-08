#!/bin/bash

##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Test runner script
##

set -e

echo "🚀 Running tests..."

# Run tests with coverage
python -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

echo "✅ All tests passed!"