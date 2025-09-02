#!/usr/bin/env python3
"""
Development Testing Script

This script provides a comprehensive testing workflow for local development,
including code quality checks, testing, and package validation.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(message: str) -> None:
    """Print a formatted header message."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_step(message: str) -> None:
    """Print a formatted step message."""
    print(f"{Colors.BOLD}{Colors.CYAN}→ {message}{Colors.END}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.BOLD}{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.BOLD}{Colors.RED}✗ {message}{Colors.END}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.BOLD}{Colors.YELLOW}⚠ {message}{Colors.END}")


def run_command(
    cmd: List[str], 
    description: str, 
    cwd: Optional[Path] = None,
    capture_output: bool = False,
    timeout: int = 300
) -> bool:
    """
    Run a command and return success status.
    
    Args:
        cmd: Command to run as list of strings
        description: Description of what the command does
        cwd: Working directory for command
        capture_output: Whether to capture output
        timeout: Command timeout in seconds
        
    Returns:
        True if command succeeded, False otherwise
    """
    print_step(f"{description}...")
    
    try:
        start_time = time.time()
        
        if capture_output:
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
        else:
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                timeout=timeout
            )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            print_success(f"{description} completed in {elapsed:.1f}s")
            return True
        else:
            print_error(f"{description} failed (exit code: {result.returncode})")
            if capture_output and result.stderr:
                print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print_error(f"{description} timed out after {timeout}s")
        return False
    except FileNotFoundError:
        print_error(f"Command not found: {' '.join(cmd)}")
        return False
    except Exception as e:
        print_error(f"{description} failed with exception: {e}")
        return False


def check_prerequisites() -> bool:
    """Check that required tools are available."""
    print_header("Checking Prerequisites")
    
    tools = [
        (["python", "--version"], "Python"),
        (["uv", "--version"], "uv"),
        (["git", "--version"], "Git"),
    ]
    
    all_good = True
    for cmd, name in tools:
        if not run_command(cmd, f"Checking {name}", capture_output=True):
            all_good = False
    
    return all_good


def setup_environment(force: bool = False) -> bool:
    """Set up development environment."""
    print_header("Setting Up Development Environment")
    
    # Check if virtual environment exists
    venv_path = Path(".venv")
    if venv_path.exists() and not force:
        print_step("Virtual environment already exists")
        print_success("Using existing virtual environment")
    else:
        if force and venv_path.exists():
            print_step("Removing existing virtual environment")
            import shutil
            shutil.rmtree(venv_path)
        
        if not run_command(["uv", "venv"], "Creating virtual environment"):
            return False
    
    # Install development dependencies
    return run_command(
        ["uv", "pip", "install", "-e", ".[dev]"], 
        "Installing development dependencies"
    )


def run_code_quality_checks(fix: bool = False) -> bool:
    """Run code quality checks."""
    print_header("Code Quality Checks")
    
    success = True
    
    # Formatting
    if fix:
        success &= run_command(
            ["uv", "run", "black", "src", "tests", "scripts"], 
            "Formatting code with black"
        )
        success &= run_command(
            ["uv", "run", "isort", "src", "tests", "scripts"], 
            "Sorting imports with isort"
        )
    else:
        success &= run_command(
            ["uv", "run", "black", "--check", "src", "tests", "scripts"], 
            "Checking code formatting"
        )
        success &= run_command(
            ["uv", "run", "isort", "--check-only", "src", "tests", "scripts"], 
            "Checking import sorting"
        )
    
    # Linting
    success &= run_command(
        ["uv", "run", "flake8", "src", "tests", "scripts"], 
        "Running flake8 linting"
    )
    
    # Type checking
    success &= run_command(
        ["uv", "run", "mypy", "src"], 
        "Running mypy type checking"
    )
    
    return success


def run_tests(test_type: str = "all", coverage: bool = True) -> bool:
    """Run tests."""
    print_header(f"Running Tests ({test_type})")
    
    cmd = ["uv", "run", "pytest"]
    
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    elif test_type == "all":
        pass  # Run all tests
    else:
        print_error(f"Unknown test type: {test_type}")
        return False
    
    if coverage:
        cmd.extend(["--cov=databricks_mcp_server", "--cov-report=term-missing"])
    
    cmd.extend(["-v", "tests/"])
    
    return run_command(cmd, f"Running {test_type} tests", timeout=600)


def build_package() -> bool:
    """Build the package."""
    print_header("Building Package")
    
    # Clean previous builds
    success = run_command(
        ["python", "-c", "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', 'src/databricks_mcp_server.egg-info']]"],
        "Cleaning build artifacts"
    )
    
    # Build package
    success &= run_command(
        ["python", "-m", "build"], 
        "Building package"
    )
    
    # Check package
    success &= run_command(
        ["twine", "check", "dist/*"], 
        "Checking package metadata"
    )
    
    return success


def test_installation() -> bool:
    """Test package installation."""
    print_header("Testing Package Installation")
    
    success = True
    
    # Test pip installation
    success &= run_command(
        ["python", "scripts/build.py", "--test-install"], 
        "Testing pip installation"
    )
    
    # Test uvx installation (if uvx is available)
    try:
        subprocess.run(["uvx", "--version"], capture_output=True, check=True)
        success &= run_command(
            ["python", "scripts/build.py", "--test-uvx"], 
            "Testing uvx installation"
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("uvx not available, skipping uvx installation test")
    
    return success


def validate_distribution() -> bool:
    """Validate the distribution package."""
    print_header("Validating Distribution")
    
    return run_command(
        ["python", "scripts/validate_distribution.py"], 
        "Running distribution validation"
    )


def run_integration_tests() -> bool:
    """Run comprehensive integration tests."""
    print_header("Running Integration Test Suite")
    
    return run_command(
        ["python", "run_integration_tests.py", "--include-slow"], 
        "Running integration test suite",
        timeout=900
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Development testing workflow for databricks-mcp-server"
    )
    
    # Workflow options
    parser.add_argument(
        "--workflow", 
        choices=["quick", "full", "ci", "release"],
        default="quick",
        help="Testing workflow to run"
    )
    
    # Individual step options
    parser.add_argument("--setup", action="store_true", help="Set up development environment")
    parser.add_argument("--setup-force", action="store_true", help="Force recreate development environment")
    parser.add_argument("--format", action="store_true", help="Format code")
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument("--test", choices=["unit", "integration", "fast", "all"], help="Run specific tests")
    parser.add_argument("--build", action="store_true", help="Build package")
    parser.add_argument("--test-install", action="store_true", help="Test package installation")
    parser.add_argument("--validate", action="store_true", help="Validate distribution")
    parser.add_argument("--integration", action="store_true", help="Run integration test suite")
    
    # Options
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--skip-prereq", action="store_true", help="Skip prerequisite checks")
    
    args = parser.parse_args()
    
    # Check prerequisites unless skipped
    if not args.skip_prereq:
        if not check_prerequisites():
            print_error("Prerequisites check failed")
            return 1
    
    success = True
    
    # Handle individual steps
    if args.setup or args.setup_force:
        success &= setup_environment(force=args.setup_force)
    
    if args.format:
        success &= run_code_quality_checks(fix=True)
    
    if args.lint:
        success &= run_code_quality_checks(fix=False)
    
    if args.test:
        success &= run_tests(args.test, coverage=not args.no_coverage)
    
    if args.build:
        success &= build_package()
    
    if args.test_install:
        success &= test_installation()
    
    if args.validate:
        success &= validate_distribution()
    
    if args.integration:
        success &= run_integration_tests()
    
    # Handle workflows
    if args.workflow == "quick":
        print_header("Quick Development Workflow")
        success &= setup_environment()
        success &= run_code_quality_checks(fix=False)
        success &= run_tests("fast", coverage=not args.no_coverage)
        
    elif args.workflow == "full":
        print_header("Full Development Workflow")
        success &= setup_environment()
        success &= run_code_quality_checks(fix=False)
        success &= run_tests("all", coverage=not args.no_coverage)
        success &= build_package()
        success &= test_installation()
        
    elif args.workflow == "ci":
        print_header("CI Simulation Workflow")
        success &= setup_environment()
        success &= run_code_quality_checks(fix=False)
        success &= run_tests("all", coverage=not args.no_coverage)
        success &= build_package()
        success &= test_installation()
        success &= validate_distribution()
        
    elif args.workflow == "release":
        print_header("Release Preparation Workflow")
        success &= setup_environment()
        success &= run_code_quality_checks(fix=False)
        success &= run_tests("all", coverage=not args.no_coverage)
        success &= build_package()
        success &= test_installation()
        success &= validate_distribution()
        success &= run_integration_tests()
    
    # Print final result
    print_header("Development Workflow Complete")
    
    if success:
        print_success("All steps completed successfully!")
        print(f"\n{Colors.BOLD}{Colors.GREEN}✓ Ready for development/deployment{Colors.END}")
        return 0
    else:
        print_error("Some steps failed!")
        print(f"\n{Colors.BOLD}{Colors.RED}✗ Please fix issues before proceeding{Colors.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())