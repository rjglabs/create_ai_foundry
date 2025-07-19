#!/usr/bin/env python3
"""
Azure AI Foundry Resource Quick Check

This script provides a quick status check of all resources created by the
AI Foundry deployment script. It's designed for fast verification and
troubleshooting.

USAGE:
    python quick-resource-check.py

FEATURES:
    - Fast resource existence check
    - Resource status overview
    - Key Vault secret verification
    - Color-coded output
    - Minimal dependencies
"""

import os
import sys
from typing import Dict, List, Optional, Set, Tuple

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.mgmt.resource import ResourceManagementClient
from dotenv import load_dotenv


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{title}{Colors.END}")
    print(f"{Colors.CYAN}{'=' * len(title)}{Colors.END}")


def print_status(item: str, status: str, details: str = "") -> None:
    """Print a status line with color coding."""
    if status == "✅":
        color = Colors.GREEN
    elif status == "❌":
        color = Colors.RED
    else:
        color = Colors.YELLOW

    print(f"{color}{status}{Colors.END} {item}")
    if details:
        print(f"    {Colors.WHITE}{details}{Colors.END}")


def get_azure_subscription_info() -> (
    Tuple[Optional[str], Optional[DefaultAzureCredential]]
):
    """Get current Azure subscription information."""
    try:
        credential = DefaultAzureCredential()

        # Try to get subscription info from environment or default
        import subprocess  # nosec B404

        az_command = "az.cmd" if os.name == "nt" else "az"
        result = subprocess.run(
            [az_command, "account", "show", "--query", "id", "-o", "tsv"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            subscription_id = result.stdout.strip()
            return subscription_id, credential
        else:
            return None, None

    except Exception:
        return None, None


def check_resource_group(
    resource_client: ResourceManagementClient, rg_name: str
) -> bool:
    """Check if resource group exists."""
    try:
        resource_client.resource_groups.get(rg_name)
        return True
    except Exception:
        return False


def check_resources_in_group(
    resource_client: ResourceManagementClient, rg_name: str
) -> Dict[str, List[str]]:
    """Get all resources in the resource group organized by type."""
    resources_by_type: Dict[str, List[str]] = {}

    try:
        # Use the list method to get all resources in the resource group
        resources = resource_client.resources.list_by_resource_group(
            resource_group_name=rg_name
        )

        for resource in resources:
            # Handle potential None values safely using try-except
            try:
                resource_type = resource.type
                resource_name = resource.name

                if resource_type and resource_name:
                    if resource_type not in resources_by_type:
                        resources_by_type[resource_type] = []
                    resources_by_type[resource_type].append(resource_name)
            except AttributeError:
                # Skip resources without type or name
                continue

    except Exception:
        # Log and continue with empty dict - this is expected behavior
        # when resource group doesn't exist or has no resources
        pass  # nosec B110

    return resources_by_type


def check_key_vault_secrets(
    keyvault_name: str, credential: DefaultAzureCredential
) -> Dict[str, bool]:
    """Check Key Vault secrets."""
    secrets_status: Dict[str, bool] = {}
    expected_secrets = [
        "ai-services-key",
        "ai-services-endpoint",
        "cognitive-search-admin-key",
        "cognitive-search-query-key",
        "cognitive-search-endpoint",
        "speechtotext-endpoint",
        "texttospeech-endpoint",
        "translator-endpoint",
    ]

    try:
        vault_url = f"https://{keyvault_name}.vault.azure.net/"
        secret_client = SecretClient(
            vault_url=vault_url, credential=credential
        )

        for secret_name in expected_secrets:
            try:
                secret = secret_client.get_secret(secret_name)
                secrets_status[secret_name] = (
                    secret.value is not None and len(secret.value.strip()) > 0
                )
            except Exception:
                secrets_status[secret_name] = False

    except Exception:
        for secret_name in expected_secrets:
            secrets_status[secret_name] = False

    return secrets_status


def get_required_env_vars() -> Tuple[Dict[str, str], List[str]]:
    """Get required environment variables and return them with missing ones."""
    required_vars = [
        "RESOURCE_GROUP",
        "KEYVAULT_NAME",
        "AI_SERVICES_NAME",
        "CONTAINER_REGISTRY_NAME",
        "STORAGE_ACCOUNT_NAME",
        "LOG_WORKSPACE_NAME",
        "APPLICATION_INSIGHTS_NAME",
        "COGNITIVE_SEARCH_NAME",
    ]

    env_vars: Dict[str, str] = {}
    missing_vars: List[str] = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            env_vars[var] = value
        else:
            missing_vars.append(var)

    return env_vars, missing_vars


def get_expected_resources(env_vars: Dict[str, str]) -> Dict[str, str]:
    """Get expected resources configuration."""
    return {
        "Microsoft.KeyVault/vaults": env_vars["KEYVAULT_NAME"],
        "Microsoft.CognitiveServices/accounts": env_vars["AI_SERVICES_NAME"],
        "Microsoft.ContainerRegistry/registries": env_vars[
            "CONTAINER_REGISTRY_NAME"
        ],
        "Microsoft.Storage/storageAccounts": env_vars["STORAGE_ACCOUNT_NAME"],
        "Microsoft.OperationalInsights/workspaces": env_vars[
            "LOG_WORKSPACE_NAME"
        ],
        "Microsoft.Insights/components": env_vars["APPLICATION_INSIGHTS_NAME"],
        "Microsoft.Search/searchServices": env_vars["COGNITIVE_SEARCH_NAME"],
    }


def get_auto_created_resources() -> Set[str]:
    """Get set of auto-created resources that are expected."""
    return {
        # Smart detection rules for App Insights
        "microsoft.alertsmanagement/smartDetectorAlertRules",
        # Action groups for alerting
        "microsoft.insights/actiongroups",
        # Case variations
        "Microsoft.AlertsManagement/smartDetectorAlertRules",
        "Microsoft.Insights/actionGroups",
        # Web tests if created
        "Microsoft.Insights/webtests",
        # Workbooks if created
        "Microsoft.Insights/workbooks",
    }


def validate_resources(
    resources_by_type: Dict[str, List[str]], expected_resources: Dict[str, str]
) -> None:
    """Validate that expected resources exist."""
    for resource_type, expected_name in expected_resources.items():
        if resource_type in resources_by_type:
            found_resource_names = resources_by_type[resource_type]
            if expected_name in found_resource_names:
                print_status(
                    f"{resource_type.split('/')[-1]}",
                    "✅",
                    f"'{expected_name}' found",
                )
            else:
                print_status(
                    f"{resource_type.split('/')[-1]}",
                    "❌",
                    f"'{expected_name}' not found",
                )
                print_status(
                    "",
                    "⚠️",
                    f"Found instead: {', '.join(found_resource_names)}",
                )
        else:
            print_status(
                f"{resource_type.split('/')[-1]}",
                "❌",
                "No resources of this type found",
            )


def check_unexpected_resources(
    resources_by_type: Dict[str, List[str]],
    expected_resources: Dict[str, str],
    auto_created_resources: Set[str],
) -> None:
    """Check for unexpected resources."""
    all_expected_types = (
        set(expected_resources.keys()) | auto_created_resources
    )
    unexpected_types = set(resources_by_type.keys()) - all_expected_types

    if unexpected_types:
        print_status(
            "Unexpected Resources",
            "⚠️",
            f"Found: {', '.join(unexpected_types)}",
        )

    # Show auto-created resources as informational
    found_auto_created = set(resources_by_type.keys()) & auto_created_resources
    if found_auto_created:
        print_status(
            "Auto-created Resources",
            "ℹ️",
            f"Found: {', '.join(found_auto_created)}",
        )
        print_status(
            "",
            "ℹ️",
            "These are automatically created by Azure and are expected",
        )


def print_summary(
    expected_resources: Dict[str, str],
    resources_by_type: Dict[str, List[str]],
    secrets_status: Dict[str, bool],
) -> None:
    """Print deployment summary."""
    print_header("📊 Summary")

    total_resources = len(expected_resources)
    found_resources = sum(
        1
        for rt, name in expected_resources.items()
        if rt in resources_by_type and name in resources_by_type[rt]
    )

    total_secrets = len(secrets_status)
    accessible_secrets = sum(1 for status in secrets_status.values() if status)

    print(
        f"{Colors.BOLD}Resources:{Colors.END} "
        f"{found_resources}/{total_resources} found"
    )
    print(
        f"{Colors.BOLD}Secrets:{Colors.END} "
        f"{accessible_secrets}/{total_secrets} accessible"
    )

    if (
        found_resources == total_resources
        and accessible_secrets == total_secrets
    ):
        print(
            f"\n{Colors.GREEN}{Colors.BOLD}✅ All resources and secrets "
            f"are accessible!{Colors.END}"
        )
        print(
            f"{Colors.GREEN}Your AI Foundry deployment is ready to use."
            f"{Colors.END}"
        )

        print(f"\n{Colors.CYAN}🚀 Next Steps:{Colors.END}")
        print("• Visit Azure AI Foundry portal: https://ai.azure.com/")
        print("• Start building your AI applications")
        print("• Monitor your resources in Azure portal")
    else:
        print(
            f"\n{Colors.RED}{Colors.BOLD}❌ Some resources or secrets "
            f"are missing!{Colors.END}"
        )
        print(
            f"{Colors.RED}Please check the deployment logs and re-run "
            f"the deployment script.{Colors.END}"
        )

        print(f"\n{Colors.YELLOW}🔧 Troubleshooting:{Colors.END}")
        print("• Check deployment logs: ai_foundry_deployment.log")
        print("• Re-run: python create-ai-foundry-project.py")
        print("• Verify Azure permissions")

        sys.exit(1)


def main() -> None:
    """Main function."""
    print_header("🔍 Azure AI Foundry Resource Quick Check")

    # Load environment variables
    load_dotenv(override=True)

    # Check required environment variables
    env_vars, missing_vars = get_required_env_vars()

    if missing_vars:
        print_status(
            "Environment Variables",
            "❌",
            f"Missing: {', '.join(missing_vars)}",
        )
        sys.exit(1)
    else:
        print_status(
            "Environment Variables", "✅", "All required variables found"
        )

    # Check Azure authentication
    subscription_id, credential = get_azure_subscription_info()

    if not subscription_id or not credential:
        print_status(
            "Azure Authentication",
            "❌",
            "Not authenticated or subscription not found",
        )
        sys.exit(1)
    else:
        print_status(
            "Azure Authentication",
            "✅",
            f"Subscription: {subscription_id[:8]}...",
        )

    # Initialize resource client
    try:
        resource_client = ResourceManagementClient(credential, subscription_id)
        print_status("Azure Resource Client", "✅", "Successfully initialized")
    except Exception as e:
        print_status(
            "Azure Resource Client", "❌", f"Failed to initialize: {e}"
        )
        sys.exit(1)

    # Check resource group
    rg_name = env_vars["RESOURCE_GROUP"]
    if check_resource_group(resource_client, rg_name):
        print_status("Resource Group", "✅", f"'{rg_name}' exists")
    else:
        print_status("Resource Group", "❌", f"'{rg_name}' not found")
        sys.exit(1)

    # Check resources in group
    print_header("📦 Resources in Resource Group")
    resources_by_type = check_resources_in_group(resource_client, rg_name)
    expected_resources = get_expected_resources(env_vars)

    # Validate resources
    validate_resources(resources_by_type, expected_resources)

    # Check for unexpected resources
    auto_created_resources = get_auto_created_resources()
    check_unexpected_resources(
        resources_by_type, expected_resources, auto_created_resources
    )

    # Check Key Vault secrets
    print_header("🔐 Key Vault Secrets")
    secrets_status = check_key_vault_secrets(
        env_vars["KEYVAULT_NAME"], credential
    )

    for secret_name, is_accessible in secrets_status.items():
        if is_accessible:
            print_status(secret_name, "✅", "Accessible and contains value")
        else:
            print_status(secret_name, "❌", "Not accessible or empty")

    # Print summary
    print_summary(expected_resources, resources_by_type, secrets_status)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Check interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {e}{Colors.END}")
        sys.exit(1)
