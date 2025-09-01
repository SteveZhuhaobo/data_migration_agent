@echo off
REM Push Snowflake MCP Docker image to Azure Container Registry
REM Usage: push-to-acr.bat <registry-name>

if "%1"=="" (
    echo Usage: %0 ^<registry-name^>
    echo Example: %0 myregistry
    exit /b 1
)

set REGISTRY_NAME=%1
set IMAGE_NAME=snowflake-mcp
set TAG=latest

echo Logging into Azure Container Registry...
az acr login --name %REGISTRY_NAME%

if errorlevel 1 (
    echo Failed to login to ACR. Make sure you're logged into Azure CLI and have access to the registry.
    exit /b 1
)

echo Tagging local image for ACR...
docker tag %IMAGE_NAME%:%TAG% %REGISTRY_NAME%.azurecr.io/%IMAGE_NAME%:%TAG%

echo Pushing image to ACR...
docker push %REGISTRY_NAME%.azurecr.io/%IMAGE_NAME%:%TAG%

if errorlevel 1 (
    echo Failed to push image to ACR.
    exit /b 1
)

echo Successfully pushed %REGISTRY_NAME%.azurecr.io/%IMAGE_NAME%:%TAG%
echo.
echo You can now deploy to ACI using:
echo deploy-snowflake-mcp.bat your-resource-group your-container-name
echo.
echo Make sure to set IMAGE environment variable:
echo set IMAGE=%REGISTRY_NAME%.azurecr.io/%IMAGE_NAME%:%TAG%