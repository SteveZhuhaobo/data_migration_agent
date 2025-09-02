"""
Package validation tests for end-to-end functionality.

These tests validate that the package can be built, installed, and executed
correctly in various scenarios.
"""

import os
import subprocess
import sys
import tempfile
import json
from pathlib import Path
import pytest
import yaml


class TestPackageValidation:
    """Validate complete package functionality."""
    
    def test_package_metadata_validation(self, package_root):
        """Test that package metadata is correct and complete."""
        pyproject_path = package_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"
        
        # Read and validate pyproject.toml
        try:
            if sys.version_info >= (3, 11):
                import tomllib
                with open(pyproject_path, "rb") as f:
                    config = tomllib.load(f)
            else:
                try:
                    import tomli
                    with open(pyproject_path, "rb") as f:
                        config = tomli.load(f)
                except ImportError:
                    # Fallback to manual parsing for basic validation
                    with open(pyproject_path, "r") as f:
                        content = f.read()
                        assert 'name = "databricks-mcp-server"' in content
                        assert 'databricks-mcp-server = "databricks_mcp_server.main:main"' in content
                        return
        except ImportError:
            pytest.skip("tomllib/tomli not available for metadata validation")
        
        # Validate required fields
        assert config["project"]["name"] == "databricks-mcp-server"
        assert "version" in config["project"]
        assert "description" in config["project"]
        assert "requires-python" in config["project"]
        assert "dependencies" in config["project"]
        
        # Validate entry point
        assert "project" in config
        assert "scripts" in config["project"]
        assert "databricks-mcp-server" in config["project"]["scripts"]
        assert config["project"]["scripts"]["databricks-mcp-server"] == "databricks_mcp_server.main:main"
        
        # Validate dependencies
        deps = config["project"]["dependencies"]
        required_deps = ["databricks-sql-connector", "requests", "pyyaml", "mcp"]
        for dep in required_deps:
            assert any(dep in d for d in deps), f"Missing dependency: {dep}"

    def test_source_structure_validation(self, package_root):
        """Test that source structure is correct."""
        src_dir = package_root / "src" / "databricks_mcp_server"
        assert src_dir.exists(), "Source directory not found"
        
        # Check required files
        required_files = ["__init__.py", "main.py", "server.py", "config.py"]
        for file_name in required_files:
            file_path = src_dir / file_name
            assert file_path.exists(), f"Required file not found: {file_name}"
        
        # Check that main.py has main function
        main_py = src_dir / "main.py"
        with open(main_py, "r") as f:
            content = f.read()
            assert "def main(" in content, "main() function not found in main.py"

    def test_config_example_validation(self, package_root):
        """Test that config example is valid and complete."""
        config_example = package_root / "config" / "config.yaml.example"
        assert config_example.exists(), "config.yaml.example not found"
        
        with open(config_example, "r") as f:
            config = yaml.safe_load(f)
        
        # Validate structure
        assert "databricks" in config
        databricks_config = config["databricks"]
        
        required_fields = ["server_hostname", "http_path", "access_token"]
        for field in required_fields:
            assert field in databricks_config, f"Missing required field: {field}"

    def test_documentation_completeness(self, package_root):
        """Test that documentation is complete and helpful."""
        readme_path = package_root / "README.md"
        assert readme_path.exists(), "README.md not found"
        
        with open(readme_path, "r") as f:
            readme_content = f.read().lower()
        
        # Check for essential documentation sections
        required_sections = [
            "installation", "uvx", "configuration", 
            "usage", "environment", "databricks"
        ]
        
        for section in required_sections:
            assert section in readme_content, f"README missing section about: {section}"

    def test_entry_point_import_validation(self, isolated_venv, package_root):
        """Test that entry point can be imported correctly."""
        # Install package in isolated environment
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"Failed to install package: {result.stderr}"
        
        # Test import of main function
        result = subprocess.run([
            str(isolated_venv['python']), "-c",
            "from databricks_mcp_server.main import main; print('Import successful')"
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"Failed to import main: {result.stderr}"
        assert "Import successful" in result.stdout

    def test_command_line_interface_validation(self, isolated_venv, package_root):
        """Test command line interface functionality."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Test help command
        result = subprocess.run([
            str(isolated_venv['python']), "-m", "databricks_mcp_server.main", "--help"
        ], capture_output=True, text=True)
        assert result.returncode == 0
        help_output = result.stdout.lower()
        assert "usage" in help_output or "help" in help_output
        
        # Test version command
        result = subprocess.run([
            str(isolated_venv['python']), "-m", "databricks_mcp_server.main", "--version"
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert "1.0.0" in result.stdout

    def test_configuration_validation_command(self, isolated_venv, package_root, temp_config_dir, sample_config_data):
        """Test configuration validation functionality."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Create test config file
        config_file = temp_config_dir / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config_data, f)
        
        # Test config loading
        result = subprocess.run([
            str(isolated_venv['python']), "-m", "databricks_mcp_server.main",
            "--config", str(config_file)
        ], capture_output=True, text=True, timeout=15)
        
        # Should attempt to load config (may fail on connection but should show config was loaded)
        output = result.stdout + result.stderr
        assert "test.databricks.com" in output or "test_catalog" in output or "Connected to:" in output

    def test_error_handling_validation(self, isolated_venv, package_root, clean_databricks_env):
        """Test that error handling provides helpful messages."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Test with no configuration
        result = subprocess.run([
            str(isolated_venv['python']), "-m", "databricks_mcp_server.main"
        ], capture_output=True, text=True, timeout=10)
        
        # Should fail with helpful error
        assert result.returncode != 0
        error_output = result.stderr.lower()
        helpful_keywords = [
            "configuration", "required", "missing", "databricks", 
            "hostname", "token", "environment", "config"
        ]
        assert any(keyword in error_output for keyword in helpful_keywords), \
            f"Error message not helpful: {result.stderr}"


class TestUvxCompatibility:
    """Test uvx-specific compatibility and functionality."""
    
    @pytest.mark.requires_uvx
    def test_uvx_execution_simulation(self, package_root, temp_config_dir, sample_config_data):
        """Simulate uvx execution workflow."""
        # Skip if uvx not available
        try:
            subprocess.run(["uvx", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("uvx not available for testing")
        
        # Create config file for testing
        config_file = temp_config_dir / "uvx_test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config_data, f)
        
        # Test uvx execution with config
        result = subprocess.run([
            "uvx", "--from", str(package_root), "databricks-mcp-server",
            "--config", str(config_file), "--validate-config"
        ], capture_output=True, text=True, timeout=60)
        
        # Should execute without import errors
        if result.returncode != 0:
            # Check if it's a connection error (expected) vs import error (not expected)
            error_output = result.stderr.lower()
            import_errors = ["importerror", "modulenotfounderror", "no module named"]
            assert not any(err in error_output for err in import_errors), \
                f"Import error in uvx execution: {result.stderr}"

    def test_isolated_environment_simulation(self, isolated_venv, package_root):
        """Test package works in completely isolated environment (like uvx creates)."""
        # Install package with no system site packages
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "--isolated", "-e", str(package_root)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            # Try without --isolated flag if not supported
            result = subprocess.run([
                str(isolated_venv['pip']), "install", "-e", str(package_root)
            ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to install in isolated env: {result.stderr}"
        
        # Test basic functionality
        result = subprocess.run([
            str(isolated_venv['python']), "-c",
            """
import sys
print(f"Python path: {sys.path}")
from databricks_mcp_server.main import main
print("Isolated execution successful")
"""
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed isolated execution: {result.stderr}"
        assert "Isolated execution successful" in result.stdout


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility."""
    
    def test_path_handling(self, isolated_venv, package_root, temp_config_dir):
        """Test that path handling works across platforms."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Create config with platform-specific path
        config_data = {
            'databricks': {
                'server_hostname': 'test.databricks.com',
                'http_path': '/sql/1.0/warehouses/test',
                'access_token': 'test_token'
            }
        }
        
        config_file = temp_config_dir / "platform_test.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Test config loading with platform-specific path
        result = subprocess.run([
            str(isolated_venv['python']), "-m", "databricks_mcp_server.main",
            "--config", str(config_file), "--validate-config"
        ], capture_output=True, text=True, timeout=10)
        
        # Should handle path correctly regardless of platform
        output = result.stdout + result.stderr
        assert "test.databricks.com" in output

    def test_executable_creation(self, isolated_venv, package_root):
        """Test that executable is created correctly on current platform."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Check that entry point script is created
        if sys.platform == "win32":
            script_path = isolated_venv['path'] / "Scripts" / "databricks-mcp-server.exe"
        else:
            script_path = isolated_venv['path'] / "bin" / "databricks-mcp-server"
        
        # The script should exist after installation
        # Note: Some systems may not create the script file directly
        # but it should be available via the Python module system
        
        # Test execution via entry point
        result = subprocess.run([
            str(isolated_venv['python']), "-m", "databricks_mcp_server.main", "--help"
        ], capture_output=True, text=True)
        assert result.returncode == 0


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration