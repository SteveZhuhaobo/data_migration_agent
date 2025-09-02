"""
Tests for build and distribution workflow.

These tests validate that the package can be built, distributed, and installed correctly.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest


class TestBuildDistribution:
    """Test build and distribution functionality."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent
    
    @pytest.fixture
    def dist_dir(self, project_root):
        """Get distribution directory."""
        return project_root / "dist"
    
    def test_pyproject_toml_valid(self, project_root):
        """Test that pyproject.toml is valid and contains required fields."""
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"
        
        content = pyproject_path.read_text()
        
        # Check required fields
        required_fields = [
            'name = "databricks-mcp-server"',
            'version =',
            'description =',
            'requires-python =',
            'dependencies =',
            '[project.scripts]',
            'databricks-mcp-server =',
            '[build-system]',
            'requires = ["hatchling"]',
            'build-backend = "hatchling.build"'
        ]
        
        for field in required_fields:
            assert field in content, f"Required field missing: {field}"
    
    def test_entry_point_configuration(self, project_root):
        """Test that entry point is correctly configured."""
        pyproject_path = project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        
        # Check entry point
        assert 'databricks-mcp-server = "databricks_mcp_server.main:main"' in content
    
    def test_dependencies_specified(self, project_root):
        """Test that all required dependencies are specified."""
        pyproject_path = project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        
        required_deps = [
            "databricks-sql-connector",
            "requests",
            "pyyaml",
            "mcp",
        ]
        
        for dep in required_deps:
            assert dep in content, f"Required dependency missing: {dep}"
    
    def test_optional_dependencies(self, project_root):
        """Test that development dependencies are specified."""
        pyproject_path = project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        
        dev_deps = [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "black",
            "isort",
            "mypy",
            "flake8",
        ]
        
        for dep in dev_deps:
            assert dep in content, f"Development dependency missing: {dep}"
    
    @pytest.mark.integration
    def test_package_build(self, project_root, tmp_path):
        """Test that package can be built successfully."""
        # Copy project to temporary directory to avoid polluting source
        import shutil
        temp_project = tmp_path / "project"
        shutil.copytree(project_root, temp_project, ignore=shutil.ignore_patterns(
            "dist", "build", "*.egg-info", "__pycache__", ".pytest_cache"
        ))
        
        # Build package
        result = subprocess.run(
            [sys.executable, "-m", "build"],
            cwd=temp_project,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        
        # Check that distribution files were created
        dist_dir = temp_project / "dist"
        assert dist_dir.exists(), "dist directory not created"
        
        wheel_files = list(dist_dir.glob("*.whl"))
        tar_files = list(dist_dir.glob("*.tar.gz"))
        
        assert len(wheel_files) == 1, f"Expected 1 wheel file, found {len(wheel_files)}"
        assert len(tar_files) == 1, f"Expected 1 tar file, found {len(tar_files)}"
    
    @pytest.mark.integration
    def test_package_check(self, project_root, tmp_path):
        """Test that built package passes twine check."""
        # Build package first
        import shutil
        temp_project = tmp_path / "project"
        shutil.copytree(project_root, temp_project, ignore=shutil.ignore_patterns(
            "dist", "build", "*.egg-info", "__pycache__", ".pytest_cache"
        ))
        
        # Build
        subprocess.run(
            [sys.executable, "-m", "build"],
            cwd=temp_project,
            check=True,
            capture_output=True
        )
        
        # Check with twine
        result = subprocess.run(
            ["twine", "check", "dist/*"],
            cwd=temp_project,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Twine check failed: {result.stderr}"
        assert "PASSED" in result.stdout, "Package validation failed"
    
    @pytest.mark.integration
    def test_wheel_installation(self, project_root, tmp_path):
        """Test that wheel can be installed and entry point works."""
        # Build package
        import shutil
        temp_project = tmp_path / "project"
        shutil.copytree(project_root, temp_project, ignore=shutil.ignore_patterns(
            "dist", "build", "*.egg-info", "__pycache__", ".pytest_cache"
        ))
        
        subprocess.run(
            [sys.executable, "-m", "build"],
            cwd=temp_project,
            check=True,
            capture_output=True
        )
        
        # Create virtual environment
        venv_dir = tmp_path / "test_env"
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True,
            capture_output=True
        )
        
        # Get paths
        if sys.platform == "win32":
            python_exe = venv_dir / "Scripts" / "python.exe"
            entry_point = venv_dir / "Scripts" / "databricks-mcp-server.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
            entry_point = venv_dir / "bin" / "databricks-mcp-server"
        
        # Find wheel file
        wheel_files = list((temp_project / "dist").glob("*.whl"))
        assert len(wheel_files) == 1, "Expected exactly one wheel file"
        wheel_file = wheel_files[0]
        
        # Install wheel
        result = subprocess.run(
            [str(python_exe), "-m", "pip", "install", str(wheel_file)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Installation failed: {result.stderr}"
        
        # Test entry point exists
        assert entry_point.exists(), f"Entry point not found: {entry_point}"
        
        # Test entry point works
        result = subprocess.run(
            [str(entry_point), "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Entry point failed: {result.stderr}"
        assert "databricks-mcp-server" in result.stdout.lower()
        
        # Test import
        result = subprocess.run(
            [str(python_exe), "-c", "import databricks_mcp_server; print('OK')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"
        assert "OK" in result.stdout
    
    @pytest.mark.integration
    @pytest.mark.skipif(not shutil.which("uvx"), reason="uvx not available")
    def test_uvx_installation(self, project_root, tmp_path):
        """Test that package can be installed and run with uvx."""
        import shutil
        
        # Build package
        temp_project = tmp_path / "project"
        shutil.copytree(project_root, temp_project, ignore=shutil.ignore_patterns(
            "dist", "build", "*.egg-info", "__pycache__", ".pytest_cache"
        ))
        
        subprocess.run(
            [sys.executable, "-m", "build"],
            cwd=temp_project,
            check=True,
            capture_output=True
        )
        
        # Find wheel file
        wheel_files = list((temp_project / "dist").glob("*.whl"))
        assert len(wheel_files) == 1, "Expected exactly one wheel file"
        wheel_file = wheel_files[0]
        
        # Test uvx installation
        result = subprocess.run(
            ["uvx", "--from", str(wheel_file), "databricks-mcp-server", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"uvx installation failed: {result.stderr}"
        assert "databricks-mcp-server" in result.stdout.lower()
    
    def test_version_management_script(self, project_root):
        """Test version management script functionality."""
        script_path = project_root / "scripts" / "bump_version.py"
        assert script_path.exists(), "Version management script not found"
        
        # Test dry run
        result = subprocess.run(
            [sys.executable, str(script_path), "patch", "--dry-run"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Version script failed: {result.stderr}"
        assert "Current version:" in result.stdout
        assert "New version:" in result.stdout
        assert "Dry run" in result.stdout
    
    def test_build_script(self, project_root):
        """Test build script functionality."""
        script_path = project_root / "scripts" / "build.py"
        assert script_path.exists(), "Build script not found"
        
        # Test help
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Build script help failed: {result.stderr}"
        assert "--clean" in result.stdout
        assert "--build" in result.stdout
        assert "--test-install" in result.stdout
    
    def test_makefile_exists(self, project_root):
        """Test that Makefile exists and contains expected targets."""
        makefile_path = project_root / "Makefile"
        assert makefile_path.exists(), "Makefile not found"
        
        content = makefile_path.read_text()
        
        expected_targets = [
            "clean",
            "lint",
            "test",
            "build",
            "install",
            "test-install",
            "test-uvx",
            "release",
        ]
        
        for target in expected_targets:
            assert f"{target}:" in content, f"Makefile target missing: {target}"
    
    def test_github_workflows_exist(self, project_root):
        """Test that GitHub Actions workflows exist."""
        workflows_dir = project_root / ".github" / "workflows"
        
        build_workflow = workflows_dir / "build.yml"
        release_workflow = workflows_dir / "release.yml"
        
        assert build_workflow.exists(), "Build workflow not found"
        assert release_workflow.exists(), "Release workflow not found"
        
        # Check build workflow content
        build_content = build_workflow.read_text()
        assert "name: Build and Test" in build_content
        assert "strategy:" in build_content
        assert "matrix:" in build_content
        assert "os:" in build_content
        assert "python-version:" in build_content
        
        # Check release workflow content
        release_content = release_workflow.read_text()
        assert "name: Release" in release_content
        assert "tags:" in release_content
        assert "TestPyPI" in release_content
        assert "PyPI" in release_content
    
    def test_validation_script_exists(self, project_root):
        """Test that distribution validation script exists."""
        validation_script = project_root / "scripts" / "validate_distribution.py"
        assert validation_script.exists(), "Distribution validation script not found"
        
        # Test help
        result = subprocess.run(
            [sys.executable, str(validation_script), "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Validation script help failed: {result.stderr}"
        assert "--project-root" in result.stdout
        assert "--report" in result.stdout
        assert "--skip-uvx" in result.stdout


class TestVersionManagement:
    """Test version management functionality."""
    
    def test_version_parsing(self, project_root):
        """Test version parsing functionality."""
        # Import the functions from the script
        import sys
        sys.path.insert(0, str(project_root / "scripts"))
        from bump_version import parse_version, format_version
        
        # Test valid versions
        assert parse_version("1.0.0") == (1, 0, 0)
        assert parse_version("2.5.10") == (2, 5, 10)
        
        # Test formatting
        assert format_version(1, 0, 0) == "1.0.0"
        assert format_version(2, 5, 10) == "2.5.10"
    
    def test_version_bumping(self, project_root):
        """Test version bumping logic."""
        # Import the function from the script
        import sys
        sys.path.insert(0, str(project_root / "scripts"))
        from bump_version import bump_version
        
        # Test patch bump
        assert bump_version("1.0.0", "patch") == "1.0.1"
        assert bump_version("1.0.5", "patch") == "1.0.6"
        
        # Test minor bump
        assert bump_version("1.0.5", "minor") == "1.1.0"
        assert bump_version("1.5.10", "minor") == "1.6.0"
        
        # Test major bump
        assert bump_version("1.5.10", "major") == "2.0.0"
        assert bump_version("5.2.1", "major") == "6.0.0"