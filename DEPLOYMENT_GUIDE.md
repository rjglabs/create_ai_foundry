# Azure AI Foundry Deployment Guide

## Complete Deployment Example

This document provides a comprehensive, step-by-step guide for deploying an Azure AI Foundry project from scratch.

### Prerequisites Checklist

Before starting the deployment, ensure you have:

- [ ] **Azure CLI** installed and updated to the latest version
- [ ] **Python 3.9.2+** installed
- [ ] **Azure subscription** with appropriate permissions
- [ ] **Required Azure permissions**:
  - Contributor or Owner role on target subscription/resource group
  - User Access Administrator role for RBAC assignments
- [ ] **Unique resource names** prepared (see naming guidelines below)

### Step 1: Environment Setup

#### 1.1 Install Azure CLI (if not already installed)

**Windows:**
```powershell
winget install -e --id Microsoft.AzureCLI
```

**macOS:**
```bash
brew install azure-cli
```

**Linux:**
```bash
curl -sL https://aka.ms/InstallAzureCLI | sudo bash
```

#### 1.2 Authenticate with Azure

```bash
# Login to Azure
az login

# Set your subscription (if you have multiple)
az account set --subscription "Your Subscription Name"

# Verify your authentication
az account show
```

#### 1.3 Clone and Setup the Project

```bash
# Clone the repository
git clone <repository-url>
cd create_ai_foundry

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration

#### 2.1 Prepare Resource Names

Create unique names for your resources. Azure has specific naming requirements:

| Resource Type | Naming Rules | Example |
|---------------|--------------|---------|
| **Resource Group** | 1-90 chars, letters, numbers, hyphens | `rg-ai-foundry-dev` |
| **Key Vault** | 3-24 chars, letters, numbers, hyphens (globally unique) | `kv-ai-foundry-dev123` |
| **Storage Account** | 3-24 chars, letters and numbers only (globally unique) | `staifondrydv123` |
| **Container Registry** | 5-50 chars, letters and numbers only (globally unique) | `cracrifondrydev123` |
| **AI Services** | 3-64 chars, letters, numbers, hyphens | `ai-services-dev` |
| **Log Analytics** | 4-63 chars, letters, numbers, hyphens | `log-ai-foundry-dev` |
| **Application Insights** | 1-255 chars, letters, numbers, hyphens | `appi-ai-foundry-dev` |

#### 2.2 Create Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your values
nano .env  # or use your preferred editor
```

**Example .env file:**
```bash
# Azure Configuration
LOCATION=eastus2
RESOURCE_GROUP=rg-ai-foundry-dev

# Globally Unique Resources (modify the suffix)
KEYVAULT_NAME=kv-ai-foundry-dev123
CONTAINER_REGISTRY_NAME=cracrifondrydev123
STORAGE_ACCOUNT_NAME=staifondrydv123

# Standard Resources
AI_SERVICES_NAME=ai-services-dev
LOG_WORKSPACE_NAME=log-ai-foundry-dev
APPLICATION_INSIGHTS_NAME=appi-ai-foundry-dev
```

### Step 3: Deployment

#### 3.1 Preview Deployment (Dry Run)

Always run a dry run first to verify your configuration:

```bash
python create-ai-foundry-project.py --dry-run
```

**Expected output:**
```
===============================================================================
🔍 DRY RUN MODE - PREVIEW OF PLANNED AI FOUNDRY DEPLOYMENT
===============================================================================
📍 Location: eastus2
📁 Resource Group: rg-ai-foundry-dev
🏷️  Tags: {'Environment': 'AI-Development', 'Project': 'ai-services-dev', 'Purpose': 'AI-Foundry', 'CreatedBy': 'create-ai-foundry-project.py'}

🤖 AI Foundry Resources to be created:
  • Key Vault: kv-ai-foundry-dev123
  • AI Services Account: ai-services-dev
  • Container Registry: cracrifondrydev123
  • Storage Account: staifondrydv123
  • Log Analytics Workspace: log-ai-foundry-dev
  • Application Insights: appi-ai-foundry-dev

🔐 Secrets & Configuration Management:
  • AI Services API Key → Key Vault
  • AI Services Endpoint → Key Vault
  • (App Configuration skipped - Free SKU limitations)

🔐 Security Configuration:
  • AI Developer role assignments
  • Managed Identity authentication
  • Diagnostic logging enabled
===============================================================================
```

#### 3.2 Execute Full Deployment

If the dry run looks correct, execute the full deployment:

```bash
python create-ai-foundry-project.py
```

**Expected deployment phases:**
1. **Environment Validation** - Verify prerequisites
2. **Resource Group Creation** - Create/verify resource group
3. **Key Vault Deployment** - Set up security foundation
4. **AI Services Account** - Deploy AI services
5. **Container Registry** - Set up model deployment
6. **Storage Account** - Configure data storage
7. **Log Analytics Workspace** - Set up monitoring
8. **Application Insights** - Deploy telemetry
9. **Secret Management** - Store API keys securely
10. **RBAC Configuration** - Set up access control

### Step 4: Post-Deployment Verification

#### 4.1 Check Deployment Status

The script generates two important files:

1. **`ai_foundry_deployment.log`** - Detailed deployment logs
2. **`ai_foundry_deployment_summary.json`** - Resource summary

#### 4.2 Verify Resources in Azure Portal

1. Navigate to [Azure Portal](https://portal.azure.com)
2. Go to your resource group
3. Verify all resources are created:
   - Key Vault
   - AI Services Account
   - Container Registry
   - Storage Account
   - Log Analytics Workspace
   - Application Insights

#### 4.3 Test AI Services Connection

```bash
# Get AI Services endpoint from Key Vault
az keyvault secret show --vault-name "kv-ai-foundry-dev123" --name "ai-services-endpoint" --query "value" -o tsv

# Get AI Services key from Key Vault
az keyvault secret show --vault-name "kv-ai-foundry-dev123" --name "ai-services-key" --query "value" -o tsv
```

### Step 5: Development Setup

#### 5.1 Configure Development Environment

```bash
# Install Azure AI SDK
pip install azure-ai-ml azure-ai-inference

# Create a simple test script
cat > test_ai_services.py << 'EOF'
import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# Initialize credential
credential = DefaultAzureCredential()

# Get secrets from Key Vault
keyvault_name = "kv-ai-foundry-dev123"  # Replace with your Key Vault name
vault_url = f"https://{keyvault_name}.vault.azure.net/"
secret_client = SecretClient(vault_url=vault_url, credential=credential)

# Retrieve AI Services configuration
endpoint = secret_client.get_secret("ai-services-endpoint").value
api_key = secret_client.get_secret("ai-services-key").value

print(f"AI Services Endpoint: {endpoint}")
print("AI Services Key: [HIDDEN]")
print("✅ Successfully retrieved AI Services configuration!")
EOF

# Run the test
python test_ai_services.py
```

#### 5.2 Access Azure AI Foundry Portal

1. Navigate to [Azure AI Foundry Portal](https://ai.azure.com/)
2. Select your subscription and resource group
3. Start building your AI projects

### Step 6: Common Post-Deployment Tasks

#### 6.1 Deploy Your First AI Model

```bash
# Example: Deploy a text completion model
az cognitiveservices account deployment create \
  --name "ai-services-dev" \
  --resource-group "rg-ai-foundry-dev" \
  --deployment-name "text-completion" \
  --model-name "text-davinci-003" \
  --model-version "1" \
  --sku-capacity 1 \
  --sku-name "Standard"
```

#### 6.2 Configure Monitoring Alerts

```bash
# Create a sample alert rule for AI Services
az monitor metrics alert create \
  --name "ai-services-high-usage" \
  --resource-group "rg-ai-foundry-dev" \
  --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-ai-foundry-dev/providers/Microsoft.CognitiveServices/accounts/ai-services-dev" \
  --condition "count >= 100" \
  --description "Alert when AI Services usage is high"
```

#### 6.3 Set Up CI/CD Pipeline

Consider setting up a CI/CD pipeline for your AI models:

1. **Azure DevOps**: Create build and release pipelines
2. **GitHub Actions**: Use GitHub Actions for automated deployment
3. **Azure ML Pipelines**: Set up ML-specific pipelines

### Troubleshooting Common Issues

#### Issue 1: Resource Name Conflicts

**Error:** `"Resource name 'xyz' is already taken"`

**Solution:**
1. Modify the resource name in your `.env` file
2. Add a unique suffix or use a different naming pattern
3. Check name availability using Azure CLI:
   ```bash
   az storage account check-name --name "yourstorageaccountname"
   ```

#### Issue 2: Insufficient Permissions

**Error:** `"Insufficient privileges to complete the operation"`

**Solution:**
1. Verify your Azure permissions:
   ```bash
   az role assignment list --assignee $(az account show --query user.name -o tsv)
   ```
2. Request appropriate permissions from your Azure administrator
3. Ensure you have both Contributor and User Access Administrator roles

#### Issue 3: Quota Limits

**Error:** `"Operation could not be completed as it results in exceeding approved quota"`

**Solution:**
1. Check your subscription quotas:
   ```bash
   az vm list-usage --location eastus2 -o table
   ```
2. Request quota increases through the Azure portal
3. Consider using a different Azure region

#### Issue 4: Network Connectivity

**Error:** `"Network connectivity issues"`

**Solution:**
1. Check your internet connection
2. Verify Azure CLI authentication:
   ```bash
   az account show
   ```
3. Try a different Azure region if there are regional issues

### Best Practices for Production

#### Security Best Practices

1. **Use Private Endpoints**: Configure private endpoints for production
2. **Network Security**: Implement network security groups and firewalls
3. **Identity Management**: Use managed identities for service authentication
4. **Key Rotation**: Implement regular key rotation policies
5. **Monitoring**: Set up comprehensive monitoring and alerting

#### Cost Optimization

1. **Right-sizing**: Choose appropriate SKUs for your workload
2. **Auto-scaling**: Implement auto-scaling where possible
3. **Reserved Instances**: Consider reserved instances for predictable workloads
4. **Cost Monitoring**: Set up cost alerts and budget controls

#### Operational Excellence

1. **Documentation**: Maintain comprehensive documentation
2. **Automation**: Automate deployment and management processes
3. **Testing**: Implement thorough testing procedures
4. **Backup**: Set up backup and disaster recovery procedures

### Additional Resources

- [Azure AI Foundry Documentation](https://docs.microsoft.com/en-us/azure/ai-foundry/)
- [Azure CLI Reference](https://docs.microsoft.com/en-us/cli/azure/)
- [Azure AI Services Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/)
- [Azure Key Vault Documentation](https://docs.microsoft.com/en-us/azure/key-vault/)
- [Azure Monitor Documentation](https://docs.microsoft.com/en-us/azure/azure-monitor/)

### Support and Community

- **Azure Support**: [Azure Support Plans](https://azure.microsoft.com/en-us/support/plans/)
- **Community Forums**: [Microsoft Q&A](https://docs.microsoft.com/en-us/answers/topics/azure.html)
- **Stack Overflow**: [Azure Tag](https://stackoverflow.com/questions/tagged/azure)
- **GitHub Issues**: Report issues in the project repository

---

**Happy AI Development with Azure AI Foundry!** 🚀🤖
