#!/usr/bin/env python3
"""
Distribution validation script.

This script validates that the built package meets all distribution requirements
and can be successfully installed and used via different methods.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DistributionValidator:
    """Validates package distribution."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.dist_dir = project_root / "dist"
        self.results: Dict[str, bool] = {}
        self.errors: List[str] = []
    
    def log_result(self, test_name: str, success: bool, error: Optional[str] = None) -> None:
        """Log test result."""
        self.results[test_name] = success
        if not success and error:
            self.errors.append(f"{test_name}: {error}")
        
        status = "✓" if success else "✗"
        print(f"{status} {test_name}")
        if error and not success:
            print(f"  Error: {error}")
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None, 
                   capture_output: bool = True) -> Tuple[int, str, str]:
        """Run command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=capture_output,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
    
    def validate_package_structure(self) -> bool:
        """Validate package structure and files."""
        print("\n=== Package Structure Validation ===")
        
        # Check dist directory exists
        if not self.dist_dir.exists():
            self.log_result("dist_directory_exists", False, "dist directory not found")
            return False
        
        self.log_result("dist_directory_exists", True)
        
        # Check for wheel and source distribution
        wheel_files = list(self.dist_dir.glob("*.whl"))
        tar_files = list(self.dist_dir.glob("*.tar.gz"))
        
        wheel_exists = len(wheel_files) == 1
        tar_exists = len(tar_files) == 1
        
        self.log_result("wheel_file_exists", wheel_exists, 
                       f"Expected 1 wheel file, found {len(wheel_files)}")
        self.log_result("source_dist_exists", tar_exists,
                       f"Expected 1 source dist, found {len(tar_files)}")
        
        return wheel_exists and tar_exists
    
    def validate_package_metadata(self) -> bool:
        """Validate package metadata using twine."""
        print("\n=== Package Metadata Validation ===")
        
        # Check with twine
        exit_code, stdout, stderr = self.run_command(["twine", "check", "dist/*"])
        
        success = exit_code == 0 and "PASSED" in stdout
        error = stderr if not success else None
        
        self.log_result("twine_check_passed", success, error)
        
        return success
    
    def validate_dependencies(self) -> bool:
        """Validate that all dependencies are correctly specified."""
        print("\n=== Dependency Validation ===")
        
        pyproject_path = self.project_root / "pyproject.toml"
        if not pyproject_path.exists():
            self.log_result("pyproject_exists", False, "pyproject.toml not found")
            return False
        
        self.log_result("pyproject_exists", True)
        
        content = pyproject_path.read_text()
        
        # Check required dependencies
        required_deps = [
            "databricks-sql-connector",
            "requests", 
            "pyyaml",
            "mcp"
        ]
        
        all_deps_found = True
        for dep in required_deps:
            found = dep in content
            self.log_result(f"dependency_{dep.replace('-', '_')}", found,
                           f"Dependency {dep} not found in pyproject.toml")
            if not found:
                all_deps_found = False
        
        # Check entry point
        entry_point_correct = 'databricks-mcp-server = "databricks_mcp_server.main:main"' in content
        self.log_result("entry_point_configured", entry_point_correct,
                       "Entry point not correctly configured")
        
        return all_deps_found and entry_point_correct
    
    def validate_pip_installation(self) -> bool:
        """Validate pip installation in clean environment."""
        print("\n=== Pip Installation Validation ===")
        
        wheel_files = list(self.dist_dir.glob("*.whl"))
        if not wheel_files:
            self.log_result("pip_install_wheel_available", False, "No wheel file found")
            return False
        
        wheel_file = wheel_files[0]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_dir = Path(temp_dir) / "test_env"
            
            # Create virtual environment
            exit_code, _, stderr = self.run_command([
                sys.executable, "-m", "venv", str(venv_dir)
            ])
            
            if exit_code != 0:
                self.log_result("pip_venv_creation", False, stderr)
                return False
            
            self.log_result("pip_venv_creation", True)
            
            # Get python executable path
            if sys.platform == "win32":
                python_exe = venv_dir / "Scripts" / "python.exe"
                entry_point = venv_dir / "Scripts" / "databricks-mcp-server.exe"
            else:
                python_exe = venv_dir / "bin" / "python"
                entry_point = venv_dir / "bin" / "databricks-mcp-server"
            
            # Install package
            exit_code, _, stderr = self.run_command([
                str(python_exe), "-m", "pip", "install", str(wheel_file)
            ])
            
            if exit_code != 0:
                self.log_result("pip_package_install", False, stderr)
                return False
            
            self.log_result("pip_package_install", True)
            
            # Check entry point exists
            entry_point_exists = entry_point.exists()
            self.log_result("pip_entry_point_created", entry_point_exists,
                           f"Entry point not found: {entry_point}")
            
            if not entry_point_exists:
                return False
            
            # Test entry point execution
            exit_code, stdout, stderr = self.run_command([str(entry_point), "--help"])
            
            entry_point_works = exit_code == 0 and "databricks-mcp-server" in stdout.lower()
            self.log_result("pip_entry_point_works", entry_point_works, stderr)
            
            # Test package import
            exit_code, stdout, stderr = self.run_command([
                str(python_exe), "-c", 
                "import databricks_mcp_server; print('Import successful')"
            ])
            
            import_works = exit_code == 0 and "Import successful" in stdout
            self.log_result("pip_package_import", import_works, stderr)
            
            return entry_point_works and import_works
    
    def validate_uvx_installation(self) -> bool:
        """Validate uvx installation."""
        print("\n=== uvx Installation Validation ===")
        
        # Check if uvx is available
        if not shutil.which("uvx"):
            self.log_result("uvx_available", False, "uvx command not found")
            return False
        
        self.log_result("uvx_available", True)
        
        wheel_files = list(self.dist_dir.glob("*.whl"))
        if not wheel_files:
            self.log_result("uvx_wheel_available", False, "No wheel file found")
            return False
        
        wheel_file = wheel_files[0]
        
        # Test uvx installation and execution
        exit_code, stdout, stderr = self.run_command([
            "uvx", "--from", str(wheel_file), "databricks-mcp-server", "--help"
        ])
        
        success = exit_code == 0 and "databricks-mcp-server" in stdout.lower()
        self.log_result("uvx_installation_works", success, stderr)
        
        return success
    
    def validate_cross_platform_compatibility(self) -> bool:
        """Validate cross-platform compatibility markers."""
        print("\n=== Cross-Platform Compatibility ===")
        
        # Check wheel file for platform tags
        wheel_files = list(self.dist_dir.glob("*.whl"))
        if not wheel_files:
            self.log_result("wheel_file_for_platform_check", False, "No wheel file found")
            return False
        
        wheel_file = wheel_files[0]
        wheel_name = wheel_file.name
        
        # Check for universal wheel (py3-none-any)
        is_universal = "py3-none-any" in wheel_name
        self.log_result("universal_wheel", is_universal,
                       f"Wheel is not universal: {wheel_name}")
        
        # Check Python version compatibility
        pyproject_path = self.project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        
        has_python_requires = "requires-python" in content
        self.log_result("python_version_specified", has_python_requires,
                       "Python version requirement not specified")
        
        return is_universal and has_python_requires
    
    def validate_version_consistency(self) -> bool:
        """Validate version consistency across files."""
        print("\n=== Version Consistency ===")
        
        # Get version from pyproject.toml
        pyproject_path = self.project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        
        import re
        version_match = re.search(r'version = "([^"]+)"', content)
        if not version_match:
            self.log_result("version_in_pyproject", False, "Version not found in pyproject.toml")
            return False
        
        pyproject_version = version_match.group(1)
        self.log_result("version_in_pyproject", True)
        
        # Check version in wheel filename
        wheel_files = list(self.dist_dir.glob("*.whl"))
        if wheel_files:
            wheel_name = wheel_files[0].name
            version_in_wheel = pyproject_version in wheel_name
            self.log_result("version_in_wheel_filename", version_in_wheel,
                           f"Version {pyproject_version} not in wheel name: {wheel_name}")
        else:
            version_in_wheel = False
            self.log_result("version_in_wheel_filename", False, "No wheel file found")
        
        return version_in_wheel
    
    def run_all_validations(self) -> bool:
        """Run all validation tests."""
        print("Starting distribution validation...")
        
        validations = [
            self.validate_package_structure,
            self.validate_package_metadata,
            self.validate_dependencies,
            self.validate_pip_installation,
            self.validate_uvx_installation,
            self.validate_cross_platform_compatibility,
            self.validate_version_consistency,
        ]
        
        all_passed = True
        for validation in validations:
            try:
                result = validation()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"Validation failed with exception: {e}")
                all_passed = False
        
        return all_passed
    
    def generate_report(self, output_file: Optional[Path] = None) -> Dict:
        """Generate validation report."""
        report = {
            "validation_results": self.results,
            "errors": self.errors,
            "summary": {
                "total_tests": len(self.results),
                "passed": sum(1 for result in self.results.values() if result),
                "failed": sum(1 for result in self.results.values() if not result),
                "success_rate": sum(1 for result in self.results.values() if result) / len(self.results) if self.results else 0
            }
        }
        
        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nValidation report saved to: {output_file}")
        
        return report
    
    def print_summary(self) -> None:
        """Print validation summary."""
        print("\n" + "="*50)
        print("VALIDATION SUMMARY")
        print("="*50)
        
        total = len(self.results)
        passed = sum(1 for result in self.results.values() if result)
        failed = total - passed
        
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {passed/total*100:.1f}%" if total > 0 else "No tests run")
        
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        overall_success = failed == 0
        status = "✓ PASS" if overall_success else "✗ FAIL"
        print(f"\nOverall result: {status}")
        
        return overall_success


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Validate databricks-mcp-server distribution"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Project root directory"
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Output file for validation report (JSON)"
    )
    parser.add_argument(
        "--skip-uvx",
        action="store_true",
        help="Skip uvx validation tests"
    )
    
    args = parser.parse_args()
    
    validator = DistributionValidator(args.project_root)
    
    # Skip uvx validation if requested
    if args.skip_uvx:
        validator.validate_uvx_installation = lambda: True
    
    try:
        success = validator.run_all_validations()
        validator.generate_report(args.report)
        validator.print_summary()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()