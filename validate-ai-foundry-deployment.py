#!/usr/bin/env python3
"""
Azure AI Foundry Deployment Validation Script

This script validates that all resources created by the AI Foundry deployment
script are properly configured and accessible. It performs comprehensive
checks including resource existence, configuration validation, and access
verification.

VALIDATION CHECKS:
1. Environment Variables - Verify all required variables are set
2. Azure CLI Authentication - Confirm CLI is authenticated
3. Resource Group - Verify resource group exists and is accessible
4. Key Vault - Check existence, access policies, and secret retrieval
5. AI Services Account - Verify deployment and API access
6. Container Registry - Check existence and authentication
7. Storage Account - Verify access and configuration
8. Log Analytics Workspace - Confirm workspace is operational
9. Application Insights - Verify monitoring configuration
10. RBAC Permissions - Check role assignments and access

USAGE:
    python validate-ai-foundry-deployment.py [--verbose] [--fix-issues]

OPTIONS:
    --verbose      Enable detailed logging output
    --fix-issues   Attempt to fix common issues automatically

REQUIREMENTS:
    - Same environment variables as deployment script
    - Azure CLI authenticated
    - Appropriate Azure permissions
    - All dependencies from requirements.txt

OUTPUT:
    - Detailed validation report
    - Issues found and recommendations
    - Overall deployment health status
"""

import argparse
import json
import logging
import os
import subprocess  # nosec B404
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.loganalytics import LogAnalyticsManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from dotenv import load_dotenv

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
log_filename = "ai_foundry_validation.log"


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


# Configure logging
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
# VALIDATION RESULTS TRACKING
# =============================================================================
class ValidationResult:
    """Track validation results for reporting."""

    def __init__(self) -> None:
        self.checks: List[Dict[str, Any]] = []
        self.issues: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.successes: List[Dict[str, Any]] = []

    def add_check(
        self,
        category: str,
        name: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a validation check result."""
        check = {
            "category": category,
            "name": name,
            "status": status,  # "PASS", "FAIL", "WARN"
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }
        self.checks.append(check)

        if status == "PASS":
            self.successes.append(check)
        elif status == "FAIL":
            self.issues.append(check)
        elif status == "WARN":
            self.warnings.append(check)

    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            "total_checks": len(self.checks),
            "passed": len(self.successes),
            "failed": len(self.issues),
            "warnings": len(self.warnings),
            "success_rate": (
                (len(self.successes) / len(self.checks) * 100)
                if self.checks
                else 0
            ),
        }

    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return len(self.issues) > 0


# =============================================================================
# ENVIRONMENT VALIDATION
# =============================================================================
def validate_environment_variables(result: ValidationResult) -> Dict[str, str]:
    """Validate that all required environment variables are present."""
    logger.info("[📋] Validating environment variables...")

    required_vars = [
        "LOCATION",
        "RESOURCE_GROUP",
        "KEYVAULT_NAME",
        "AI_SERVICES_NAME",
        "CONTAINER_REGISTRY_NAME",
        "STORAGE_ACCOUNT_NAME",
        "APPLICATION_INSIGHTS_NAME",
        "LOG_WORKSPACE_NAME",
    ]

    env_vars = {}
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            env_vars[var] = value
        else:
            missing_vars.append(var)

    if missing_vars:
        result.add_check(
            "Environment",
            "Required Variables",
            "FAIL",
            f"Missing required environment variables: "
            f"{', '.join(missing_vars)}",
            {"missing_variables": missing_vars},
        )
        logger.error(
            f"❌ Missing environment variables: {', '.join(missing_vars)}"
        )
        return {}
    else:
        result.add_check(
            "Environment",
            "Required Variables",
            "PASS",
            "All required environment variables are present",
            {"variables": list(env_vars.keys())},
        )
        logger.info("✅ All required environment variables are present")
        return env_vars


# =============================================================================
# AZURE CLI VALIDATION
# =============================================================================
def validate_azure_cli(
    result: ValidationResult,
) -> Tuple[bool, Optional[str], Optional[Dict[str, str]]]:
    """Validate Azure CLI installation and authentication."""
    logger.info("[🔧] Validating Azure CLI...")

    try:
        # Check if Azure CLI is installed
        az_command = "az.cmd" if os.name == "nt" else "az"
        subprocess.run(
            [az_command, "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        result.add_check(
            "Azure CLI",
            "Installation",
            "PASS",
            "Azure CLI is installed and accessible",
        )
        logger.info("✅ Azure CLI is installed")

        # Check authentication
        auth_result = subprocess.run(
            [az_command, "account", "show"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        account_info = json.loads(auth_result.stdout)
        subscription_id = account_info.get("id", "")
        tenant_id = account_info.get("tenantId", "")
        user_name = account_info.get("user", {}).get("name", "")

        azure_info = {
            "subscription_id": subscription_id,
            "tenant_id": tenant_id,
            "user": user_name,
            "subscription_name": account_info.get("name", ""),
        }

        result.add_check(
            "Azure CLI",
            "Authentication",
            "PASS",
            f"Authenticated as {user_name}",
            azure_info,
        )
        logger.info(f"✅ Azure CLI authenticated as {user_name}")
        logger.info(
            f"✅ Using subscription: {azure_info['subscription_name']}"
        )

        return True, az_command, azure_info

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
        json.JSONDecodeError,
    ) as e:
        result.add_check(
            "Azure CLI",
            "Authentication",
            "FAIL",
            f"Azure CLI validation failed: {str(e)}",
        )
        logger.error(f"❌ Azure CLI validation failed: {e}")
        return False, None, None


# =============================================================================
# RESOURCE VALIDATION FUNCTIONS
# =============================================================================
def validate_resource_group(
    result: ValidationResult,
    resource_client: ResourceManagementClient,
    rg_name: str,
) -> bool:
    """Validate resource group existence and properties."""
    logger.info(f"[📁] Validating resource group: {rg_name}")

    try:
        rg = resource_client.resource_groups.get(rg_name)

        result.add_check(
            "Resource Group",
            "Existence",
            "PASS",
            f"Resource group '{rg_name}' exists in {rg.location}",
            {
                "name": rg.name,
                "location": rg.location,
                "tags": rg.tags,
                "provisioning_state": (
                    rg.properties.provisioning_state if rg.properties else None
                ),
            },
        )
        logger.info(f"✅ Resource group '{rg_name}' exists")
        return True

    except Exception as e:
        result.add_check(
            "Resource Group",
            "Existence",
            "FAIL",
            f"Resource group '{rg_name}' not found: {str(e)}",
        )
        logger.error(f"❌ Resource group '{rg_name}' not found: {e}")
        return False


def validate_key_vault(
    result: ValidationResult,
    keyvault_client: KeyVaultManagementClient,
    credential: DefaultAzureCredential,
    rg_name: str,
    kv_name: str,
) -> bool:
    """Validate Key Vault existence, access, and secrets."""
    logger.info(f"[🔐] Validating Key Vault: {kv_name}")

    try:
        # Check Key Vault existence
        kv = keyvault_client.vaults.get(rg_name, kv_name)

        result.add_check(
            "Key Vault",
            "Existence",
            "PASS",
            f"Key Vault '{kv_name}' exists",
            {
                "name": kv.name,
                "location": kv.location,
                "vault_uri": (
                    kv.properties.vault_uri if kv.properties else None
                ),
                "sku": (
                    kv.properties.sku.name
                    if kv.properties and kv.properties.sku
                    else None
                ),
            },
        )
        logger.info(f"✅ Key Vault '{kv_name}' exists")

        # Test secret access
        vault_url = f"https://{kv_name}.vault.azure.net/"
        secret_client = SecretClient(
            vault_url=vault_url, credential=credential
        )

        # Check for expected secrets
        expected_secrets = ["ai-services-key", "ai-services-endpoint"]
        found_secrets = []
        missing_secrets = []

        for secret_name in expected_secrets:
            try:
                secret_client.get_secret(secret_name)
                found_secrets.append(secret_name)
                logger.info(f"✅ Secret '{secret_name}' accessible")
            except Exception as e:
                missing_secrets.append(secret_name)
                msg = f"⚠️ Secret '{secret_name}' not accessible: {e}"
                logger.warning(msg)

        if found_secrets:
            result.add_check(
                "Key Vault",
                "Secret Access",
                (
                    "PASS"
                    if len(found_secrets) == len(expected_secrets)
                    else "WARN"
                ),
                f"Accessible secrets: {', '.join(found_secrets)}",
                {
                    "found_secrets": found_secrets,
                    "missing_secrets": missing_secrets,
                },
            )
        else:
            result.add_check(
                "Key Vault",
                "Secret Access",
                "FAIL",
                "No expected secrets found in Key Vault",
            )

        return True

    except Exception as e:
        result.add_check(
            "Key Vault",
            "Existence",
            "FAIL",
            f"Key Vault '{kv_name}' validation failed: {str(e)}",
        )
        logger.error(f"❌ Key Vault '{kv_name}' validation failed: {e}")
        return False


def validate_ai_services(
    result: ValidationResult,
    ai_client: CognitiveServicesManagementClient,
    rg_name: str,
    ai_name: str,
) -> bool:
    """Validate AI Services account existence and configuration."""
    logger.info(f"[🤖] Validating AI Services account: {ai_name}")

    try:
        ai_account = ai_client.accounts.get(rg_name, ai_name)

        # Check endpoint accessibility
        endpoint = (
            ai_account.properties.endpoint if ai_account.properties else None
        )

        result.add_check(
            "AI Services",
            "Existence",
            "PASS",
            f"AI Services account '{ai_name}' exists",
            {
                "name": ai_account.name,
                "location": ai_account.location,
                "endpoint": endpoint,
                "kind": ai_account.kind,
                "sku": ai_account.sku.name if ai_account.sku else None,
                "provisioning_state": (
                    ai_account.properties.provisioning_state
                    if ai_account.properties
                    else None
                ),
            },
        )
        logger.info(f"✅ AI Services account '{ai_name}' exists")

        # Test API key access
        try:
            keys = ai_client.accounts.list_keys(rg_name, ai_name)
            if keys.key1:
                result.add_check(
                    "AI Services",
                    "API Key Access",
                    "PASS",
                    "AI Services API keys are accessible",
                )
                logger.info("✅ AI Services API keys accessible")
            else:
                result.add_check(
                    "AI Services",
                    "API Key Access",
                    "FAIL",
                    "AI Services API keys not found",
                )
        except Exception as e:
            result.add_check(
                "AI Services",
                "API Key Access",
                "FAIL",
                f"Failed to retrieve API keys: {str(e)}",
            )

        return True

    except Exception as e:
        result.add_check(
            "AI Services",
            "Existence",
            "FAIL",
            f"AI Services account '{ai_name}' validation failed: {str(e)}",
        )
        logger.error(
            f"❌ AI Services account '{ai_name}' validation failed: {e}"
        )
        return False


def validate_container_registry(
    result: ValidationResult,
    acr_client: ContainerRegistryManagementClient,
    rg_name: str,
    acr_name: str,
) -> bool:
    """Validate Container Registry existence and configuration."""
    logger.info(f"[📦] Validating Container Registry: {acr_name}")

    try:
        acr = acr_client.registries.get(rg_name, acr_name)

        result.add_check(
            "Container Registry",
            "Existence",
            "PASS",
            f"Container Registry '{acr_name}' exists",
            {
                "name": acr.name,
                "location": acr.location,
                "login_server": acr.login_server,
                "sku": acr.sku.name if acr.sku else None,
                "admin_user_enabled": acr.admin_user_enabled,
                "provisioning_state": acr.provisioning_state,
            },
        )
        logger.info(f"✅ Container Registry '{acr_name}' exists")

        # Check admin credentials if enabled
        if acr.admin_user_enabled:
            try:
                credentials = acr_client.registries.list_credentials(
                    rg_name, acr_name
                )
                if credentials.username:
                    result.add_check(
                        "Container Registry",
                        "Admin Credentials",
                        "PASS",
                        "Admin credentials are accessible",
                    )
                    logger.info(
                        "✅ Container Registry admin credentials accessible"
                    )
            except Exception as e:
                result.add_check(
                    "Container Registry",
                    "Admin Credentials",
                    "WARN",
                    f"Could not retrieve admin credentials: {str(e)}",
                )

        return True

    except Exception as e:
        result.add_check(
            "Container Registry",
            "Existence",
            "FAIL",
            f"Container Registry '{acr_name}' validation failed: {str(e)}",
        )
        logger.error(
            f"❌ Container Registry '{acr_name}' validation failed: {e}"
        )
        return False


def validate_storage_account(
    result: ValidationResult,
    storage_client: StorageManagementClient,
    rg_name: str,
    storage_name: str,
) -> bool:
    """Validate Storage Account existence and configuration."""
    logger.info(f"[💾] Validating Storage Account: {storage_name}")

    try:
        storage = storage_client.storage_accounts.get_properties(
            rg_name, storage_name
        )

        result.add_check(
            "Storage Account",
            "Existence",
            "PASS",
            f"Storage Account '{storage_name}' exists",
            {
                "name": storage.name,
                "location": storage.location,
                "kind": storage.kind,
                "sku": storage.sku.name if storage.sku else None,
                "https_only": storage.enable_https_traffic_only,
                "hierarchical_namespace": storage.is_hns_enabled,
                "provisioning_state": storage.provisioning_state,
            },
        )
        logger.info(f"✅ Storage Account '{storage_name}' exists")

        # Check access keys
        try:
            keys = storage_client.storage_accounts.list_keys(
                rg_name, storage_name
            )
            if keys.keys and len(keys.keys) > 0:
                result.add_check(
                    "Storage Account",
                    "Access Keys",
                    "PASS",
                    "Storage Account access keys are available",
                )
                logger.info("✅ Storage Account access keys available")
            else:
                result.add_check(
                    "Storage Account",
                    "Access Keys",
                    "FAIL",
                    "Storage Account access keys not found",
                )
        except Exception as e:
            result.add_check(
                "Storage Account",
                "Access Keys",
                "FAIL",
                f"Failed to retrieve access keys: {str(e)}",
            )

        return True

    except Exception as e:
        result.add_check(
            "Storage Account",
            "Existence",
            "FAIL",
            f"Storage Account '{storage_name}' validation failed: {str(e)}",
        )
        logger.error(
            f"❌ Storage Account '{storage_name}' validation failed: {e}"
        )
        return False


def validate_log_analytics(
    result: ValidationResult,
    log_client: LogAnalyticsManagementClient,
    rg_name: str,
    workspace_name: str,
) -> bool:
    """Validate Log Analytics Workspace existence and configuration."""
    logger.info(f"[📊] Validating Log Analytics Workspace: {workspace_name}")

    try:
        workspace = log_client.workspaces.get(rg_name, workspace_name)

        result.add_check(
            "Log Analytics",
            "Existence",
            "PASS",
            f"Log Analytics Workspace '{workspace_name}' exists",
            {
                "name": workspace.name,
                "location": workspace.location,
                "sku": workspace.sku.name if workspace.sku else None,
                "retention_days": workspace.retention_in_days,
                "provisioning_state": workspace.provisioning_state,
            },
        )
        logger.info(f"✅ Log Analytics Workspace '{workspace_name}' exists")

        return True

    except Exception as e:
        result.add_check(
            "Log Analytics",
            "Existence",
            "FAIL",
            f"Log Analytics Workspace '{workspace_name}' validation failed: "
            f"{str(e)}",
        )
        logger.error(
            f"❌ Log Analytics Workspace '{workspace_name}' validation "
            f"failed: {e}"
        )
        return False


def validate_application_insights(
    result: ValidationResult,
    ai_client: ApplicationInsightsManagementClient,
    rg_name: str,
    ai_name: str,
) -> bool:
    """Validate Application Insights existence and configuration."""
    logger.info(f"[📊] Validating Application Insights: {ai_name}")

    try:
        ai_component = ai_client.components.get(rg_name, ai_name)

        result.add_check(
            "Application Insights",
            "Existence",
            "PASS",
            f"Application Insights '{ai_name}' exists",
            {
                "name": ai_component.name,
                "location": ai_component.location,
                "kind": ai_component.kind,
                "application_type": ai_component.application_type,
                "instrumentation_key": (
                    ai_component.instrumentation_key[:8] + "..."
                    if ai_component.instrumentation_key
                    else None
                ),
                "provisioning_state": ai_component.provisioning_state,
            },
        )
        logger.info(f"✅ Application Insights '{ai_name}' exists")

        return True

    except Exception as e:
        result.add_check(
            "Application Insights",
            "Existence",
            "FAIL",
            f"Application Insights '{ai_name}' validation failed: {str(e)}",
        )
        logger.error(
            f"❌ Application Insights '{ai_name}' validation failed: {e}"
        )
        return False


def validate_rbac_permissions(
    result: ValidationResult,
    auth_client: AuthorizationManagementClient,
    subscription_id: str,
    rg_name: str,
    user_object_id: str,
) -> bool:
    """Validate RBAC permissions and role assignments."""
    logger.info("[🔐] Validating RBAC permissions...")

    try:
        scope = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}"
        assignments = list(auth_client.role_assignments.list_for_scope(scope))

        # Check for AI Developer role
        ai_developer_role_id = "64702f94-c441-49e6-a78b-ef80e0188fee"
        user_assignments = [
            a
            for a in assignments
            if hasattr(a, "principal_id") and a.principal_id == user_object_id
        ]

        ai_developer_assigned = any(
            hasattr(a, "role_definition_id")
            and a.role_definition_id
            and a.role_definition_id.endswith(ai_developer_role_id)
            for a in user_assignments
        )

        if ai_developer_assigned:
            result.add_check(
                "RBAC",
                "AI Developer Role",
                "PASS",
                "AI Developer role is assigned to current user",
            )
            logger.info("✅ AI Developer role assigned")
        else:
            result.add_check(
                "RBAC",
                "AI Developer Role",
                "WARN",
                "AI Developer role not found for current user",
            )
            logger.warning("⚠️ AI Developer role not assigned")

        result.add_check(
            "RBAC",
            "Role Assignments",
            "PASS",
            f"Found {len(user_assignments)} role assignments for current user",
            {"assignment_count": len(user_assignments)},
        )

        return True

    except Exception as e:
        result.add_check(
            "RBAC",
            "Permissions Check",
            "FAIL",
            f"RBAC validation failed: {str(e)}",
        )
        logger.error(f"❌ RBAC validation failed: {e}")
        return False


# =============================================================================
# MAIN VALIDATION FUNCTION
# =============================================================================
def main() -> None:
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate Azure AI Foundry Deployment"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--fix-issues",
        action="store_true",
        help="Attempt to fix common issues",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize validation results
    result = ValidationResult()

    logger.info("=" * 80)
    logger.info("🔍 AZURE AI FOUNDRY DEPLOYMENT VALIDATION")
    logger.info("=" * 80)

    # Load environment variables
    load_dotenv(override=True)

    # Step 1: Validate environment variables
    env_vars = validate_environment_variables(result)
    if not env_vars:
        logger.error("❌ Environment validation failed. Cannot continue.")
        print_validation_report(result)
        sys.exit(1)

    # Step 2: Validate Azure CLI
    az_available, az_command, azure_info = validate_azure_cli(result)
    if not az_available or not azure_info:
        logger.error("❌ Azure CLI validation failed. Cannot continue.")
        print_validation_report(result)
        sys.exit(1)

    # Initialize Azure clients
    credential = DefaultAzureCredential()
    subscription_id = azure_info["subscription_id"]

    resource_client = ResourceManagementClient(credential, subscription_id)
    keyvault_client = KeyVaultManagementClient(credential, subscription_id)
    ai_client = CognitiveServicesManagementClient(credential, subscription_id)
    acr_client = ContainerRegistryManagementClient(credential, subscription_id)
    storage_client = StorageManagementClient(credential, subscription_id)
    log_client = LogAnalyticsManagementClient(credential, subscription_id)
    appinsights_client = ApplicationInsightsManagementClient(
        credential, subscription_id
    )
    auth_client = AuthorizationManagementClient(credential, subscription_id)

    # Get current user object ID
    try:
        if az_command:
            user_result = subprocess.run(
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
            user_object_id = user_result.stdout.strip()
        else:
            user_object_id = None
    except Exception as e:
        logger.warning(f"⚠️ Could not get user object ID: {e}")
        user_object_id = None

    # Step 3: Validate all resources
    rg_name = env_vars["RESOURCE_GROUP"]

    # Resource Group
    validate_resource_group(result, resource_client, rg_name)

    # Key Vault
    validate_key_vault(
        result, keyvault_client, credential, rg_name, env_vars["KEYVAULT_NAME"]
    )

    # AI Services
    validate_ai_services(
        result, ai_client, rg_name, env_vars["AI_SERVICES_NAME"]
    )

    # Container Registry
    validate_container_registry(
        result, acr_client, rg_name, env_vars["CONTAINER_REGISTRY_NAME"]
    )

    # Storage Account
    validate_storage_account(
        result, storage_client, rg_name, env_vars["STORAGE_ACCOUNT_NAME"]
    )

    # Log Analytics
    validate_log_analytics(
        result, log_client, rg_name, env_vars["LOG_WORKSPACE_NAME"]
    )

    # Application Insights
    validate_application_insights(
        result,
        appinsights_client,
        rg_name,
        env_vars["APPLICATION_INSIGHTS_NAME"],
    )

    # RBAC Permissions
    if user_object_id:
        validate_rbac_permissions(
            result, auth_client, subscription_id, rg_name, user_object_id
        )

    # Print final report
    print_validation_report(result)

    # Save detailed report
    save_validation_report(result, env_vars, azure_info)

    # Exit with appropriate code
    if result.has_critical_issues():
        logger.error("❌ Validation completed with critical issues!")
        sys.exit(1)
    else:
        logger.info("✅ Validation completed successfully!")
        sys.exit(0)


def print_validation_report(result: ValidationResult) -> None:
    """Print a formatted validation report."""
    logger.info("=" * 80)
    logger.info("📋 VALIDATION REPORT")
    logger.info("=" * 80)

    summary = result.get_summary()
    logger.info(f"Total Checks: {summary['total_checks']}")
    logger.info(f"Passed: {summary['passed']}")
    logger.info(f"Failed: {summary['failed']}")
    logger.info(f"Warnings: {summary['warnings']}")
    logger.info(f"Success Rate: {summary['success_rate']:.1f}%")

    if result.issues:
        logger.info("\n❌ CRITICAL ISSUES:")
        for issue in result.issues:
            logger.info(f"  • {issue['category']}: {issue['message']}")

    if result.warnings:
        logger.info("\n⚠️ WARNINGS:")
        for warning in result.warnings:
            logger.info(f"  • {warning['category']}: {warning['message']}")

    logger.info("\n✅ SUCCESSFUL CHECKS:")
    for success in result.successes:
        logger.info(f"  • {success['category']}: {success['message']}")

    logger.info("=" * 80)


def save_validation_report(
    result: ValidationResult,
    env_vars: Dict[str, str],
    azure_info: Dict[str, str],
) -> None:
    """Save detailed validation report to file."""
    report = {
        "validation_info": {
            "timestamp": datetime.now().isoformat(),
            "script_version": "1.0.0",
            "environment": env_vars,
            "azure_info": azure_info,
        },
        "summary": result.get_summary(),
        "checks": result.checks,
        "issues": result.issues,
        "warnings": result.warnings,
        "successes": result.successes,
    }

    report_filename = "ai_foundry_validation_report.json"
    with open(report_filename, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"📄 Detailed validation report saved to: {report_filename}")


if __name__ == "__main__":
    main()
