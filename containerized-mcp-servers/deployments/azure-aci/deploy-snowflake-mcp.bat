@echo off
REM Azure Container Instances deployment script for Snowflake MCP Server
REM Usage: deploy-snowflake-mcp.bat <resource-group> <container-name>

if "%~2"=="" (
    echo Usage: %0 ^<resource-group^> ^<container-name^>
    echo Example: %0 my-resource-group snowflake-mcp-prod
    exit /b 1
)

set RESOURCE_GROUP=%1
set CONTAINER_NAME=%2
if "%LOCATION%"=="" set LOCATION=East US
if "%IMAGE%"=="" set IMAGE=ghcr.io/your-org/snowflake-mcp:latest

REM Check if Azure CLI is installed
az --version >nul 2>&1
if errorlevel 1 (
    echo Azure CLI is not installed. Please install it first.
    exit /b 1
)

REM Check if logged in
az account show >nul 2>&1
if errorlevel 1 (
    echo Please log in to Azure CLI first: az login
    exit /b 1
)

REM Prompt for required environment variables if not set
if "%SNOWFLAKE_ACCOUNT%"=="" set /p SNOWFLAKE_ACCOUNT=Enter Snowflake Account: 
if "%SNOWFLAKE_USER%"=="" set /p SNOWFLAKE_USER=Enter Snowflake User: 
if "%SNOWFLAKE_PASSWORD%"=="" set /p SNOWFLAKE_PASSWORD=Enter Snowflake Password: 
if "%SNOWFLAKE_DATABASE%"=="" set /p SNOWFLAKE_DATABASE=Enter Snowflake Database: 
if "%SNOWFLAKE_WAREHOUSE%"=="" set /p SNOWFLAKE_WAREHOUSE=Enter Snowflake Warehouse: 
if "%SNOWFLAKE_SCHEMA%"=="" set SNOWFLAKE_SCHEMA=public

echo Deploying Snowflake MCP Server to Azure Container Instances...

REM Create the container instance
az container create ^
    --resource-group "%RESOURCE_GROUP%" ^
    --name "%CONTAINER_NAME%" ^
    --image "%IMAGE%" ^
    --location "%LOCATION%" ^
    --cpu 0.5 ^
    --memory 1 ^
    --restart-policy OnFailure ^
    --environment-variables ^
        SNOWFLAKE_ACCOUNT="%SNOWFLAKE_ACCOUNT%" ^
        SNOWFLAKE_USER="%SNOWFLAKE_USER%" ^
        SNOWFLAKE_DATABASE="%SNOWFLAKE_DATABASE%" ^
        SNOWFLAKE_WAREHOUSE="%SNOWFLAKE_WAREHOUSE%" ^
        SNOWFLAKE_SCHEMA="%SNOWFLAKE_SCHEMA%" ^
        SNOWFLAKE_ROLE="%SNOWFLAKE_ROLE%" ^
    --secure-environment-variables ^
        SNOWFLAKE_PASSWORD="%SNOWFLAKE_PASSWORD%" ^
    --ports 8080 ^
    --protocol TCP ^
    --os-type Linux ^
    --assign-identity ^
    --tags ^
        Environment=production ^
        Service=snowflake-mcp ^
        ManagedBy=azure-cli

if errorlevel 1 (
    echo Container deployment failed!
    exit /b 1
)

echo Container deployment initiated. Checking status...

REM Wait for the container to be in running state
echo Waiting for container to start...
az container wait ^
    --resource-group "%RESOURCE_GROUP%" ^
    --name "%CONTAINER_NAME%" ^
    --condition Running ^
    --timeout 300

REM Show container details
echo Container deployed successfully!
az container show ^
    --resource-group "%RESOURCE_GROUP%" ^
    --name "%CONTAINER_NAME%" ^
    --query "{Name:name,State:containers[0].instanceView.currentState.state,IP:ipAddress.ip,FQDN:ipAddress.fqdn}" ^
    --output table

echo.
echo To view logs: az container logs --resource-group %RESOURCE_GROUP% --name %CONTAINER_NAME%
echo To delete: az container delete --resource-group %RESOURCE_GROUP% --name %CONTAINER_NAME% --yes