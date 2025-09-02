#!/usr/bin/env python3
"""
Publication Testing Script

This script helps test the complete publication and setup process
by simulating a fresh user experience.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class PublicationTester:
    """Tests the complete publication and setup process."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.test_results = {}
        self.temp_dir = None
    
    def print_header(self, message: str) -> None:
        """Print a formatted header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{message.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    def print_step(self, message: str) -> None:
        """Print a step message."""
        print(f"{Colors.BOLD}{Colors.BLUE}→ {message}{Colors.END}")
    
    def print_success(self, message: str) -> None:
        """Print a success message."""
        print(f"{Colors.BOLD}{Colors.GREEN}✓ {message}{Colors.END}")
    
    def print_error(self, message: str) -> None:
        """Print an error message."""
        print(f"{Colors.BOLD}{Colors.RED}✗ {message}{Colors.END}")
    
    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        print(f"{Colors.BOLD}{Colors.YELLOW}⚠ {message}{Colors.END}")
    
    def run_command(
        self, 
        cmd: List[str], 
        description: str,
        cwd: Optional[Path] = None,
        timeout: int = 300
    ) -> bool:
        """Run a command and return success status."""
        self.print_step(f"{description}...")
        
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd,
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            
            if result.returncode == 0:
                self.print_success(f"{description} completed")
                if self.verbose and result.stdout:
                    print(f"Output: {result.stdout.strip()}")
                return True
            else:
                self.print_error(f"{description} failed (exit code: {result.returncode})")
                if result.stderr:
                    print(f"Error: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            self.print_error(f"{description} timed out after {timeout}s")
            return False
        except FileNotFoundError:
            self.print_error(f"Command not found: {' '.join(cmd)}")
            return False
        except Exception as e:
            self.print_error(f"{description} failed with exception: {e}")
            return False
    
    def test_prerequisites(self) -> bool:
        """Test that required tools are available."""
        self.print_header("Testing Prerequisites")
        
        tools = [
            (["python", "--version"], "Python"),
            (["git", "--version"], "Git"),
            (["uv", "--version"], "uv (optional but recommended)"),
        ]
        
        all_good = True
        for cmd, name in tools:
            success = self.run_command(cmd, f"Checking {name}")
            if not success and "uv" not in name:
                all_good = False
            elif not success and "uv" in name:
                self.print_warning("uv not found - some features may not work optimally")
        
        self.test_results["prerequisites"] = all_good
        return all_good
    
    def test_fresh_clone(self, repo_url: str) -> bool:
        """Test cloning the repository in a fresh environment."""
        self.print_header("Testing Fresh Repository Clone")
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="databricks_mcp_test_"))
        self.print_step(f"Created temporary directory: {self.temp_dir}")
        
        # Clone repository
        success = self.run_command(
            ["git", "clone", repo_url, "databricks-mcp-server"],
            "Cloning repository",
            cwd=self.temp_dir
        )
        
        if success:
            self.project_dir = self.temp_dir / "databricks-mcp-server"
            self.print_success(f"Repository cloned to: {self.project_dir}")
        
        self.test_results["fresh_clone"] = success
        return success
    
    def test_local_setup(self) -> bool:
        """Test the local setup process."""
        if not hasattr(self, 'project_dir'):
            self.print_error("No project directory available")
            return False
        
        self.print_header("Testing Local Setup Process")
        
        # Test automated setup
        success = self.run_command(
            ["python", "scripts/setup_dev.py", "--quick"],
            "Running automated setup",
            cwd=self.project_dir
        )
        
        if success:
            # Verify setup worked
            success = self.run_command(
                ["python", "-c", "import databricks_mcp_server; print('Import successful')"],
                "Testing package import",
                cwd=self.project_dir
            )
        
        if success:
            # Test CLI command
            success = self.run_command(
                ["python", "-m", "databricks_mcp_server", "--help"],
                "Testing CLI command",
                cwd=self.project_dir
            )
        
        self.test_results["local_setup"] = success
        return success
    
    def test_development_workflows(self) -> bool:
        """Test development workflows."""
        if not hasattr(self, 'project_dir'):
            self.print_error("No project directory available")
            return False
        
        self.print_header("Testing Development Workflows")
        
        workflows = [
            (["python", "scripts/local_test_workflow.py", "--workflow", "quick"], "Quick workflow"),
            (["python", "scripts/dev_test.py", "--workflow", "quick", "--skip-prereq"], "Dev test workflow"),
        ]
        
        success = True
        for cmd, description in workflows:
            result = self.run_command(cmd, description, cwd=self.project_dir, timeout=600)
            success = success and result
        
        self.test_results["development_workflows"] = success
        return success
    
    def test_package_building(self) -> bool:
        """Test package building process."""
        if not hasattr(self, 'project_dir'):
            self.print_error("No project directory available")
            return False
        
        self.print_header("Testing Package Building")
        
        # Install build dependencies
        success = self.run_command(
            ["python", "-m", "pip", "install", "build", "twine"],
            "Installing build dependencies",
            cwd=self.project_dir
        )
        
        if success:
            # Build package
            success = self.run_command(
                ["python", "-m", "build"],
                "Building package",
                cwd=self.project_dir
            )
        
        if success:
            # Check package
            success = self.run_command(
                ["twine", "check", "dist/*"],
                "Checking package metadata",
                cwd=self.project_dir
            )
        
        if success:
            # Test wheel installation in clean environment
            success = self.test_wheel_installation()
        
        self.test_results["package_building"] = success
        return success
    
    def test_wheel_installation(self) -> bool:
        """Test wheel installation in a clean environment."""
        if not hasattr(self, 'project_dir'):
            return False
        
        self.print_step("Testing wheel installation in clean environment")
        
        # Create clean test environment
        test_env_dir = self.temp_dir / "test-wheel-env"
        
        success = self.run_command(
            ["python", "-m", "venv", str(test_env_dir)],
            "Creating test environment"
        )
        
        if success:
            # Determine activation script
            if os.name == 'nt':  # Windows
                activate_script = test_env_dir / "Scripts" / "activate.bat"
                python_exe = test_env_dir / "Scripts" / "python.exe"
            else:  # Unix/macOS
                activate_script = test_env_dir / "bin" / "activate"
                python_exe = test_env_dir / "bin" / "python"
            
            # Find wheel file
            dist_dir = self.project_dir / "dist"
            wheel_files = list(dist_dir.glob("*.whl"))
            
            if wheel_files:
                wheel_file = wheel_files[0]
                
                # Install wheel
                success = self.run_command(
                    [str(python_exe), "-m", "pip", "install", str(wheel_file)],
                    "Installing wheel package"
                )
                
                if success:
                    # Test installed package
                    success = self.run_command(
                        [str(python_exe), "-c", "import databricks_mcp_server; print('Wheel installation successful')"],
                        "Testing installed package"
                    )
                    
                    if success:
                        # Test CLI
                        success = self.run_command(
                            [str(python_exe), "-m", "databricks_mcp_server", "--help"],
                            "Testing CLI from installed package"
                        )
            else:
                self.print_error("No wheel file found")
                success = False
        
        return success
    
    def test_uvx_installation(self) -> bool:
        """Test uvx installation if available."""
        if not hasattr(self, 'project_dir'):
            return False
        
        self.print_header("Testing UVX Installation")
        
        # Check if uvx is available
        uvx_available = self.run_command(
            ["uvx", "--version"],
            "Checking uvx availability"
        )
        
        if not uvx_available:
            self.print_warning("uvx not available, skipping uvx installation test")
            self.test_results["uvx_installation"] = True  # Not a failure
            return True
        
        # Find wheel file
        dist_dir = self.project_dir / "dist"
        wheel_files = list(dist_dir.glob("*.whl"))
        
        if wheel_files:
            wheel_file = wheel_files[0]
            
            # Test uvx installation
            success = self.run_command(
                ["uvx", "--from", str(wheel_file), "databricks-mcp-server", "--help"],
                "Testing uvx installation"
            )
        else:
            self.print_error("No wheel file found for uvx testing")
            success = False
        
        self.test_results["uvx_installation"] = success
        return success
    
    def test_documentation(self) -> bool:
        """Test documentation completeness."""
        if not hasattr(self, 'project_dir'):
            return False
        
        self.print_header("Testing Documentation")
        
        required_docs = [
            "README.md",
            "DEVELOPMENT.md",
            "DEVELOPMENT_SETUP.md",
            "DEVELOPMENT_WORKFLOW.md",
            "CONTRIBUTING.md",
            "PUBLICATION_GUIDE.md",
        ]
        
        success = True
        for doc in required_docs:
            doc_path = self.project_dir / doc
            if doc_path.exists():
                self.print_success(f"Found {doc}")
            else:
                self.print_error(f"Missing {doc}")
                success = False
        
        # Test that key scripts exist
        key_scripts = [
            "scripts/setup_dev.py",
            "scripts/dev_test.py",
            "scripts/local_test_workflow.py",
        ]
        
        for script in key_scripts:
            script_path = self.project_dir / script
            if script_path.exists():
                self.print_success(f"Found {script}")
            else:
                self.print_error(f"Missing {script}")
                success = False
        
        self.test_results["documentation"] = success
        return success
    
    def cleanup(self) -> None:
        """Clean up temporary directories."""
        if self.temp_dir and self.temp_dir.exists():
            self.print_step(f"Cleaning up temporary directory: {self.temp_dir}")
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def print_summary(self) -> bool:
        """Print test summary."""
        self.print_header("Test Summary")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"Tests passed: {passed_tests}/{total_tests}")
        print()
        
        for test_name, result in self.test_results.items():
            status = "✓" if result else "✗"
            color = Colors.GREEN if result else Colors.RED
            print(f"{color}{status} {test_name.replace('_', ' ').title()}{Colors.END}")
        
        print()
        
        if all(self.test_results.values()):
            self.print_success("All tests passed! 🎉")
            self.print_success("The project is ready for publication and use!")
            return True
        else:
            self.print_error("Some tests failed! 😞")
            self.print_error("Please fix the issues before publishing.")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test the complete publication and setup process"
    )
    parser.add_argument(
        "repo_url",
        help="Repository URL to test (e.g., https://github.com/username/databricks-mcp-server.git)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--skip-clone",
        action="store_true",
        help="Skip cloning (test current directory)"
    )
    parser.add_argument(
        "--skip-uvx",
        action="store_true",
        help="Skip uvx installation testing"
    )
    
    args = parser.parse_args()
    
    tester = PublicationTester(verbose=args.verbose)
    
    try:
        print(f"{Colors.BOLD}{Colors.BLUE}Databricks MCP Server - Publication Testing{Colors.END}")
        print("=" * 70)
        
        success = True
        
        # Test prerequisites
        success &= tester.test_prerequisites()
        
        # Test fresh clone or use current directory
        if not args.skip_clone:
            success &= tester.test_fresh_clone(args.repo_url)
        else:
            tester.project_dir = Path.cwd()
            tester.print_step(f"Using current directory: {tester.project_dir}")
        
        # Test setup process
        if success:
            success &= tester.test_local_setup()
        
        # Test development workflows
        if success:
            success &= tester.test_development_workflows()
        
        # Test package building
        if success:
            success &= tester.test_package_building()
        
        # Test uvx installation
        if success and not args.skip_uvx:
            success &= tester.test_uvx_installation()
        
        # Test documentation
        success &= tester.test_documentation()
        
        # Print summary
        overall_success = tester.print_summary()
        
        return 0 if overall_success else 1
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Testing interrupted by user{Colors.END}")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}Testing failed with exception: {e}{Colors.END}")
        return 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())