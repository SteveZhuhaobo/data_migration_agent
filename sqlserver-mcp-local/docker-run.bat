@echo off
REM SQL Server MCP Docker Runner
REM Edit the environment variables below with your SQL Server details

echo Starting SQL Server MCP Container...

docker run -it --rm ^
  --name sqlserver-mcp-server ^
  -e SQLSERVER_SERVER=host.docker.internal ^
  -e SQLSERVER_DATABASE=Test_Steve ^
  -e SQLSERVER_USERNAME=steve_test ^
  -e SQLSERVER_PASSWORD=SteveTest!23 ^
  -e SQLSERVER_DRIVER="ODBC Driver 18 for SQL Server" ^
  -e SQLSERVER_ENCRYPT=no ^
  -e SQLSERVER_TRUST_CERTIFICATE=yes ^
  sqlserver-mcp:latest

echo Container stopped.
pause