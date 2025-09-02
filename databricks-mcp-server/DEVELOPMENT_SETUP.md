# Development Setup Guide

This guide provides step-by-step instructions for setting up a complete development environment for the databricks-mcp-server project.

## Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd databricks-mcp-server

# 2. Run automated setup
python scripts/setup_dev.py

# 3. Verify setup
make dev-quick
```

## Prerequisites

### Required Tools

1. **Python 3.8+** (3.10+ recommended)
   ```bash
   python --version  # Should be 3.8+
   ```

2. **Git** for version control
   ```bash
   git --version
   ```

3. **uv/uvx** for fast dependency management
   ```bash
   # Install uv
   # On macOS/Linux:
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # On Windows:
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Verify installation
   uv --version
   uvx --version
   ```

### Optional Tools

- **make** for build automation (comes with most systems)
- **Docker** for containerized testing (optional)
- **IDE/Editor** with Python support (VS Code, PyCharm, etc.)

## Setup Methods

### Method 1: Automated Setup (Recommended)

The automated setup script handles everything for you:

```bash
# Complete setup with all features
python scripts/setup_dev.py

# Quick setup (minimal validation)
python scripts/setup_dev.py --quick

# Force recreate environment
python scripts/setup_dev.py --force

# Skip optional components
python scripts/setup_dev.py --no-hooks --no-test
```

**What the script does:**
- ✅ Checks prerequisites
- ✅ Creates virtual environment
- ✅ Installs development dependencies
- ✅ Sets up pre-commit hooks
- ✅ Validates installation
- ✅ Runs initial tests

### Method 2: Manual Setup

If you prefer manual control:

```bash
# 1. Create virtual environment
uv venv

# 2. Activate virtual environment
# On Unix/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# 3. Install development dependencies
uv pip install -e ".[dev]"

# 4. Verify installation
databricks-mcp-server --help
pytest --version

# 5. Run initial tests
make test
```

### Method 3: Using Make

For a streamlined approach:

```bash
# Install development dependencies
make dev-install

# Run development workflow
make dev-quick
```

## Development Dependencies

The `[dev]` extra includes all tools needed for development:

### Testing Framework
- **pytest** - Main testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking utilities

### Code Quality Tools
- **black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting and style checking
- **mypy** - Static type checking

### Build and Distribution
- **build** - Package building
- **twine** - Package uploading to PyPI
- **wheel** - Wheel format support

### Security and Auditing
- **pip-audit** - Security vulnerability scanning
- **bandit** - Security linting

### Development Utilities
- **pre-commit** - Git hooks for quality checks
- **memory-profiler** - Memory usage profiling
- **psutil** - System and process utilities

## IDE Configuration

### VS Code Setup

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    },
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true
}
```

### PyCharm Setup

1. **Set Python Interpreter**:
   - File → Settings → Project → Python Interpreter
   - Select `.venv/bin/python` (or `.venv\Scripts\python.exe` on Windows)

2. **Configure Test Runner**:
   - File → Settings → Tools → Python Integrated Tools
   - Set "Default test runner" to "pytest"

3. **Enable Code Formatting**:
   - File → Settings → Tools → External Tools
   - Add black and isort as external tools

4. **Configure Type Checking**:
   - Install mypy plugin
   - Enable type checking in settings

## Development Workflows

### Daily Development Workflow

```bash
# 1. Start development session
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 2. Pull latest changes
git pull origin develop

# 3. Run quick checks during development
make dev-quick
# or
python scripts/local_test_workflow.py --workflow quick

# 4. Make your changes...

# 5. Run tests frequently
make test
# or
pytest tests/test_your_module.py -v

# 6. Format code before committing
make format

# 7. Run full validation before push
make dev-full
```

### Pre-Commit Workflow

```bash
# 1. Stage your changes
git add .

# 2. Run comprehensive checks
python scripts/local_test_workflow.py --workflow full

# 3. Fix any issues found

# 4. Commit with conventional message
git commit -m "feat(scope): description"

# 5. Push to your branch
git push origin feature/your-feature
```

### Testing Workflows

#### Quick Testing (2-3 minutes)
```bash
# Fast feedback loop
python scripts/local_test_workflow.py --workflow quick
```

#### Standard Testing (5-8 minutes)
```bash
# Comprehensive validation
python scripts/local_test_workflow.py --workflow standard
```

#### Full Testing (10-15 minutes)
```bash
# Complete validation including security and performance
python scripts/local_test_workflow.py --workflow full
```

#### CI Simulation (15-20 minutes)
```bash
# Simulate complete CI pipeline
python scripts/local_test_workflow.py --workflow ci
```

## Testing Strategies

### Test Categories

The project uses pytest markers to categorize tests:

```bash
# Unit tests (fast, isolated)
pytest -m unit

# Integration tests (end-to-end)
pytest -m integration

# Slow tests (package building, installation)
pytest -m slow

# Tests requiring uvx
pytest -m requires_uvx

# All tests
pytest
```

### Test-Driven Development

```bash
# 1. Write failing test
pytest tests/test_new_feature.py::test_new_functionality -v

# 2. Implement feature to make test pass
# ... code changes ...

# 3. Run test until it passes
pytest tests/test_new_feature.py::test_new_functionality -v

# 4. Refactor and ensure tests still pass
pytest tests/test_new_feature.py -v

# 5. Run full test suite
make test
```

### Coverage-Driven Development

```bash
# Generate coverage report
pytest --cov=databricks_mcp_server --cov-report=html

# Open coverage report in browser
# Open htmlcov/index.html

# Focus on uncovered code
pytest --cov=databricks_mcp_server --cov-report=term-missing
```

## Code Quality Standards

### Formatting

Code is automatically formatted using black and isort:

```bash
# Auto-format code
make format

# Check formatting without changes
make check-format
```

**Configuration**:
- Line length: 88 characters (black default)
- Import sorting: black-compatible profile
- Target: Python 3.8+

### Linting

Multiple linting tools ensure code quality:

```bash
# Run all linting checks
make lint

# Individual tools
uv run flake8 src tests scripts  # Style and error checking
uv run mypy src                  # Type checking
```

### Pre-commit Hooks

Automated quality checks run on every commit:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Build and Distribution

### Local Package Building

```bash
# Build package
make build

# Test installation
make test-install

# Test uvx installation
make test-uvx

# Complete validation
make validate-dist
```

### Release Preparation

```bash
# Run complete release workflow
python scripts/local_test_workflow.py --workflow release

# Update version
python scripts/bump_version.py minor

# Create release
git tag v1.2.0
git push origin v1.2.0
```

## Troubleshooting

### Common Setup Issues

#### Virtual Environment Problems
```bash
# Clean and recreate
rm -rf .venv
python scripts/setup_dev.py --force
```

#### Dependency Conflicts
```bash
# Check for issues
uv pip check

# Force reinstall
uv pip install --force-reinstall -e ".[dev]"
```

#### Import Errors
```bash
# Verify package installation
python -c "import databricks_mcp_server; print('OK')"

# Check Python path
python -c "import sys; print(sys.path)"
```

### Test Issues

#### Tests Not Found
```bash
# Check test discovery
pytest --collect-only tests/

# Verify markers
pytest --markers
```

#### Slow Tests
```bash
# Skip slow tests during development
pytest -m "not slow"

# Run only unit tests
pytest -m unit
```

#### Coverage Issues
```bash
# Detailed coverage
pytest --cov=databricks_mcp_server --cov-report=html --cov-report=term-missing

# Open coverage report
# Open htmlcov/index.html in browser
```

### Build Issues

#### Package Build Failures
```bash
# Clean and rebuild
make clean build

# Verbose build output
python -m build --verbose

# Check package contents
python -m zipfile -l dist/*.whl
```

#### Installation Test Failures
```bash
# Test in clean environment
python -m venv clean-test
source clean-test/bin/activate
pip install dist/*.whl
databricks-mcp-server --help
```

### Platform-Specific Issues

#### Windows
- Use `Scripts\activate` instead of `bin/activate`
- Some tests may require elevated permissions
- Path handling is automatic

#### macOS
- Install Xcode command line tools: `xcode-select --install`
- May need to install certificates for HTTPS
- Use Homebrew for additional tools

#### Linux
- Install development headers: `sudo apt-get install python3-dev`
- Check file permissions for executables
- Consider SELinux/AppArmor policies

## Advanced Development

### Adding New Features

1. **Create feature branch**:
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Write tests first** (TDD approach):
   ```python
   # tests/test_new_feature.py
   def test_new_functionality():
       # Test implementation
       pass
   ```

3. **Implement feature**:
   ```python
   # src/databricks_mcp_server/new_module.py
   def new_function():
       # Implementation
       pass
   ```

4. **Run tests and iterate**:
   ```bash
   pytest tests/test_new_feature.py -v
   ```

5. **Update documentation**:
   - Update README.md
   - Add docstrings
   - Update configuration examples

### Performance Optimization

```bash
# Profile code execution
python -m cProfile -o profile.stats -m pytest tests/test_server.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"

# Memory profiling
python -m memory_profiler tests/test_server.py

# Performance testing
python scripts/local_test_workflow.py --performance
```

### Security Best Practices

```bash
# Security scanning
python scripts/local_test_workflow.py --security

# Dependency auditing
uv run pip-audit

# Code security scanning
uv run bandit -r src/
```

## Getting Help

### Documentation
- **README.md** - Usage and installation
- **DEVELOPMENT.md** - Comprehensive development guide
- **CONTRIBUTING.md** - Contribution guidelines
- **INTEGRATION_TESTING.md** - Testing documentation
- **BUILD_AND_DISTRIBUTION.md** - Build process

### Community
- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Questions and ideas
- **Pull Requests** - Code contributions

### Debugging
1. **Enable debug logging**: `databricks-mcp-server --log-level DEBUG`
2. **Use development scripts**: `python scripts/local_test_workflow.py --help`
3. **Interactive debugging**: `pytest --pdb tests/test_module.py`
4. **Check CI logs**: Review GitHub Actions workflow logs

## Development Best Practices

### Code Quality
- Follow PEP 8 style guidelines
- Add type hints to all public functions
- Write comprehensive docstrings
- Handle errors gracefully with specific exceptions

### Testing
- Aim for >90% test coverage
- Write unit tests for business logic
- Write integration tests for workflows
- Use fixtures for test data
- Keep tests independent and repeatable

### Performance
- Profile code regularly
- Use lazy loading for heavy imports
- Implement connection pooling
- Cache expensive operations
- Clean up resources properly

### Security
- Never log or expose credentials
- Validate all user inputs
- Keep dependencies updated
- Use environment variables for secrets
- Follow security scanning recommendations

This development setup guide ensures you have everything needed to contribute effectively to the databricks-mcp-server project. Follow these practices to maintain high code quality and smooth collaboration.