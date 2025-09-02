"""
Integration tests for databricks-mcp-server package functionality.

These tests validate end-to-end package installation, uvx execution,
entry point functionality, and configuration integration.
"""

import os
import subprocess
import sys
import tempfile
import time
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import pytest
import yaml


class TestPackageInstallation:
    """Test package installation via pip and uvx."""
    
    def test_pip_install_from_source(self, tmp_path):
        """Test installing package from source using pip."""
        # Get the package root directory
        package_root = Path(__file__).parent.parent
        
        # Create a virtual environment for testing
        venv_path = tmp_path / "test_venv"
        
        # Create virtual environment
        result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"Failed to create venv: {result.stderr}"
        
        # Get the python executable in the venv
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        # Install the package in editable mode
        result = subprocess.run([
            str(pip_exe), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"Failed to install package: {result.stderr}"
        
        # Verify the package is installed
        result = subprocess.run([
            str(pip_exe), "list"
        ], capture_output=True, text=True)
        assert "databricks-mcp-server" in result.stdout
        
        # Verify the entry point is available
        result = subprocess.run([
            str(python_exe), "-c", 
            "import pkg_resources; print([ep.name for ep in pkg_resources.iter_entry_points('console_scripts') if 'databricks-mcp-server' in ep.name])"
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert "databricks-mcp-server" in result.stdout

    @pytest.mark.slow
    def test_uvx_installation_workflow(self, tmp_path):
        """Test uvx installation and execution workflow."""
        # Skip if uvx is not available
        try:
            subprocess.run(["uvx", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("uvx not available for testing")
        
        # Get the package root directory
        package_root = Path(__file__).parent.parent
        
        # Test uvx installation from local source
        # Note: In real scenarios, this would be from PyPI
        result = subprocess.run([
            "uvx", "--from", str(package_root), "databricks-mcp-server", "--help"
        ], capture_output=True, text=True, timeout=60)
        
        # Should show help output without errors
        assert result.returncode == 0, f"uvx execution failed: {result.stderr}"
        assert "Databricks MCP Server" in result.stdout or "usage:" in result.stdout.lower()

    def test_package_build_and_install(self, tmp_path):
        """Test building package and installing from wheel."""
        package_root = Path(__file__).parent.parent
        
        # Build the package
        result = subprocess.run([
            sys.executable, "-m", "build", str(package_root), "--outdir", str(tmp_path)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            # Try with pip if build module is not available
            result = subprocess.run([
                sys.executable, "setup.py", "bdist_wheel", "--dist-dir", str(tmp_path)
            ], cwd=str(package_root), capture_output=True, text=True)
        
        # Find the built wheel
        wheel_files = list(tmp_path.glob("*.whl"))
        if not wheel_files:
            pytest.skip("Could not build wheel for testing")
        
        wheel_file = wheel_files[0]
        
        # Create a virtual environment for testing
        venv_path = tmp_path / "wheel_test_venv"
        result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Get the pip executable in the venv
        if sys.platform == "win32":
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            pip_exe = venv_path / "bin" / "pip"
        
        # Install from wheel
        result = subprocess.run([
            str(pip_exe), "install", str(wheel_file)
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"Failed to install wheel: {result.stderr}"


class TestEntryPointExecution:
    """Test entry point execution and server startup."""
    
    def test_entry_point_help(self, tmp_path):
        """Test that entry point shows help correctly."""
        package_root = Path(__file__).parent.parent
        
        # Create a virtual environment
        venv_path = tmp_path / "entry_test_venv"
        result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Install package
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        result = subprocess.run([
            str(pip_exe), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Test help command
        result = subprocess.run([
            str(python_exe), "-m", "databricks_mcp_server.main", "--help"
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower() or "help" in result.stdout.lower()

    def test_entry_point_version(self, tmp_path):
        """Test that entry point shows version correctly."""
        package_root = Path(__file__).parent.parent
        
        # Create a virtual environment
        venv_path = tmp_path / "version_test_venv"
        result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Install package
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        result = subprocess.run([
            str(pip_exe), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Test version command
        result = subprocess.run([
            str(python_exe), "-m", "databricks_mcp_server.main", "--version"
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert "1.0.0" in result.stdout

    def test_server_startup_with_invalid_config(self, tmp_path):
        """Test server startup behavior with invalid configuration."""
        package_root = Path(__file__).parent.parent
        
        # Create a virtual environment
        venv_path = tmp_path / "startup_test_venv"
        result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Install package
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        result = subprocess.run([
            str(pip_exe), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Test startup with no configuration (should fail gracefully)
        result = subprocess.run([
            str(python_exe), "-m", "databricks_mcp_server.main"
        ], capture_output=True, text=True, timeout=10)
        
        # Should exit with error code but provide helpful error message
        assert result.returncode != 0
        assert "configuration" in result.stderr.lower() or "databricks" in result.stderr.lower()


class TestConfigurationIntegration:
    """Test configuration file and environment variable integration."""
    
    def test_config_file_loading(self, tmp_path):
        """Test loading configuration from file."""
        # Create a test config file
        config_data = {
            'databricks': {
                'server_hostname': 'test.databricks.com',
                'http_path': '/sql/1.0/warehouses/test',
                'access_token': 'test_token_123',
                'catalog': 'test_catalog',
                'schema': 'test_schema'
            },
            'server': {
                'log_level': 'DEBUG'
            }
        }
        
        config_file = tmp_path / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Test config loading
        package_root = Path(__file__).parent.parent
        venv_path = tmp_path / "config_test_venv"
        
        result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        result = subprocess.run([
            str(pip_exe), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Test config loading (should fail due to invalid token but show config was loaded)
        result = subprocess.run([
            str(python_exe), "-m", "databricks_mcp_server.main", 
            "--config", str(config_file)
        ], capture_output=True, text=True, timeout=10)
        
        # Should show that config was loaded (even if connection fails)
        output = result.stdout + result.stderr
        # The server will try to connect and fail, but should show it loaded the config
        assert "test.databricks.com" in output or "test_catalog" in output or "Connected to:" in output

    def test_environment_variable_integration(self, tmp_path):
        """Test configuration via environment variables."""
        package_root = Path(__file__).parent.parent
        
        # Create a virtual environment
        venv_path = tmp_path / "env_test_venv"
        result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        result = subprocess.run([
            str(pip_exe), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Set environment variables
        env = os.environ.copy()
        env.update({
            'DATABRICKS_SERVER_HOSTNAME': 'env-test.databricks.com',
            'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/env-test',
            'DATABRICKS_ACCESS_TOKEN': 'env_test_token_456',
            'DATABRICKS_CATALOG': 'env_test_catalog',
            'DATABRICKS_SCHEMA': 'env_test_schema',
            'DATABRICKS_MCP_LOG_LEVEL': 'INFO'
        })
        
        # Test with environment variables
        result = subprocess.run([
            str(python_exe), "-m", "databricks_mcp_server.main"
        ], capture_output=True, text=True, env=env, timeout=10)
        
        # Should show that env vars were loaded
        output = result.stdout + result.stderr
        assert "env-test.databricks.com" in output or "env_test_catalog" in output or "Connected to:" in output

    def test_config_precedence(self, tmp_path):
        """Test that environment variables take precedence over config files."""
        # Create a config file
        config_data = {
            'databricks': {
                'server_hostname': 'file.databricks.com',
                'http_path': '/sql/1.0/warehouses/file',
                'access_token': 'file_token',
                'catalog': 'file_catalog'
            }
        }
        
        config_file = tmp_path / "precedence_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        package_root = Path(__file__).parent.parent
        venv_path = tmp_path / "precedence_test_venv"
        
        result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        result = subprocess.run([
            str(pip_exe), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Set environment variables that should override config file
        env = os.environ.copy()
        env.update({
            'DATABRICKS_SERVER_HOSTNAME': 'env-override.databricks.com',
            'DATABRICKS_CATALOG': 'env_override_catalog'
        })
        
        # Test with both config file and env vars - use invalid tokens to force quick failure
        env.update({
            'DATABRICKS_ACCESS_TOKEN': 'invalid_token_for_testing',
            'DATABRICKS_HTTP_PATH': '/invalid/path'
        })
        
        result = subprocess.run([
            str(python_exe), "-m", "databricks_mcp_server.main", 
            "--config", str(config_file)
        ], capture_output=True, text=True, env=env, timeout=5)
        
        output = result.stdout + result.stderr
        # Should show env var values were used (even if connection fails)
        # Look for the hostname in the connection attempt or error messages
        assert "env-override.databricks.com" in output or "Connected to: env-override.databricks.com" in output
        
        # Test without env vars to confirm config file is used when no env vars present
        clean_env = {k: v for k, v in os.environ.items() 
                    if not k.startswith('DATABRICKS')}
        
        result2 = subprocess.run([
            str(python_exe), "-m", "databricks_mcp_server.main", 
            "--config", str(config_file)
        ], capture_output=True, text=True, env=clean_env, timeout=5)
        
        output2 = result2.stdout + result2.stderr
        # Should show config file values when no env vars present
        assert "file.databricks.com" in output2 or "Connected to: file.databricks.com" in output2

    def test_missing_required_config(self, tmp_path):
        """Test behavior when required configuration is missing."""
        package_root = Path(__file__).parent.parent
        
        venv_path = tmp_path / "missing_config_test_venv"
        result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        result = subprocess.run([
            str(pip_exe), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Clear environment of any Databricks variables
        env = {k: v for k, v in os.environ.items() 
               if not k.startswith('DATABRICKS')}
        
        # Test with no configuration
        result = subprocess.run([
            str(python_exe), "-m", "databricks_mcp_server.main"
        ], capture_output=True, text=True, env=env, timeout=10)
        
        # Should fail with helpful error message
        assert result.returncode != 0
        error_output = result.stderr.lower()
        assert any(word in error_output for word in [
            'configuration', 'required', 'missing', 'databricks', 'hostname', 'token'
        ])


class TestCrossCompatibility:
    """Test cross-platform and cross-Python version compatibility."""
    
    def test_python_version_compatibility(self, tmp_path):
        """Test that package works with supported Python versions."""
        package_root = Path(__file__).parent.parent
        
        # Test with current Python version
        venv_path = tmp_path / "compat_test_venv"
        result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        # Install and test basic functionality
        result = subprocess.run([
            str(pip_exe), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Test basic import
        result = subprocess.run([
            str(python_exe), "-c", 
            "import databricks_mcp_server; print('Import successful')"
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert "Import successful" in result.stdout

    def test_dependency_resolution(self, tmp_path):
        """Test that all dependencies are correctly resolved."""
        package_root = Path(__file__).parent.parent
        
        venv_path = tmp_path / "deps_test_venv"
        result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        # Install package
        result = subprocess.run([
            str(pip_exe), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Check that all required dependencies are installed
        result = subprocess.run([
            str(pip_exe), "list"
        ], capture_output=True, text=True)
        
        required_packages = [
            "databricks-sql-connector",
            "requests", 
            "pyyaml",
            "mcp"
        ]
        
        for package in required_packages:
            assert package.lower() in result.stdout.lower(), f"Missing dependency: {package}"

    def test_isolated_environment(self, tmp_path):
        """Test that package works in isolated environment (simulating uvx)."""
        package_root = Path(__file__).parent.parent
        
        # Create completely isolated environment
        isolated_path = tmp_path / "isolated_env"
        result = subprocess.run([
            sys.executable, "-m", "venv", "--clear", str(isolated_path)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        if sys.platform == "win32":
            python_exe = isolated_path / "Scripts" / "python.exe"
            pip_exe = isolated_path / "Scripts" / "pip.exe"
        else:
            python_exe = isolated_path / "bin" / "python"
            pip_exe = isolated_path / "bin" / "pip"
        
        # Install only our package (no system packages)
        result = subprocess.run([
            str(pip_exe), "install", "--no-deps", str(package_root)
        ], capture_output=True, text=True)
        
        # Then install dependencies
        result = subprocess.run([
            str(pip_exe), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Test that it works in isolation
        result = subprocess.run([
            str(python_exe), "-c", 
            "from databricks_mcp_server.main import main; print('Isolated import successful')"
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert "Isolated import successful" in result.stdout


@pytest.fixture
def clean_environment():
    """Fixture to provide clean environment for testing."""
    original_env = os.environ.copy()
    
    # Remove any existing Databricks environment variables
    for key in list(os.environ.keys()):
        if key.startswith('DATABRICKS'):
            del os.environ[key]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Integration test markers
pytestmark = pytest.mark.integration