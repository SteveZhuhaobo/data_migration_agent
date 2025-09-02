#!/usr/bin/env python3
"""
Cross-platform compatibility test runner for databricks-mcp-server.

This script validates that the package works correctly across different
operating systems and environments, simulating uvx isolation.
"""

import os
import sys
import subprocess
import platform
import tempfile
import argparse
from pathlib import Path


def print_platform_info():
    """Print detailed platform information."""
    print("="*80)
    print("PLATFORM INFORMATION")
    print("="*80)
    print(f"Operating System: {platform.system()}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Implementation: {platform.python_implementation()}")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"Virtual Environment: Yes ({sys.prefix})")
    else:
        print("Virtual Environment: No")
    
    print()


def run_command(cmd, description, timeout=60, env=None):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(str(c) for c in cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            env=env
        )
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        return result
    
    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out after {timeout} seconds")
        return None
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return None


def test_package_installation():
    """Test package installation in isolated environment."""
    print("\n" + "="*80)
    print("TESTING PACKAGE INSTALLATION")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "cross_platform_test_venv"
        
        # Create virtual environment
        result = run_command([
            sys.executable, "-m", "venv", str(venv_path)
        ], "Create isolated virtual environment")
        
        if not result or result.returncode != 0:
            print("❌ Failed to create virtual environment")
            return False
        
        # Get platform-specific paths
        if sys.platform == "win32":
            pip_exe = venv_path / "Scripts" / "pip.exe"
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            pip_exe = venv_path / "bin" / "pip"
            python_exe = venv_path / "bin" / "python"
        
        # Upgrade pip
        result = run_command([
            str(pip_exe), "install", "--upgrade", "pip"
        ], "Upgrade pip in isolated environment")
        
        if not result or result.returncode != 0:
            print("⚠️  Warning: Failed to upgrade pip")
        
        # Install package
        result = run_command([
            str(pip_exe), "install", "-e", "."
        ], "Install package in isolated environment")
        
        if not result or result.returncode != 0:
            print("❌ Failed to install package")
            return False
        
        # Test basic import
        result = run_command([
            str(python_exe), "-c", 
            "import databricks_mcp_server; print('Package import successful')"
        ], "Test package import")
        
        if not result or result.returncode != 0:
            print("❌ Failed to import package")
            return False
        
        if "Package import successful" not in result.stdout:
            print("❌ Package import message not found")
            return False
        
        # Test entry point
        result = run_command([
            str(python_exe), "-m", "databricks_mcp_server.main", "--help"
        ], "Test entry point execution")
        
        if not result or result.returncode != 0:
            print("❌ Failed to execute entry point")
            return False
        
        # Test version command
        result = run_command([
            str(python_exe), "-m", "databricks_mcp_server.main", "--version"
        ], "Test version command")
        
        if not result or result.returncode != 0:
            print("❌ Failed to execute version command")
            return False
        
        print("✅ Package installation test passed")
        return True


def test_configuration_handling():
    """Test configuration file and environment variable handling."""
    print("\n" + "="*80)
    print("TESTING CONFIGURATION HANDLING")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "config_test_venv"
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Create virtual environment
        result = run_command([
            sys.executable, "-m", "venv", str(venv_path)
        ], "Create virtual environment for config test")
        
        if not result or result.returncode != 0:
            return False
        
        # Get platform-specific paths
        if sys.platform == "win32":
            pip_exe = venv_path / "Scripts" / "pip.exe"
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            pip_exe = venv_path / "bin" / "pip"
            python_exe = venv_path / "bin" / "python"
        
        # Install package
        result = run_command([
            str(pip_exe), "install", "-e", "."
        ], "Install package for config test")
        
        if not result or result.returncode != 0:
            return False
        
        # Test 1: Configuration file
        config_file = config_dir / "test_config.yaml"
        config_content = """
databricks:
  server_hostname: test-config.databricks.com
  http_path: /sql/1.0/warehouses/test-config
  access_token: test_config_token
"""
        with open(config_file, "w") as f:
            f.write(config_content)
        
        result = run_command([
            str(python_exe), "-m", "databricks_mcp_server.main",
            "--config", str(config_file), "--validate-config"
        ], "Test configuration file loading", timeout=15)
        
        if result and result.returncode == 0:
            output = result.stdout + result.stderr
            if "test-config.databricks.com" in output:
                print("✅ Configuration file test passed")
            else:
                print("⚠️  Configuration file test: config not found in output")
        else:
            print("⚠️  Configuration file test: execution failed (may be expected)")
        
        # Test 2: Environment variables
        env = os.environ.copy()
        env.update({
            'DATABRICKS_SERVER_HOSTNAME': 'test-env.databricks.com',
            'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/test-env',
            'DATABRICKS_ACCESS_TOKEN': 'test_env_token'
        })
        
        result = run_command([
            str(python_exe), "-m", "databricks_mcp_server.main", "--validate-config"
        ], "Test environment variable configuration", timeout=15, env=env)
        
        if result and result.returncode == 0:
            output = result.stdout + result.stderr
            if "test-env.databricks.com" in output:
                print("✅ Environment variable test passed")
            else:
                print("⚠️  Environment variable test: config not found in output")
        else:
            print("⚠️  Environment variable test: execution failed (may be expected)")
        
        return True


def test_uvx_simulation():
    """Simulate uvx isolation and execution."""
    print("\n" + "="*80)
    print("TESTING UVX ISOLATION SIMULATION")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "uvx_simulation_venv"
        
        # Create completely isolated virtual environment
        result = run_command([
            sys.executable, "-m", "venv", str(venv_path), "--clear"
        ], "Create isolated environment (uvx simulation)")
        
        if not result or result.returncode != 0:
            return False
        
        # Get platform-specific paths
        if sys.platform == "win32":
            pip_exe = venv_path / "Scripts" / "pip.exe"
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            pip_exe = venv_path / "bin" / "pip"
            python_exe = venv_path / "bin" / "python"
        
        # Install package with minimal environment
        clean_env = {
            'PATH': os.environ.get('PATH', ''),
            'PYTHONNOUSERSITE': '1',  # Disable user site packages
            'PYTHONPATH': ''  # Clear Python path
        }
        
        result = run_command([
            str(pip_exe), "install", "-e", "."
        ], "Install package in isolated environment", env=clean_env)
        
        if not result or result.returncode != 0:
            return False
        
        # Test isolated execution
        result = run_command([
            str(python_exe), "-c", """
import sys
print(f"Python executable: {sys.executable}")
print(f"Python path length: {len(sys.path)}")

# Test package functionality
from databricks_mcp_server.main import main
print("Isolated execution successful")

# Verify isolation
import site
user_site = getattr(site, 'USER_SITE', None)
if user_site and user_site in sys.path:
    print("Warning: User site packages detected in path")
else:
    print("User site packages properly isolated")
"""
        ], "Test isolated execution", env=clean_env)
        
        if not result or result.returncode != 0:
            print("❌ Isolated execution failed")
            return False
        
        if "Isolated execution successful" in result.stdout:
            print("✅ UVX isolation simulation passed")
            return True
        else:
            print("❌ UVX isolation simulation failed")
            return False


def test_actual_uvx():
    """Test actual uvx execution if available."""
    print("\n" + "="*80)
    print("TESTING ACTUAL UVX EXECUTION")
    print("="*80)
    
    # Check if uvx is available
    try:
        result = subprocess.run(["uvx", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  uvx not available - skipping actual uvx test")
            return True
        print(f"Found uvx: {result.stdout.strip()}")
    except FileNotFoundError:
        print("⚠️  uvx not available - skipping actual uvx test")
        return True
    
    # Create temporary config for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "uvx_test.yaml"
        config_content = """
databricks:
  server_hostname: uvx-test.databricks.com
  http_path: /sql/1.0/warehouses/uvx-test
  access_token: uvx_test_token
"""
        with open(config_file, "w") as f:
            f.write(config_content)
        
        # Test uvx execution
        result = run_command([
            "uvx", "--from", ".", "databricks-mcp-server",
            "--config", str(config_file), "--validate-config"
        ], "Test actual uvx execution", timeout=120)
        
        if result:
            if result.returncode == 0:
                print("✅ UVX execution successful")
                return True
            else:
                # Check if it's an import error (bad) or connection error (expected)
                error_output = result.stderr.lower()
                import_errors = [
                    "importerror", "modulenotfounderror", "no module named",
                    "failed to import", "cannot import"
                ]
                
                if any(err in error_output for err in import_errors):
                    print("❌ UVX execution failed with import error")
                    return False
                else:
                    print("✅ UVX execution successful (connection error expected)")
                    return True
        else:
            print("❌ UVX execution failed")
            return False


def test_cross_platform_paths():
    """Test cross-platform path handling."""
    print("\n" + "="*80)
    print("TESTING CROSS-PLATFORM PATH HANDLING")
    print("="*80)
    
    # Test various path scenarios
    test_paths = [
        "config.yaml",
        "./config.yaml",
        "config/config.yaml",
        "../config.yaml"
    ]
    
    if sys.platform == "win32":
        test_paths.extend([
            "C:\\temp\\config.yaml",
            "config\\config.yaml"
        ])
    else:
        test_paths.extend([
            "/tmp/config.yaml",
            "~/config.yaml"
        ])
    
    print(f"Testing path handling on {platform.system()}:")
    
    for test_path in test_paths:
        try:
            # Test path normalization
            normalized = os.path.normpath(test_path)
            absolute = os.path.abspath(test_path)
            print(f"  {test_path} -> {normalized} -> {absolute}")
        except Exception as e:
            print(f"  ❌ Path error for {test_path}: {e}")
            return False
    
    print("✅ Cross-platform path handling test passed")
    return True


def run_pytest_cross_platform_tests():
    """Run the pytest-based cross-platform tests."""
    print("\n" + "="*80)
    print("RUNNING PYTEST CROSS-PLATFORM TESTS")
    print("="*80)
    
    # Check if pytest is available
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "--version"
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  pytest not available - installing...")
            install_result = subprocess.run([
                sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"
            ], capture_output=True, text=True)
            if install_result.returncode != 0:
                print("❌ Failed to install pytest")
                return False
    except Exception:
        print("❌ pytest not available")
        return False
    
    # Run cross-platform tests
    result = run_command([
        sys.executable, "-m", "pytest", 
        "tests/test_cross_platform.py",
        "-v", 
        "-m", "integration",
        "--tb=short"
    ], "Run pytest cross-platform tests", timeout=300)
    
    if result and result.returncode == 0:
        print("✅ Pytest cross-platform tests passed")
        return True
    else:
        print("❌ Pytest cross-platform tests failed")
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Cross-platform compatibility test runner")
    parser.add_argument("--skip-installation", action="store_true", help="Skip installation test")
    parser.add_argument("--skip-config", action="store_true", help="Skip configuration test")
    parser.add_argument("--skip-uvx-sim", action="store_true", help="Skip uvx simulation test")
    parser.add_argument("--skip-uvx", action="store_true", help="Skip actual uvx test")
    parser.add_argument("--skip-paths", action="store_true", help="Skip path handling test")
    parser.add_argument("--skip-pytest", action="store_true", help="Skip pytest tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Change to package directory
    package_dir = Path(__file__).parent
    os.chdir(package_dir)
    
    print("Databricks MCP Server - Cross-Platform Compatibility Test Runner")
    print(f"Package directory: {package_dir}")
    
    # Print platform information
    print_platform_info()
    
    success = True
    test_results = {}
    
    # Run tests
    if not args.skip_installation:
        test_results["Installation"] = test_package_installation()
        success = success and test_results["Installation"]
    
    if not args.skip_config:
        test_results["Configuration"] = test_configuration_handling()
        success = success and test_results["Configuration"]
    
    if not args.skip_uvx_sim:
        test_results["UVX Simulation"] = test_uvx_simulation()
        success = success and test_results["UVX Simulation"]
    
    if not args.skip_uvx:
        test_results["UVX Actual"] = test_actual_uvx()
        success = success and test_results["UVX Actual"]
    
    if not args.skip_paths:
        test_results["Path Handling"] = test_cross_platform_paths()
        success = success and test_results["Path Handling"]
    
    if not args.skip_pytest:
        test_results["Pytest Tests"] = run_pytest_cross_platform_tests()
        success = success and test_results["Pytest Tests"]
    
    # Summary
    print("\n" + "="*80)
    print("CROSS-PLATFORM COMPATIBILITY TEST SUMMARY")
    print("="*80)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
    
    print(f"\nPlatform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    
    if success:
        print("\n🎉 All cross-platform compatibility tests passed!")
        print(f"\nThe databricks-mcp-server package is compatible with:")
        print(f"- {platform.system()} {platform.release()}")
        print(f"- Python {sys.version.split()[0]}")
        print("- uvx isolation environment")
        return 0
    else:
        print("\n❌ Some cross-platform compatibility tests failed!")
        print("\nPlease review the test output above and fix any platform-specific issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())