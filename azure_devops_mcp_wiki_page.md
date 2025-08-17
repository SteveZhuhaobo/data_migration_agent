# How to Start Using Azure DevOps MCP

## Overview

The Azure DevOps MCP (Model Context Protocol) server brings the power of Azure DevOps directly to your AI agents and applications. This server enables seamless integration between AI systems and Azure DevOps services, allowing you to manage work items, repositories, builds, releases, and more through natural language interactions.

## What is Azure DevOps MCP?

Azure DevOps MCP is a server implementation that provides AI agents with direct access to Azure DevOps functionality through the Model Context Protocol. It acts as a bridge between AI systems and Azure DevOps, enabling automated project management, code repository operations, and DevOps workflow automation.

## Key Features

### Work Item Management
- Create, read, update, and delete work items (tasks, bugs, user stories, etc.)
- Manage work item relationships and hierarchies
- Add comments and track work item history
- Batch operations for efficient bulk updates

### Repository Operations
- List repositories and branches
- Create and manage pull requests
- Handle pull request reviews and comments
- Search commits and link work items to pull requests

### Build and Release Management
- Monitor build definitions and execution
- Trigger builds and track their status
- Manage release pipelines
- Access build logs and artifacts

### Project and Team Management
- List projects and teams
- Manage iterations and sprints
- Handle project configurations
- User and identity management

### Advanced Features
- Wiki page management
- Test plan and case management
- Advanced security alerts
- Search capabilities across code, work items, and wiki

## Getting Started

### Prerequisites
- Azure DevOps organization and project
- Personal Access Token (PAT) with appropriate permissions
- MCP-compatible AI system or application

### Installation

1. **Install the Azure DevOps MCP Server**
   ```bash
   npm install @microsoft/azure-devops-mcp
   ```

2. **Configure Authentication**
   - Generate a Personal Access Token in Azure DevOps
   - Set up environment variables or configuration file
   - Ensure proper permissions for your use case

3. **Initialize the Server**
   ```javascript
   const { AzureDevOpsMCPServer } = require('@microsoft/azure-devops-mcp');
   
   const server = new AzureDevOpsMCPServer({
     organization: 'your-org',
     token: 'your-pat-token'
   });
   ```

### Basic Usage Examples

#### Creating a Work Item
```javascript
// Create a new task
const task = await server.createWorkItem({
  project: 'MyProject',
  workItemType: 'Task',
  title: 'Implement new feature',
  description: 'Add user authentication functionality'
});
```

#### Managing Pull Requests
```javascript
// Create a pull request
const pr = await server.createPullRequest({
  repository: 'my-repo',
  sourceRefName: 'refs/heads/feature-branch',
  targetRefName: 'refs/heads/main',
  title: 'Add new feature',
  description: 'Implementation of user authentication'
});
```

#### Monitoring Builds
```javascript
// Get build status
const builds = await server.getBuilds({
  project: 'MyProject',
  definitions: [123]
});
```

## Best Practices

### Security
- Use least-privilege PAT tokens
- Regularly rotate access tokens
- Monitor API usage and access patterns
- Implement proper error handling

### Performance
- Use batch operations when possible
- Implement caching for frequently accessed data
- Monitor rate limits and implement backoff strategies
- Optimize queries with appropriate filters

### Integration Patterns
- Design idempotent operations
- Implement proper logging and monitoring
- Use webhooks for real-time updates
- Handle network failures gracefully

## Common Use Cases

### Automated Project Management
- Create work items from natural language descriptions
- Update task status based on code commits
- Generate reports and dashboards
- Automate sprint planning and retrospectives

### Code Review Automation
- Automatically assign reviewers based on code changes
- Generate pull request descriptions from commits
- Enforce coding standards and policies
- Track review metrics and performance

### CI/CD Integration
- Trigger builds based on work item updates
- Link deployments to work items
- Automate release notes generation
- Monitor deployment success and rollback procedures

## Troubleshooting

### Common Issues
- **Authentication Errors**: Verify PAT token permissions and expiration
- **Rate Limiting**: Implement exponential backoff and respect API limits
- **Network Timeouts**: Configure appropriate timeout values
- **Permission Denied**: Check user permissions for specific operations

### Debugging Tips
- Enable detailed logging for API calls
- Use Azure DevOps REST API documentation for reference
- Test operations manually before automation
- Monitor Azure DevOps service health status

## Resources

- [Azure DevOps REST API Documentation](https://docs.microsoft.com/en-us/rest/api/azure/devops/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Azure DevOps MCP GitHub Repository](https://github.com/microsoft/azure-devops-mcp)
- [Azure DevOps Developer Community](https://developercommunity.visualstudio.com/spaces/21/index.html)

## Support and Contributing

For issues, feature requests, or contributions, please visit the [Azure DevOps MCP GitHub repository](https://github.com/microsoft/azure-devops-mcp). The project welcomes community contributions and feedback.

---

*This wiki page was generated to help teams get started with Azure DevOps MCP integration. For the most up-to-date information, please refer to the official documentation and repository.*