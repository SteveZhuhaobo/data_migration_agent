@echo off
REM Test SQL Server connection from Docker container
echo Testing SQL Server connection...

docker run --rm ^
  -e SQLSERVER_SERVER=host.docker.internal ^
  -e SQLSERVER_DATABASE=poc_tnz ^
  -e SQLSERVER_USERNAME=steve_test ^
  -e SQLSERVER_PASSWORD=SteveTest!23 ^
  -e SQLSERVER_DRIVER="ODBC Driver 18 for SQL Server" ^
  -e SQLSERVER_ENCRYPT=no ^
  -e SQLSERVER_TRUST_CERTIFICATE=yes ^
  sqlserver-mcp:latest python test_connection.py

pause