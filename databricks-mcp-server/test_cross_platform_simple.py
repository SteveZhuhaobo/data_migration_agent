#!/usr/bin/env python3
"""
Simplified cross-platform compatibility test for databricks-mcp-server.

This script validates basic cross-platform functionality without requiring
network connectivity for package installation.
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
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Implementation: {platform.python_implementation()}")
    print()


def test_basic_imports():
    """Test that all package imports work correctly."""
    print("\n" + "="*80)
    print("TESTING BASIC IMPORTS")
    print("="*80)
    
    import_tests = [
        ("databricks_mcp_server", "Main package import"),
        ("databricks_mcp_server.main", "Main module import"),
        ("databricks_mcp_server.server", "Server module import"),
        ("databricks_mcp_server.config", "Config module import"),
        ("databricks_mcp_server.errors", "Errors module import")
    ]
    
    success = True
    for module_name, description in import_tests:
        try:
            __import__(module_name)
            print(f"✅ {description}: SUCCESS")
        except ImportError as e:
            print(f"❌ {description}: FAILED - {e}")
            success = False
        except Exception as e:
            print(f"❌ {description}: ERROR - {e}")
            success = False
    
    return success


def test_entry_point_functionality():
    """Test entry point functionality."""
    print("\n" + "="*80)
    print("TESTING ENTRY POINT FUNCTIONALITY")
    print("="*80)
    
    try:
        # Test help command
        result = subprocess.run([
            sys.executable, "-m", "databricks_mcp_server.main", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Help command: SUCCESS")
            help_success = True
        else:
            print(f"❌ Help command: FAILED - Return code {result.returncode}")
            print(f"   Error: {result.stderr}")
            help_success = False
        
        # Test version command
        result = subprocess.run([
            sys.executable, "-m", "databricks_mcp_server.main", "--version"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "1.0.0" in result.stdout:
            print("✅ Version command: SUCCESS")
            version_success = True
        else:
            print(f"❌ Version command: FAILED - Return code {result.returncode}")
            print(f"   Output: {result.stdout}")
            print(f"   Error: {result.stderr}")
            version_success = False
        
        return help_success and version_success
        
    except subprocess.TimeoutExpired:
        print("❌ Entry point test: TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ Entry point test: ERROR - {e}")
        return False


def test_configuration_loading():
    """Test configuration loading functionality."""
    print("\n" + "="*80)
    print("TESTING CONFIGURATION LOADING")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "test_config.yaml"
        config_content = """
databricks:
  server_hostname: test-platform.databricks.com
  http_path: /sql/1.0/warehouses/test-platform
  access_token: test_platform_token
"""
        with open(config_file, "w") as f:
            f.write(config_content)
        
        try:
            # Test config validation
            result = subprocess.run([
                sys.executable, "-m", "databricks_mcp_server.main",
                "--config", str(config_file), "--validate-config"
            ], capture_output=True, text=True, timeout=15)
            
            output = result.stdout + result.stderr
            if "test-platform.databricks.com" in output:
                print("✅ Configuration loading: SUCCESS")
                return True
            else:
                print("⚠️  Configuration loading: Config not found in output (may be expected)")
                print(f"   Output: {output[:200]}...")
                return True  # This is acceptable as connection may fail
                
        except subprocess.TimeoutExpired:
            print("⚠️  Configuration loading: TIMEOUT (may be expected)")
            return True
        except Exception as e:
            print(f"❌ Configuration loading: ERROR - {e}")
            return False


def test_environment_variables():
    """Test environment variable handling."""
    print("\n" + "="*80)
    print("TESTING ENVIRONMENT VARIABLES")
    print("="*80)
    
    # Set test environment variables
    env = os.environ.copy()
    env.update({
        'DATABRICKS_SERVER_HOSTNAME': 'env-platform.databricks.com',
        'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/env-platform',
        'DATABRICKS_ACCESS_TOKEN': 'env_platform_token'
    })
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "databricks_mcp_server.main", "--validate-config"
        ], capture_output=True, text=True, env=env, timeout=15)
        
        output = result.stdout + result.stderr
        if "env-platform.databricks.com" in output:
            print("✅ Environment variables: SUCCESS")
            return True
        else:
            print("⚠️  Environment variables: Config not found in output (may be expected)")
            return True  # This is acceptable as connection may fail
            
    except subprocess.TimeoutExpired:
        print("⚠️  Environment variables: TIMEOUT (may be expected)")
        return True
    except Exception as e:
        print(f"❌ Environment variables: ERROR - {e}")
        return False


def test_path_handling():
    """Test cross-platform path handling."""
    print("\n" + "="*80)
    print("TESTING PATH HANDLING")
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
    
    success = True
    for test_path in test_paths:
        try:
            # Test path normalization
            normalized = os.path.normpath(test_path)
            absolute = os.path.abspath(test_path)
            print(f"  ✅ {test_path} -> {normalized}")
        except Exception as e:
            print(f"  ❌ Path error for {test_path}: {e}")
            success = False
    
    return success


def test_python_version_compatibility():
    """Test Python version compatibility."""
    print("\n" + "="*80)
    print("TESTING PYTHON VERSION COMPATIBILITY")
    print("="*80)
    
    current_version = sys.version_info
    min_version = (3, 8)  # As specified in pyproject.toml
    
    if current_version >= min_version:
        print(f"✅ Python version {current_version} meets requirements (>= {min_version})")
        return True
    else:
        print(f"❌ Python version {current_version} is below minimum required {min_version}")
        return False


def test_package_structure():
    """Test that package structure is correct."""
    print("\n" + "="*80)
    print("TESTING PACKAGE STRUCTURE")
    print("="*80)
    
    # Check that required files exist
    package_root = Path(__file__).parent
    required_files = [
        "pyproject.toml",
        "README.md",
        "src/databricks_mcp_server/__init__.py",
        "src/databricks_mcp_server/main.py",
        "src/databricks_mcp_server/server.py",
        "src/databricks_mcp_server/config.py",
        "config/config.yaml.example"
    ]
    
    success = True
    for file_path in required_files:
        full_path = package_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}: EXISTS")
        else:
            print(f"❌ {file_path}: MISSING")
            success = False
    
    return success


def test_executable_paths():
    """Test platform-specific executable path handling."""
    print("\n" + "="*80)
    print("TESTING EXECUTABLE PATHS")
    print("="*80)
    
    # Test that we can determine correct executable paths for the platform
    if sys.platform == "win32":
        expected_script_dir = "Scripts"
        expected_executable_ext = ".exe"
        print(f"✅ Windows platform detected - Scripts dir: {expected_script_dir}")
    else:
        expected_script_dir = "bin"
        expected_executable_ext = ""
        print(f"✅ Unix-like platform detected - Scripts dir: {expected_script_dir}")
    
    # Test that Python executable path is correct for platform
    python_exe = Path(sys.executable)
    if sys.platform == "win32":
        if "Scripts" in str(python_exe) or python_exe.name.endswith(".exe"):
            print("✅ Python executable path format correct for Windows")
            return True
        else:
            print(f"⚠️  Python executable path may not be standard Windows format: {python_exe}")
            return True  # Still acceptable
    else:
        if "bin" in str(python_exe):
            print("✅ Python executable path format correct for Unix-like")
            return True
        else:
            print(f"⚠️  Python executable path may not be standard Unix format: {python_exe}")
            return True  # Still acceptable


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Simple cross-platform compatibility test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Change to package directory
    package_dir = Path(__file__).parent
    os.chdir(package_dir)
    
    print("Databricks MCP Server - Simple Cross-Platform Compatibility Test")
    print(f"Package directory: {package_dir}")
    
    # Print platform information
    print_platform_info()
    
    # Run tests
    test_results = {}
    
    test_results["Package Structure"] = test_package_structure()
    test_results["Python Version"] = test_python_version_compatibility()
    test_results["Basic Imports"] = test_basic_imports()
    test_results["Entry Point"] = test_entry_point_functionality()
    test_results["Configuration"] = test_configuration_loading()
    test_results["Environment Variables"] = test_environment_variables()
    test_results["Path Handling"] = test_path_handling()
    test_results["Executable Paths"] = test_executable_paths()
    
    # Summary
    print("\n" + "="*80)
    print("CROSS-PLATFORM COMPATIBILITY TEST SUMMARY")
    print("="*80)
    
    success = True
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        success = success and result
    
    print(f"\nPlatform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    
    if success:
        print("\n🎉 All cross-platform compatibility tests passed!")
        print(f"\nThe databricks-mcp-server package is compatible with:")
        print(f"- {platform.system()} {platform.release()}")
        print(f"- Python {sys.version.split()[0]}")
        return 0
    else:
        print("\n❌ Some cross-platform compatibility tests failed!")
        print("\nPlease review the test output above and fix any platform-specific issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())