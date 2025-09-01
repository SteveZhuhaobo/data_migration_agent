@echo off
REM Test SQL Server MCP startup components
echo Testing SQL Server MCP startup components...

docker run --rm ^
  -e SQLSERVER_SERVER=host.docker.internal ^
  -e SQLSERVER_DATABASE=Test_Steve ^
  -e SQLSERVER_USERNAME=steve_test ^
  -e SQLSERVER_PASSWORD=SteveTest!23 ^
  -e SQLSERVER_DRIVER="ODBC Driver 18 for SQL Server" ^
  -e SQLSERVER_ENCRYPT=no ^
  -e SQLSERVER_TRUST_CERTIFICATE=yes ^
  sqlserver-mcp:latest python test_startup.py

pause