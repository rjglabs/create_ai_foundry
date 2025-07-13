# Changelog

All notable changes to the Azure AI Foundry project creation script will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive README.md with detailed setup instructions
- DEPLOYMENT_GUIDE.md with step-by-step deployment walkthrough
- QUICK_REFERENCE.md for rapid reference
- MIT License file
- Enhanced docstrings for key functions with examples
- Type hints throughout the codebase
- Comprehensive error handling and logging

### Changed
- Improved script header documentation with detailed architecture overview
- Enhanced environment variable validation with clear error messages
- Better resource naming guidelines and validation
- Improved dry-run output with detailed resource preview

### Fixed
- Pre-commit hooks configuration for consistent code quality
- Poetry configuration for dependency management
- Environment variable handling and validation
- Resource existence checking with proper error handling

## [1.0.0] - 2024-01-XX

### Added
- Initial release of Azure AI Foundry project creation script
- Complete Azure AI Foundry infrastructure deployment
- Key Vault integration for secure secret management
- AI Services account deployment with S0 tier
- Container Registry for model deployment
- Storage Account for data and artifacts
- Log Analytics Workspace for centralized monitoring
- Application Insights for AI workload telemetry
- Role-based access control (RBAC) configuration
- Comprehensive logging and error handling
- Dry-run mode for deployment preview
- Environment variable configuration support
- Azure CLI integration and validation
- Resource tagging for governance
- Security best practices implementation

### Security Features
- Zero hardcoded secrets - all stored in Key Vault
- DefaultAzureCredential for secure authentication
- RBAC integration with AI Developer role
- Audit logging enabled for all resources
- Encryption at rest and in transit
- Soft delete and purge protection for Key Vault
- Managed identity support

### Monitoring & Observability
- Centralized logging through Log Analytics
- Application performance monitoring via Application Insights
- Resource-level diagnostic settings
- Custom metrics and alerts support
- Integration with Azure Monitor

### Resources Created
- Resource Group with consistent tagging
- Key Vault (Standard tier) with access policies
- AI Services Account (S0 tier) with custom subdomain
- Container Registry (Basic tier) with admin access
- Storage Account (Standard_LRS) with hierarchical namespace
- Log Analytics Workspace (PerGB2018) with 30-day retention
- Application Insights (Web) linked to Log Analytics
- Role assignments for proper access control

### Development Tools
- Poetry support for dependency management
- Pre-commit hooks for code quality
- Pytest for testing framework
- Black for code formatting
- Flake8 for linting
- isort for import sorting
- Bandit for security analysis
- MyPy for type checking

### Documentation
- Comprehensive inline documentation
- Step-by-step deployment guide
- Troubleshooting section
- Security best practices
- Cost optimization guidelines
- Development setup instructions

### Files Structure
```
create_ai_foundry/
├── create-ai-foundry-project.py  # Main deployment script
├── requirements.txt              # Python dependencies
├── dev-requirements.txt          # Development dependencies
├── pyproject.toml               # Poetry configuration
├── .env.example                 # Environment template
├── .pre-commit-config.yaml      # Pre-commit hooks
├── README.md                    # Main documentation
├── DEPLOYMENT_GUIDE.md          # Detailed deployment guide
├── QUICK_REFERENCE.md           # Quick reference card
├── CHANGELOG.md                 # This file
├── LICENSE                      # MIT License
└── tests/                       # Test files
    ├── __init__.py
    └── test_placeholder.py
```

### Known Limitations
- App Configuration skipped due to Free SKU soft delete limitations
- Type checking warnings with Azure SDK (doesn't affect functionality)
- Basic tier resources used for development (can be upgraded for production)
- Public endpoints enabled by default (can be configured for private access)

### Prerequisites
- Python 3.9.2 or higher
- Azure CLI installed and authenticated
- Azure subscription with appropriate permissions
- Contributor or Owner role on subscription/resource group
- User Access Administrator for role assignments

### Environment Variables Required
- `LOCATION`: Azure region for deployment
- `RESOURCE_GROUP`: Target resource group name
- `KEYVAULT_NAME`: Key Vault name (globally unique)
- `AI_SERVICES_NAME`: AI Services account name
- `CONTAINER_REGISTRY_NAME`: Container registry name (globally unique)
- `STORAGE_ACCOUNT_NAME`: Storage account name (globally unique)
- `LOG_WORKSPACE_NAME`: Log Analytics workspace name
- `APPLICATION_INSIGHTS_NAME`: Application Insights component name

### Usage
```bash
# Preview deployment
python create-ai-foundry-project.py --dry-run

# Execute deployment
python create-ai-foundry-project.py
```

### Output Files
- `ai_foundry_deployment.log`: Detailed deployment logs
- `ai_foundry_deployment_summary.json`: Resource summary and details

### Support
- GitHub Issues for bug reports
- Azure Support for platform issues
- Community forums for general questions
- Documentation for detailed guidance

---

## Contributing

When contributing to this project, please:

1. Update the changelog for any notable changes
2. Follow the established coding standards
3. Add tests for new functionality
4. Update documentation as needed
5. Use semantic versioning for releases

## Links

- [Azure AI Foundry Portal](https://ai.azure.com/)
- [Azure Portal](https://portal.azure.com/)
- [Azure AI Foundry Documentation](https://docs.microsoft.com/azure/ai-foundry/)
- [Azure CLI Documentation](https://docs.microsoft.com/cli/azure/)
- [Python Azure SDK](https://github.com/Azure/azure-sdk-for-python)

---

*This project is maintained with ❤️ for the Azure AI community*
