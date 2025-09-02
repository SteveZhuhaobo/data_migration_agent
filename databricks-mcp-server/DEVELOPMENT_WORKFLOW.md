# Development Workflow Guide

This guide provides a comprehensive overview of the development workflow for the databricks-mcp-server project, including setup, testing, and contribution processes.

## Quick Start

```bash
# 1. Clone and setup
git clone <repository-url>
cd databricks-mcp-server
python scripts/setup_dev.py

# 2. Start developing
make dev-quick  # Quick development workflow

# 3. Before committing
make dev-full   # Full validation workflow
```

## Development Workflows

### 1. Quick Development Workflow (`make dev-quick`)

**Use case**: Daily development, quick feedback loop
**Duration**: ~2-3 minutes

```bash
make dev-quick
# or
python scripts/dev_test.py --workflow quick
```

**Steps**:
- ✅ Code formatting check
- ✅ Linting (flake8, mypy)
- ✅ Fast unit tests (excludes slow tests)
- ✅ Basic validation

**When to use**: 
- During active development
- Before small commits
- Quick validation of changes

### 2. Full Development Workflow (`make dev-full`)

**Use case**: Complete validation before major commits
**Duration**: ~5-8 minutes

```bash
make dev-full
# or
python scripts/dev_test.py --workflow full
```

**Steps**:
- ✅ Code formatting check
- ✅ Complete linting
- ✅ All unit and integration tests
- ✅ Package building
- ✅ Installation testing
- ✅ Basic distribution validation

**When to use**:
- Before pull requests
- After significant changes
- Weekly development validation

### 3. CI Simulation Workflow (`make dev-ci`)

**Use case**: Simulate complete CI pipeline locally
**Duration**: ~10-15 minutes

```bash
make dev-ci
# or
python scripts/dev_test.py --workflow ci
```

**Steps**:
- ✅ Complete code quality checks
- ✅ All tests with coverage
- ✅ Package building and validation
- ✅ Installation testing (pip + uvx)
- ✅ Distribution validation
- ✅ Cross-platform compatibility checks

**When to use**:
- Before major releases
- Debugging CI failures
- Complete validation

### 4. Release Preparation Workflow

**Use case**: Prepare for production release
**Duration**: ~15-20 minutes

```bash
python scripts/dev_test.py --workflow release
```

**Steps**:
- ✅ All CI simulation steps
- ✅ Integration test suite
- ✅ Cross-platform validation
- ✅ Security auditing
- ✅ Documentation validation

**When to use**:
- Before version releases
- Production deployment preparation

## Development Environment Setup

### Automated Setup (Recommended)

```bash
# Complete setup with all features
python scripts/setup_dev.py

# Quick setup (minimal validation)
python scripts/setup_dev.py --quick

# Force recreate environment
python scripts/setup_dev.py --force
```

### Manual Setup

```bash
# 1. Create virtual environment
uv venv

# 2. Activate environment
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows

# 3. Install development dependencies
uv pip install -e ".[dev]"

# 4. Validate setup
databricks-mcp-server --help
pytest --version
```

### Development Dependencies

The `[dev]` extra includes:

**Testing**:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities

**Code Quality**:
- `black` - Code formatting
- `isort` - Import sorting
- `flake8` - Linting
- `mypy` - Type checking

**Build Tools**:
- `build` - Package building
- `twine` - Package uploading
- `wheel` - Wheel building

**Development Tools**:
- `pre-commit` - Git hooks
- `pip-audit` - Security auditing

## Local Testing Strategies

### Test Categories

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

### Test-Driven Development Workflow

```bash
# 1. Write failing test
pytest tests/test_new_feature.py::test_new_functionality -v

# 2. Implement feature
# ... code changes ...

# 3. Run test until it passes
pytest tests/test_new_feature.py::test_new_functionality -v

# 4. Run related tests
pytest tests/test_new_feature.py -v

# 5. Run full test suite
make test
```

### Coverage-Driven Development

```bash
# Generate coverage report
pytest --cov=databricks_mcp_server --cov-report=html

# Open coverage report
# Open htmlcov/index.html in browser

# Focus on uncovered code
pytest --cov=databricks_mcp_server --cov-report=term-missing
```

### Performance Testing

```bash
# Profile test execution
python -m cProfile -o profile.stats -m pytest tests/test_server.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"

# Memory profiling
python -m memory_profiler tests/test_server.py
```

## Automated Testing Pipeline

### GitHub Actions Workflows

#### 1. Build Workflow (`.github/workflows/build.yml`)

**Triggers**: Push to main/develop, PRs to main

**Matrix Testing**:
- **OS**: Ubuntu, Windows, macOS
- **Python**: 3.10, 3.11, 3.12

**Pipeline Steps**:
1. **Linting**: Code quality across all platforms
2. **Unit Tests**: Fast test suite with coverage
3. **Package Build**: Distribution package creation
4. **Installation Tests**: pip and uvx validation
5. **Artifact Storage**: Build artifacts for download

#### 2. Release Workflow (`.github/workflows/release.yml`)

**Triggers**: Git tags (`v*`)

**Pipeline Steps**:
1. **Build**: Create distribution packages
2. **Validation**: Comprehensive package validation
3. **TestPyPI**: Publish to test repository
4. **Testing**: Validate TestPyPI installation
5. **PyPI**: Production repository publication
6. **GitHub Release**: Release creation with artifacts

#### 3. Development Workflow (`.github/workflows/development.yml`)

**Triggers**: Push to feature branches

**Pipeline Steps**:
1. **Quick Validation**: Fast checks for development
2. **Unit Tests**: Core functionality validation
3. **Integration Tests**: End-to-end validation
4. **Feedback**: Quick developer feedback

### Local CI Simulation

```bash
# Simulate complete CI pipeline
make ci

# Simulate specific workflow steps
python scripts/dev_test.py --lint
python scripts/dev_test.py --test all
python scripts/dev_test.py --build
python scripts/dev_test.py --test-install
```

### Continuous Integration Best Practices

1. **Fast Feedback**: Quick checks run first
2. **Parallel Execution**: Matrix testing across platforms
3. **Artifact Caching**: Dependencies and build caches
4. **Failure Isolation**: Independent test categories
5. **Clear Reporting**: Detailed failure information

## Code Quality Standards

### Formatting Standards

```bash
# Auto-format code
make format

# Check formatting
make check-format

# Manual formatting
uv run black src tests scripts
uv run isort src tests scripts
```

**Configuration**:
- **black**: Line length 88, Python 3.8+ target
- **isort**: Black-compatible profile
- **Automatic**: Format on save (IDE configuration)

### Linting Standards

```bash
# Run all linting
make lint

# Individual tools
uv run flake8 src tests scripts  # Style checking
uv run mypy src                  # Type checking
```

**Standards**:
- **PEP 8**: Python style guide compliance
- **Type Hints**: All public functions typed
- **Docstrings**: All public APIs documented
- **Error Handling**: Specific exception types

### Code Review Checklist

- [ ] **Functionality**: Does it work as intended?
- [ ] **Tests**: Adequate test coverage (>90%)?
- [ ] **Documentation**: Public APIs documented?
- [ ] **Style**: Follows project conventions?
- [ ] **Performance**: No performance regressions?
- [ ] **Security**: No security vulnerabilities?
- [ ] **Compatibility**: Works across supported platforms?

## Contribution Process

### Branch Strategy

```
main
├── develop (integration branch)
│   ├── feature/new-feature
│   ├── feature/another-feature
│   └── bugfix/fix-issue
└── hotfix/critical-fix (emergency fixes)
```

### Contribution Workflow

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/databricks-mcp-server.git
cd databricks-mcp-server

# 2. Set up development environment
python scripts/setup_dev.py

# 3. Create feature branch
git checkout -b feature/your-feature-name

# 4. Develop with testing
make dev-quick  # Frequent validation

# 5. Complete validation
make dev-full

# 6. Commit and push
git add .
git commit -m "feat(scope): description"
git push origin feature/your-feature-name

# 7. Create pull request
# Use GitHub interface
```

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:
```
feat(config): add support for multiple config file locations
fix(server): handle connection timeout gracefully
docs(readme): update installation instructions
test(integration): add uvx installation tests
```

### Pull Request Process

1. **Create PR**: Target `develop` branch
2. **Automated Checks**: CI pipeline validation
3. **Code Review**: Maintainer review
4. **Address Feedback**: Make requested changes
5. **Approval**: Merge after approval

## Troubleshooting Development Issues

### Common Setup Issues

#### Virtual Environment Problems
```bash
# Clean and recreate
rm -rf .venv
python scripts/setup_dev.py --force
```

#### Dependency Conflicts
```bash
# Check dependencies
uv pip check

# Reinstall dependencies
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

# Verify test markers
pytest --markers
```

#### Slow Tests
```bash
# Skip slow tests during development
pytest -m "not slow"

# Run only fast tests
pytest -m unit --maxfail=1
```

#### Coverage Issues
```bash
# Detailed coverage report
pytest --cov=databricks_mcp_server --cov-report=html --cov-report=term-missing

# Focus on specific modules
pytest --cov=databricks_mcp_server.config --cov-report=term-missing
```

### Build Issues

#### Package Build Failures
```bash
# Clean build
make clean build

# Verbose build
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
- Install Xcode command line tools
- Certificate issues with HTTPS requests
- Permission issues with system Python

#### Linux
- Install development headers (`python3-dev`)
- Check file permissions for executables
- SELinux/AppArmor considerations

## Advanced Development Topics

### Adding New Features

#### 1. Configuration Options
```python
# src/databricks_mcp_server/config.py
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
# src/databricks_mcp_server/server.py
@server.tool()
async def new_tool(arg1: str, arg2: int = 10) -> str:
    """New MCP tool description."""
    try:
        # Implementation
        return result
    except Exception as e:
        raise DatabricksMCPError(f"Tool failed: {e}")
```

#### 3. Error Handling
```python
# src/databricks_mcp_server/errors.py
class NewFeatureError(DatabricksMCPError):
    """Specific error for new functionality."""
    pass
```

### Testing New Features

#### Unit Tests
```python
# tests/test_new_feature.py
import pytest
from databricks_mcp_server.new_module import NewClass

@pytest.mark.unit
class TestNewFeature:
    def test_new_functionality(self):
        # Arrange
        instance = NewClass()
        
        # Act
        result = instance.new_method("test")
        
        # Assert
        assert result == "expected"
```

#### Integration Tests
```python
# tests/test_integration.py
@pytest.mark.integration
async def test_new_feature_integration():
    # End-to-end test with real components
    pass
```

### Performance Optimization

#### Profiling
```bash
# Profile specific functions
python -m cProfile -s cumulative -m pytest tests/test_server.py

# Memory profiling
python -m memory_profiler tests/test_server.py
```

#### Optimization Strategies
- **Lazy Loading**: Import heavy dependencies when needed
- **Connection Pooling**: Reuse database connections
- **Caching**: Cache configuration and metadata
- **Async Operations**: Use async/await for I/O

### Documentation Standards

#### API Documentation
```python
def new_function(param: str, optional: int = 10) -> str:
    """Brief description of function.
    
    Longer description with more details about the function's
    purpose and behavior.
    
    Args:
        param: Description of the parameter
        optional: Optional parameter with default value
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When parameter is invalid
        DatabricksMCPError: When operation fails
        
    Example:
        >>> result = new_function("test")
        >>> print(result)
        "processed: test"
    """
```

#### README Updates
- Update feature lists
- Add configuration examples
- Include usage examples
- Update troubleshooting section

## Development Best Practices

### Code Quality
- **Follow PEP 8**: Use automated formatting
- **Type Hints**: Add type annotations
- **Docstrings**: Document public APIs
- **Error Handling**: Provide actionable messages

### Testing
- **Test Coverage**: Aim for >90% coverage
- **Test Types**: Unit tests for logic, integration for workflows
- **Test Data**: Use fixtures and factories
- **Test Isolation**: Independent, repeatable tests

### Performance
- **Lazy Loading**: Import when needed
- **Resource Management**: Clean up resources
- **Caching**: Cache expensive operations
- **Monitoring**: Profile performance regularly

### Security
- **Credential Handling**: Never log credentials
- **Input Validation**: Validate all inputs
- **Dependencies**: Keep dependencies updated
- **Secrets**: Use environment variables

## Getting Help

### Resources
- **Documentation**: README.md, DEVELOPMENT.md, CONTRIBUTING.md
- **Examples**: config/, tests/, scripts/
- **CI Logs**: GitHub Actions workflow logs

### Community
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and ideas
- **Pull Requests**: Code contributions

### Debugging
1. **Enable debug logging**: `--log-level DEBUG`
2. **Use development script**: `python scripts/dev_test.py --help`
3. **Run with debugger**: `pytest --pdb`
4. **Check CI logs**: Review GitHub Actions output

This comprehensive development workflow ensures efficient, high-quality development while maintaining consistency across the project.