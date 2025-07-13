#!/usr/bin/env python3
"""
Azure AI Foundry Deployment Summary

This script provides a comprehensive overview of your AI Foundry deployment,
including resource status, access information, and next steps for getting
started with AI development.

USAGE:
    python deployment-summary.py

FEATURES:
    - Complete deployment status overview
    - Resource access information
    - Next steps for AI development
    - Troubleshooting guidance
    - Cost estimation and monitoring setup
"""

import json
import os
import sys
from typing import Any, Dict, List, cast

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
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
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def print_header(title: str, char: str = "=") -> None:
    """Print a formatted header with colors."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{title}{Colors.END}")
    print(f"{Colors.CYAN}{char * len(title)}{Colors.END}")


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BLUE}{'-' * len(title)}{Colors.END}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def get_deployment_summary() -> Dict[str, Any]:
    """Load and return the deployment summary."""
    summary_file = "ai_foundry_deployment_summary.json"
    if os.path.exists(summary_file):
        with open(summary_file, "r") as f:
            data = json.load(f)
            return cast(Dict[str, Any], data if isinstance(data, dict) else {})
    return {}


def get_validation_report() -> Dict[str, Any]:
    """Load and return the validation report."""
    report_file = "ai_foundry_validation_report.json"
    if os.path.exists(report_file):
        with open(report_file, "r") as f:
            data = json.load(f)
            return cast(Dict[str, Any], data if isinstance(data, dict) else {})
    return {}


def get_resource_costs() -> Dict[str, str]:
    """Estimate monthly costs for deployed resources."""
    return {
        "Key Vault": "$0.03/10,000 operations",
        "AI Services (S0)": "$22.00/month base + usage",
        "Container Registry (Basic)": "$5.00/month + storage",
        "Storage Account": "$0.024/GB/month + operations",
        "Log Analytics": "$2.30/GB ingested",
        "Application Insights": "$2.88/GB ingested",
        "Total Estimated": "$30-50/month (depends on usage)",
    }


def get_key_vault_secrets() -> List[str]:
    """Get list of secrets from Key Vault."""
    try:
        load_dotenv(override=True)
        keyvault_name = os.getenv("KEYVAULT_NAME")
        if not keyvault_name:
            return []

        credential = DefaultAzureCredential()
        client = SecretClient(
            vault_url=f"https://{keyvault_name}.vault.azure.net/",
            credential=credential,
        )

        secrets: List[str] = []
        for secret in client.list_properties_of_secrets():
            if secret.name:
                secrets.append(secret.name)

        return secrets
    except Exception:
        return []


def display_deployment_overview() -> None:
    """Display comprehensive deployment overview."""
    print_header("🚀 Azure AI Foundry Deployment Overview", "=")

    # Load data
    deployment_summary = get_deployment_summary()
    validation_report = get_validation_report()

    # Basic deployment info
    print_section("📊 Deployment Status")

    if validation_report.get("summary", {}).get("success_rate", 0) == 100:
        print_success("Deployment completed successfully!")
        print_success(
            f"All {validation_report['summary']['total_checks']} "
            "validation checks passed"
        )
    else:
        print_warning("Some validation checks failed - see validation report")

    # Environment info
    if deployment_summary.get("azure_info"):
        azure_info = deployment_summary["azure_info"]
        print_info(
            f"Subscription: {azure_info.get('subscription_id', 'Unknown')}"
        )
        print_info(
            f"Resource Group: {azure_info.get('resource_group', 'Unknown')}"
        )
        print_info(f"Location: {azure_info.get('location', 'Unknown')}")

    # Resources overview
    print_section("📦 Deployed Resources")

    if deployment_summary.get("ai_foundry_resources"):
        resources = deployment_summary["ai_foundry_resources"]
        for _, resource_info in resources.items():
            resource_name = resource_info.get("name", "Unknown")
            resource_type = resource_info.get("type", "Unknown")
            purpose = resource_info.get("purpose", "No description")

            print_success(f"{resource_name}")
            print(f"   Type: {resource_type}")
            print(f"   Purpose: {purpose}")

    # Security configuration
    print_section("🔐 Security Configuration")

    secrets = get_key_vault_secrets()
    if secrets:
        print_success(f"Key Vault accessible with {len(secrets)} secrets:")
        for secret in secrets:
            print(f"   • {secret}")

    if deployment_summary.get("security_configuration"):
        security = deployment_summary["security_configuration"]
        print_info(f"RBAC: {security.get('rbac_assignments', 'Unknown')}")
        print_info(
            f"Authentication: {security.get('authentication', 'Unknown')}"
        )
        print_info(
            f"Network Access: {security.get('network_access', 'Unknown')}"
        )
        print_info(
            f"Diagnostic Logging: "
            f"{security.get('diagnostic_logging', 'Unknown')}"
        )


def display_getting_started() -> None:
    """Display getting started information."""
    print_header("🎯 Getting Started with AI Foundry")

    print_section("1. Access Azure AI Foundry")
    print("   • Visit: https://ai.azure.com/")
    print("   • Sign in with your Azure account")
    print("   • Create a new AI project")
    print("   • Connect to your deployed resources")

    print_section("2. Development Environment Setup")
    print("   • Install Azure AI SDK: pip install azure-ai-ml")
    print("   • Configure environment variables from .env file")
    print("   • Test connection with validation scripts")

    print_section("3. Sample Code to Get Started")
    print(
        """
   # Connect to AI Services
   from azure.ai.ml import MLClient
   from azure.identity import DefaultAzureCredential

   credential = DefaultAzureCredential()
   ml_client = MLClient(
       credential=credential,
       subscription_id="your-subscription-id",
       resource_group_name="your-resource-group"
   )
   """
    )

    print_section("4. Key Vault Integration")
    print("   • Use secrets for API keys and connection strings")
    print("   • Never hardcode credentials in your applications")
    print("   • Test with: python validate-keyvault-access.py")


def display_monitoring_setup() -> None:
    """Display monitoring and cost management information."""
    print_header("📊 Monitoring & Cost Management")

    print_section("💰 Estimated Monthly Costs")
    costs = get_resource_costs()
    for resource, cost in costs.items():
        if resource == "Total Estimated":
            print_success(f"{resource}: {cost}")
        else:
            print_info(f"{resource}: {cost}")

    print_section("📈 Monitoring Setup")
    print("   • Application Insights configured for telemetry")
    print("   • Log Analytics workspace for centralized logging")
    print("   • Set up alerts in Azure Monitor")
    print("   • Configure cost alerts in Azure Cost Management")

    print_section("🔍 Monitoring Commands")
    print("   • Check resources: python quick-resource-check.py")
    print("   • Validate deployment: python validate-ai-foundry-deployment.py")
    print("   • Test Key Vault: python validate-keyvault-access.py")


def display_troubleshooting() -> None:
    """Display troubleshooting information."""
    print_header("🔧 Troubleshooting")

    print_section("Common Issues & Solutions")

    print_info("Authentication Issues:")
    print("   • Run: az login")
    print("   • Check: az account show")
    print("   • Verify permissions on resource group")

    print_info("Resource Access Issues:")
    print("   • Check RBAC assignments")
    print("   • Verify resource group permissions")
    print("   • Re-run validation scripts")

    print_info("Key Vault Access Issues:")
    print("   • Check access policies in Azure portal")
    print("   • Verify user permissions")
    print("   • Test with validate-keyvault-access.py")

    print_section("Useful Commands")
    print("   • List resources: az resource list --resource-group <rg-name>")
    print(
        "   • Check AI Services: az cognitiveservices account show "
        "--name <name> --resource-group <rg>"
    )
    print(
        "   • Test Key Vault: az keyvault secret list "
        "--vault-name <vault-name>"
    )

    print_section("Support Resources")
    print("   • Azure AI Documentation: https://docs.microsoft.com/azure/ai/")
    print("   • Azure AI Foundry: https://ai.azure.com/")
    print("   • Deployment logs: ai_foundry_deployment.log")
    print("   • Validation report: ai_foundry_validation_report.json")


def display_next_steps() -> None:
    """Display next steps for development."""
    print_header("🚀 Next Steps")

    print_section("Immediate Actions")
    print_success("1. Test your deployment with the validation scripts")
    print_success("2. Visit Azure AI Foundry portal (https://ai.azure.com/)")
    print_success("3. Create your first AI project")
    print_success("4. Set up cost monitoring alerts")

    print_section("Development Workflow")
    print("   • Start with sample notebooks and tutorials")
    print("   • Use Azure AI SDK for programmatic access")
    print("   • Implement proper error handling and logging")
    print("   • Set up CI/CD pipelines for model deployment")

    print_section("Security Best Practices")
    print("   • Always use Key Vault for secrets")
    print("   • Implement proper RBAC for team access")
    print("   • Enable audit logging for compliance")
    print("   • Regular security reviews and updates")

    print_section("Scaling Considerations")
    print("   • Monitor resource utilization")
    print("   • Plan for data growth and model complexity")
    print("   • Consider private endpoints for production")
    print("   • Implement automated scaling policies")


def main() -> None:
    """Main function to display deployment summary."""
    try:
        display_deployment_overview()
        display_getting_started()
        display_monitoring_setup()
        display_troubleshooting()
        display_next_steps()

        print_header("🎉 Deployment Complete!")
        print_success(
            "Your Azure AI Foundry environment is ready for development!"
        )
        print_info(
            "Run the validation scripts regularly to ensure everything "
            "is working correctly."
        )

    except Exception as e:
        print(
            f"{Colors.RED}❌ Error generating deployment summary: "
            f"{e}{Colors.END}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
