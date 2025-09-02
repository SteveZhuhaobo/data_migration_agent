# Development Guide

This guide provides comprehensive instructions for setting up a development environment, running tests, and contributing to the databricks-mcp-server project.

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd databricks-mcp-server

# Set up development environment
make dev-install

# Run tests
make test

# Build package
make build
```

## Development Environment Setup

### Prerequisites

- **Python 3.8 or higher** (3.10+ recommended)
- **Git** for version control
- **uv/uvx** for dependency management and testing

### Installing Prerequisites

#### Python
Ensure you have Python 3.8+ installed:
```bash
python --version  # Should be 3.8+
```

#### uv/uvx
Install uv for fast dependency management:
```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
uvx --version
```

### Setting Up Development Environment

#### Option 1: Using Make (Recommended)
```bash
# Clone repository
git clone <repository-url>
cd databricks-mcp-server

# Install development dependencies
make dev-install

# Verify setup
databricks-mcp-server --help
```

#### Option 2: Manual Setup
```bash
# Clone repository
git clone <repository-url>
cd databricks-mcp-server

# Create virtual environment
uv venv

# Activate virtual environment
# On Unix/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install package in development mode with dev dependencies
uv pip install -e ".[dev]"

# Verify installation
databricks-mcp-server --help
```

### Development Dependencies

The `[dev]` extra includes:
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Code Quality**: black, isort, flake8, mypy
- **Build Tools**: build, twine
- **Documentation**: Additional tools for docs generation

## Local Testing Workflow

### Running Tests

#### Quick Test Commands
```bash
# Run unit tests (fast)
make test
# or
make test-unit

# Run all tests including integration tests
make test-all

# Run integration tests only
make test-integration

# Run tests with coverage report
uv run pytest tests/ --cov-report=html
```

#### Detailed Test Options
```bash
# Run specific test file
uv run pytest tests/test_config.py -v

# Run specific test method
uv run pytest tests/test_config.py::TestConfigManager::test_load_config -v

# Run tests matching pattern
uv run pytest -k "config" -v

# Run tests with markers
uv run pytest -m "unit" -v          # Unit tests only
uv run pytest -m "integration" -v   # Integration tests only
uv run pytest -m "not slow" -v      # Exclude slow tests
```

#### Test Categories

- **Unit Tests** (`-m unit`): Fast, isolated tests
- **Integration Tests** (`-m integration`): End-to-end functionality
- **Slow Tests** (`-m slow`): Package building, installation tests
- **UVX Tests** (`-m requires_uvx`): Tests requiring uvx installation

### Code Quality Checks

#### Formatting
```bash
# Format code automatically
make format
# or
uv run black src tests scripts
uv run isort src tests scripts

# Check formatting without changes
make check-format
# or
uv run black --check src tests scripts
uv run isort --check-only src tests scripts
```

#### Linting
```bash
# Run all linting checks
make lint

# Individual linting tools
uv run flake8 src tests scripts    # Style and error checking
uv run mypy src                    # Type checking
```

### Package Testing

#### Build and Test Package
```bash
# Build package
make build

# Test pip installation
make test-install

# Test uvx installation (requires uvx)
make test-uvx

# Comprehensive validation
make validate-dist

# Complete release workflow
make release
```

#### Manual Package Testing
```bash
# Build package manually
python -m build

# Test wheel installation in clean environment
uv venv test-env
source test-env/bin/activate  # or test-env\Scripts\activate on Windows
pip install dist/*.whl
databricks-mcp-server --help
deactivate

# Test uvx installation
uvx --from dist/*.whl databricks-mcp-server --help
```

### Development Workflow

#### Daily Development Cycle
```bash
# 1. Start development session
make dev-install

# 2. Make your changes...

# 3. Run tests frequently
make test

# 4. Format and lint before committing
make format lint

# 5. Run comprehensive tests
make test-all

# 6. Build and test package
make build test-install
```

#### Pre-Commit Checklist
- [ ] All tests pass (`make test-all`)
- [ ] Code is formatted (`make format`)
- [ ] Linting passes (`make lint`)
- [ ] Package builds successfully (`make build`)
- [ ] Installation tests pass (`make test-install`)
- [ ] Documentation is updated
- [ ] Commit message follows conventions

## Automated Testing Pipeline

### GitHub Actions Workflows

The project includes comprehensive CI/CD workflows:

#### Build Workflow (`.github/workflows/build.yml`)
**Triggers**: Push to main/develop, PRs to main

**Test Matrix**:
- **OS**: Ubuntu, Windows, macOS
- **Python**: 3.10, 3.11, 3.12

**Steps**:
1. **Linting**: Code quality checks across all platforms
2. **Unit Tests**: Fast test suite with coverage reporting
3. **Package Build**: Build and validate distribution packages
4. **Installation Tests**: Test pip and uvx installation
5. **Artifact Upload**: Store build artifacts for download

#### Release Workflow (`.github/workflows/release.yml`)
**Triggers**: Git tags matching `v*` pattern

**Steps**:
1. **Build**: Create distribution packages
2. **Validation**: Comprehensive package validation
3. **TestPyPI**: Publish to test repository
4. **Testing**: Validate TestPyPI installation
5. **PyPI**: Publish to production repository
6. **GitHub Release**: Create release with artifacts

#### Distribution Validation (`.github/workflows/validate-distribution.yml`)
**Triggers**: Weekly schedule, manual dispatch

**Features**:
- Security auditing with `pip-audit`
- Metadata validation
- Cross-platform compatibility testing
- Dependency vulnerability scanning

### Local CI Simulation

```bash
# Simulate complete CI pipeline
make ci

# This runs:
# - clean: Clean build artifacts
# - lint: Code quality checks
# - test-all: All tests including integration
# - build: Package building
# - test-install: Installation validation
# - test-uvx: UVX installation testing
# - validate-dist: Distribution validation
```

### Running Specific Workflow Steps

```bash
# Test matrix simulation (run tests on multiple Python versions)
# Requires multiple Python versions installed
python3.10 -m pytest tests/ -m unit
python3.11 -m pytest tests/ -m unit
python3.12 -m pytest tests/ -m unit

# Cross-platform testing
python test_cross_platform.py --verbose

# Integration test suite
python run_integration_tests.py --include-slow --include-uvx
```

## Configuration for Development

### Test Configuration

Create a test configuration file for development:

```bash
# Copy example config
cp config/config.yaml.example config/config.yaml

# Edit with your test credentials (optional)
# Note: Tests should work without real credentials
```

### Environment Variables for Testing

```bash
# Optional: Set test credentials for integration tests
export DATABRICKS_SERVER_HOSTNAME="test.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/test-warehouse"
export DATABRICKS_ACCESS_TOKEN="test-token"

# Development settings
export DATABRICKS_MCP_LOG_LEVEL="DEBUG"
```

### IDE Configuration

#### VS Code Settings
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
    }
}
```

#### PyCharm Configuration
1. Set interpreter to `.venv/bin/python`
2. Configure pytest as test runner
3. Enable black formatter
4. Configure isort for import sorting

## Contributing Process

### Getting Started
1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create** a feature branch from `develop`
4. **Set up** development environment
5. **Make** your changes with tests
6. **Test** thoroughly
7. **Submit** a pull request

### Branch Strategy
- `main`: Stable releases
- `develop`: Development integration
- `feature/*`: Feature development
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical fixes

### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(config): add support for multiple config file locations
fix(server): handle connection timeout gracefully
docs(readme): update installation instructions
test(integration): add uvx installation tests
```

### Pull Request Process
1. **Update** documentation if needed
2. **Add** tests for new functionality
3. **Ensure** all tests pass
4. **Update** CHANGELOG.md
5. **Request** review from maintainers

### Code Review Guidelines
- **Functionality**: Does it work as intended?
- **Tests**: Are there adequate tests?
- **Documentation**: Is it properly documented?
- **Style**: Does it follow project conventions?
- **Performance**: Are there any performance implications?

## Troubleshooting Development Issues

### Common Setup Issues

#### Virtual Environment Problems
```bash
# Clean and recreate virtual environment
rm -rf .venv
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"
```

#### Dependency Conflicts
```bash
# Check for dependency issues
uv pip check

# Reinstall dependencies
uv pip install --force-reinstall -e ".[dev]"
```

#### Import Errors
```bash
# Ensure package is installed in development mode
uv pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

### Test Issues

#### Tests Not Found
```bash
# Ensure pytest can find tests
python -m pytest --collect-only

# Check test discovery
python -m pytest tests/ --collect-only -q
```

#### Slow Tests
```bash
# Skip slow tests during development
pytest -m "not slow"

# Run only fast unit tests
pytest -m unit
```

#### Coverage Issues
```bash
# Generate detailed coverage report
pytest --cov=databricks_mcp_server --cov-report=html
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
# Test in completely clean environment
python -m venv clean-test
source clean-test/bin/activate
pip install dist/*.whl
databricks-mcp-server --help
```

### Platform-Specific Issues

#### Windows
- Use `Scripts\activate` instead of `bin/activate`
- Path separators are handled automatically
- Some tests may require elevated permissions

#### macOS
- Ensure Xcode command line tools are installed
- May need to install certificates for HTTPS

#### Linux
- Ensure development headers are installed
- Check file permissions for executable creation

## Advanced Development Topics

### Adding New Features

#### 1. Configuration Options
```python
# Add to src/databricks_mcp_server/config.py
@dataclass
class ServerConfig:
    # ... existing fields ...
    new_option: str = "default_value"

# Add environment variable mapping
ENV_VAR_MAPPING = {
    # ... existing mappings ...
    "DATABRICKS_NEW_OPTION": "new_option",
}
```

#### 2. MCP Tools
```python
# Add to src/databricks_mcp_server/server.py
@server.tool()
async def new_tool(arg1: str, arg2: int = 10) -> str:
    """New MCP tool description."""
    # Implementation
    return result
```

#### 3. Error Handling
```python
# Add to src/databricks_mcp_server/errors.py
class NewError(DatabricksMCPError):
    """Specific error for new functionality."""
    pass
```

### Testing New Features

#### 1. Unit Tests
```python
# tests/test_new_feature.py
import pytest
from databricks_mcp_server.new_module import NewClass

@pytest.mark.unit
class TestNewFeature:
    def test_new_functionality(self):
        # Test implementation
        pass
```

#### 2. Integration Tests
```python
# tests/test_integration.py
@pytest.mark.integration
def test_new_feature_integration():
    # End-to-end test
    pass
```

### Performance Optimization

#### Profiling
```bash
# Profile test execution
python -m cProfile -o profile.stats -m pytest tests/test_server.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

#### Memory Usage
```bash
# Monitor memory usage during tests
python -m memory_profiler tests/test_server.py
```

### Documentation

#### API Documentation
```python
# Use comprehensive docstrings
def new_function(param: str) -> str:
    """Brief description.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When parameter is invalid
        
    Example:
        >>> new_function("test")
        "result"
    """
```

#### README Updates
- Update feature lists
- Add new configuration options
- Include usage examples
- Update troubleshooting section

## Additional Development Resources

### Comprehensive Documentation

- **[DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md)** - Detailed setup instructions
- **[DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)** - Workflow-focused guide
- **[DEVELOPMENT_INTEGRATION.md](DEVELOPMENT_INTEGRATION.md)** - Component integration
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[INTEGRATION_TESTING.md](INTEGRATION_TESTING.md)** - Testing documentation
- **[BUILD_AND_DISTRIBUTION.md](BUILD_AND_DISTRIBUTION.md)** - Build process
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

### Development Scripts

- **`scripts/setup_dev.py`** - Automated development environment setup
- **`scripts/dev_test.py`** - Development testing workflows
- **`scripts/local_test_workflow.py`** - Local testing automation
- **`scripts/build.py`** - Build and distribution automation
- **`scripts/validate_distribution.py`** - Package validation

### Quick Reference

```bash
# Setup and workflows
python scripts/setup_dev.py                    # Setup environment
make dev-quick                                 # Quick development workflow
make dev-full                                  # Full development workflow
python scripts/local_test_workflow.py --help  # Local testing options

# Testing
pytest -m unit                                 # Unit tests
pytest -m integration                          # Integration tests
pytest --cov=databricks_mcp_server            # With coverage

# Quality
make format                                    # Format code
make lint                                      # Run linting
make ci                                        # Complete CI simulation
```

## Getting Help

### Resources
- **Documentation**: Comprehensive guides in project root
- **Examples**: config/config.yaml.example, tests/ directory
- **Scripts**: Automated tools in scripts/ directory
- **CI Workflows**: .github/workflows/ for automation examples

### Community
- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Pull Requests**: Contribute improvements and fixes

### Debugging
1. **Enable debug logging**: `databricks-mcp-server --log-level DEBUG`
2. **Use development scripts**: `python scripts/local_test_workflow.py --verbose`
3. **Interactive debugging**: `pytest --pdb tests/test_module.py`
4. **Check CI logs**: Review GitHub Actions workflow logs
5. **Local CI simulation**: `python scripts/local_test_workflow.py --workflow ci`

## Development Best Practices

### Code Quality
- **Follow PEP 8**: Use black and isort for formatting
- **Type Hints**: Add type annotations for better IDE support
- **Docstrings**: Document all public functions and classes
- **Error Handling**: Provide clear, actionable error messages

### Testing
- **Test Coverage**: Aim for >90% test coverage
- **Test Types**: Unit tests for logic, integration tests for workflows
- **Test Data**: Use fixtures and mocks for consistent test data
- **Test Isolation**: Each test should be independent

### Performance
- **Lazy Loading**: Import heavy dependencies only when needed
- **Connection Pooling**: Reuse database connections
- **Caching**: Cache configuration and metadata when appropriate
- **Resource Cleanup**: Always clean up resources in tests

### Security
- **Credential Handling**: Never log or expose credentials
- **Input Validation**: Validate all user inputs
- **Dependency Updates**: Keep dependencies updated for security
- **Secrets Management**: Use environment variables for sensitive data

This development guide provides everything needed to contribute effectively to the databricks-mcp-server project. Follow these practices to maintain code quality and ensure smooth collaboration.