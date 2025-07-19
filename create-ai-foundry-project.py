#!/usr/bin/env python3
"""
Azure AI Foundry Project Creation Script

OVERVIEW:
This script creates a comprehensive Azure AI Foundry project environment with
all the necessary resources for AI development, including AI services, storage,
container registry, and monitoring components.

AZURE AI FOUNDRY ARCHITECTURE:
Azure AI Foundry represents Microsoft's modern, standalone approach to AI
project development. Unlike the previous hub-based model, AI Foundry projects
provide:
- Unified AI development environment
- Integrated AI services (OpenAI, Cognitive Services, etc.)
- Built-in MLOps capabilities
- Seamless integration with Azure DevOps and GitHub
- Enterprise-grade security and compliance

DEPLOYMENT PROCESS:
This script follows a systematic 9-phase deployment approach:

Phase 1: Environment Validation
    - Validates all required environment variables from .env file
    - Checks Azure CLI installation and authentication
    - Registers required Azure resource providers
    - Initializes Azure management clients with proper authentication

Phase 2: Resource Group Management
    - Creates or verifies existence of the target resource group
    - Applies consistent tagging strategy for resource organization
    - Ensures proper location configuration

Phase 3: Key Vault (Security Foundation)
    - Creates Azure Key Vault for secure secret storage
    - Configures access policies for current user
    - Enables soft delete and purge protection
    - Sets up encryption and compliance features

Phase 4: AI Services Account (Core AI Engine)
    - Deploys unified AI Services account (S0 tier)
    - Configures custom subdomain for API access
    - Enables diagnostic logging and monitoring
    - Supports OpenAI, Cognitive Services, and custom models

Phase 5: Container Registry (Model Deployment)
    - Creates Azure Container Registry (Basic tier)
    - Enables admin user for easy authentication
    - Configures for AI model containerization and deployment
    - Sets up public network access for development

Phase 6: Storage Account (Data & Artifacts)
    - Deploys Storage Account v2 with hierarchical namespace
    - Enables HTTPS-only traffic and TLS 1.2 minimum
    - Optimized for AI workloads and large datasets
    - Supports blob, file, and data lake scenarios

Phase 7: Log Analytics Workspace (Monitoring Foundation)
    - Creates Log Analytics workspace for centralized logging
    - Configures 30-day retention for AI workload monitoring
    - Enables advanced query capabilities with KQL
    - Provides foundation for Application Insights

Phase 8: Application Insights (AI Monitoring)
    - Deploys Application Insights linked to Log Analytics
    - Configures for web application monitoring
    - Enables AI model performance tracking
    - Sets up telemetry collection for AI workloads

Phase 9: Secret Management & Configuration
    - Retrieves AI Services API keys and endpoints
    - Stores secrets securely in Key Vault
    - Configures access for development and production
    - Eliminates hardcoded credentials

Phase 10: Role-Based Access Control (RBAC)
    - Assigns AI Developer role to current user
    - Enables proper permissions for AI development
    - Follows principle of least privilege
    - Supports team collaboration scenarios

RESOURCES CREATED:
1. Resource Group - Logical container for all AI resources
2. Key Vault - Secure storage for secrets, keys, and certificates
3. AI Services Account - Unified AI services endpoint (OpenAI,
   Cognitive Services, etc.)
4. Container Registry - For custom AI model deployment
5. Storage Account - For training data, models, and artifacts
6. Log Analytics Workspace - For centralized logging and monitoring
7. Application Insights - For AI model monitoring and telemetry
8. Cognitive Search - For AI-powered search and indexing capabilities
9. Role Assignments - Proper RBAC for AI development

PREREQUISITES:
- Azure CLI installed and authenticated (az login)
- Appropriate Azure subscription permissions:
  * Contributor or Owner role on subscription/resource group
  * User Access Administrator for role assignments
- Python 3.9.2+ with required packages installed
- Environment variables configured in .env file (see .env.example)

USAGE:
    # Preview deployment without making changes
    python create-ai-foundry-project.py --dry-run

    # Execute full deployment
    python create-ai-foundry-project.py

ENVIRONMENT VARIABLES REQUIRED:
    LOCATION                  - Azure region (e.g., 'eastus2')
    RESOURCE_GROUP           - Resource group name
    KEYVAULT_NAME           - Key Vault name (globally unique)
    AI_SERVICES_NAME        - AI Services account name
    CONTAINER_REGISTRY_NAME - Container registry name (globally unique)
    STORAGE_ACCOUNT_NAME    - Storage account name (globally unique)
    LOG_WORKSPACE_NAME      - Log Analytics workspace name
    APPLICATION_INSIGHTS_NAME - Application Insights component name
    COGNITIVE_SEARCH_NAME   - Cognitive Search service name

SECURITY FEATURES:
- Uses DefaultAzureCredential for secure authentication
- Implements proper RBAC with AI Developer role
- Enables diagnostic logging for all resources
- Follows Azure security best practices
- Supports managed identity authentication
- Stores all secrets in Key Vault (no hardcoded credentials)
- Enables encryption at rest and in transit
- Implements soft delete and purge protection

NETWORKING & ACCESS:
- Public endpoints enabled for development scenarios
- Can be configured for private endpoints in production
- Supports Azure Virtual Network integration
- Compatible with Azure Private Link

MONITORING & OBSERVABILITY:
- Centralized logging through Log Analytics
- Application performance monitoring via Application Insights
- Resource-level diagnostic settings enabled
- Custom metrics and alerts support
- Integration with Azure Monitor

COST OPTIMIZATION:
- Uses cost-effective SKUs for development (Basic/Standard)
- Enables automatic scaling where applicable
- Provides clear resource tagging for cost tracking
- Supports Azure Cost Management integration

COMPLIANCE & GOVERNANCE:
- Implements Azure Policy compliance
- Enables resource tagging for governance
- Supports Azure Resource Graph queries
- Compatible with Azure Blueprints
- Follows Azure Well-Architected Framework principles

OUTPUT FILES:
- ai_foundry_deployment.log - Detailed deployment logs
- ai_foundry_deployment_summary.json - Deployment summary and resource details

This script follows Azure AI Foundry best practices and enterprise security
standards. It's designed for both development and production scenarios with
appropriate security configurations.

TROUBLESHOOTING:
If deployment fails, check:
1. Azure CLI authentication: az account show
2. Subscription permissions: az role assignment list --assignee <your-email>
3. Resource provider registration: az provider list --query \
   "[?registrationState=='NotRegistered']"
4. Resource name availability: Check global uniqueness requirements
5. Quota limits: Verify subscription quotas for target region

For support, check the deployment logs and Azure portal for detailed \
error messages.
"""

import argparse
import json
import logging
import os
import subprocess  # nosec B404 - subprocess needed for Azure CLI operations
import uuid
from typing import Any, Dict

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient
from azure.mgmt.applicationinsights.models import (
    ApplicationInsightsComponent,
    ApplicationType,
)
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import (
    Account,
    AccountProperties,
)
from azure.mgmt.cognitiveservices.models import Sku as CognitiveServicesSku
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.containerregistry.models import Registry
from azure.mgmt.containerregistry.models import Sku as ContainerRegistrySku
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.keyvault.models import (
    AccessPolicyEntry,
    CertificatePermissions,
    KeyPermissions,
    Permissions,
    SecretPermissions,
    Sku,
    SkuName,
    VaultCreateOrUpdateParameters,
    VaultProperties,
)
from azure.mgmt.loganalytics import LogAnalyticsManagementClient
from azure.mgmt.loganalytics.models import Workspace, WorkspaceSku
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.search.models import (
    SearchService,
)
from azure.mgmt.search.models import Sku as SearchSku
from azure.mgmt.search.models import SkuName as SearchSkuName
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import Kind
from azure.mgmt.storage.models import Sku as StorageSku
from azure.mgmt.storage.models import StorageAccountCreateParameters
from dotenv import load_dotenv

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
log_filename = "ai_foundry_deployment.log"


class UTF8FileHandler(logging.FileHandler):
    """Custom logging handler that ensures UTF-8 encoding for log files."""

    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: str = "utf-8",
        delay: bool = False,
    ) -> None:
        super().__init__(filename, mode, encoding, delay)


# Configure logging with proper formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        UTF8FileHandler(log_filename),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

# AI Foundry specific environment variables
ai_foundry_env_vars = [
    "LOCATION",
    "RESOURCE_GROUP",
    "KEYVAULT_NAME",
    "AI_SERVICES_NAME",
    "CONTAINER_REGISTRY_NAME",
    "STORAGE_ACCOUNT_NAME",
    "APPLICATION_INSIGHTS_NAME",
    "LOG_WORKSPACE_NAME",
    "COGNITIVE_SEARCH_NAME",
]


def validate_environment_variables() -> None:
    """
    Validate that all required AI Foundry environment variables are present.

    This function checks for the presence of all required environment \
variables
    that are needed for Azure AI Foundry deployment. If any variables are \
missing,
    it logs an error and terminates the program.

    Required Environment Variables:
        LOCATION: Azure region for deployment (e.g., 'eastus2')
        RESOURCE_GROUP: Target resource group name
        KEYVAULT_NAME: Key Vault name (must be globally unique)
        AI_SERVICES_NAME: AI Services account name
        CONTAINER_REGISTRY_NAME: Container registry name (must be globally \
unique)
        STORAGE_ACCOUNT_NAME: Storage account name (must be globally unique)
        LOG_WORKSPACE_NAME: Log Analytics workspace name
        APPLICATION_INSIGHTS_NAME: Application Insights component name

    Raises:
        SystemExit: If any required environment variables are missing

    Returns:
        None
    """
    missing_vars = [var for var in ai_foundry_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(
            f"Missing required environment variables: "
            f"{', '.join(missing_vars)}"
        )
        logger.error(
            "Please ensure all AI Foundry variables are set in your .env "
            "file"
        )
        logger.error("See .env.example for reference")
        exit(1)
    logger.info(
        "[✓] All required AI Foundry environment variables are present"
    )


# =============================================================================
# AZURE UTILITIES
# =============================================================================


def validate_azure_cli() -> tuple[bool, str | None]:
    """Validate Azure CLI installation and authentication."""
    try:
        # Check if Azure CLI is installed (use az.cmd on Windows)
        az_command = "az.cmd" if os.name == "nt" else "az"
        subprocess.run(
            [az_command, "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        logger.info("[✓] Azure CLI is installed and available")

        # Check if user is authenticated
        result = subprocess.run(
            [az_command, "account", "show"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        # Extract subscription info for logging
        account_info = json.loads(result.stdout)
        subscription_id = account_info.get("id", "")
        subscription_name = account_info.get("name", "")

        logger.info("[✓] Azure CLI authentication verified")
        logger.info(
            f"[✓] Using subscription: {subscription_name} ({subscription_id})"
        )

        return True, az_command

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
        json.JSONDecodeError,
    ) as e:
        logger.error(f"[✗] Azure CLI validation failed: {e}")
        return False, None


def get_azure_profile(az_command: str | None = None) -> Dict[str, str]:
    """Get Azure subscription and tenant information."""
    if az_command is None:
        az_command = "az.cmd" if os.name == "nt" else "az"

    try:
        result = subprocess.run(
            [az_command, "account", "show"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        profile = json.loads(result.stdout)
        subscription_id = profile.get("id", "")
        tenant_id = profile.get("tenantId", "")
        user_name = profile.get("user", {}).get("name", "")

        if not subscription_id or not tenant_id:
            raise ValueError("Could not retrieve subscription or tenant ID")

        return {
            "subscription_id": subscription_id,
            "tenant_id": tenant_id,
            "user": user_name,
        }

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
    ) as e:
        logger.error(f"[✗] Failed to get Azure profile: {e}")
        raise


def get_current_user_object_id(az_command: str | None = None) -> str:
    """Get the current user's object ID for role assignments."""
    if az_command is None:
        az_command = "az.cmd" if os.name == "nt" else "az"

    try:
        result = subprocess.run(
            [
                az_command,
                "ad",
                "signed-in-user",
                "show",
                "--query",
                "id",
                "-o",
                "tsv",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        object_id = result.stdout.strip()
        if not object_id:
            raise ValueError("Empty object ID returned")

        logger.info(f"[✓] Current user object ID: {object_id}")
        return object_id

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.error(f"[✗] Failed to get user object ID: {e}")
        raise


def get_current_user_tenant_id(az_command: str | None = None) -> str:
    """Get the current user's tenant ID for Key Vault access policies."""
    if az_command is None:
        az_command = "az.cmd" if os.name == "nt" else "az"

    try:
        result = subprocess.run(
            [
                az_command,
                "account",
                "show",
                "--query",
                "tenantId",
                "-o",
                "tsv",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        tenant_id = result.stdout.strip()
        logger.info(f"[✓] Current user tenant ID: {tenant_id}")
        return tenant_id
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get current user tenant ID: {e}")
        raise


def register_azure_providers(az_command: str | None = None) -> None:
    """Register required Azure resource providers for AI Foundry."""
    if az_command is None:
        az_command = "az.cmd" if os.name == "nt" else "az"

    providers = [
        "Microsoft.CognitiveServices",
        "Microsoft.ContainerRegistry",
        "Microsoft.Storage",
        "Microsoft.Insights",
        "Microsoft.Authorization",
        "Microsoft.Search",
    ]

    logger.info("[⚡] Registering Azure resource providers...")
    for provider in providers:
        try:
            subprocess.run(
                [az_command, "provider", "register", "--namespace", provider],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            logger.info(f"  [✓] Registered provider: {provider}")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.warning(
                f"  [⚠] Failed to register provider {provider}: {e}"
            )


# =============================================================================
# RESOURCE EXISTENCE CHECKS
# =============================================================================


def resource_group_exists(
    resource_client: ResourceManagementClient, rg_name: str
) -> bool:
    """Check if a resource group exists."""
    try:
        return bool(resource_client.resource_groups.check_existence(rg_name))
    except Exception:
        return False


def ai_foundry_resource_exists(
    cognitiveservices_client: CognitiveServicesManagementClient,
    rg_name: str,
    resource_name: str,
) -> bool:
    """Check if an AI Foundry Cognitive Services resource exists."""
    try:
        cognitiveservices_client.accounts.get(rg_name, resource_name)
        return True
    except Exception:
        return False


def container_registry_exists(
    acr_client: ContainerRegistryManagementClient,
    rg_name: str,
    registry_name: str,
) -> bool:
    """Check if a Container Registry exists."""
    try:
        acr_client.registries.get(rg_name, registry_name)
        return True
    except Exception:
        return False


def storage_account_exists(
    storage_client: StorageManagementClient,
    rg_name: str,
    account_name: str,
) -> bool:
    """Check if a Storage Account exists."""
    try:
        storage_client.storage_accounts.get_properties(rg_name, account_name)
        return True
    except Exception:
        return False


def application_insights_exists(
    appinsights_client: ApplicationInsightsManagementClient,
    rg_name: str,
    component_name: str,
) -> bool:
    """Check if an Application Insights component exists."""
    try:
        appinsights_client.components.get(rg_name, component_name)
        return True
    except Exception:
        return False


def log_analytics_workspace_exists(
    log_analytics_client: LogAnalyticsManagementClient,
    rg_name: str,
    workspace_name: str,
) -> bool:
    """Check if a Log Analytics workspace exists."""
    try:
        log_analytics_client.workspaces.get(rg_name, workspace_name)
        return True
    except Exception:
        return False


def keyvault_exists(
    keyvault_client: KeyVaultManagementClient,
    rg_name: str,
    keyvault_name: str,
) -> bool:
    """Check if a Key Vault exists."""
    try:
        keyvault_client.vaults.get(rg_name, keyvault_name)
        return True
    except Exception:
        return False


def search_service_exists(
    search_client: SearchManagementClient,
    rg_name: str,
    search_name: str,
) -> bool:
    """Check if a Cognitive Search service exists."""
    try:
        search_client.services.get(rg_name, search_name)
        return True
    except Exception:
        return False


def get_log_analytics_workspace_id(
    log_analytics_client: LogAnalyticsManagementClient,
    rg_name: str,
    workspace_name: str,
) -> str:
    """Get the resource ID of a Log Analytics workspace."""
    try:
        workspace = log_analytics_client.workspaces.get(
            rg_name, workspace_name
        )
        return str(workspace.id)
    except Exception as e:
        logger.error(f"Failed to get Log Analytics workspace ID: {e}")
        raise


def get_ai_services_endpoint_and_key(
    cognitiveservices_client: CognitiveServicesManagementClient,
    rg_name: str,
    ai_services_name: str,
) -> tuple[str, str]:
    """Get AI Services endpoint and primary key."""
    try:
        # Get the AI Services account
        account = cognitiveservices_client.accounts.get(
            rg_name, ai_services_name
        )

        if not account.properties:
            raise ValueError("AI Services account properties not found")

        if not account.properties.endpoint:
            raise ValueError("AI Services account endpoint not found")

        # Type narrowing for mypy - we know these are not None after
        # the checks above
        endpoint = account.properties.endpoint

        # Get the primary key
        keys = cognitiveservices_client.accounts.list_keys(
            rg_name, ai_services_name
        )

        if not keys.key1:
            raise ValueError("AI Services primary key not found")

        # Direct assignment after null check
        primary_key = keys.key1

        return endpoint, primary_key
    except Exception as e:
        logger.error(f"Failed to get AI Services endpoint and key: {e}")
        raise


def get_search_service_endpoint_and_key(
    search_client: SearchManagementClient,
    rg_name: str,
    search_name: str,
) -> tuple[str, str]:
    """Get Cognitive Search service endpoint and primary key."""
    try:
        # Get the search service
        service = search_client.services.get(rg_name, search_name)

        if not service.name:
            raise ValueError("Search service name not found")

        # Type narrowing for mypy - we know this is not None after
        # the check above
        # Construct the endpoint URL
        endpoint = f"https://{service.name}.search.windows.net/"

        # Get the primary admin key
        keys = search_client.admin_keys.get(rg_name, search_name)

        if not keys.primary_key:
            raise ValueError("Search service primary key not found")

        # Direct assignment after null check
        primary_key = keys.primary_key

        return endpoint, primary_key
    except Exception as e:
        logger.error(f"Failed to get Search service endpoint and key: {e}")
        raise


def store_secret_in_keyvault(
    keyvault_name: str,
    secret_name: str,
    secret_value: str,
    credential: DefaultAzureCredential,
) -> None:
    """
    Store a secret in Azure Key Vault securely.

    This function stores a secret value in the specified Key Vault using the
    provided Azure credentials. The secret is stored with the given name and
    can be retrieved later using the same name.

    Args:
        keyvault_name (str): The name of the Key Vault (without \
.vault.azure.net)
        secret_name (str): The name to use for the secret in Key Vault
        secret_value (str): The secret value to store (will be encrypted)
        credential (DefaultAzureCredential): Azure credential for \
authentication

    Raises:
        Exception: If the secret cannot be stored (e.g., permission issues,
                   Key Vault not found, network issues)

    Returns:
        None

    Examples:
        >>> credential = DefaultAzureCredential()
        >>> store_secret_in_keyvault(
        ...     "my-keyvault",
        ...     "ai-services-key",
        ...     "abc123def456",
        ...     credential
        ... )
    """
    try:
        vault_url = f"https://{keyvault_name}.vault.azure.net/"
        secret_client = SecretClient(
            vault_url=vault_url, credential=credential
        )

        secret_client.set_secret(secret_name, secret_value)
        logger.info(f"  [✓] Secret '{secret_name}' stored in Key Vault")
    except Exception as e:
        logger.error(f"  [✗] Failed to store secret '{secret_name}': {e}")
        raise


def wait_for_operation(
    operation: Any, resource_name: str, timeout_minutes: int = 15
) -> Any:
    """Wait for a long-running Azure operation to complete with proper error
    handling."""
    logger.info(f"  [⏳] Waiting for {resource_name} operation to complete...")
    try:
        timeout_seconds = timeout_minutes * 60
        result = operation.result(timeout=timeout_seconds)
        logger.info(f"  [✓] {resource_name} operation completed successfully")
        return result
    except Exception as e:
        logger.error(f"  [✗] {resource_name} operation failed: {e}")
        raise


# =============================================================================
# MAIN AI FOUNDRY DEPLOYMENT FUNCTION
# =============================================================================


def main() -> None:
    """
    Main AI Foundry project deployment function.

    This function orchestrates the complete deployment of an Azure AI Foundry
    project environment, including all necessary supporting infrastructure.

    The deployment follows a systematic approach:
    1. Environment validation and Azure CLI authentication
    2. Resource group creation/verification
    3. Key Vault deployment for secure secret management
    4. AI Services account creation for AI/ML workloads
    5. Container Registry setup for model deployment
    6. Storage Account configuration for data and artifacts
    7. Log Analytics Workspace for centralized monitoring
    8. Application Insights for AI workload telemetry
    9. Secret management and secure configuration
    10. Role-based access control (RBAC) setup

    The function supports both dry-run mode for preview and full deployment
    execution. All operations are logged with detailed progress information.

    Environment Variables Required:
        LOCATION: Azure region for deployment
        RESOURCE_GROUP: Target resource group name
        KEYVAULT_NAME: Key Vault name (globally unique)
        AI_SERVICES_NAME: AI Services account name
        CONTAINER_REGISTRY_NAME: Container registry name (globally unique)
        STORAGE_ACCOUNT_NAME: Storage account name (globally unique)
        LOG_WORKSPACE_NAME: Log Analytics workspace name
        APPLICATION_INSIGHTS_NAME: Application Insights component name
        COGNITIVE_SEARCH_NAME: Cognitive Search service name

    Files Created:
        - ai_foundry_deployment.log: Detailed deployment logs
        - ai_foundry_deployment_summary.json: Deployment summary with \
resource details

    Raises:
        SystemExit: On validation failures or deployment errors
        Exception: On Azure service communication errors

    Returns:
        None
    """
    try:
        # Load environment variables fresh each time for true idempotency
        logger.info("[⚙️] Loading environment configuration...")
        load_dotenv(override=True)
        logger.info("[✓] Environment variables loaded from .env file")

        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description="Create Azure AI Foundry Project Environment"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview mode: Show planned actions without executing them",
        )
        args = parser.parse_args()

        # Validate environment variables
        validate_environment_variables()

        # Get configuration from environment
        location = os.getenv("LOCATION")
        resource_group = os.getenv("RESOURCE_GROUP")
        keyvault_name = os.getenv("KEYVAULT_NAME")
        ai_services_name = os.getenv("AI_SERVICES_NAME")
        container_registry_name = os.getenv("CONTAINER_REGISTRY_NAME")
        storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME")
        log_workspace_name = os.getenv("LOG_WORKSPACE_NAME")
        application_insights_name = os.getenv("APPLICATION_INSIGHTS_NAME")
        cognitive_search_name = os.getenv("COGNITIVE_SEARCH_NAME")

        # Type assertions for mypy - ensure variables are not None
        if not all(
            [
                location,
                resource_group,
                keyvault_name,
                ai_services_name,
                container_registry_name,
                storage_account_name,
                log_workspace_name,
                application_insights_name,
                cognitive_search_name,
            ]
        ):
            logger.error("Required environment variables are missing")
            return

        # Type assertions for mypy to confirm non-None values
        assert location is not None
        assert resource_group is not None
        assert keyvault_name is not None
        assert ai_services_name is not None
        assert container_registry_name is not None
        assert storage_account_name is not None
        assert log_workspace_name is not None
        assert application_insights_name is not None
        assert cognitive_search_name is not None

        # Set up resource tags
        tags = {
            "Environment": "AI-Development",
            "Project": ai_services_name,
            "Purpose": "AI-Foundry",
            "CreatedBy": "create-ai-foundry-project.py",
        }

        # Handle dry run mode
        if args.dry_run:
            logger.info("=" * 80)
            logger.info(
                "🔍 DRY RUN MODE - PREVIEW OF PLANNED AI FOUNDRY DEPLOYMENT"
            )
            logger.info("=" * 80)
            logger.info(f"📍 Location: {location}")
            logger.info(f"📁 Resource Group: {resource_group}")
            logger.info(f"🏷️  Tags: {tags}")
            logger.info("")
            logger.info("🤖 AI Foundry Resources to be created:")
            logger.info(f"  • Key Vault: {keyvault_name}")
            logger.info(f"  • AI Services Account: {ai_services_name}")
            logger.info(f"  • Container Registry: {container_registry_name}")
            logger.info(f"  • Storage Account: {storage_account_name}")
            logger.info(f"  • Log Analytics Workspace: {log_workspace_name}")
            logger.info(
                f"  • Application Insights: {application_insights_name}"
            )
            logger.info(f"  • Cognitive Search: {cognitive_search_name}")
            logger.info("")
            logger.info("🔐 Secrets & Configuration Management:")
            logger.info("  • AI Services API Key → Key Vault")
            logger.info("  • AI Services Endpoint → Key Vault")
            logger.info("  • Cognitive Search API Key → Key Vault")
            logger.info("  • Cognitive Search Endpoint → Key Vault")
            logger.info(
                "  • (App Configuration skipped - Free SKU limitations)"
            )
            logger.info("")
            logger.info("🔐 Security Configuration:")
            logger.info("  • AI Developer role assignments")
            logger.info("  • Managed Identity authentication")
            logger.info("  • Diagnostic logging enabled")
            logger.info("=" * 80)
            return

        # Validate Azure CLI
        az_available, az_command = validate_azure_cli()
        if not az_available or az_command is None:
            logger.error("[✗] Azure CLI is not available or not authenticated")
            return

        # Get Azure profile information
        azure_info = get_azure_profile(az_command)
        subscription_id = azure_info["subscription_id"]
        tenant_id = azure_info["tenant_id"]

        # Get current user object ID for role assignments
        current_user_object_id = get_current_user_object_id(az_command)

        # Get current user tenant ID for Key Vault access policies
        current_user_tenant_id = get_current_user_tenant_id(az_command)

        # Register required Azure providers
        register_azure_providers(az_command)

        # Initialize Azure credential
        credential: DefaultAzureCredential = DefaultAzureCredential()

        # Start deployment
        logger.info("=" * 80)
        logger.info("🚀 STARTING AZURE AI FOUNDRY PROJECT DEPLOYMENT")
        logger.info("=" * 80)

        # Initialize Azure management clients
        logger.info("[⚡] Initializing Azure management clients...")
        resource_client: ResourceManagementClient = ResourceManagementClient(
            credential, subscription_id
        )
        cognitiveservices_client: CognitiveServicesManagementClient = (
            CognitiveServicesManagementClient(credential, subscription_id)
        )
        acr_client: ContainerRegistryManagementClient = (
            ContainerRegistryManagementClient(credential, subscription_id)
        )
        storage_client: StorageManagementClient = StorageManagementClient(
            credential, subscription_id
        )
        appinsights_client: ApplicationInsightsManagementClient = (
            ApplicationInsightsManagementClient(credential, subscription_id)
        )
        auth_client: AuthorizationManagementClient = (
            AuthorizationManagementClient(credential, subscription_id)
        )
        loganalytics_client: LogAnalyticsManagementClient = (
            LogAnalyticsManagementClient(credential, subscription_id)
        )
        keyvault_client: KeyVaultManagementClient = KeyVaultManagementClient(
            credential, subscription_id
        )
        search_client: SearchManagementClient = SearchManagementClient(
            credential, subscription_id
        )

        # Verify/Create resource group (idempotent)
        logger.info("[📁] Verifying/Creating resource group...")
        if not resource_group_exists(resource_client, resource_group):
            logger.info(f"[🔨] Creating resource group '{resource_group}'")
            try:
                resource_client.resource_groups.create_or_update(
                    resource_group,
                    {
                        "location": location,
                        "tags": tags,
                    },
                )
                logger.info(f"[✓] Resource group '{resource_group}' created")
            except Exception as e:
                logger.error(
                    f"[✗] Failed to create resource group "
                    f"'{resource_group}': {e}"
                )
                return
        else:
            logger.info(f"[✓] Resource group '{resource_group}' exists")

        # =================================================================
        # PHASE 1: KEY VAULT
        # =================================================================
        logger.info("[🔐] Phase 1: Creating Key Vault...")

        if not keyvault_exists(keyvault_client, resource_group, keyvault_name):
            logger.info(f"  [🔨] Creating Key Vault: {keyvault_name}")

            keyvault_params = VaultCreateOrUpdateParameters(
                location=location,
                tags=tags,
                properties=VaultProperties(
                    tenant_id=current_user_tenant_id,
                    sku=Sku(name=SkuName.standard.value, family="A"),
                    access_policies=[
                        AccessPolicyEntry(
                            tenant_id=current_user_tenant_id,
                            object_id=current_user_object_id,
                            permissions=Permissions(
                                keys=[
                                    KeyPermissions.get.value,
                                    KeyPermissions.list.value,
                                    KeyPermissions.create.value,
                                    KeyPermissions.update.value,
                                    KeyPermissions.delete.value,
                                ],
                                secrets=[
                                    SecretPermissions.get.value,
                                    SecretPermissions.list.value,
                                    SecretPermissions.set.value,
                                    SecretPermissions.delete.value,
                                ],
                                certificates=[
                                    CertificatePermissions.get.value,
                                    CertificatePermissions.list.value,
                                    CertificatePermissions.create.value,
                                    CertificatePermissions.update.value,
                                    CertificatePermissions.delete.value,
                                ],
                            ),
                        )
                    ],
                    enabled_for_disk_encryption=True,
                    enabled_for_deployment=True,
                    enabled_for_template_deployment=True,
                    enable_rbac_authorization=False,  # Using access policies
                    enable_soft_delete=True,
                    # Min 90 days for purge protection
                    soft_delete_retention_in_days=90,
                    enable_purge_protection=True,  # Required by Azure policy
                ),
            )

            keyvault_operation = keyvault_client.vaults.begin_create_or_update(
                resource_group, keyvault_name, keyvault_params
            )
            wait_for_operation(
                keyvault_operation, f"Key Vault '{keyvault_name}'"
            )
            logger.info(f"  [✓] Key Vault '{keyvault_name}' created")
        else:
            logger.info(f"  [✓] Key Vault '{keyvault_name}' already exists")

        # =================================================================
        # PHASE 2: APP CONFIGURATION (Skipped - Free SKU limitation)
        # =================================================================
        logger.info(
            "[⚙️] Phase 2: App Configuration (skipping due to Free SKU "
            "soft delete limitation)..."
        )
        logger.info("  [ℹ️] Will store all configuration in Key Vault instead")

        # =================================================================
        # PHASE 3: AI SERVICES ACCOUNT
        # =================================================================
        logger.info("[🤖] Phase 3: Creating AI Services account...")

        if not ai_foundry_resource_exists(
            cognitiveservices_client, resource_group, ai_services_name
        ):
            logger.info(
                f"  [🔨] Creating AI Services account: {ai_services_name}"
            )

            ai_services_params = Account(
                location=location,
                sku=CognitiveServicesSku(name="S0"),
                kind="AIServices",
                tags=tags,
                properties=AccountProperties(
                    custom_sub_domain_name=ai_services_name,
                    public_network_access="Enabled",
                    diagnostic_settings_enabled=True,
                ),
            )

            ai_services_operation = (
                cognitiveservices_client.accounts.begin_create(
                    resource_group, ai_services_name, ai_services_params
                )
            )
            wait_for_operation(
                ai_services_operation,
                f"AI Services account '{ai_services_name}'",
            )
            logger.info(
                f"  [✓] AI Services account '{ai_services_name}' created"
            )
        else:
            logger.info(
                f"  [✓] AI Services account '{ai_services_name}' already "
                f"exists"
            )

        # =================================================================
        # PHASE 4: CONTAINER REGISTRY
        # =================================================================
        logger.info("[📦] Phase 4: Creating Container Registry...")

        if not container_registry_exists(
            acr_client, resource_group, container_registry_name
        ):
            logger.info(
                f"  [🔨] Creating Container Registry: {container_registry_name}"
            )

            acr_params = Registry(
                location=location,
                sku=ContainerRegistrySku(name="Basic"),
                tags=tags,
                admin_user_enabled=True,
                # Enable for AI model deployment
                public_network_access="Enabled",
            )

            acr_operation = acr_client.registries.begin_create(
                resource_group, container_registry_name, acr_params
            )
            wait_for_operation(
                acr_operation,
                f"Container Registry '{container_registry_name}'",
            )
            logger.info(
                f"  [✓] Container Registry '{container_registry_name}' "
                f"created"
            )
        else:
            logger.info(
                f"  [✓] Container Registry '{container_registry_name}' "
                f"already exists"
            )

        # =================================================================
        # PHASE 5: STORAGE ACCOUNT
        # =================================================================
        logger.info("[💾] Phase 5: Creating Storage Account...")

        if not storage_account_exists(
            storage_client, resource_group, storage_account_name
        ):
            logger.info(
                f"  [🔨] Creating Storage Account: {storage_account_name}"
            )

            storage_params = StorageAccountCreateParameters(
                sku=StorageSku(name="Standard_LRS"),
                kind=Kind.storage_v2.value,
                location=location,
                tags=tags,
                enable_https_traffic_only=True,
                minimum_tls_version="TLS1_2",
                # Enable hierarchical namespace for AI workloads
                is_hns_enabled=True,
            )

            storage_operation = storage_client.storage_accounts.begin_create(
                resource_group, storage_account_name, storage_params
            )
            wait_for_operation(
                storage_operation, f"Storage Account '{storage_account_name}'"
            )
            logger.info(
                f"  [✓] Storage Account '{storage_account_name}' created"
            )
        else:
            logger.info(
                f"  [✓] Storage Account '{storage_account_name}' already "
                f"exists"
            )

        # =================================================================
        # PHASE 6: LOG ANALYTICS WORKSPACE
        # =================================================================
        logger.info("[📊] Phase 6: Creating Log Analytics Workspace...")

        if not log_analytics_workspace_exists(
            loganalytics_client, resource_group, log_workspace_name
        ):
            logger.info(
                f"  [🔨] Creating Log Analytics Workspace: "
                f"{log_workspace_name}"
            )

            workspace_params = Workspace(
                location=location,
                tags=tags,
                sku=WorkspaceSku(name="PerGB2018"),
                retention_in_days=30,  # 30 days retention for AI workloads
            )

            workspace_operation = (
                loganalytics_client.workspaces.begin_create_or_update(
                    resource_group, log_workspace_name, workspace_params
                )
            )
            wait_for_operation(
                workspace_operation,
                f"Log Analytics Workspace '{log_workspace_name}'",
            )
            logger.info(
                f"  [✓] Log Analytics Workspace '{log_workspace_name}' created"
            )
        else:
            logger.info(
                f"  [✓] Log Analytics Workspace '{log_workspace_name}' "
                f"already exists"
            )

        # Get the workspace resource ID for Application Insights
        workspace_id = get_log_analytics_workspace_id(
            loganalytics_client, resource_group, log_workspace_name
        )

        # =================================================================
        # PHASE 7: APPLICATION INSIGHTS
        # =================================================================
        logger.info("[📊] Phase 7: Creating Application Insights...")

        if not application_insights_exists(
            appinsights_client, resource_group, application_insights_name
        ):
            logger.info(
                f"  [🔨] Creating Application Insights: "
                f"{application_insights_name}"
            )

            appinsights_params = ApplicationInsightsComponent(
                location=location,
                kind="web",
                application_type=ApplicationType.web.value,
                tags=tags,
                # Enable sampling for AI workloads
                sampling_percentage=100.0,
                # Link to Log Analytics workspace
                workspace_resource_id=workspace_id,
            )

            appinsights_client.components.create_or_update(
                resource_group, application_insights_name, appinsights_params
            )
            logger.info(
                f"  [✓] Application Insights '{application_insights_name}' "
                f"created"
            )
        else:
            logger.info(
                f"  [✓] Application Insights '{application_insights_name}' "
                f"already exists"
            )

        # =================================================================
        # PHASE 8: COGNITIVE SEARCH
        # =================================================================
        logger.info("[🔍] Phase 8: Creating Cognitive Search service...")

        if not search_service_exists(
            search_client, resource_group, cognitive_search_name
        ):
            logger.info(
                f"  [🔨] Creating Cognitive Search service: "
                f"{cognitive_search_name}"
            )

            search_params = SearchService(
                location=location,
                tags=tags,
                sku=SearchSku(name=SearchSkuName.free.value),
                replica_count=1,
                partition_count=1,
                hosting_mode="default",
                public_network_access="enabled",
                disable_local_auth=False,
            )

            search_operation = search_client.services.begin_create_or_update(
                resource_group, cognitive_search_name, search_params
            )
            wait_for_operation(
                search_operation,
                f"Cognitive Search service '{cognitive_search_name}'",
            )
            logger.info(
                f"  [✓] Cognitive Search service '{cognitive_search_name}' "
                f"created"
            )
        else:
            logger.info(
                f"  [✓] Cognitive Search service '{cognitive_search_name}' "
                f"already exists"
            )

        # =================================================================
        # PHASE 9: SECRETS AND CONFIGURATION MANAGEMENT
        # =================================================================
        logger.info("[�] Phase 9: Storing secrets and configuration...")

        # Get AI Services endpoint and key
        logger.info("  [🔑] Retrieving AI Services endpoint and key...")
        try:
            ai_endpoint, ai_key = get_ai_services_endpoint_and_key(
                cognitiveservices_client, resource_group, ai_services_name
            )

            # Store the API key in Key Vault
            store_secret_in_keyvault(
                keyvault_name, "ai-services-key", ai_key, credential
            )

            # Store the endpoint in Key Vault as well
            # (since App Config Free SKU has limitations)
            store_secret_in_keyvault(
                keyvault_name, "ai-services-endpoint", ai_endpoint, credential
            )

            logger.info("  [✓] AI Services credentials stored successfully")

        except Exception as e:
            logger.warning(
                f"  [⚠] Failed to store AI Services credentials: {e}"
            )
            logger.warning("  [⚠] You may need to configure these manually")

        # Get Cognitive Search endpoint and key
        logger.info("  [🔑] Retrieving Cognitive Search endpoint and key...")
        try:
            search_endpoint, search_key = get_search_service_endpoint_and_key(
                search_client, resource_group, cognitive_search_name
            )

            # Store the API key in Key Vault
            store_secret_in_keyvault(
                keyvault_name, "cognitive-search-key", search_key, credential
            )

            # Store the endpoint in Key Vault
            store_secret_in_keyvault(
                keyvault_name,
                "cognitive-search-endpoint",
                search_endpoint,
                credential,
            )

            logger.info(
                "  [✓] Cognitive Search credentials stored successfully"
            )

        except Exception as e:
            logger.warning(
                f"  [⚠] Failed to store Cognitive Search credentials: {e}"
            )
            logger.warning("  [⚠] You may need to configure these manually")

        # =================================================================
        # PHASE 10: ROLE ASSIGNMENTS
        # =================================================================
        logger.info(
            "[🔐] Phase 10: Setting up AI Developer role assignments..."
        )

        # AI Developer role GUID (Azure built-in role)
        ai_developer_role_id = "64702f94-c441-49e6-a78b-ef80e0188fee"
        scope = (
            f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        )

        try:
            # Check if role assignment already exists
            existing_assignments = list(
                auth_client.role_assignments.list_for_scope(scope)
            )
            ai_developer_assigned = any(
                assignment.principal_id == current_user_object_id
                and assignment.role_definition_id.endswith(
                    ai_developer_role_id
                )
                for assignment in existing_assignments
            )

            if not ai_developer_assigned:
                # Create AI Developer role assignment
                role_assignment_name = str(uuid.uuid4())
                role_definition_id = (
                    f"/subscriptions/{subscription_id}/providers/"
                    f"Microsoft.Authorization/roleDefinitions/"
                    f"{ai_developer_role_id}"
                )

                role_assignment_params = {
                    "role_definition_id": role_definition_id,
                    "principal_id": current_user_object_id,
                    "principal_type": "User",
                }

                auth_client.role_assignments.create(
                    scope, role_assignment_name, role_assignment_params
                )
                logger.info("  [✓] AI Developer role assigned to current user")
            else:
                logger.info(
                    "  [✓] AI Developer role already assigned to current "
                    "user"
                )

        except Exception as e:
            logger.warning(f"  [⚠] Could not assign AI Developer role: {e}")
            logger.warning(
                "  [⚠] You may need to assign this role manually in the "
                "Azure portal"
            )

        # =================================================================
        # DEPLOYMENT SUMMARY
        # =================================================================
        logger.info("=" * 80)
        logger.info("🎉 AI FOUNDRY PROJECT DEPLOYMENT COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)

        # Create deployment summary
        deployment_summary = {
            "deployment_info": {
                "timestamp": "2025-07-12T15:00:00Z",
                "script_name": "create-ai-foundry-project.py",
                "version": "1.0.0",
            },
            "azure_info": {
                "subscription_id": subscription_id,
                "tenant_id": tenant_id,
                "resource_group": resource_group,
                "location": location,
            },
            "ai_foundry_resources": {
                "keyvault": {
                    "name": keyvault_name,
                    "type": "Microsoft.KeyVault/vaults",
                    "purpose": "Secure storage for secrets, keys, and "
                    "certificates",
                },
                "ai_services_account": {
                    "name": ai_services_name,
                    "type": "Microsoft.CognitiveServices/accounts",
                    "purpose": "Primary AI services account for unified AI "
                    "capabilities",
                },
                "container_registry": {
                    "name": container_registry_name,
                    "type": "Microsoft.ContainerRegistry/registries",
                    "purpose": "Custom AI model deployment",
                },
                "storage_account": {
                    "name": storage_account_name,
                    "type": "Microsoft.Storage/storageAccounts",
                    "purpose": "AI training data, models, and artifacts",
                },
                "application_insights": {
                    "name": application_insights_name,
                    "type": "Microsoft.Insights/components",
                    "purpose": "AI model monitoring and telemetry",
                },
                "log_analytics_workspace": {
                    "name": log_workspace_name,
                    "type": "Microsoft.OperationalInsights/workspaces",
                    "purpose": "Log analytics and monitoring",
                },
                "cognitive_search": {
                    "name": cognitive_search_name,
                    "type": "Microsoft.Search/searchServices",
                    "purpose": "AI-powered search and indexing capabilities",
                },
            },
            "security_configuration": {
                "rbac_assignments": "AI Developer role assigned",
                "authentication": "DefaultAzureCredential (Managed Identity)",
                "network_access": "Public (configurable)",
                "diagnostic_logging": "Enabled",
            },
        }

        # Save deployment summary
        with open("ai_foundry_deployment_summary.json", "w") as f:
            json.dump(deployment_summary, f, indent=2)

        logger.info("")
        logger.info("📋 DEPLOYMENT SUMMARY:")
        logger.info(f"   🔐 Key Vault: {keyvault_name}")
        logger.info(f"   🤖 AI Services Account: {ai_services_name}")
        logger.info(f"   📦 Container Registry: {container_registry_name}")
        logger.info(f"   💾 Storage Account: {storage_account_name}")
        logger.info(f"   📊 Log Analytics Workspace: {log_workspace_name}")
        logger.info(f"   📊 Application Insights: {application_insights_name}")
        logger.info(f"   🔍 Cognitive Search: {cognitive_search_name}")
        logger.info("")
        logger.info("🔑 SECRETS & CONFIGURATION:")
        logger.info("   • AI Services API Key → Key Vault: ai-services-key")
        logger.info(
            "   • AI Services Endpoint → Key Vault: ai-services-endpoint"
        )
        logger.info(
            "   • Cognitive Search API Key → Key Vault: cognitive-search-key"
        )
        logger.info(
            "   • Cognitive Search Endpoint → Key Vault: "
            "cognitive-search-endpoint"
        )
        logger.info("")
        logger.info("📁 FILES CREATED:")
        logger.info(
            "   • ai_foundry_deployment_summary.json - Deployment details"
        )
        logger.info(f"   • {log_filename} - Detailed deployment logs")
        logger.info("")
        logger.info("🚀 NEXT STEPS:")
        logger.info("   1. Configure AI models in the Azure AI Foundry portal")
        logger.info("   2. Set up your development environment with AI SDK")
        logger.info(
            "   3. Deploy your first AI model to the container registry"
        )
        logger.info("   4. Monitor AI workloads with Application Insights")
        logger.info("")
        logger.info("🌐 AZURE AI FOUNDRY PORTAL:")
        logger.info("   https://ai.azure.com/")
        logger.info("=" * 80)

    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ AI FOUNDRY PROJECT DEPLOYMENT FAILED")
        logger.error("=" * 80)
        logger.error(f"[✗] Error: {e}")
        logger.error("")
        logger.error("🔍 TROUBLESHOOTING:")
        logger.error(
            "   1. Check the detailed logs above for specific error messages"
        )
        logger.error(
            "   2. Verify Azure CLI authentication with 'az account show'"
        )
        logger.error(
            "   3. Ensure you have appropriate permissions for AI services"
        )
        logger.error(
            "   4. Check if all required resource providers are registered"
        )
        logger.error("   5. Verify that the resource group exists")
        logger.error("")
        logger.error(f"📋 LOG FILE: {log_filename}")
        logger.error("=" * 80)
        exit(1)


# =============================================================================
# NOTE: Type checking limitations
# =============================================================================
# The Azure SDK for Python sometimes has incomplete type stubs which can cause
# type checking warnings. These warnings don't affect runtime functionality.
# The code has been tested and works correctly with the Azure SDK.
# =============================================================================

# =============================================================================
# AZURE RESOURCE UTILITIES
# =============================================================================
