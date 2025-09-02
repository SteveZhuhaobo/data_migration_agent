#!/usr/bin/env python3
"""
Integration test runner for databricks-mcp-server package.

This script runs comprehensive integration tests to validate:
- Package installation via pip
- uvx installation and execution workflow  
- Entry point execution and server startup
- Configuration file and environment variable integration
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description, timeout=60):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout
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
        print(f"Command timed out after {timeout} seconds")
        return None
    except Exception as e:
        print(f"Error running command: {e}")
        return None


def check_prerequisites():
    """Check that required tools are available."""
    print("Checking prerequisites...")
    
    # Check Python
    print(f"Python version: {sys.version}")
    
    # Check pip
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"pip: {result.stdout.strip()}")
        else:
            print("pip: Not available")
            return False
    except Exception:
        print("pip: Not available")
        return False
    
    # Check pytest
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"pytest: {result.stdout.strip()}")
        else:
            print("pytest: Not available - installing...")
            install_result = subprocess.run([
                sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio", "pytest-cov"
            ], capture_output=True, text=True)
            if install_result.returncode != 0:
                print("Failed to install pytest")
                return False
    except Exception:
        print("pytest: Not available")
        return False
    
    # Check uvx (optional)
    try:
        result = subprocess.run(["uvx", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"uvx: {result.stdout.strip()}")
        else:
            print("uvx: Not available (uvx tests will be skipped)")
    except Exception:
        print("uvx: Not available (uvx tests will be skipped)")
    
    return True


def run_unit_tests():
    """Run unit tests first to ensure basic functionality."""
    print("\n" + "="*80)
    print("RUNNING UNIT TESTS")
    print("="*80)
    
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v", 
        "-m", "not integration",
        "--tb=short"
    ]
    
    result = run_command(cmd, "Unit tests")
    return result and result.returncode == 0


def run_integration_tests(test_filter=None, include_slow=False, include_uvx=False):
    """Run integration tests."""
    print("\n" + "="*80)
    print("RUNNING INTEGRATION TESTS")
    print("="*80)
    
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_integration.py",
        "tests/test_package_validation.py",
        "-v", 
        "-m", "integration",
        "--tb=short"
    ]
    
    # Add test filter if specified
    if test_filter:
        cmd.extend(["-k", test_filter])
    
    # Skip slow tests unless requested
    if not include_slow:
        cmd.extend(["-m", "integration and not slow"])
    
    # Skip uvx tests unless requested
    if not include_uvx:
        cmd.extend(["-m", "integration and not requires_uvx"])
    
    result = run_command(cmd, "Integration tests", timeout=300)
    return result and result.returncode == 0


def run_package_build_test():
    """Test package building."""
    print("\n" + "="*80)
    print("TESTING PACKAGE BUILD")
    print("="*80)
    
    # Try to build the package
    try:
        import build
        cmd = [sys.executable, "-m", "build", ".", "--outdir", "dist"]
    except ImportError:
        print("build module not available, trying setup.py...")
        cmd = [sys.executable, "setup.py", "bdist_wheel"]
    
    result = run_command(cmd, "Package build test")
    return result and result.returncode == 0


def run_installation_test():
    """Test package installation in clean environment."""
    print("\n" + "="*80)
    print("TESTING PACKAGE INSTALLATION")
    print("="*80)
    
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "test_install_venv"
        
        # Create virtual environment
        cmd = [sys.executable, "-m", "venv", str(venv_path)]
        result = run_command(cmd, "Create test virtual environment")
        if not result or result.returncode != 0:
            return False
        
        # Get pip path
        if sys.platform == "win32":
            pip_exe = venv_path / "Scripts" / "pip.exe"
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            pip_exe = venv_path / "bin" / "pip"
            python_exe = venv_path / "bin" / "python"
        
        # Install package
        cmd = [str(pip_exe), "install", "-e", "."]
        result = run_command(cmd, "Install package in test environment")
        if not result or result.returncode != 0:
            return False
        
        # Test basic import
        cmd = [str(python_exe), "-c", "import databricks_mcp_server; print('Import successful')"]
        result = run_command(cmd, "Test package import")
        if not result or result.returncode != 0:
            return False
        
        # Test entry point
        cmd = [str(python_exe), "-m", "databricks_mcp_server.main", "--help"]
        result = run_command(cmd, "Test entry point")
        if not result or result.returncode != 0:
            return False
    
    return True


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Run integration tests for databricks-mcp-server")
    parser.add_argument("--skip-unit", action="store_true", help="Skip unit tests")
    parser.add_argument("--skip-integration", action="store_true", help="Skip integration tests")
    parser.add_argument("--skip-build", action="store_true", help="Skip build test")
    parser.add_argument("--skip-install", action="store_true", help="Skip installation test")
    parser.add_argument("--include-slow", action="store_true", help="Include slow tests")
    parser.add_argument("--include-uvx", action="store_true", help="Include uvx tests")
    parser.add_argument("--filter", help="Filter tests by name pattern")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Change to package directory
    package_dir = Path(__file__).parent
    os.chdir(package_dir)
    
    print("Databricks MCP Server - Integration Test Runner")
    print(f"Package directory: {package_dir}")
    print(f"Python executable: {sys.executable}")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\nPrerequisite check failed!")
        return 1
    
    success = True
    
    # Run unit tests first
    if not args.skip_unit:
        if not run_unit_tests():
            print("\nUnit tests failed!")
            success = False
    
    # Run integration tests
    if not args.skip_integration and success:
        if not run_integration_tests(
            test_filter=args.filter,
            include_slow=args.include_slow,
            include_uvx=args.include_uvx
        ):
            print("\nIntegration tests failed!")
            success = False
    
    # Test package building
    if not args.skip_build and success:
        if not run_package_build_test():
            print("\nPackage build test failed!")
            success = False
    
    # Test package installation
    if not args.skip_install and success:
        if not run_installation_test():
            print("\nPackage installation test failed!")
            success = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    if success:
        print("✅ All tests passed!")
        print("\nThe databricks-mcp-server package is ready for:")
        print("- Installation via pip")
        print("- Execution via uvx")
        print("- Distribution to users")
        return 0
    else:
        print("❌ Some tests failed!")
        print("\nPlease review the test output above and fix any issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())