#!/usr/bin/env python3
"""
Development Environment Setup Script

This script sets up a complete development environment for the databricks-mcp-server project.
It handles dependency installation, tool configuration, and environment validation.
"""

import argparse
import os
import subprocess
import sys
import shutil
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


def print_step(message: str) -> None:
    """Print a formatted step message."""
    print(f"{Colors.BOLD}{Colors.BLUE}→ {message}{Colors.END}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.BOLD}{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.BOLD}{Colors.RED}✗ {message}{Colors.END}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.BOLD}{Colors.YELLOW}⚠ {message}{Colors.END}")


def run_command(cmd: List[str], description: str, check: bool = True) -> bool:
    """Run a command and return success status."""
    print_step(f"{description}...")
    
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"{description} completed")
            return True
        else:
            print_error(f"{description} failed: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        print_error(f"{description} failed: {e}")
        return False
    except FileNotFoundError:
        print_error(f"Command not found: {' '.join(cmd)}")
        return False


def check_prerequisites() -> bool:
    """Check that required tools are available."""
    print(f"\n{Colors.BOLD}Checking Prerequisites{Colors.END}")
    print("=" * 50)
    
    tools = [
        (["python", "--version"], "Python 3.8+"),
        (["git", "--version"], "Git"),
        (["uv", "--version"], "uv package manager"),
    ]
    
    all_good = True
    for cmd, name in tools:
        if run_command(cmd, f"Checking {name}", check=False):
            # Check Python version specifically
            if cmd[0] == "python":
                result = subprocess.run(cmd, capture_output=True, text=True)
                version_line = result.stdout.strip()
                print(f"  Found: {version_line}")
        else:
            all_good = False
            if cmd[0] == "uv":
                print_warning("uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh")
    
    return all_good


def setup_virtual_environment(force: bool = False) -> bool:
    """Set up Python virtual environment."""
    print(f"\n{Colors.BOLD}Setting Up Virtual Environment{Colors.END}")
    print("=" * 50)
    
    venv_path = Path(".venv")
    
    if venv_path.exists():
        if force:
            print_step("Removing existing virtual environment")
            shutil.rmtree(venv_path)
        else:
            print_success("Virtual environment already exists")
            return True
    
    return run_command(["uv", "venv"], "Creating virtual environment")


def install_dependencies(dev: bool = True) -> bool:
    """Install project dependencies."""
    print(f"\n{Colors.BOLD}Installing Dependencies{Colors.END}")
    print("=" * 50)
    
    if dev:
        cmd = ["uv", "pip", "install", "-e", ".[dev]"]
        description = "Installing development dependencies"
    else:
        cmd = ["uv", "pip", "install", "-e", "."]
        description = "Installing project dependencies"
    
    return run_command(cmd, description)


def setup_pre_commit_hooks() -> bool:
    """Set up pre-commit hooks."""
    print(f"\n{Colors.BOLD}Setting Up Pre-commit Hooks{Colors.END}")
    print("=" * 50)
    
    if not Path(".pre-commit-config.yaml").exists():
        print_warning("No pre-commit configuration found, skipping")
        return True
    
    success = run_command(["uv", "pip", "install", "pre-commit"], "Installing pre-commit")
    if success:
        success = run_command(["pre-commit", "install"], "Installing pre-commit hooks")
    
    return success


def validate_installation() -> bool:
    """Validate that the installation works correctly."""
    print(f"\n{Colors.BOLD}Validating Installation{Colors.END}")
    print("=" * 50)
    
    # Test that the package can be imported
    success = run_command(
        ["python", "-c", "import databricks_mcp_server; print('Package import successful')"],
        "Testing package import"
    )
    
    # Test that the CLI works
    if success:
        success = run_command(
            ["databricks-mcp-server", "--help"],
            "Testing CLI command"
        )
    
    # Test that development tools work
    if success:
        success = run_command(
            ["uv", "run", "pytest", "--version"],
            "Testing pytest"
        )
    
    return success


def run_initial_tests() -> bool:
    """Run initial test suite to verify setup."""
    print(f"\n{Colors.BOLD}Running Initial Tests{Colors.END}")
    print("=" * 50)
    
    # Run unit tests only for quick validation
    return run_command(
        ["uv", "run", "pytest", "tests/", "-m", "unit", "-v", "--tb=short"],
        "Running unit tests"
    )


def print_next_steps() -> None:
    """Print next steps for development."""
    print(f"\n{Colors.BOLD}{Colors.GREEN}Development Environment Ready!{Colors.END}")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':  # Windows
        print("   .venv\\Scripts\\activate")
    else:  # Unix/macOS
        print("   source .venv/bin/activate")
    
    print("\n2. Run development workflow:")
    print("   make dev-quick          # Quick development checks")
    print("   make dev-full           # Full development workflow")
    print("   python scripts/dev_test.py --help  # See all options")
    
    print("\n3. Common development commands:")
    print("   make test               # Run unit tests")
    print("   make lint               # Run code quality checks")
    print("   make format             # Format code")
    print("   make build              # Build package")
    
    print("\n4. Documentation:")
    print("   README.md               # Usage and installation")
    print("   DEVELOPMENT.md          # Development guide")
    print("   CONTRIBUTING.md         # Contribution guidelines")
    
    print(f"\n{Colors.BOLD}Happy coding! 🚀{Colors.END}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Set up development environment for databricks-mcp-server"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force recreate virtual environment"
    )
    parser.add_argument(
        "--no-dev", 
        action="store_true", 
        help="Skip development dependencies"
    )
    parser.add_argument(
        "--no-hooks", 
        action="store_true", 
        help="Skip pre-commit hooks setup"
    )
    parser.add_argument(
        "--no-test", 
        action="store_true", 
        help="Skip initial test run"
    )
    parser.add_argument(
        "--quick", 
        action="store_true", 
        help="Quick setup (skip validation and tests)"
    )
    
    args = parser.parse_args()
    
    print(f"{Colors.BOLD}{Colors.BLUE}Databricks MCP Server - Development Setup{Colors.END}")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites check failed. Please install missing tools.")
        return 1
    
    # Set up virtual environment
    if not setup_virtual_environment(force=args.force):
        print_error("Failed to set up virtual environment")
        return 1
    
    # Install dependencies
    if not install_dependencies(dev=not args.no_dev):
        print_error("Failed to install dependencies")
        return 1
    
    # Set up pre-commit hooks
    if not args.no_hooks:
        if not setup_pre_commit_hooks():
            print_warning("Pre-commit hooks setup failed, continuing...")
    
    # Validate installation
    if not args.quick:
        if not validate_installation():
            print_error("Installation validation failed")
            return 1
        
        # Run initial tests
        if not args.no_test:
            if not run_initial_tests():
                print_warning("Initial tests failed, but setup is complete")
    
    # Print next steps
    print_next_steps()
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 