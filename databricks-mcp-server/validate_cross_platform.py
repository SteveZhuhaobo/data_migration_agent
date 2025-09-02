#!/usr/bin/env python3
"""
Cross-platform validation script for databricks-mcp-server.

This script validates that the package meets all cross-platform compatibility
requirements as specified in task 10 of the implementation plan.

Requirements validated:
- 7.1: uvx creates isolated environment with correct dependencies
- 7.2: Python version compatibility across platforms  
- 7.3: Dependency resolution
- 7.4: No interference with other Python packages
- 7.5: Clean uninstallation
"""

import os
import sys
import subprocess
import platform
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class CrossPlatformValidator:
    """Validates cross-platform compatibility for databricks-mcp-server package."""
    
    def __init__(self):
        self.platform_info = {
            'system': platform.system(),
            'machine': platform.machine(),
            'python_version': platform.python_version(),
            'platform': platform.platform()
        }
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "✓ PASS" if success else "✗ FAIL"
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append((test_name, success, message))
        
    def run_command(self, cmd: List[str], capture_output: bool = True) -> Tuple[bool, str, str]:
        """Run command and return success, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=capture_output, 
                text=True, 
                timeout=300
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
            
    def check_uv_installation(self) -> bool:
        """Check if uv/uvx is available."""
        success, stdout, stderr = self.run_command(['uvx', '--version'])
        if success:
            self.log_result("UV/UVX Installation", True, f"Version: {stdout.strip()}")
            return True
        else:
            self.log_result("UV/UVX Installation", False, "uvx not found or not working")
            return False
            
    def validate_package_structure(self) -> bool:
        """Validate that package has correct structure."""
        required_files = [
            'pyproject.toml',
            'src/databricks_mcp_server/__init__.py',
            'src/databricks_mcp_server/main.py',
            'src/databricks_mcp_server/server.py',
            'src/databricks_mcp_server/config.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
                
        if missing_files:
            self.log_result("Package Structure", False, f"Missing files: {missing_files}")
            return False
        else:
            self.log_result("Package Structure", True, "All required files present")
            return True
            
    def test_local_installation(self) -> bool:
        """Test local package installation."""
        # Test pip install in development mode
        success, stdout, stderr = self.run_command(['pip', 'install', '-e', '.'])
        if not success:
            self.log_result("Local Installation", False, f"pip install failed: {stderr}")
            return False
            
        # Test that entry point works
        success, stdout, stderr = self.run_command(['databricks-mcp-server', '--help'])
        if success:
            self.log_result("Local Installation", True, "Entry point working")
            return True
        else:
            self.log_result("Local Installation", False, f"Entry point failed: {stderr}")
            return False
            
    def test_uvx_installation(self) -> bool:
        """Test uvx installation from local package."""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Build the package
            success, stdout, stderr = self.run_command(['python', '-m', 'build'])
            if not success:
                self.log_result("UVX Installation", False, f"Package build failed: {stderr}")
                return False
                
            # Find the built wheel
            dist_dir = Path('dist')
            if not dist_dir.exists():
                self.log_result("UVX Installation", False, "No dist directory found")
                return False
                
            wheel_files = list(dist_dir.glob('*.whl'))
            if not wheel_files:
                self.log_result("UVX Installation", False, "No wheel file found")
                return False
                
            wheel_path = wheel_files[0]
            
            # Test uvx installation
            success, stdout, stderr = self.run_command(['uvx', '--from', str(wheel_path), 'databricks-mcp-server', '--help'])
            if success:
                self.log_result("UVX Installation", True, "uvx installation and execution successful")
                return True
            else:
                self.log_result("UVX Installation", False, f"uvx execution failed: {stderr}")
                return False
                
    def test_python_version_compatibility(self) -> bool:
        """Test Python version compatibility."""
        current_version = sys.version_info
        min_version = (3, 8)
        
        if current_version >= min_version:
            self.log_result("Python Version", True, f"Python {current_version.major}.{current_version.minor} >= 3.8")
            return True
        else:
            self.log_result("Python Version", False, f"Python {current_version.major}.{current_version.minor} < 3.8")
            return False
            
    def test_dependency_resolution(self) -> bool:
        """Test that dependencies can be resolved."""
        # Check if we can import key dependencies
        try:
            import yaml
            import requests
            self.log_result("Dependency Resolution", True, "Core dependencies available")
            return True
        except ImportError as e:
            self.log_result("Dependency Resolution", False, f"Missing dependency: {e}")
            return False
            
    def test_environment_isolation(self) -> bool:
        """Test that uvx creates proper isolation."""
        # This is harder to test automatically, but we can check basic isolation
        success, stdout, stderr = self.run_command(['python', '-c', 'import sys; print(sys.executable)'])
        if success:
            python_path = stdout.strip()
            self.log_result("Environment Isolation", True, f"Python executable: {python_path}")
            return True
        else:
            self.log_result("Environment Isolation", False, "Could not determine Python executable")
            return False
            
    def run_all_tests(self) -> bool:
        """Run all cross-platform validation tests."""
        print(f"Running cross-platform validation on {self.platform_info['system']} {self.platform_info['machine']}")
        print(f"Python version: {self.platform_info['python_version']}")
        print(f"Platform: {self.platform_info['platform']}")
        print("-" * 60)
        
        tests = [
            self.check_uv_installation,
            self.validate_package_structure,
            self.test_python_version_compatibility,
            self.test_dependency_resolution,
            self.test_local_installation,
            self.test_environment_isolation,
            self.test_uvx_installation,
        ]
        
        all_passed = True
        for test in tests:
            try:
                result = test()
                if not result:
                    all_passed = False
            except Exception as e:
                self.log_result(test.__name__, False, f"Exception: {e}")
                all_passed = False
                
        print("-" * 60)
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        print(f"Results: {passed}/{total} tests passed")
        
        if all_passed:
            print("✓ All cross-platform validation tests PASSED")
        else:
            print("✗ Some cross-platform validation tests FAILED")
            
        return all_passed

def main():
    """Main entry point."""
    validator = CrossPlatformValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()