# Integration Testing Guide

This document describes the comprehensive integration testing suite for the databricks-mcp-server package.

## Overview

The integration tests validate end-to-end functionality including:

- **Package Installation**: Testing pip and uvx installation workflows
- **Entry Point Execution**: Validating command-line interface and server startup
- **Configuration Integration**: Testing config files and environment variables
- **Cross-Platform Compatibility**: Ensuring the package works across different platforms

## Test Structure

### Test Files

- `tests/test_integration.py` - Core integration tests
- `tests/test_package_validation.py` - Package validation and metadata tests
- `tests/test_cross_platform.py` - Cross-platform compatibility tests
- `tests/conftest.py` - Test fixtures and configuration
- `run_integration_tests.py` - Test runner script
- `test_cross_platform.py` - Standalone cross-platform test runner

### Test Categories

#### 1. Package Installation Tests (`TestPackageInstallation`)

- **pip installation from source**: Validates editable installation
- **uvx installation workflow**: Tests uvx execution (requires uvx)
- **wheel build and install**: Tests package building and wheel installation

#### 2. Entry Point Execution Tests (`TestEntryPointExecution`)

- **Help command**: Validates `--help` functionality
- **Version command**: Tests `--version` output
- **Invalid config handling**: Tests graceful error handling

#### 3. Configuration Integration Tests (`TestConfigurationIntegration`)

- **Config file loading**: Tests YAML configuration file processing
- **Environment variable integration**: Validates env var configuration
- **Configuration precedence**: Tests that env vars override config files
- **Missing config handling**: Tests error messages for missing configuration

#### 4. Cross-Platform Compatibility Tests (`TestCrossCompatibility`)

- **Python version compatibility**: Tests with current Python version
- **Dependency resolution**: Validates all dependencies are installed
- **Isolated environment**: Simulates uvx isolation

#### 5. Comprehensive Cross-Platform Tests (`TestCrossPlatformCompatibility`)

- **Platform detection**: Validates platform identification and handling
- **Path separator handling**: Tests Windows vs Unix path separators
- **Executable creation**: Tests platform-specific executable generation
- **Environment variables**: Tests env var handling across platforms
- **File permissions**: Tests permission handling (Unix vs Windows)
- **Unicode paths**: Tests Unicode character support in file paths
- **Python version compatibility**: Tests across supported Python versions
- **UVX isolation**: Tests actual uvx isolation functionality

#### 5. Package Validation Tests (`TestPackageValidation`)

- **Metadata validation**: Validates pyproject.toml structure
- **Source structure**: Checks required files and structure
- **Documentation completeness**: Validates README and examples
- **CLI interface**: Tests command-line functionality

## Running Integration Tests

### Quick Start

```bash
# Run all integration tests (excluding slow and uvx tests)
python run_integration_tests.py

# Run with all tests including slow ones
python run_integration_tests.py --include-slow

# Run with uvx tests (requires uvx installation)
python run_integration_tests.py --include-uvx

# Run specific test category
python run_integration_tests.py --filter "TestPackageInstallation"

# Run comprehensive cross-platform tests
python test_cross_platform.py

# Run cross-platform tests with specific options
python test_cross_platform.py --skip-uvx --verbose
```

### Manual Test Execution

```bash
# Run integration tests directly with pytest
python -m pytest tests/test_integration.py -v -m integration

# Run package validation tests
python -m pytest tests/test_package_validation.py -v -m integration

# Run specific test
python -m pytest tests/test_integration.py::TestConfigurationIntegration::test_config_file_loading -v
```

### Test Runner Options

```bash
python run_integration_tests.py --help
```

Available options:
- `--skip-unit`: Skip unit tests
- `--skip-integration`: Skip integration tests  
- `--skip-build`: Skip package build test
- `--skip-install`: Skip installation test
- `--include-slow`: Include slow-running tests
- `--include-uvx`: Include uvx-specific tests
- `--filter PATTERN`: Filter tests by name pattern
- `--verbose`: Verbose output

## Test Requirements

### Prerequisites

- Python 3.8+
- pip
- pytest (automatically installed if missing)
- Virtual environment support

### Optional Requirements

- **uvx**: Required for uvx-specific tests
- **build module**: For package building tests
- **tomli/tomllib**: For advanced pyproject.toml validation

### Installing Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Install uvx (optional, for uvx tests)
pip install uv
# or follow installation guide: https://docs.astral.sh/uv/getting-started/installation/

# Install build tools (optional, for build tests)
pip install build
```

## Test Markers

The tests use pytest markers for categorization:

- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Slow-running tests (package building, installation)
- `@pytest.mark.requires_uvx`: Tests requiring uvx installation

### Running Tests by Marker

```bash
# Run only integration tests
python -m pytest -m integration

# Run integration tests excluding slow ones
python -m pytest -m "integration and not slow"

# Run only uvx tests
python -m pytest -m requires_uvx
```

## Test Environment

### Isolated Testing

Tests create isolated virtual environments to ensure:
- No interference with system packages
- Clean dependency resolution
- Accurate simulation of user installation experience

### Configuration Testing

Tests use temporary directories and mock configurations:
- No modification of user's actual configuration
- Safe testing of error conditions
- Validation of configuration precedence rules

## Expected Test Results

### Successful Test Run

```
✅ All tests passed!

The databricks-mcp-server package is ready for:
- Installation via pip
- Execution via uvx  
- Distribution to users
```

### Common Test Failures

#### Missing Dependencies
```
ERROR: ModuleNotFoundError: No module named 'databricks_sql_connector'
```
**Solution**: Install package dependencies: `pip install -e .`

#### uvx Not Available
```
SKIPPED: uvx not available for testing
```
**Solution**: Install uvx or run with `--skip-uvx` flag

#### Virtual Environment Creation Failed
```
ERROR: Failed to create virtual environment
```
**Solution**: Ensure Python venv module is available

## Continuous Integration

### GitHub Actions Example

```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.8, 3.9, '3.10', 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run integration tests
      run: python run_integration_tests.py --include-slow
```

## Troubleshooting

### Test Timeouts

Some tests have timeouts to prevent hanging:
- Package installation: 60 seconds
- Server startup: 10 seconds  
- uvx execution: 60 seconds

Increase timeouts in test code if needed for slower systems.

### Windows-Specific Issues

- Path separators are handled automatically
- Virtual environment scripts are in `Scripts/` directory
- Some tests may require elevated permissions

### macOS/Linux-Specific Issues

- Virtual environment scripts are in `bin/` directory
- File permissions may need adjustment
- Some package managers may interfere with isolated testing

## Contributing

When adding new integration tests:

1. Use appropriate test markers (`@pytest.mark.integration`)
2. Create isolated test environments
3. Clean up temporary files and directories
4. Add timeout limits for long-running operations
5. Provide clear error messages for test failures
6. Update this documentation for new test categories

## Test Coverage

Integration tests focus on:
- ✅ Package installation workflows
- ✅ Entry point functionality  
- ✅ Configuration loading and validation
- ✅ Cross-platform compatibility
- ✅ Error handling and user experience
- ✅ uvx compatibility and isolation

Areas not covered by integration tests:
- Actual Databricks connectivity (requires credentials)
- MCP protocol communication (covered by unit tests)
- Performance benchmarking
- Security vulnerability testing