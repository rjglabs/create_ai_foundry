# Azure AI Foundry - Quick Reference

## 🚀 Quick Start Commands

```bash
# 1. Setup
git clone <repo> && cd create_ai_foundry
python -m venv venv && source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your values

# 3. Deploy
python create-ai-foundry-project.py --dry-run  # Preview
python create-ai-foundry-project.py           # Deploy
```

## 📋 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LOCATION` | Azure region | `eastus2` |
| `RESOURCE_GROUP` | Resource group name | `rg-ai-foundry-dev` |
| `KEYVAULT_NAME` | Key Vault name (unique) | `kv-ai-foundry-dev123` |
| `AI_SERVICES_NAME` | AI Services name | `ai-services-dev` |
| `CONTAINER_REGISTRY_NAME` | ACR name (unique) | `cracrifondrydev123` |
| `STORAGE_ACCOUNT_NAME` | Storage name (unique) | `staifondrydv123` |
| `LOG_WORKSPACE_NAME` | Log Analytics name | `log-ai-foundry-dev` |
| `APPLICATION_INSIGHTS_NAME` | App Insights name | `appi-ai-foundry-dev` |

## 🛠️ Resources Created

| Resource | Purpose | SKU |
|----------|---------|-----|
| **Key Vault** | Secure secret storage | Standard |
| **AI Services** | AI/ML capabilities | S0 |
| **Container Registry** | Model deployment | Basic |
| **Storage Account** | Data & artifacts | Standard_LRS |
| **Log Analytics** | Centralized logging | PerGB2018 |
| **Application Insights** | Monitoring & telemetry | Web |

## 🔐 Security Features

- ✅ **Zero hardcoded secrets** - All secrets in Key Vault
- ✅ **RBAC integration** - AI Developer role assigned
- ✅ **Audit logging** - Comprehensive monitoring
- ✅ **Encryption** - At rest and in transit
- ✅ **Managed identity** - Secure authentication

## 🚨 Troubleshooting

### Common Errors

**Name conflicts:**
```bash
# Check storage account name availability
az storage account check-name --name "yourstorageaccountname"
```

**Permission issues:**
```bash
# Check your permissions
az role assignment list --assignee $(az account show --query user.name -o tsv)
```

**Authentication problems:**
```bash
# Re-authenticate
az login
az account show
```

### Files to Check

- `ai_foundry_deployment.log` - Detailed logs
- `ai_foundry_deployment_summary.json` - Resource summary
- `.env` - Environment configuration

## 📊 Post-Deployment

### Verify Resources
```bash
# List resources in resource group
az resource list --resource-group "rg-ai-foundry-dev" --output table

# Get AI Services endpoint
az keyvault secret show --vault-name "kv-ai-foundry-dev123" --name "ai-services-endpoint"
```

### Test Connection
```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
secret_client = SecretClient(
    vault_url="https://kv-ai-foundry-dev123.vault.azure.net/",
    credential=credential
)
endpoint = secret_client.get_secret("ai-services-endpoint").value
print(f"AI Services ready at: {endpoint}")
```

## 🌐 Key URLs

- **Azure AI Foundry Portal**: https://ai.azure.com/
- **Azure Portal**: https://portal.azure.com/
- **Documentation**: https://docs.microsoft.com/azure/ai-foundry/
- **Support**: https://azure.microsoft.com/support/

## 💡 Development Tips

1. **Always run dry-run first** before deployment
2. **Use unique suffixes** for globally unique resources
3. **Check quotas** before deployment in new regions
4. **Enable monitoring** from day one
5. **Document your configurations** for team members

## 📱 CLI Extensions

```bash
# Useful Azure CLI extensions
az extension add --name ai-examples
az extension add --name ml
az extension add --name application-insights
```

---
*For detailed information, see [README.md](README.md) and [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)*
