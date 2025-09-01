# SQL Server MCP Local Setup

This folder contains everything you need to run your SQL Server MCP as a Docker container.

## Prerequisites

1. Docker Desktop installed and running
2. SQL Server MCP Docker image built

## Quick Start

### Step 1: Build the Docker Image (One-time setup)

Open PowerShell/Command Prompt in your main project directory and run:

```powershell
docker build -t sqlserver-mcp:latest containerized-mcp-servers/sqlserver-mcp/
```

### Step 2: Configure Your SQL Server Connection

Edit the `docker-run.bat` (Windows) or `docker-run.sh` (Linux/Mac) file and update these variables with your SQL Server details:

- `SQLSERVER_SERVER` - Your SQL Server hostname/IP
- `SQLSERVER_DATABASE` - Your database name
- `SQLSERVER_USERNAME` - Your SQL Server username
- `SQLSERVER_PASSWORD` - Your SQL Server password

### Step 3: Run the MCP Server

**On Windows:**
```cmd
docker-run.bat
```

**On Linux/Mac:**
```bash
chmod +x docker-run.sh
./docker-run.sh
```

## What This Does

The Docker container will:
1. Start the SQL Server MCP server
2. Connect to your SQL Server using the provided credentials
3. Provide MCP functionality through stdio (standard input/output)
4. Run interactively so you can see logs and interact with it

## Stopping the Container

Press `Ctrl+C` to stop the container. It will automatically be removed due to the `--rm` flag.

## Troubleshooting

### Container won't start
- Make sure Docker Desktop is running
- Verify the image was built: `docker images | grep sqlserver-mcp`

### Can't connect to SQL Server
- Check your SQL Server is running
- Verify the connection details in the run script
- Make sure SQL Server allows connections from Docker containers

### Permission issues
- On Windows, you might need to run as Administrator
- On Linux/Mac, make sure the script is executable: `chmod +x docker-run.sh`

## Advanced Usage

### Run in background (detached mode)
Replace `-it --rm` with `-d` in the docker run command:

```bash
docker run -d \
  --name sqlserver-mcp-server \
  -e SQLSERVER_SERVER=localhost \
  # ... other environment variables
  sqlserver-mcp:latest
```

### View logs of background container
```bash
docker logs sqlserver-mcp-server -f
```

### Stop background container
```bash
docker stop sqlserver-mcp-server
docker rm sqlserver-mcp-server
```

## Files in this folder

- `docker-run.bat` - Windows batch script to run the container
- `docker-run.sh` - Linux/Mac shell script to run the container  
- `README.md` - This documentation file