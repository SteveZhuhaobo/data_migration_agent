@echo off
setlocal enabledelayedexpansion

echo 🧪 Running Snowflake MCP Server Tests
echo ====================================

REM Create test results directory
if not exist test_results mkdir test_results

echo 🏗️  Building test environment...
docker-compose -f docker-compose.test.yml build

if !errorlevel! neq 0 (
    echo ❌ Build failed
    goto cleanup
)

echo 🚀 Running unit tests...
docker-compose -f docker-compose.test.yml run --rm snowflake-mcp-test python -m pytest test_server.py -v --tb=short --junit-xml=test_results/unit_tests.xml

if !errorlevel! neq 0 (
    echo ❌ Unit tests failed
    goto cleanup
)

echo 🔗 Running integration tests...
docker-compose -f docker-compose.test.yml run --rm snowflake-mcp-test python -c "import unittest; import sys; import os; sys.path.insert(0, '/app'); print('Running basic integration validation...'); import server; import env_validator; import health_check; print('✅ All modules imported successfully'); os.environ.update({'SNOWFLAKE_ACCOUNT': 'test_account', 'SNOWFLAKE_USER': 'test_user', 'SNOWFLAKE_PASSWORD': 'test_password'}); server.load_config(); print('✅ Configuration loaded successfully'); server.validate_connection(); print('✅ Connection validation passed'); print('🎉 Basic integration tests passed!')"

echo 📊 Test Results:
echo ===============

if exist test_results\unit_tests.xml (
    echo ✅ Unit test results saved to test_results\unit_tests.xml
) else (
    echo ⚠️  Unit test results not found
)

echo 🎉 All tests completed!
echo.
echo To view detailed results:
echo   - Unit tests: type test_results\unit_tests.xml
echo   - Integration tests: Check console output above

:cleanup
echo 🧹 Cleaning up test environment...
docker-compose -f docker-compose.test.yml down -v --remove-orphans >nul 2>&1

endlocal