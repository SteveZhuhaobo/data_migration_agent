"""
Tests for the complete distribution workflow.

These tests validate the entire build and distribution process end-to-end.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest


class TestDistributionWorkflow:
    """Test complete distribution workflow."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent
    
    @pytest.fixture
    def temp_project(self, project_root, tmp_path):
        """Create temporary copy of project for testing."""
        temp_project = tmp_path / "project"
        shutil.copytree(
            project_root, 
            temp_project, 
            ignore=shutil.ignore_patterns(
                "dist", "build", "*.egg-info", "__pycache__", 
                ".pytest_cache", ".coverage", "htmlcov"
            )
        )
        return temp_project
    
    @pytest.mark.integration
    def test_complete_build_workflow(self, temp_project):
        """Test complete build workflow using Makefile."""
        # Run clean
        result = subprocess.run(
            ["make", "clean"],
            cwd=temp_project,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Clean failed: {result.stderr}"
        
        # Run build
        result = subprocess.run(
            ["make", "build"],
            cwd=temp_project,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        
        # Verify artifacts
        dist_dir = temp_project / "dist"
        assert dist_dir.exists()
        assert len(list(dist_dir.glob("*.whl"))) == 1
        assert len(list(dist_dir.glob("*.tar.gz"))) == 1
    
    @pytest.mark.integration
    def test_validation_workflow(self, temp_project):
        """Test distribution validation workflow."""
        # Build first
        subprocess.run(
            ["make", "build"],
            cwd=temp_project,
            check=True,
            capture_output=True
        )
        
        # Run validation
        result = subprocess.run(
            [sys.executable, "scripts/validate_distribution.py", "--skip-uvx"],
            cwd=temp_project,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Validation failed: {result.stderr}"
        assert "✓" in result.stdout  # Success indicators    

    @pytest.mark.integration
    def test_release_workflow(self, temp_project):
        """Test release workflow without git operations."""
        # Run release workflow (excluding git operations)
        result = subprocess.run(
            [sys.executable, "scripts/build.py", "--all", "--skip-tests"],
            cwd=temp_project,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Release workflow failed: {result.stderr}"
        
        # Verify all artifacts exist
        dist_dir = temp_project / "dist"
        assert dist_dir.exists()
        assert len(list(dist_dir.glob("*.whl"))) == 1
        assert len(list(dist_dir.glob("*.tar.gz"))) == 1
    
    @pytest.mark.integration
    def test_cross_platform_build(self, temp_project):
        """Test that build produces cross-platform compatible packages."""
        # Build package
        subprocess.run(
            ["make", "build"],
            cwd=temp_project,
            check=True,
            capture_output=True
        )
        
        # Check wheel is universal
        wheel_files = list((temp_project / "dist").glob("*.whl"))
        assert len(wheel_files) == 1
        
        wheel_name = wheel_files[0].name
        assert "py3-none-any" in wheel_name, f"Wheel is not universal: {wheel_name}"
    
    @pytest.mark.integration
    def test_dependency_validation(self, temp_project):
        """Test that all dependencies are correctly specified and installable."""
        # Build package
        subprocess.run(
            ["make", "build"],
            cwd=temp_project,
            check=True,
            capture_output=True
        )
        
        # Create test environment
        venv_dir = temp_project / "test_env"
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True,
            capture_output=True
        )
        
        # Get python executable
        if sys.platform == "win32":
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
        
        # Install package
        wheel_files = list((temp_project / "dist").glob("*.whl"))
        wheel_file = wheel_files[0]
        
        result = subprocess.run(
            [str(python_exe), "-m", "pip", "install", str(wheel_file)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Installation failed: {result.stderr}"
        
        # Check dependencies
        result = subprocess.run(
            [str(python_exe), "-m", "pip", "check"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Dependency check failed: {result.stderr}"
    
    def test_version_consistency(self, temp_project):
        """Test version consistency across all files."""
        # Get version from pyproject.toml
        pyproject_path = temp_project / "pyproject.toml"
        content = pyproject_path.read_text()
        
        import re
        version_match = re.search(r'version = "([^"]+)"', content)
        assert version_match, "Version not found in pyproject.toml"
        version = version_match.group(1)
        
        # Build package
        subprocess.run(
            ["make", "build"],
            cwd=temp_project,
            check=True,
            capture_output=True
        )
        
        # Check version in wheel filename
        wheel_files = list((temp_project / "dist").glob("*.whl"))
        assert len(wheel_files) == 1
        
        wheel_name = wheel_files[0].name
        assert version in wheel_name, f"Version {version} not in wheel name: {wheel_name}"
        
        # Check version in source distribution
        tar_files = list((temp_project / "dist").glob("*.tar.gz"))
        assert len(tar_files) == 1
        
        tar_name = tar_files[0].name
        assert version in tar_name, f"Version {version} not in tar name: {tar_name}"


class TestAutomatedWorkflows:
    """Test automated workflow components."""
    
    def test_github_actions_syntax(self, project_root):
        """Test that GitHub Actions workflows have valid syntax."""
        workflows_dir = project_root / ".github" / "workflows"
        
        for workflow_file in workflows_dir.glob("*.yml"):
            content = workflow_file.read_text()
            
            # Basic YAML syntax checks
            assert "name:" in content
            assert "on:" in content
            assert "jobs:" in content
            
            # Check for required workflow elements
            if "build" in workflow_file.name:
                assert "strategy:" in content
                assert "matrix:" in content
            elif "release" in workflow_file.name:
                assert "tags:" in content
                assert "TestPyPI" in content or "testpypi" in content
    
    def test_makefile_targets(self, project_root):
        """Test that all Makefile targets are properly defined."""
        makefile_path = project_root / "Makefile"
        content = makefile_path.read_text()
        
        # Check that targets have proper dependencies
        assert "build: clean" in content
        assert "release:" in content
        assert "test-install: build" in content
        assert "test-uvx: build" in content
        
        # Check for help target
        assert "help:" in content
        assert "@echo" in content
    
    def test_script_executability(self, project_root):
        """Test that all scripts are executable and have proper shebangs."""
        scripts_dir = project_root / "scripts"
        
        for script_file in scripts_dir.glob("*.py"):
            content = script_file.read_text()
            
            # Check shebang
            lines = content.split('\n')
            assert lines[0].startswith("#!/usr/bin/env python"), f"Missing shebang in {script_file}"
            
            # Check if script can be imported (basic syntax check)
            try:
                compile(content, str(script_file), 'exec')
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {script_file}: {e}")


class TestDistributionValidation:
    """Test distribution validation functionality."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent
    
    def test_validation_script_functionality(self, project_root, tmp_path):
        """Test that validation script works correctly."""
        # Create temporary project
        temp_project = tmp_path / "project"
        shutil.copytree(
            project_root, 
            temp_project, 
            ignore=shutil.ignore_patterns(
                "dist", "build", "*.egg-info", "__pycache__", 
                ".pytest_cache", ".coverage", "htmlcov"
            )
        )
        
        # Build package
        subprocess.run(
            ["make", "build"],
            cwd=temp_project,
            check=True,
            capture_output=True
        )
        
        # Run validation with report generation
        report_file = tmp_path / "validation_report.json"
        result = subprocess.run(
            [
                sys.executable, 
                "scripts/validate_distribution.py",
                "--skip-uvx",
                "--report", str(report_file)
            ],
            cwd=temp_project,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Validation failed: {result.stderr}"
        
        # Check report was generated
        assert report_file.exists()
        
        # Validate report content
        with open(report_file) as f:
            report = json.load(f)
        
        assert "validation_results" in report
        assert "summary" in report
        assert report["summary"]["total_tests"] > 0
        assert report["summary"]["success_rate"] > 0.8  # At least 80% success rate