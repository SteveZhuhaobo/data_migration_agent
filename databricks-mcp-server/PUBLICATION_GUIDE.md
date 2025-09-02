# Publication and Testing Guide

This guide helps you publish the databricks-mcp-server project and test the complete installation and setup process.

## Publication Steps

### 1. GitHub Repository Setup

```bash
# 1. Create a new GitHub repository
# Go to GitHub.com → New Repository
# Name: databricks-mcp-server
# Description: MCP server for Databricks integration with uvx packaging support

# 2. Initialize and push your code
cd databricks-mcp-server
git init
git add .
git commit -m "Initial commit: Complete databricks-mcp-server implementation"

# 3. Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/databricks-mcp-server.git
git branch -M main
git push -u origin main

# 4. Create develop branch for development workflow
git checkout -b develop
git push -u origin develop
```

### 2. Repository Configuration

After pushing to GitHub:

1. **Enable GitHub Actions**:
   - Go to repository → Actions tab
   - Enable workflows if prompted
   - The workflows will run automatically on push

2. **Set up branch protection** (optional but recommended):
   - Settings → Branches → Add rule
   - Branch name pattern: `main`
   - Require pull request reviews
   - Require status checks to pass

3. **Configure repository settings**:
   - Add repository description
   - Add topics: `mcp`, `databricks`, `python`, `uvx`, `packaging`
   - Enable Issues and Discussions

### 3. TestPyPI Publication (Optional)

For testing package installation:

```bash
# 1. Build the package
make build

# 2. Upload to TestPyPI (requires account)
twine upload --repository testpypi dist/*

# 3. Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ databricks-mcp-server
```

## Testing Plan

### Phase 1: Fresh Environment Testing

Test the complete setup process in a clean environment:

```bash
# 1. Clone in a fresh directory
cd /tmp
git clone https://github.com/YOUR_USERNAME/databricks-mcp-server.git
cd databricks-mcp-server

# 2. Test automated setup
python scripts/setup_dev.py

# 3. Test development workflows
make dev-quick
make dev-full

# 4. Test local testing workflows
python scripts/local_test_workflow.py --workflow quick
python scripts/local_test_workflow.py --workflow standard
```

### Phase 2: Cross-Platform Testing

Test on different platforms:

#### Windows Testing
```cmd
# Clone repository
git clone https://github.com/YOUR_USERNAME/databricks-mcp-server.git
cd databricks-mcp-server

# Test setup
python scripts/setup_dev.py

# Test workflows
python scripts/local_test_workflow.py --workflow quick
```

#### macOS Testing
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/databricks-mcp-server.git
cd databricks-mcp-server

# Test setup
python scripts/setup_dev.py

# Test workflows
make dev-quick
```

#### Linux Testing
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/databricks-mcp-server.git
cd databricks-mcp-server

# Test setup
python scripts/setup_dev.py

# Test workflows
make dev-full
```

### Phase 3: Package Installation Testing

Test the complete package installation workflow:

```bash
# 1. Build package locally
make build

# 2. Test pip installation
python -m venv test-pip
source test-pip/bin/activate  # or test-pip\Scripts\activate on Windows
pip install dist/*.whl
databricks-mcp-server --help
deactivate

# 3. Test uvx installation (if uvx is available)
uvx --from dist/*.whl databricks-mcp-server --help

# 4. Test from TestPyPI (if published)
pip install --index-url https://test.pypi.org/simple/ databricks-mcp-server
```

### Phase 4: CI/CD Testing

Test the automated workflows:

1. **Push to feature branch** - triggers development workflow
2. **Create pull request** - triggers build workflow
3. **Merge to main** - triggers full build and validation
4. **Create tag** - triggers release workflow (if configured)

### Phase 5: Documentation Testing

Test all documentation and guides:

```bash
# 1. Follow README.md installation instructions
# 2. Follow DEVELOPMENT_SETUP.md setup instructions
# 3. Follow CONTRIBUTING.md contribution process
# 4. Test all code examples in documentation
# 5. Verify all links work
```

## Testing Checklist

### ✅ Repository Setup
- [ ] Repository created and code pushed
- [ ] GitHub Actions enabled and running
- [ ] Branch protection configured (optional)
- [ ] Repository metadata configured

### ✅ Fresh Environment Testing
- [ ] Clone repository in clean environment
- [ ] Run `python scripts/setup_dev.py` successfully
- [ ] All prerequisites detected correctly
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Initial tests pass

### ✅ Development Workflow Testing
- [ ] `make dev-quick` completes successfully
- [ ] `make dev-full` completes successfully
- [ ] `python scripts/local_test_workflow.py --workflow quick` works
- [ ] `python scripts/local_test_workflow.py --workflow standard` works
- [ ] `python scripts/local_test_workflow.py --workflow full` works

### ✅ Code Quality Testing
- [ ] `make format` works correctly
- [ ] `make lint` passes all checks
- [ ] `make test` runs all tests successfully
- [ ] Coverage reports generated correctly

### ✅ Build and Distribution Testing
- [ ] `make build` creates distribution packages
- [ ] `make test-install` validates pip installation
- [ ] `make test-uvx` validates uvx installation (if available)
- [ ] `make validate-dist` passes all validations

### ✅ Cross-Platform Testing
- [ ] Windows setup and workflows work
- [ ] macOS setup and workflows work
- [ ] Linux setup and workflows work
- [ ] All platforms can build and install packages

### ✅ CI/CD Testing
- [ ] Development workflow runs on feature branches
- [ ] Build workflow runs on main branch
- [ ] All CI checks pass
- [ ] Artifacts are generated correctly

### ✅ Documentation Testing
- [ ] README.md instructions work end-to-end
- [ ] DEVELOPMENT_SETUP.md setup process works
- [ ] All code examples in documentation execute correctly
- [ ] All internal links work
- [ ] External links are accessible

### ✅ Package Installation Testing
- [ ] Local wheel installation works
- [ ] UVX installation works (if available)
- [ ] TestPyPI installation works (if published)
- [ ] Package can be imported and used

## Common Issues and Solutions

### Setup Issues

**Issue**: `uv` not found
```bash
# Solution: Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # Unix/macOS
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
```

**Issue**: Virtual environment creation fails
```bash
# Solution: Clean and retry
rm -rf .venv
python scripts/setup_dev.py --force
```

**Issue**: Dependency installation fails
```bash
# Solution: Update pip and retry
python -m pip install --upgrade pip
uv pip install --force-reinstall -e ".[dev]"
```

### Testing Issues

**Issue**: Tests fail due to missing dependencies
```bash
# Solution: Reinstall development dependencies
uv pip install -e ".[dev]"
```

**Issue**: Import errors during testing
```bash
# Solution: Ensure package is installed in development mode
uv pip install -e .
```

**Issue**: UVX tests fail
```bash
# Solution: Install uvx or skip uvx tests
# Install uvx with uv, or run tests with --skip-uvx flag
```

### Build Issues

**Issue**: Package build fails
```bash
# Solution: Clean and rebuild
make clean build
```

**Issue**: Installation tests fail
```bash
# Solution: Check package contents and dependencies
python -m zipfile -l dist/*.whl
twine check dist/*
```

## Success Criteria

The publication and testing is successful when:

1. ✅ **Repository is accessible** - Anyone can clone and access the code
2. ✅ **Setup works everywhere** - Fresh environment setup succeeds on all platforms
3. ✅ **Workflows are reliable** - All development workflows complete successfully
4. ✅ **Quality is maintained** - All quality checks pass consistently
5. ✅ **Package installs correctly** - Both pip and uvx installation work
6. ✅ **Documentation is accurate** - All instructions work as documented
7. ✅ **CI/CD is functional** - Automated workflows run and pass
8. ✅ **Cross-platform compatibility** - Works on Windows, macOS, and Linux

## Next Steps After Testing

Once testing is complete and successful:

1. **Create release** - Tag a version and create GitHub release
2. **Publish to PyPI** - Make package available for public installation
3. **Update documentation** - Incorporate any lessons learned from testing
4. **Share with community** - Announce the project and gather feedback
5. **Iterate and improve** - Use feedback to enhance the project

This comprehensive testing approach ensures the project works reliably for all users and use cases.