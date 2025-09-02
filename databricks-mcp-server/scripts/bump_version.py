#!/usr/bin/env python3
"""
Version management script for databricks-mcp-server.

This script handles version bumping in pyproject.toml and creates git tags.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Tuple


def get_current_version(pyproject_path: Path) -> str:
    """Get current version from pyproject.toml."""
    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        raise ValueError("Version not found in pyproject.toml")
    return match.group(1)


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse semantic version string."""
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-.*)?$', version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def format_version(major: int, minor: int, patch: int) -> str:
    """Format version tuple as string."""
    return f"{major}.{minor}.{patch}"


def bump_version(current_version: str, bump_type: str) -> str:
    """Bump version according to type."""
    major, minor, patch = parse_version(current_version)
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return format_version(major, minor, patch)


def update_version_in_file(pyproject_path: Path, new_version: str) -> None:
    """Update version in pyproject.toml."""
    content = pyproject_path.read_text()
    new_content = re.sub(
        r'version = "[^"]+"',
        f'version = "{new_version}"',
        content
    )
    pyproject_path.write_text(new_content)


def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run command and return result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    
    return result


def check_git_status() -> bool:
    """Check if git working directory is clean."""
    result = run_command(["git", "status", "--porcelain"], check=False)
    return result.returncode == 0 and not result.stdout.strip()


def create_git_tag(version: str, push: bool = False) -> None:
    """Create and optionally push git tag."""
    tag_name = f"v{version}"
    
    # Create tag
    run_command(["git", "add", "pyproject.toml"])
    run_command(["git", "commit", "-m", f"Bump version to {version}"])
    run_command(["git", "tag", "-a", tag_name, "-m", f"Release {version}"])
    
    print(f"Created tag: {tag_name}")
    
    if push:
        run_command(["git", "push"])
        run_command(["git", "push", "--tags"])
        print("Pushed changes and tags to remote")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Bump version for databricks-mcp-server")
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Project root directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Don't create git commit and tag"
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push changes and tags to remote"
    )
    
    args = parser.parse_args()
    
    pyproject_path = args.project_root / "pyproject.toml"
    
    if not pyproject_path.exists():
        print(f"Error: pyproject.toml not found at {pyproject_path}")
        sys.exit(1)
    
    try:
        # Get current version
        current_version = get_current_version(pyproject_path)
        print(f"Current version: {current_version}")
        
        # Calculate new version
        new_version = bump_version(current_version, args.bump_type)
        print(f"New version: {new_version}")
        
        if args.dry_run:
            print("Dry run - no changes made")
            return
        
        # Check git status if we're going to create commits
        if not args.no_git:
            if not check_git_status():
                print("Error: Git working directory is not clean")
                print("Please commit or stash your changes first")
                sys.exit(1)
        
        # Update version
        update_version_in_file(pyproject_path, new_version)
        print(f"Updated version in {pyproject_path}")
        
        # Create git tag if requested
        if not args.no_git:
            create_git_tag(new_version, args.push)
        
        print(f"Version bumped successfully: {current_version} -> {new_version}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()