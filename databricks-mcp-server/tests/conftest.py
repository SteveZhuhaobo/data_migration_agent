"""
Pytest configuration and fixtures for databricks-mcp-server tests.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def package_root():
    """Get the package root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary directory for config files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        'databricks': {
            'server_hostname': 'test.databricks.com',
            'http_path': '/sql/1.0/warehouses/test123',
            'access_token': 'dapi1234567890abcdef',
            'catalog': 'test_catalog',
            'schema': 'test_schema',
            'timeout': 120
        },
        'server': {
            'log_level': 'INFO'
        }
    }


@pytest.fixture
def clean_databricks_env():
    """Clean Databricks environment variables for testing."""
    original_env = {}
    
    # Store and remove existing Databricks env vars
    for key in list(os.environ.keys()):
        if key.startswith('DATABRICKS'):
            original_env[key] = os.environ[key]
            del os.environ[key]
    
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        os.environ[key] = value


@pytest.fixture
def mock_databricks_env():
    """Set up mock Databricks environment variables."""
    env_vars = {
        'DATABRICKS_SERVER_HOSTNAME': 'mock.databricks.com',
        'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/mock123',
        'DATABRICKS_ACCESS_TOKEN': 'mock_token_123456',
        'DATABRICKS_CATALOG': 'mock_catalog',
        'DATABRICKS_SCHEMA': 'mock_schema'
    }
    
    original_env = {}
    
    # Store original values and set mock values
    for key, value in env_vars.items():
        if key in os.environ:
            original_env[key] = os.environ[key]
        os.environ[key] = value
    
    yield env_vars
    
    # Restore original environment
    for key in env_vars.keys():
        if key in original_env:
            os.environ[key] = original_env[key]
        else:
            del os.environ[key]


@pytest.fixture
def isolated_venv(tmp_path):
    """Create an isolated virtual environment for testing."""
    import subprocess
    import sys
    
    venv_path = tmp_path / "test_venv"
    
    # Create virtual environment
    result = subprocess.run([
        sys.executable, "-m", "venv", str(venv_path)
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        pytest.skip(f"Could not create virtual environment: {result.stderr}")
    
    # Return paths to executables
    if sys.platform == "win32":
        return {
            'path': venv_path,
            'python': venv_path / "Scripts" / "python.exe",
            'pip': venv_path / "Scripts" / "pip.exe"
        }
    else:
        return {
            'path': venv_path,
            'python': venv_path / "bin" / "python",
            'pip': venv_path / "bin" / "pip"
        }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_uvx: mark test as requiring uvx installation"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle markers."""
    # Add integration marker to integration tests
    for item in items:
        if "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark uvx tests
        if "uvx" in item.name.lower():
            item.add_marker(pytest.mark.requires_uvx)
        
        # Mark slow tests
        if any(marker in item.name.lower() for marker in ["install", "build", "package"]):
            item.add_marker(pytest.mark.slow)