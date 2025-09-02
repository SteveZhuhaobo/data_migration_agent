#!/usr/bin/env python3
"""
Build script for databricks-mcp-server package.

This script provides a convenient way to build and test the package locally.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(cmd: list, cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if check and result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    
    return result


def clean_build_artifacts(project_root: Path) -> None:
    """Clean build artifacts."""
    print("Cleaning build artifacts...")
    
    artifacts = [
        "build",
        "dist",
        "*.egg-info",
        "__pycache__",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        "coverage.xml"
    ]
    
    for pattern in artifacts:
        if "*" in pattern:
            # Handle glob patterns
            for path in project_root.rglob(pattern.replace("*", "")):
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                elif path.is_file():
                    path.unlink(missing_ok=True)
        else:
            path = project_root / pattern
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            elif path.is_file():
                path.unlink(missing_ok=True)


def run_linting(project_root: Path) -> bool:
    """Run linting checks."""
    print("Running linting checks...")
    
    commands = [
        ["uv", "run", "black", "--check", "src", "tests"],
        ["uv", "run", "isort", "--check-only", "src", "tests"],
        ["uv", "run", "flake8", "src", "tests"],
        ["uv", "run", "mypy", "src"]
    ]
    
    all_passed = True
    for cmd in commands:
        result = run_command(cmd, cwd=project_root, check=False)
        if result.returncode != 0:
            all_passed = False
    
    return all_passed


def run_tests(project_root: Path, test_type: str = "unit") -> bool:
    """Run tests."""
    print(f"Running {test_type} tests...")
    
    cmd = ["uv", "run", "pytest", "tests/"]
    
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "all":
        pass  # Run all tests
    
    cmd.extend(["--cov-report=term-missing", "--cov-report=html"])
    
    result = run_command(cmd, cwd=project_root, check=False)
    return result.returncode == 0


def build_package(project_root: Path) -> bool:
    """Build the package."""
    print("Building package...")
    
    # Install build dependencies
    run_command(["python", "-m", "pip", "install", "--upgrade", "build", "twine"], cwd=project_root)
    
    # Build package
    result = run_command(["python", "-m", "build"], cwd=project_root, check=False)
    if result.returncode != 0:
        return False
    
    # Check package
    result = run_command(["twine", "check", "dist/*"], cwd=project_root, check=False)
    return result.returncode == 0


def test_package_installation(project_root: Path) -> bool:
    """Test package installation in a clean environment."""
    print("Testing package installation...")
    
    dist_dir = project_root / "dist"
    if not dist_dir.exists():
        print("No dist directory found. Build the package first.")
        return False
    
    # Find the wheel file
    wheel_files = list(dist_dir.glob("*.whl"))
    if not wheel_files:
        print("No wheel file found in dist directory.")
        return False
    
    wheel_file = wheel_files[0]
    print(f"Testing installation of: {wheel_file}")
    
    # Create temporary virtual environment
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_dir = Path(temp_dir) / "test_env"
        
        # Create virtual environment
        result = run_command(["python", "-m", "venv", str(venv_dir)], check=False)
        if result.returncode != 0:
            return False
        
        # Determine activation script
        if sys.platform == "win32":
            activate_script = venv_dir / "Scripts" / "activate.bat"
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            activate_script = venv_dir / "bin" / "activate"
            python_exe = venv_dir / "bin" / "python"
        
        # Install package
        result = run_command([str(python_exe), "-m", "pip", "install", str(wheel_file)], check=False)
        if result.returncode != 0:
            return False
        
        # Test entry point
        if sys.platform == "win32":
            entry_point = venv_dir / "Scripts" / "databricks-mcp-server.exe"
        else:
            entry_point = venv_dir / "bin" / "databricks-mcp-server"
        
        if not entry_point.exists():
            print(f"Entry point not found: {entry_point}")
            return False
        
        # Test help command
        result = run_command([str(entry_point), "--help"], check=False)
        if result.returncode != 0:
            return False
        
        # Test import
        result = run_command([
            str(python_exe), "-c", 
            "import databricks_mcp_server; print('Package imported successfully')"
        ], check=False)
        
        return result.returncode == 0


def test_uvx_installation(project_root: Path) -> bool:
    """Test uvx installation."""
    print("Testing uvx installation...")
    
    dist_dir = project_root / "dist"
    wheel_files = list(dist_dir.glob("*.whl"))
    if not wheel_files:
        print("No wheel file found for uvx testing.")
        return False
    
    wheel_file = wheel_files[0]
    
    # Test uvx installation
    result = run_command([
        "uvx", "--from", str(wheel_file), "databricks-mcp-server", "--help"
    ], check=False)
    
    return result.returncode == 0


def validate_distribution(project_root: Path) -> bool:
    """Run distribution validation."""
    print("Running distribution validation...")
    
    validation_script = project_root / "scripts" / "validate_distribution.py"
    if not validation_script.exists():
        print("Distribution validation script not found.")
        return False
    
    result = run_command([sys.executable, str(validation_script)], cwd=project_root, check=False)
    return result.returncode == 0


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Build databricks-mcp-server package")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument("--test", choices=["unit", "integration", "all"], help="Run tests")
    parser.add_argument("--build", action="store_true", help="Build package")
    parser.add_argument("--test-install", action="store_true", help="Test package installation")
    parser.add_argument("--test-uvx", action="store_true", help="Test uvx installation")
    parser.add_argument("--validate", action="store_true", help="Validate distribution")
    parser.add_argument("--all", action="store_true", help="Run all steps")
    parser.add_argument("--skip-tests", action="store_true", help="Skip tests when running --all")
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    
    if not any([args.clean, args.lint, args.test, args.build, args.test_install, args.test_uvx, args.validate, args.all]):
        parser.print_help()
        return
    
    success = True
    
    try:
        if args.all or args.clean:
            clean_build_artifacts(project_root)
        
        if args.all or args.lint:
            if not run_linting(project_root):
                print("Linting checks failed!")
                success = False
        
        if (args.all and not args.skip_tests) or args.test:
            test_type = args.test if args.test else "unit"
            if not run_tests(project_root, test_type):
                print("Tests failed!")
                success = False
        
        if args.all or args.build:
            if not build_package(project_root):
                print("Package build failed!")
                success = False
        
        if args.all or args.test_install:
            if not test_package_installation(project_root):
                print("Package installation test failed!")
                success = False
        
        if args.all or args.test_uvx:
            if not test_uvx_installation(project_root):
                print("uvx installation test failed!")
                success = False
        
        if args.all or args.validate:
            if not validate_distribution(project_root):
                print("Distribution validation failed!")
                success = False
        
        if success:
            print("All steps completed successfully!")
        else:
            print("Some steps failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nBuild interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Build failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()