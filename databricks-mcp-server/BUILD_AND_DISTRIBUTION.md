# Build and Distribution Guide

This document describes the build and distribution workflow for the databricks-mcp-server package.

## Overview

The databricks-mcp-server uses a modern Python packaging approach with:
- `pyproject.toml` for package configuration
- Hatchling as the build backend
- GitHub Actions for CI/CD
- Automated testing and validation
- Support for both PyPI and TestPyPI distribution

## Quick Start

### Prerequisites

- Python 3.8 or higher
- uv/uvx installed
- Git for version management

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd databricks-mcp-server

# Install development dependencies
make dev-install
# or
uv pip install -e ".[dev]"
```

### Build Commands

```bash
# Clean build artifacts
make clean

# Format code
make format

# Run linting
make lint

# Run tests
make test           # Unit tests only
make test-all       # All tests

# Build package
make build

# Test installation
make test-install   # Test pip installation
make test-uvx       # Test uvx installation

# Validate distribution
make validate-dist  # Comprehensive distribution validation

# Complete release workflow
make release        # Includes all above steps

# CI simulation
make ci             # Simulate CI/CD pipeline
```

## Build System

### Package Configuration

The package is configured in `pyproject.toml` with:

- **Build system**: Hatchling
- **Entry point**: `databricks-mcp-server` command
- **Dependencies**: Specified with version constraints
- **Development dependencies**: Available as optional extras

### Directory Structure

```
databricks-mcp-server/
├── pyproject.toml              # Package configuration
├── Makefile                    # Build commands
├── src/
│   └── databricks_mcp_server/  # Source code
├── tests/                      # Test suite
├── scripts/                    # Build and utility scripts
├── .github/workflows/          # CI/CD workflows
└── config/                     # Configuration examples
```

## Scripts

### Build Script (`scripts/build.py`)

Comprehensive build script with options:

```bash
python scripts/build.py --help
python scripts/build.py --all          # Run complete workflow
python scripts/build.py --clean        # Clean artifacts
python scripts/build.py --lint         # Run linting
python scripts/build.py --test unit    # Run unit tests
python scripts/build.py --build        # Build package
python scripts/build.py --test-install # Test installation
python scripts/build.py --test-uvx     # Test uvx installation
python scripts/build.py --validate     # Validate distribution
```

### Version Management (`scripts/bump_version.py`)

Automated version bumping:

```bash
python scripts/bump_version.py patch   # 1.0.0 -> 1.0.1
python scripts/bump_version.py minor   # 1.0.0 -> 1.1.0
python scripts/bump_version.py major   # 1.0.0 -> 2.0.0

# Options
python scripts/bump_version.py patch --dry-run    # Preview changes
python scripts/bump_version.py patch --no-tag     # Don't create git tag
python scripts/bump_version.py patch --message "Custom message"
```

### Distribution Validation (`scripts/validate_distribution.py`)

Comprehensive distribution validation:

```bash
python scripts/validate_distribution.py                    # Full validation
python scripts/validate_distribution.py --skip-uvx        # Skip uvx tests
python scripts/validate_distribution.py --report report.json  # Generate report

# Validation includes:
# - Package structure and metadata
# - Dependency specification
# - pip installation testing
# - uvx installation testing  
# - Cross-platform compatibility
# - Version consistency
```

## CI/CD Workflows

### Build Workflow (`.github/workflows/build.yml`)

Triggered on:
- Push to main/develop branches
- Pull requests to main

Steps:
1. **Test Matrix**: Tests across multiple OS and Python versions
2. **Linting**: Code quality checks
3. **Unit Tests**: Fast test suite with coverage
4. **Build**: Package building and validation
5. **Distribution Validation**: Comprehensive package validation
6. **Installation Tests**: Verify package installation works

### Release Workflow (`.github/workflows/release.yml`)

Triggered on:
- Git tags matching `v*` pattern

Steps:
1. **Build**: Create distribution packages
2. **Distribution Validation**: Comprehensive package validation
3. **Test Release**: Validate packages across platforms
4. **TestPyPI**: Publish to test repository
5. **Test TestPyPI**: Verify installation from TestPyPI
6. **PyPI**: Publish to production repository
7. **GitHub Release**: Create release with artifacts

## Testing Strategy

### Test Categories

- **Unit Tests**: Fast, isolated tests (`pytest -m unit`)
- **Integration Tests**: End-to-end functionality (`pytest -m integration`)
- **Build Tests**: Package building and installation validation

### Test Coverage

- Configuration management
- Server functionality
- Error handling
- Package installation
- Entry point execution
- Cross-platform compatibility

### Running Tests

```bash
# Unit tests only (fast)
make test-unit
pytest tests/ -m unit

# Integration tests (slower, may require credentials)
make test-integration
pytest tests/ -m integration

# All tests
make test-all
pytest tests/

# With coverage
pytest tests/ --cov=databricks_mcp_server --cov-report=html
```

## Distribution

### Package Types

The build process creates two distribution formats:

1. **Wheel (`.whl`)**: Binary distribution for faster installation
2. **Source Distribution (`.tar.gz`)**: Source code archive

### Installation Methods

#### Via uvx (Recommended)

```bash
# From PyPI
uvx databricks-mcp-server

# From local wheel
uvx --from dist/databricks_mcp_server-*.whl databricks-mcp-server

# From TestPyPI
uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ databricks-mcp-server
```

#### Via pip

```bash
# From PyPI
pip install databricks-mcp-server

# From local wheel
pip install dist/databricks_mcp_server-*.whl

# Development installation
pip install -e .
```

### Repository Configuration

#### TestPyPI (Staging)

- URL: https://test.pypi.org/
- Used for testing releases
- Automatic cleanup of old versions

#### PyPI (Production)

- URL: https://pypi.org/
- Production releases
- Permanent storage

## Release Process

### Automated Release

1. **Prepare Release**:
   ```bash
   # Update version
   python scripts/bump_version.py minor
   
   # This creates a git tag and pushes it
   ```

2. **GitHub Actions**: Automatically triggered by tag push
   - Builds package
   - Runs tests
   - Publishes to TestPyPI
   - Tests TestPyPI installation
   - Publishes to PyPI
   - Creates GitHub release

### Manual Release

1. **Build and Test**:
   ```bash
   make release
   ```

2. **Upload to TestPyPI**:
   ```bash
   twine upload --repository testpypi dist/*
   ```

3. **Test Installation**:
   ```bash
   uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ databricks-mcp-server
   ```

4. **Upload to PyPI**:
   ```bash
   twine upload dist/*
   ```

## Validation

### Pre-Release Checklist

- [ ] All tests pass
- [ ] Code is formatted and linted
- [ ] Version is updated
- [ ] CHANGELOG is updated
- [ ] Documentation is current
- [ ] Package builds successfully
- [ ] Distribution validation passes
- [ ] Installation tests pass
- [ ] uvx installation works
- [ ] Cross-platform compatibility verified

### Post-Release Validation

- [ ] Package available on PyPI
- [ ] uvx installation works from PyPI
- [ ] GitHub release created
- [ ] Documentation updated
- [ ] Version tags pushed

## Troubleshooting

### Common Issues

#### Build Failures

```bash
# Clean and rebuild
make clean build

# Check dependencies
uv pip check

# Verbose build
python -m build --verbose
```

#### Test Failures

```bash
# Run specific test
pytest tests/test_build_distribution.py::TestBuildDistribution::test_package_build -v

# Debug mode
pytest --pdb tests/test_build_distribution.py
```

#### Installation Issues

```bash
# Check wheel contents
unzip -l dist/*.whl

# Test in clean environment
python -m venv test_env
source test_env/bin/activate
pip install dist/*.whl
databricks-mcp-server --help
```

#### uvx Issues

```bash
# Clear uvx cache
uvx cache clear

# Verbose uvx
uvx --verbose databricks-mcp-server --help

# Check uvx environment
uvx --from dist/*.whl --python python3.11 databricks-mcp-server --help
```

### Getting Help

1. Check the build logs in GitHub Actions
2. Review test output for specific failures
3. Validate package contents with `twine check`
4. Test installation in clean environments
5. Check dependency compatibility

## Development Workflow

### Daily Development

```bash
# Start development
make dev-install

# Make changes...

# Test changes
make format lint test

# Build and test package
make build test-install
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the full test suite
5. Submit a pull request

The CI system will automatically:
- Run tests across multiple platforms
- Check code quality
- Build and validate the package
- Test installation methods

## Automated Workflows

### GitHub Actions Workflows

The project includes several automated workflows:

#### Build Workflow (`.github/workflows/build.yml`)
- **Trigger**: Push to main/develop, PRs to main
- **Matrix**: Multiple OS and Python versions
- **Steps**: Lint, test, build, validate, upload artifacts

#### Release Workflow (`.github/workflows/release.yml`)
- **Trigger**: Git tags matching `v*`
- **Steps**: Build → Test → TestPyPI → Validate → PyPI → GitHub Release
- **Environments**: Uses GitHub environments for deployment protection

#### Distribution Validation (`.github/workflows/validate-distribution.yml`)
- **Trigger**: Weekly schedule, manual dispatch
- **Purpose**: Comprehensive validation of build process
- **Features**: Security auditing, metadata validation, cross-platform testing

### Workflow Configuration

#### Required Secrets

For the release workflow to work, configure these secrets in GitHub:

- `TEST_PYPI_API_TOKEN`: Token for TestPyPI uploads
- `PYPI_API_TOKEN`: Token for PyPI uploads

#### Environment Protection

Configure GitHub environments:
- `testpypi`: For TestPyPI deployments
- `pypi`: For PyPI deployments (with required reviewers)

## Security Considerations

### Dependency Management

- Pin dependency versions in `pyproject.toml`
- Regular security updates via Dependabot
- Automated dependency scanning with `pip-audit`
- Weekly validation workflow checks for vulnerabilities

### Distribution Security

- Use trusted publishing for PyPI (recommended)
- Verify package signatures with `twine check`
- Monitor for supply chain attacks
- Skip existing uploads to prevent overwrites

### Credential Management

- Never include credentials in package
- Use environment variables for configuration
- Secure CI/CD secrets management
- Rotate tokens regularly

### Build Security

- Isolated build environments
- Reproducible builds with pinned dependencies
- Artifact validation before distribution
- Cross-platform compatibility verification