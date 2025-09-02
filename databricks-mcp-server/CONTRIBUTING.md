# Contributing to Databricks MCP Server

Thank you for your interest in contributing to the Databricks MCP Server! This guide will help you get started with contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)
- [Getting Help](#getting-help)

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Python 3.8+** (3.10+ recommended)
- **Git** for version control
- **uv/uvx** for dependency management
- **GitHub account** for submitting pull requests

### Fork and Clone

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/databricks-mcp-server.git
   cd databricks-mcp-server
   ```
3. **Add upstream** remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/databricks-mcp-server.git
   ```

## Development Setup

### Quick Setup

```bash
# Set up development environment
make dev-install

# Verify setup
databricks-mcp-server --help
```

### Manual Setup

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate     # Windows

# Install in development mode
uv pip install -e ".[dev]"
```

### Development Tools

The development environment includes:

- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Code Quality**: black, isort, flake8, mypy
- **Build Tools**: build, twine
- **Development Script**: `scripts/dev_test.py`

## Making Changes

### Branch Strategy

- `main`: Stable releases only
- `develop`: Integration branch for development
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical fixes for production

### Creating a Feature Branch

```bash
# Update your fork
git fetch upstream
git checkout develop
git merge upstream/develop

# Create feature branch
git checkout -b feature/your-feature-name
```

### Development Workflow

1. **Make your changes** with appropriate tests
2. **Run tests frequently** during development:
   ```bash
   # Quick tests
   python scripts/dev_test.py --workflow quick
   
   # Or use make
   make test
   ```
3. **Format and lint** your code:
   ```bash
   make format lint
   ```
4. **Commit your changes** with clear messages

### Commit Message Format

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(config): add support for multiple config file locations
fix(server): handle connection timeout gracefully
docs(readme): update installation instructions
test(integration): add uvx installation tests
```

## Testing

### Test Categories

- **Unit Tests**: Fast, isolated tests (`pytest -m unit`)
- **Integration Tests**: End-to-end functionality (`pytest -m integration`)
- **Slow Tests**: Package building, installation (`pytest -m slow`)
- **UVX Tests**: Require uvx installation (`pytest -m requires_uvx`)

### Running Tests

```bash
# Quick development tests
python scripts/dev_test.py --test fast

# All tests
python scripts/dev_test.py --test all

# Specific test categories
make test-unit           # Unit tests only
make test-integration    # Integration tests only
make test-all           # All tests

# Individual test files
pytest tests/test_config.py -v
```

### Writing Tests

#### Unit Tests
```python
import pytest
from databricks_mcp_server.config import ConfigManager

@pytest.mark.unit
class TestConfigManager:
    def test_load_config_from_env(self):
        # Test implementation
        pass
```

#### Integration Tests
```python
@pytest.mark.integration
def test_server_startup():
    # End-to-end test
    pass
```

#### Test Requirements

- **Coverage**: New code should have >90% test coverage
- **Isolation**: Tests should not depend on external services
- **Mocking**: Use mocks for external dependencies
- **Documentation**: Include docstrings for complex test logic

## Code Quality

### Formatting

Code is automatically formatted using:

- **black**: Code formatting
- **isort**: Import sorting

```bash
# Format code
make format

# Check formatting
make check-format
```

### Linting

Code quality is enforced using:

- **flake8**: Style and error checking
- **mypy**: Type checking

```bash
# Run all linting
make lint

# Individual tools
uv run flake8 src tests scripts
uv run mypy src
```

### Code Style Guidelines

- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Add type annotations for all public functions
- **Docstrings**: Document all public classes and functions
- **Error Handling**: Provide clear, actionable error messages

#### Example Function
```python
def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or environment variables.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Dictionary containing configuration values
        
    Raises:
        ConfigurationError: When configuration is invalid
        FileNotFoundError: When config file doesn't exist
        
    Example:
        >>> config = load_config("config.yaml")
        >>> print(config["databricks"]["server_hostname"])
    """
```

## Submitting Changes

### Pre-Submission Checklist

Before submitting a pull request:

- [ ] All tests pass (`make test-all`)
- [ ] Code is formatted (`make format`)
- [ ] Linting passes (`make lint`)
- [ ] Package builds successfully (`make build`)
- [ ] Installation tests pass (`make test-install`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (for significant changes)
- [ ] Commit messages follow conventions

### Running Pre-Submission Tests

```bash
# Complete validation
python scripts/dev_test.py --workflow ci

# Or use make
make ci
```

### Creating Pull Request

1. **Push** your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create pull request** on GitHub:
   - Target the `develop` branch
   - Provide clear title and description
   - Reference any related issues
   - Include testing instructions

3. **Pull Request Template**:
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Refactoring
   
   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests added/updated
   - [ ] Manual testing performed
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Tests pass locally
   ```

### Review Process

1. **Automated Checks**: CI will run tests and quality checks
2. **Code Review**: Maintainers will review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged

## Release Process

### Version Management

The project uses semantic versioning (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Workflow

1. **Prepare Release**:
   ```bash
   # Update version
   python scripts/bump_version.py minor
   
   # Update CHANGELOG.md
   # Create release notes
   ```

2. **Automated Release**: GitHub Actions handles:
   - Building packages
   - Running tests
   - Publishing to PyPI
   - Creating GitHub release

### Contributing to Releases

- **Bug Fixes**: Target `develop` branch
- **Features**: Target `develop` branch
- **Hotfixes**: Target `main` branch (critical fixes only)

## Getting Help

### Resources

- **Documentation**: 
  - [README.md](README.md) - Usage and installation
  - [DEVELOPMENT.md](DEVELOPMENT.md) - Development setup
  - [INTEGRATION_TESTING.md](INTEGRATION_TESTING.md) - Testing guide
  - [BUILD_AND_DISTRIBUTION.md](BUILD_AND_DISTRIBUTION.md) - Build process

- **Examples**: 
  - `config/config.yaml.example` - Configuration examples
  - `tests/` - Test examples and patterns

### Community

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Pull Requests**: Contribute code improvements

### Debugging

1. **Enable debug logging**:
   ```bash
   databricks-mcp-server --log-level DEBUG
   ```

2. **Run tests with debugging**:
   ```bash
   pytest --pdb tests/test_config.py
   ```

3. **Check CI logs**: Review GitHub Actions workflow logs

4. **Use development script**:
   ```bash
   python scripts/dev_test.py --workflow full
   ```

## Development Best Practices

### Code Organization

- **Modular Design**: Keep functions and classes focused
- **Separation of Concerns**: Separate configuration, business logic, and I/O
- **Error Handling**: Use specific exception types
- **Logging**: Use appropriate log levels

### Testing Best Practices

- **Test Pyramid**: More unit tests, fewer integration tests
- **Test Isolation**: Each test should be independent
- **Mock External Dependencies**: Don't rely on external services
- **Test Edge Cases**: Include error conditions and boundary cases

### Documentation

- **Code Comments**: Explain complex logic
- **Docstrings**: Document all public APIs
- **README Updates**: Keep usage examples current
- **Changelog**: Document all user-facing changes

### Performance

- **Lazy Loading**: Import heavy dependencies only when needed
- **Connection Pooling**: Reuse database connections
- **Caching**: Cache configuration and metadata appropriately
- **Resource Cleanup**: Always clean up resources

### Security

- **Credential Handling**: Never log or expose credentials
- **Input Validation**: Validate all user inputs
- **Dependency Updates**: Keep dependencies updated
- **Secrets Management**: Use environment variables for sensitive data

## Common Development Tasks

### Adding New Configuration Options

1. **Update config dataclass**:
   ```python
   @dataclass
   class DatabricksConfig:
       # ... existing fields ...
       new_option: str = "default_value"
   ```

2. **Add environment variable mapping**:
   ```python
   ENV_VAR_MAPPING = {
       # ... existing mappings ...
       "DATABRICKS_NEW_OPTION": "new_option",
   }
   ```

3. **Update documentation**:
   - README.md configuration section
   - config.yaml.example
   - ENVIRONMENT_VARIABLES.md

4. **Add tests**:
   ```python
   def test_new_option_configuration():
       # Test implementation
   ```

### Adding New MCP Tools

1. **Implement tool function**:
   ```python
   @server.tool()
   async def new_tool(arg1: str, arg2: int = 10) -> str:
       """Tool description."""
       # Implementation
       return result
   ```

2. **Add error handling**:
   ```python
   try:
       # Tool logic
   except SpecificError as e:
       raise DatabricksMCPError(f"Tool failed: {e}")
   ```

3. **Write tests**:
   ```python
   @pytest.mark.unit
   async def test_new_tool():
       # Test implementation
   ```

4. **Update documentation**:
   - README.md tools section
   - Add usage examples

### Debugging Common Issues

#### Import Errors
```bash
# Ensure package is installed in development mode
uv pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Test Failures
```bash
# Run specific test with verbose output
pytest tests/test_config.py::TestConfigManager::test_load_config -v

# Run with debugger
pytest --pdb tests/test_config.py
```

#### Build Issues
```bash
# Clean and rebuild
make clean build

# Check package contents
python -m zipfile -l dist/*.whl
```

## Thank You

Thank you for contributing to the Databricks MCP Server! Your contributions help make this tool better for everyone in the community.

For questions or additional help, please:
1. Check existing documentation
2. Search GitHub issues
3. Create a new issue with detailed information
4. Join community discussions

Happy coding! 🚀