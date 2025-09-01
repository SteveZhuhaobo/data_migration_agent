@echo off
REM Snowflake MCP Server Build Script for Windows
REM This script builds the Snowflake MCP Docker container

setlocal enabledelayedexpansion

REM Configuration
set IMAGE_NAME=snowflake-mcp
set IMAGE_TAG=%1
if "%IMAGE_TAG%"=="" set IMAGE_TAG=latest
set REGISTRY=%REGISTRY%
set PLATFORM=%PLATFORM%
if "%PLATFORM%"=="" set PLATFORM=linux/amd64,linux/arm64

REM Parse command line arguments
set TEST_IMAGE=false
set NO_CACHE=false

:parse_args
if "%1"=="--help" goto show_usage
if "%1"=="-h" goto show_usage
if "%1"=="--test" (
    set TEST_IMAGE=true
    shift
    goto parse_args
)
if "%1"=="--no-cache" (
    set NO_CACHE=true
    shift
    goto parse_args
)

REM Function to check if Docker is running
echo [INFO] Checking Docker availability...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running or not accessible
    exit /b 1
)

REM Build the image
set FULL_IMAGE_NAME=%IMAGE_NAME%:%IMAGE_TAG%
if not "%REGISTRY%"=="" set FULL_IMAGE_NAME=%REGISTRY%/%FULL_IMAGE_NAME%

echo [INFO] Building Snowflake MCP Server Docker image...
echo [INFO] Image name: %FULL_IMAGE_NAME%
echo [INFO] Platform: %PLATFORM%

REM Check if buildx is available
docker buildx version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Docker buildx not available, building for current platform only
    if "%NO_CACHE%"=="true" (
        docker build --no-cache --tag %FULL_IMAGE_NAME% .
    ) else (
        docker build --tag %FULL_IMAGE_NAME% .
    )
) else (
    REM Use buildx for multi-platform builds
    if "%NO_CACHE%"=="true" (
        docker buildx build --no-cache --platform %PLATFORM% --tag %FULL_IMAGE_NAME% --load .
    ) else (
        docker buildx build --platform %PLATFORM% --tag %FULL_IMAGE_NAME% --load .
    )
)

if errorlevel 1 (
    echo [ERROR] Failed to build Docker image
    exit /b 1
)

echo [SUCCESS] Successfully built %FULL_IMAGE_NAME%

REM Test the image if requested
if "%TEST_IMAGE%"=="true" (
    echo [INFO] Testing the built image...
    docker run --rm %FULL_IMAGE_NAME% python -c "import server; print('Image test passed')"
    if errorlevel 1 (
        echo [ERROR] Image test failed
        exit /b 1
    )
    echo [SUCCESS] Image test passed
)

REM Show image information
echo [INFO] Image information:
docker images %FULL_IMAGE_NAME% --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo [SUCCESS] Build process completed successfully!
echo.
echo [INFO] Next steps:
echo   1. Test the container: docker-compose up
echo   2. Push to registry: docker push %FULL_IMAGE_NAME%
echo   3. Run the container: docker run -e SNOWFLAKE_ACCOUNT=... -e SNOWFLAKE_USER=... -e SNOWFLAKE_PASSWORD=... %FULL_IMAGE_NAME%

goto end

:show_usage
echo Usage: %0 [TAG] [OPTIONS]
echo.
echo Build the Snowflake MCP Server Docker image
echo.
echo Arguments:
echo   TAG                 Image tag (default: latest)
echo.
echo Environment Variables:
echo   REGISTRY           Container registry prefix (optional)
echo   PLATFORM           Target platforms (default: linux/amd64,linux/arm64)
echo.
echo Examples:
echo   %0                 # Build with 'latest' tag
echo   %0 v1.0.0          # Build with 'v1.0.0' tag
echo   set REGISTRY=ghcr.io/myorg ^& %0 v1.0.0  # Build with registry prefix
echo.
echo Options:
echo   --help, -h         Show this help message
echo   --test             Run image tests after building
echo   --no-cache         Build without using cache
goto end

:end
endlocal