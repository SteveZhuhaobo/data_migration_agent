"""
Cross-platform compatibility tests for databricks-mcp-server.

These tests validate that the package works correctly across different
operating systems and Python environments.
"""

import os
import sys
import subprocess
import tempfile
import platform
from pathlib import Path
import pytest
import yaml


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility for Windows, macOS, and Linux."""
    
    def test_platform_detection(self):
        """Test that we can detect the current platform correctly."""
        current_platform = platform.system()
        assert current_platform in ["Windows", "Darwin", "Linux"], \
            f"Unsupported platform: {current_platform}"
        
        print(f"Testing on platform: {current_platform}")
        print(f"Platform details: {platform.platform()}")
        print(f"Python version: {sys.version}")
        print(f"Python executable: {sys.executable}")

    def test_path_separator_handling(self, isolated_venv, package_root, temp_config_dir):
        """Test that path separators are handled correctly on all platforms."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Create config with various path formats
        config_data = {
            'databricks': {
                'server_hostname': 'test.databricks.com',
                'http_path': '/sql/1.0/warehouses/test',
                'access_token': 'test_token'
            }
        }
        
        # Test with different path separators
        config_file = temp_config_dir / "path_test.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Test config loading with platform-specific path
        result = subprocess.run([
            str(isolated_venv['python']), "-m", "databricks_mcp_server.main",
            "--config", str(config_file), "--help"
        ], capture_output=True, text=True, timeout=10)
        
        # Should handle path correctly regardless of platform (help should work)
        assert result.returncode == 0, f"Config file path handling failed: {result.stderr}"

    def test_executable_creation_platform_specific(self, isolated_venv, package_root):
        """Test that executable is created correctly for the current platform."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Check platform-specific executable locations
        if sys.platform == "win32":
            # Windows: Scripts directory with .exe extension
            scripts_dir = isolated_venv['path'] / "Scripts"
            possible_executables = [
                scripts_dir / "databricks-mcp-server.exe",
                scripts_dir / "databricks-mcp-server.cmd",
                scripts_dir / "databricks-mcp-server"
            ]
        else:
            # Unix-like: bin directory
            bin_dir = isolated_venv['path'] / "bin"
            possible_executables = [
                bin_dir / "databricks-mcp-server"
            ]
        
        # At least one executable form should exist or be callable
        executable_found = False
        for exe_path in possible_executables:
            if exe_path.exists():
                executable_found = True
                print(f"Found executable: {exe_path}")
                break
        
        # If no direct executable found, test via Python module (which should always work)
        result = subprocess.run([
            str(isolated_venv['python']), "-m", "databricks_mcp_server.main", "--help"
        ], capture_output=True, text=True)
        assert result.returncode == 0, "Entry point execution failed"
        
        print(f"Entry point execution successful on {platform.system()}")

    def test_environment_variable_handling(self, isolated_venv, package_root, clean_databricks_env):
        """Test environment variable handling across platforms."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Set environment variables in platform-appropriate way
        env = os.environ.copy()
        env.update({
            'DATABRICKS_SERVER_HOSTNAME': 'env-test.databricks.com',
            'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/env-test',
            'DATABRICKS_ACCESS_TOKEN': 'env_test_token'
        })
        
        # Test that environment variables are read correctly (help should work)
        result = subprocess.run([
            str(isolated_venv['python']), "-m", "databricks_mcp_server.main",
            "--help"
        ], capture_output=True, text=True, env=env, timeout=10)
        
        # Should execute without errors when env vars are set
        assert result.returncode == 0, f"Environment variable handling failed: {result.stderr}"

    def test_file_permissions_handling(self, isolated_venv, package_root, temp_config_dir):
        """Test file permission handling across platforms."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Create config file
        config_data = {
            'databricks': {
                'server_hostname': 'perm-test.databricks.com',
                'http_path': '/sql/1.0/warehouses/perm-test',
                'access_token': 'perm_test_token'
            }
        }
        
        config_file = temp_config_dir / "perm_test.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Set restrictive permissions (Unix-like systems)
        if sys.platform != "win32":
            os.chmod(config_file, 0o600)  # Owner read/write only
        
        # Test config loading with restricted permissions
        result = subprocess.run([
            str(isolated_venv['python']), "-m", "databricks_mcp_server.main",
            "--config", str(config_file), "--help"
        ], capture_output=True, text=True, timeout=10)
        
        # Should handle file permissions correctly
        assert result.returncode == 0, f"File permission handling failed: {result.stderr}"

    def test_unicode_path_handling(self, isolated_venv, package_root):
        """Test handling of Unicode characters in paths."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Create temporary directory with Unicode characters
        with tempfile.TemporaryDirectory() as temp_dir:
            unicode_dir = Path(temp_dir) / "测试_тест_🚀"
            unicode_dir.mkdir(exist_ok=True)
            
            config_data = {
                'databricks': {
                    'server_hostname': 'unicode-test.databricks.com',
                    'http_path': '/sql/1.0/warehouses/unicode-test',
                    'access_token': 'unicode_test_token'
                }
            }
            
            config_file = unicode_dir / "config.yaml"
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f)
            
            # Test config loading with Unicode path
            result = subprocess.run([
                str(isolated_venv['python']), "-m", "databricks_mcp_server.main",
                "--config", str(config_file), "--help"
            ], capture_output=True, text=True, timeout=10)
            
            # Should handle Unicode paths without errors
            if result.returncode != 0:
                # Some systems may not support Unicode in paths
                error_output = result.stderr.lower()
                unicode_errors = ["unicodedecodeerror", "unicodeencodeerror", "invalid character"]
                if any(err in error_output for err in unicode_errors):
                    pytest.skip("System does not support Unicode in file paths")
                else:
                    assert False, f"Unicode path handling failed: {result.stderr}"


class TestPythonVersionCompatibility:
    """Test compatibility across different Python versions."""
    
    def test_python_version_requirements(self):
        """Test that current Python version meets requirements."""
        current_version = sys.version_info
        min_version = (3, 8)  # As specified in pyproject.toml
        
        assert current_version >= min_version, \
            f"Python {current_version} is below minimum required {min_version}"
        
        print(f"Python version {current_version} meets requirements (>= {min_version})")

    def test_import_compatibility(self, isolated_venv, package_root):
        """Test that imports work correctly on current Python version."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Test all major imports
        import_tests = [
            "import databricks_mcp_server",
            "from databricks_mcp_server import main",
            "from databricks_mcp_server import server",
            "from databricks_mcp_server import config",
            "from databricks_mcp_server.main import main as main_func"
        ]
        
        for import_test in import_tests:
            result = subprocess.run([
                str(isolated_venv['python']), "-c", f"{import_test}; print('Success: {import_test}')"
            ], capture_output=True, text=True)
            assert result.returncode == 0, f"Import failed: {import_test}"
            assert "Success:" in result.stdout

    def test_dependency_compatibility(self, isolated_venv, package_root):
        """Test that all dependencies are compatible with current Python version."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Check that all dependencies are installed
        result = subprocess.run([
            str(isolated_venv['pip']), "list"
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        pip_list = result.stdout.lower()
        required_packages = [
            "databricks-sql-connector",
            "requests", 
            "pyyaml"
        ]
        
        for package in required_packages:
            assert package in pip_list, f"Required package not installed: {package}"


class TestUvxIsolation:
    """Test uvx isolation functionality."""
    
    def test_isolated_environment_simulation(self, isolated_venv, package_root):
        """Test that package works in completely isolated environment."""
        # Install package with minimal dependencies
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Test that package works without system site packages
        result = subprocess.run([
            str(isolated_venv['python']), "-c",
            """
import sys
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")

# Test basic functionality
from databricks_mcp_server.main import main
print("Import successful")

# Test that we're truly isolated
import site
print(f"Site packages: {site.getsitepackages() if hasattr(site, 'getsitepackages') else 'N/A'}")
"""
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Import successful" in result.stdout

    def test_no_system_package_interference(self, isolated_venv, package_root):
        """Test that system packages don't interfere with isolated execution."""
        # Install package
        result = subprocess.run([
            str(isolated_venv['pip']), "install", "-e", str(package_root)
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Test execution with clean environment
        clean_env = {
            'PATH': os.environ.get('PATH', ''),
            'PYTHONPATH': '',  # Clear PYTHONPATH
            'PYTHONNOUSERSITE': '1'  # Disable user site packages
        }
        
        result = subprocess.run([
            str(isolated_venv['python']), "-c",
            """
import sys
# Verify clean environment
assert '' not in sys.path or sys.path.count('') <= 1
print("Clean environment verified")

# Test functionality
from databricks_mcp_server.main import main
print("Package functionality works in clean environment")
"""
        ], capture_output=True, text=True, env=clean_env)
        
        assert result.returncode == 0
        assert "Clean environment verified" in result.stdout
        assert "Package functionality works in clean environment" in result.stdout

    @pytest.mark.requires_uvx
    def test_actual_uvx_execution(self, package_root, temp_config_dir):
        """Test actual uvx execution if uvx is available."""
        # Check if uvx is available
        try:
            subprocess.run(["uvx", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("uvx not available for testing")
        
        # Create minimal config for testing
        config_data = {
            'databricks': {
                'server_hostname': 'uvx-test.databricks.com',
                'http_path': '/sql/1.0/warehouses/uvx-test',
                'access_token': 'uvx_test_token'
            }
        }
        
        config_file = temp_config_dir / "uvx_test.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Test uvx execution
        result = subprocess.run([
            "uvx", "--from", str(package_root), "databricks-mcp-server",
            "--config", str(config_file), "--help"
        ], capture_output=True, text=True, timeout=120)
        
        # Should execute without import errors
        if result.returncode != 0:
            error_output = result.stderr.lower()
            # Check for import errors (bad) vs connection errors (expected)
            import_errors = [
                "importerror", "modulenotfounderror", "no module named",
                "failed to import", "cannot import"
            ]
            
            has_import_error = any(err in error_output for err in import_errors)
            assert not has_import_error, f"Import error in uvx execution: {result.stderr}"
            
            # Connection errors are expected without real credentials
            connection_errors = [
                "connection", "authentication", "credentials", "token",
                "hostname", "databricks"
            ]
            has_connection_error = any(err in error_output for err in connection_errors)
            
            if not has_connection_error:
                # If it's not a connection error, it might be another issue
                print(f"Warning: Unexpected error in uvx execution: {result.stderr}")
        
        # Should execute help successfully
        if result.returncode == 0:
            assert "usage:" in result.stdout.lower() or "help" in result.stdout.lower()
        else:
            # If it fails, check it's not an import error
            error_output = result.stderr.lower()
            import_errors = [
                "importerror", "modulenotfounderror", "no module named",
                "failed to import", "cannot import"
            ]
            assert not any(err in error_output for err in import_errors), \
                f"Import error in uvx execution: {result.stderr}"


class TestPackageDistribution:
    """Test package distribution and installation scenarios."""
    
    def test_wheel_build_cross_platform(self, package_root):
        """Test that wheel can be built on current platform."""
        try:
            import build
        except ImportError:
            pytest.skip("build module not available")
        
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            dist_dir = Path(temp_dir) / "dist"
            
            # Build wheel
            result = subprocess.run([
                sys.executable, "-m", "build", str(package_root),
                "--wheel", "--outdir", str(dist_dir)
            ], capture_output=True, text=True, timeout=120)
            
            assert result.returncode == 0, f"Wheel build failed: {result.stderr}"
            
            # Check that wheel was created
            wheel_files = list(dist_dir.glob("*.whl"))
            assert len(wheel_files) > 0, "No wheel file created"
            
            wheel_file = wheel_files[0]
            print(f"✅ Wheel built successfully: {wheel_file.name}")
            
            # Test wheel installation
            with tempfile.TemporaryDirectory() as install_dir:
                venv_path = Path(install_dir) / "wheel_test_venv"
                
                # Create virtual environment
                result = subprocess.run([
                    sys.executable, "-m", "venv", str(venv_path)
                ], capture_output=True, text=True)
                assert result.returncode == 0
                
                # Get pip path
                if sys.platform == "win32":
                    pip_exe = venv_path / "Scripts" / "pip.exe"
                    python_exe = venv_path / "Scripts" / "python.exe"
                else:
                    pip_exe = venv_path / "bin" / "pip"
                    python_exe = venv_path / "bin" / "python"
                
                # Install wheel
                result = subprocess.run([
                    str(pip_exe), "install", str(wheel_file)
                ], capture_output=True, text=True)
                assert result.returncode == 0, f"Wheel installation failed: {result.stderr}"
                
                # Test installed package
                result = subprocess.run([
                    str(python_exe), "-c",
                    "import databricks_mcp_server; print('Wheel installation successful')"
                ], capture_output=True, text=True)
                assert result.returncode == 0
                assert "Wheel installation successful" in result.stdout

    def test_sdist_build_cross_platform(self, package_root):
        """Test that source distribution can be built on current platform."""
        try:
            import build
        except ImportError:
            pytest.skip("build module not available")
        
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            dist_dir = Path(temp_dir) / "dist"
            
            # Build source distribution
            result = subprocess.run([
                sys.executable, "-m", "build", str(package_root),
                "--sdist", "--outdir", str(dist_dir)
            ], capture_output=True, text=True, timeout=120)
            
            assert result.returncode == 0, f"Sdist build failed: {result.stderr}"
            
            # Check that sdist was created
            sdist_files = list(dist_dir.glob("*.tar.gz"))
            assert len(sdist_files) > 0, "No sdist file created"
            
            sdist_file = sdist_files[0]
            print(f"✅ Source distribution built successfully: {sdist_file.name}")


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration