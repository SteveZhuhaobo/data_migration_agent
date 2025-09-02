# Makefile for databricks-mcp-server

.PHONY: help clean lint test test-unit test-integration build install test-install test-uvx release dev-install format check-format dev-workflow dev-quick dev-full dev-ci

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Development:"
	@echo "  dev-install    - Install development dependencies"
	@echo "  dev-quick      - Quick development workflow (format, lint, fast tests)"
	@echo "  dev-full       - Full development workflow (all tests, build, install test)"
	@echo "  dev-ci         - CI simulation workflow"
	@echo "  dev-workflow   - Interactive development workflow selection"
	@echo ""
	@echo "Code Quality:"
	@echo "  format         - Format code with black and isort"
	@echo "  check-format   - Check code formatting"
	@echo "  lint           - Run linting checks"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run unit tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-all       - Run all tests"
	@echo ""
	@echo "Build & Distribution:"
	@echo "  clean          - Clean build artifacts"
	@echo "  build          - Build package"
	@echo "  install        - Install package in development mode"
	@echo "  test-install   - Test package installation"
	@echo "  test-uvx       - Test uvx installation"
	@echo "  validate-dist  - Validate distribution package"
	@echo "  release        - Build and test package for release"
	@echo ""
	@echo "Utilities:"
	@echo "  all            - Run clean, lint, test, build, test-install"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .coverage htmlcov/ coverage.xml
	@echo "Clean complete"

# Install development dependencies
dev-install:
	@echo "Installing development dependencies..."
	@uv pip install -e ".[dev]"

# Format code
format:
	@echo "Formatting code..."
	@uv run black src tests scripts
	@uv run isort src tests scripts

# Check code formatting
check-format:
	@echo "Checking code formatting..."
	@uv run black --check src tests scripts
	@uv run isort --check-only src tests scripts

# Run linting
lint: check-format
	@echo "Running linting checks..."
	@uv run flake8 src tests scripts
	@uv run mypy src

# Run unit tests
test-unit:
	@echo "Running unit tests..."
	@uv run pytest tests/ -m "unit" --cov-report=term-missing --cov-report=html

# Run integration tests
test-integration:
	@echo "Running integration tests..."
	@uv run pytest tests/ -m "integration" --cov-report=term-missing

# Run all tests
test-all:
	@echo "Running all tests..."
	@uv run pytest tests/ --cov-report=term-missing --cov-report=html

# Default test target (unit tests)
test: test-unit

# Build package
build: clean
	@echo "Building package..."
	@python -m pip install --upgrade build twine
	@python -m build
	@twine check dist/*
	@echo "Build complete"

# Install package in development mode
install:
	@echo "Installing package in development mode..."
	@uv pip install -e .

# Test package installation
test-install: build
	@echo "Testing package installation..."
	@python scripts/build.py --test-install

# Test uvx installation
test-uvx: build
	@echo "Testing uvx installation..."
	@python scripts/build.py --test-uvx

# Validate distribution
validate-dist: build
	@echo "Validating distribution..."
	@python scripts/validate_distribution.py

# Release workflow
release: clean lint test-unit build test-install test-uvx validate-dist
	@echo "Release build complete and tested!"
	@echo "Package is ready for distribution"
	@ls -la dist/

# Complete workflow
all: clean lint test build test-install
	@echo "All steps completed successfully!"

# Version management
bump-patch:
	@python scripts/bump_version.py patch

bump-minor:
	@python scripts/bump_version.py minor

bump-major:
	@python scripts/bump_version.py major

# Development workflow
dev: dev-install format lint test
	@echo "Development workflow complete!"

# Development workflows
dev-quick:
	@echo "Running quick development workflow..."
	@python scripts/dev_test.py --workflow quick

dev-full:
	@echo "Running full development workflow..."
	@python scripts/dev_test.py --workflow full

dev-ci:
	@echo "Running CI simulation workflow..."
	@python scripts/dev_test.py --workflow ci

dev-workflow:
	@echo "Available development workflows:"
	@echo "  make dev-quick     - Quick workflow (format, lint, fast tests)"
	@echo "  make dev-full      - Full workflow (all tests, build, install test)"
	@echo "  make dev-ci        - CI simulation workflow"
	@echo "  make dev-setup     - Set up development environment"
	@echo "  make dev-local     - Run local testing workflow"
	@echo ""
	@echo "Development scripts:"
	@echo "  python scripts/setup_dev.py --help"
	@echo "  python scripts/dev_test.py --help"
	@echo "  python scripts/local_test_workflow.py --help"

# Additional development targets
dev-setup:
	@echo "Setting up development environment..."
	@python scripts/setup_dev.py

dev-local:
	@echo "Running local testing workflow..."
	@python scripts/local_test_workflow.py --workflow standard

dev-local-quick:
	@echo "Running quick local testing workflow..."
	@python scripts/local_test_workflow.py --workflow quick

dev-local-full:
	@echo "Running full local testing workflow..."
	@python scripts/local_test_workflow.py --workflow full

dev-security:
	@echo "Running security checks..."
	@python scripts/local_test_workflow.py --security

dev-performance:
	@echo "Running performance tests..."
	@python scripts/local_test_workflow.py --performance

# CI simulation
ci: clean lint test-all build test-install test-uvx validate-dist
	@echo "CI simulation complete!"