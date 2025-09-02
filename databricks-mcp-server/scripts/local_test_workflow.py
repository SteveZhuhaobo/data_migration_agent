#!/usr/bin/env python3
"""
Local Testing Workflow Script

This script provides various testing workflows for local development,
allowing developers to run the same checks that run in CI/CD locally.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


class TestWorkflow:
    """Manages local testing workflows."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: Dict[str, bool] = {}
        self.timings: Dict[str, float] = {}
    
    def print_header(self, message: str) -> None:
        """Print a formatted header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{message.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    def print_step(self, message: str) -> None:
        """Print a step message."""
        print(f"{Colors.BOLD}{Colors.CYAN}→ {message}{Colors.END}")
    
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
        timeout: int = 300,
        capture_output: bool = False
    ) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        self.print_step(f"{description}...")
        
        start_time = time.time()
        
        try:
            if capture_output:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=timeout
                )
                output = result.stdout + result.stderr
            else:
                result = subprocess.run(cmd, timeout=timeout)
                output = ""
            
            elapsed = time.time() - start_time
            self.timings[description] = elapsed
            
            if result.returncode == 0:
                self.print_success(f"{description} completed in {elapsed:.1f}s")
                self.results[description] = True
                return True, output
            else:
                self.print_error(f"{description} failed (exit code: {result.returncode})")
                if capture_output and output and self.verbose:
                    print(f"Output: {output}")
                self.results[description] = False
                return False, output
                
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            self.timings[description] = elapsed
            self.print_error(f"{description} timed out after {timeout}s")
            self.results[description] = False
            return False, ""
        except FileNotFoundError:
            self.print_error(f"Command not found: {' '.join(cmd)}")
            self.results[description] = False
            return False, ""
        except Exception as e:
            elapsed = time.time() - start_time
            self.timings[description] = elapsed
            self.print_error(f"{description} failed with exception: {e}")
            self.results[description] = False
            return False, str(e)
    
    def check_prerequisites(self) -> bool:
        """Check that required tools are available."""
        self.print_header("Prerequisites Check")
        
        tools = [
            (["python", "--version"], "Python"),
            (["uv", "--version"], "uv"),
            (["git", "--version"], "Git"),
        ]
        
        all_good = True
        for cmd, name in tools:
            success, output = self.run_command(cmd, f"Checking {name}", capture_output=True)
            if success and self.verbose:
                print(f"  {output.strip()}")
            all_good = all_good and success
        
        return all_good
    
    def setup_environment(self) -> bool:
        """Set up development environment."""
        self.print_header("Environment Setup")
        
        # Check if virtual environment exists
        venv_path = Path(".venv")
        if venv_path.exists():
            self.print_success("Virtual environment already exists")
        else:
            success, _ = self.run_command(["uv", "venv"], "Creating virtual environment")
            if not success:
                return False
        
        # Install dependencies
        return self.run_command(
            ["uv", "pip", "install", "-e", ".[dev]"], 
            "Installing development dependencies"
        )[0]
    
    def run_code_quality_checks(self, fix: bool = False) -> bool:
        """Run code quality checks."""
        self.print_header("Code Quality Checks")
        
        success = True
        
        # Formatting
        if fix:
            success &= self.run_command(
                ["uv", "run", "black", "src", "tests", "scripts"], 
                "Formatting code with black"
            )[0]
            success &= self.run_command(
                ["uv", "run", "isort", "src", "tests", "scripts"], 
                "Sorting imports with isort"
            )[0]
        else:
            success &= self.run_command(
                ["uv", "run", "black", "--check", "src", "tests", "scripts"], 
                "Checking code formatting"
            )[0]
            success &= self.run_command(
                ["uv", "run", "isort", "--check-only", "src", "tests", "scripts"], 
                "Checking import sorting"
            )[0]
        
        # Linting
        success &= self.run_command(
            ["uv", "run", "flake8", "src", "tests", "scripts"], 
            "Running flake8 linting"
        )[0]
        
        # Type checking
        success &= self.run_command(
            ["uv", "run", "mypy", "src"], 
            "Running mypy type checking"
        )[0]
        
        return success
    
    def run_security_checks(self) -> bool:
        """Run security checks."""
        self.print_header("Security Checks")
        
        success = True
        
        # Install security tools
        success &= self.run_command(
            ["uv", "pip", "install", "pip-audit", "bandit"], 
            "Installing security tools"
        )[0]
        
        if success:
            # Run pip-audit
            success &= self.run_command(
                ["uv", "run", "pip-audit"], 
                "Running pip-audit security scan"
            )[0]
            
            # Run bandit
            success &= self.run_command(
                ["uv", "run", "bandit", "-r", "src/"], 
                "Running bandit security scan"
            )[0]
        
        return success
    
    def run_tests(self, test_type: str = "all", coverage: bool = True) -> bool:
        """Run tests."""
        self.print_header(f"Running Tests ({test_type})")
        
        cmd = ["uv", "run", "pytest"]
        
        if test_type == "unit":
            cmd.extend(["-m", "unit"])
        elif test_type == "integration":
            cmd.extend(["-m", "integration"])
        elif test_type == "fast":
            cmd.extend(["-m", "not slow"])
        elif test_type == "slow":
            cmd.extend(["-m", "slow"])
        elif test_type == "all":
            pass  # Run all tests
        else:
            self.print_error(f"Unknown test type: {test_type}")
            return False
        
        if coverage:
            cmd.extend([
                "--cov=databricks_mcp_server", 
                "--cov-report=term-missing",
                "--cov-report=html"
            ])
        
        cmd.extend(["-v", "tests/"])
        
        return self.run_command(cmd, f"Running {test_type} tests", timeout=600)[0]
    
    def run_performance_tests(self) -> bool:
        """Run performance tests."""
        self.print_header("Performance Tests")
        
        success = True
        
        # Test startup time
        success &= self.run_command([
            "python", "-c", 
            """
import time
import subprocess
start = time.time()
result = subprocess.run(['databricks-mcp-server', '--help'], 
                       capture_output=True, timeout=30)
elapsed = time.time() - start
print(f'Startup time: {elapsed:.2f}s')
if elapsed > 5.0:
    print('WARNING: Startup time is slow')
    exit(1)
print('Startup performance acceptable')
            """
        ], "Testing startup performance")[0]
        
        # Test memory usage
        success &= self.run_command([
            "python", "-c",
            """
import subprocess
import psutil
import time
proc = subprocess.Popen(['databricks-mcp-server', '--help'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(1)
try:
    process = psutil.Process(proc.pid)
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f'Memory usage: {memory_mb:.1f} MB')
    if memory_mb > 100:
        print('WARNING: High memory usage')
    else:
        print('Memory usage acceptable')
except psutil.NoSuchProcess:
    print('Process completed quickly')
finally:
    proc.terminate()
    proc.wait()
            """
        ], "Testing memory usage")[0]
        
        return success
    
    def build_and_test_package(self) -> bool:
        """Build and test package."""
        self.print_header("Package Build and Test")
        
        success = True
        
        # Clean previous builds
        success &= self.run_command([
            "python", "-c", 
            "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', 'src/databricks_mcp_server.egg-info']]"
        ], "Cleaning build artifacts")[0]
        
        # Build package
        success &= self.run_command(
            ["python", "-m", "build"], 
            "Building package"
        )[0]
        
        # Check package
        success &= self.run_command(
            ["twine", "check", "dist/*"], 
            "Checking package metadata"
        )[0]
        
        # Test installation
        if success:
            success &= self.run_command(
                ["python", "scripts/build.py", "--test-install"], 
                "Testing pip installation"
            )[0]
            
            # Test uvx installation if available
            try:
                subprocess.run(["uvx", "--version"], capture_output=True, check=True)
                success &= self.run_command(
                    ["python", "scripts/build.py", "--test-uvx"], 
                    "Testing uvx installation"
                )[0]
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.print_warning("uvx not available, skipping uvx installation test")
        
        return success
    
    def run_integration_suite(self) -> bool:
        """Run comprehensive integration tests."""
        self.print_header("Integration Test Suite")
        
        return self.run_command(
            ["python", "run_integration_tests.py", "--include-slow"], 
            "Running integration test suite",
            timeout=900
        )[0]
    
    def validate_distribution(self) -> bool:
        """Validate distribution package."""
        self.print_header("Distribution Validation")
        
        return self.run_command(
            ["python", "scripts/validate_distribution.py"], 
            "Running distribution validation"
        )[0]
    
    def run_cross_platform_tests(self) -> bool:
        """Run cross-platform compatibility tests."""
        self.print_header("Cross-Platform Tests")
        
        return self.run_command(
            ["python", "test_cross_platform.py", "--verbose"], 
            "Running cross-platform tests"
        )[0]
    
    def print_summary(self) -> None:
        """Print workflow summary."""
        self.print_header("Workflow Summary")
        
        total_time = sum(self.timings.values())
        passed = sum(1 for result in self.results.values() if result)
        total = len(self.results)
        
        print(f"Total execution time: {total_time:.1f}s")
        print(f"Tests passed: {passed}/{total}")
        print()
        
        # Print detailed results
        for step, result in self.results.items():
            timing = self.timings.get(step, 0)
            status = "✓" if result else "✗"
            color = Colors.GREEN if result else Colors.RED
            print(f"{color}{status} {step} ({timing:.1f}s){Colors.END}")
        
        print()
        
        if all(self.results.values()):
            self.print_success("All checks passed! 🎉")
            return True
        else:
            self.print_error("Some checks failed! 😞")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Local testing workflow for databricks-mcp-server"
    )
    
    # Workflow presets
    parser.add_argument(
        "--workflow", 
        choices=["quick", "standard", "full", "ci", "release"],
        default="standard",
        help="Predefined workflow to run"
    )
    
    # Individual components
    parser.add_argument("--setup", action="store_true", help="Set up environment")
    parser.add_argument("--prereq", action="store_true", help="Check prerequisites")
    parser.add_argument("--format", action="store_true", help="Format code")
    parser.add_argument("--quality", action="store_true", help="Run code quality checks")
    parser.add_argument("--security", action="store_true", help="Run security checks")
    parser.add_argument("--test", choices=["unit", "integration", "fast", "slow", "all"], help="Run tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--build", action="store_true", help="Build and test package")
    parser.add_argument("--integration-suite", action="store_true", help="Run integration test suite")
    parser.add_argument("--validate", action="store_true", help="Validate distribution")
    parser.add_argument("--cross-platform", action="store_true", help="Run cross-platform tests")
    
    # Options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--fix", action="store_true", help="Fix formatting issues")
    
    args = parser.parse_args()
    
    workflow = TestWorkflow(verbose=args.verbose)
    
    print(f"{Colors.BOLD}{Colors.BLUE}Databricks MCP Server - Local Testing Workflow{Colors.END}")
    print("=" * 70)
    
    success = True
    
    # Handle individual components
    if args.prereq:
        success &= workflow.check_prerequisites()
    
    if args.setup:
        success &= workflow.setup_environment()
    
    if args.format:
        success &= workflow.run_code_quality_checks(fix=args.fix)
    
    if args.quality:
        success &= workflow.run_code_quality_checks(fix=False)
    
    if args.security:
        success &= workflow.run_security_checks()
    
    if args.test:
        success &= workflow.run_tests(args.test, coverage=not args.no_coverage)
    
    if args.performance:
        success &= workflow.run_performance_tests()
    
    if args.build:
        success &= workflow.build_and_test_package()
    
    if args.integration_suite:
        success &= workflow.run_integration_suite()
    
    if args.validate:
        success &= workflow.validate_distribution()
    
    if args.cross_platform:
        success &= workflow.run_cross_platform_tests()
    
    # Handle workflow presets
    if args.workflow == "quick":
        workflow.print_header("Quick Development Workflow")
        success &= workflow.setup_environment()
        success &= workflow.run_code_quality_checks(fix=False)
        success &= workflow.run_tests("fast", coverage=not args.no_coverage)
        
    elif args.workflow == "standard":
        workflow.print_header("Standard Development Workflow")
        success &= workflow.setup_environment()
        success &= workflow.run_code_quality_checks(fix=False)
        success &= workflow.run_tests("unit", coverage=not args.no_coverage)
        success &= workflow.run_tests("integration", coverage=False)
        
    elif args.workflow == "full":
        workflow.print_header("Full Development Workflow")
        success &= workflow.setup_environment()
        success &= workflow.run_code_quality_checks(fix=False)
        success &= workflow.run_security_checks()
        success &= workflow.run_tests("all", coverage=not args.no_coverage)
        success &= workflow.build_and_test_package()
        
    elif args.workflow == "ci":
        workflow.print_header("CI Simulation Workflow")
        success &= workflow.check_prerequisites()
        success &= workflow.setup_environment()
        success &= workflow.run_code_quality_checks(fix=False)
        success &= workflow.run_security_checks()
        success &= workflow.run_tests("all", coverage=not args.no_coverage)
        success &= workflow.run_performance_tests()
        success &= workflow.build_and_test_package()
        success &= workflow.validate_distribution()
        
    elif args.workflow == "release":
        workflow.print_header("Release Preparation Workflow")
        success &= workflow.check_prerequisites()
        success &= workflow.setup_environment()
        success &= workflow.run_code_quality_checks(fix=False)
        success &= workflow.run_security_checks()
        success &= workflow.run_tests("all", coverage=not args.no_coverage)
        success &= workflow.run_performance_tests()
        success &= workflow.build_and_test_package()
        success &= workflow.validate_distribution()
        success &= workflow.run_integration_suite()
        success &= workflow.run_cross_platform_tests()
    
    # Print summary
    workflow.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())