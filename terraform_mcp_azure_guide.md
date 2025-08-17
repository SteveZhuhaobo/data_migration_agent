# Terraform MCP Server Integration with Azure DevOps

## Overview

The Terraform MCP Server provides seamless integration with the Terraform ecosystem, enabling advanced automation and interaction capabilities for Infrastructure as Code (IaC) development. When combined with Azure DevOps MCP, you can create a powerful CI/CD pipeline for Azure infrastructure deployment.

## What is Terraform MCP Server?

The Terraform MCP Server is a Model Context Protocol implementation that allows AI agents to:
- Generate Terraform configurations
- Validate and plan Terraform deployments
- Execute Terraform commands
- Manage Terraform state
- Interact with Terraform providers (including Azure)

## Integration Architecture

```
AI Agent/Kiro → Terraform MCP Server → Terraform CLI → Azure Provider → Azure Resources
                     ↓
Azure DevOps MCP → Work Items/Repos/Pipelines
```

## Setup and Configuration

### Prerequisites
- Terraform CLI installed
- Azure CLI installed and authenticated
- Azure DevOps project with appropriate permissions
- Terraform MCP Server configured

### Installation

1. **Install Terraform MCP Server**
   ```bash
   npm install @hashicorp/terraform-mcp-server
   ```

2. **Configure Azure Provider**
   ```hcl
   terraform {
     required_providers {
       azurerm = {
         source  = "hashicorp/azurerm"
         version = "~>3.0"
       }
     }
   }

   provider "azurerm" {
     features {}
   }
   ```

3. **Set up Authentication**
   ```bash
   # Service Principal authentication
   export ARM_CLIENT_ID="your-client-id"
   export ARM_CLIENT_SECRET="your-client-secret"
   export ARM_SUBSCRIPTION_ID="your-subscription-id"
   export ARM_TENANT_ID="your-tenant-id"
   ```

## Common Azure Infrastructure Patterns

### 1. Resource Group and Storage Account
```hcl
# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location

  tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# Storage Account
resource "azurerm_storage_account" "main" {
  name                     = "st${var.project_name}${var.environment}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = azurerm_resource_group.main.tags
}
```

### 2. Azure App Service
```hcl
# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "asp-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "B1"

  tags = azurerm_resource_group.main.tags
}

# App Service
resource "azurerm_linux_web_app" "main" {
  name                = "app-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_service_plan.main.location
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    application_stack {
      node_version = "18-lts"
    }
  }

  app_settings = {
    "WEBSITE_NODE_DEFAULT_VERSION" = "~18"
  }

  tags = azurerm_resource_group.main.tags
}
```

### 3. Azure SQL Database
```hcl
# SQL Server
resource "azurerm_mssql_server" "main" {
  name                         = "sql-${var.project_name}-${var.environment}"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  version                      = "12.0"
  administrator_login          = var.sql_admin_username
  administrator_login_password = var.sql_admin_password

  tags = azurerm_resource_group.main.tags
}

# SQL Database
resource "azurerm_mssql_database" "main" {
  name           = "sqldb-${var.project_name}-${var.environment}"
  server_id      = azurerm_mssql_server.main.id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  license_type   = "LicenseIncluded"
  max_size_gb    = 4
  sku_name       = "S0"

  tags = azurerm_resource_group.main.tags
}
```

### 4. Azure Key Vault
```hcl
# Get current client configuration
data "azurerm_client_config" "current" {}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                = "kv-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Get", "List", "Create", "Delete", "Update"
    ]

    secret_permissions = [
      "Get", "List", "Set", "Delete"
    ]
  }

  tags = azurerm_resource_group.main.tags
}
```

## Variables Configuration

### variables.tf
```hcl
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "myproject"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "sql_admin_username" {
  description = "SQL Server administrator username"
  type        = string
  sensitive   = true
}

variable "sql_admin_password" {
  description = "SQL Server administrator password"
  type        = string
  sensitive   = true
}
```

### terraform.tfvars (example)
```hcl
project_name = "triplist"
environment  = "dev"
location     = "Australia East"
sql_admin_username = "sqladmin"
sql_admin_password = "YourSecurePassword123!"
```

## Outputs Configuration

### outputs.tf
```hcl
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "app_service_url" {
  description = "URL of the App Service"
  value       = "https://${azurerm_linux_web_app.main.name}.azurewebsites.net"
}

output "sql_server_fqdn" {
  description = "Fully qualified domain name of the SQL server"
  value       = azurerm_mssql_server.main.fully_qualified_domain_name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}
```

## Azure DevOps Integration Workflow

### 1. Using Terraform MCP with Azure DevOps MCP

```javascript
// Example workflow combining both MCP servers
async function deployInfrastructure() {
  // 1. Create work item for infrastructure deployment
  const workItem = await azureDevOpsMCP.createWorkItem({
    project: 'AzureDataBricks',
    workItemType: 'Task',
    title: 'Deploy Azure infrastructure with Terraform',
    description: 'Deploy storage, app service, and database infrastructure'
  });

  // 2. Generate Terraform configuration
  const terraformConfig = await terraformMCP.generateConfiguration({
    provider: 'azurerm',
    resources: ['resource_group', 'storage_account', 'app_service', 'sql_database']
  });

  // 3. Validate configuration
  const validation = await terraformMCP.validate({
    configuration: terraformConfig
  });

  // 4. Plan deployment
  const plan = await terraformMCP.plan({
    configuration: terraformConfig
  });

  // 5. Update work item with plan results
  await azureDevOpsMCP.addWorkItemComment({
    workItemId: workItem.id,
    comment: `Terraform plan completed. Resources to create: ${plan.resourcesToAdd}`
  });

  // 6. Apply if approved
  if (plan.approved) {
    const result = await terraformMCP.apply({
      configuration: terraformConfig
    });

    // 7. Update work item with deployment results
    await azureDevOpsMCP.updateWorkItem({
      id: workItem.id,
      state: 'Done',
      comment: `Infrastructure deployed successfully. Resources created: ${result.resourcesCreated}`
    });
  }
}
```

### 2. Azure DevOps Pipeline Integration

```yaml
# azure-pipelines.yml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

variables:
  terraformVersion: '1.5.0'
  workingDirectory: '$(System.DefaultWorkingDirectory)/terraform'

stages:
- stage: Plan
  jobs:
  - job: TerraformPlan
    steps:
    - task: TerraformInstaller@0
      inputs:
        terraformVersion: $(terraformVersion)
    
    - task: TerraformTaskV3@3
      inputs:
        provider: 'azurerm'
        command: 'init'
        workingDirectory: $(workingDirectory)
        backendServiceArm: 'Azure-Connection'
        backendAzureRmResourceGroupName: 'rg-terraform-state'
        backendAzureRmStorageAccountName: 'stterraformstate'
        backendAzureRmContainerName: 'tfstate'
        backendAzureRmKey: 'terraform.tfstate'
    
    - task: TerraformTaskV3@3
      inputs:
        provider: 'azurerm'
        command: 'plan'
        workingDirectory: $(workingDirectory)
        environmentServiceNameAzureRM: 'Azure-Connection'

- stage: Apply
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
  jobs:
  - deployment: TerraformApply
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: TerraformTaskV3@3
            inputs:
              provider: 'azurerm'
              command: 'apply'
              workingDirectory: $(workingDirectory)
              environmentServiceNameAzureRM: 'Azure-Connection'
```

## Best Practices

### 1. State Management
```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "stterraformstate"
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"
  }
}
```

### 2. Environment-Specific Configurations
```
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
└── modules/
    ├── app-service/
    ├── database/
    └── storage/
```

### 3. Security Considerations
- Store sensitive variables in Azure Key Vault
- Use managed identities when possible
- Implement least-privilege access
- Enable audit logging
- Use private endpoints for sensitive resources

## Common Use Cases for Trip List Validation Project

### Infrastructure for Trip List Processing
```hcl
# Data processing infrastructure
module "data_processing" {
  source = "./modules/data-processing"
  
  project_name = "triplist"
  environment  = var.environment
  location     = var.location
  
  # Storage for trip list files
  storage_containers = ["raw-data", "processed-data", "validation-reports"]
  
  # Function App for validation processing
  function_app_settings = {
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "VALIDATION_RULES_PATH"    = "/app/validation-rules"
  }
  
  # Service Bus for processing queue
  service_bus_queues = ["trip-validation-queue", "report-generation-queue"]
}
```

This integration allows you to:
1. **Automate Infrastructure Deployment** - Use AI to generate and deploy Azure resources
2. **Track Infrastructure Changes** - Link Terraform deployments to Azure DevOps work items
3. **Implement GitOps** - Store Terraform configurations in Azure DevOps repos
4. **Monitor Deployments** - Use Azure DevOps pipelines to track deployment status
5. **Manage Multiple Environments** - Deploy to dev, staging, and production environments

The combination of Terraform MCP Server and Azure DevOps MCP provides a powerful platform for Infrastructure as Code automation and project management.