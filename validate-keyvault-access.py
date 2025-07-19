#!/usr/bin/env python3
"""
Azure AI Foundry Key Vault Access Validator

This script specifically validates access to the Key Vault and verifies that
all expected secrets are accessible. It's designed to be run after the main
deployment to ensure the security configuration is working correctly.

VALIDATION CHECKS:
1. Key Vault accessibility
2. Secret retrieval (ai-services-key, ai-services-endpoint,
   cognitive-search-key, cognitive-search-endpoint)
3. Secret content validation
4. Access permissions verification

USAGE:
    python validate-keyvault-access.py

REQUIREMENTS:
    - KEYVAULT_NAME environment variable set
    - Azure CLI authenticated
    - Appropriate Key Vault permissions
"""

import os
import sys
import uuid
from typing import Any, Dict, Optional, Tuple

from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv


def initialize_keyvault_client(
    keyvault_name: str,
) -> Tuple[Optional[SecretClient], bool]:
    """
    Initialize Key Vault client and credential.

    Args:
        keyvault_name: Name of the Key Vault

    Returns:
        Tuple of (SecretClient, success_flag)
    """
    try:
        credential = DefaultAzureCredential()
        print("✅ Azure credential initialized")

        vault_url = f"https://{keyvault_name}.vault.azure.net/"
        secret_client = SecretClient(
            vault_url=vault_url, credential=credential
        )
        print(f"✅ Key Vault client created for: {vault_url}")
        return secret_client, True
    except Exception as e:
        print(f"❌ Failed to initialize Key Vault client: {e}")
        return None, False


def test_keyvault_connectivity(secret_client: SecretClient) -> bool:
    """
    Test basic Key Vault connectivity.

    Args:
        secret_client: Azure Key Vault SecretClient

    Returns:
        bool: True if connectivity test passes
    """
    try:
        secrets = list(secret_client.list_properties_of_secrets())
        print(
            f"✅ Key Vault connectivity verified ({len(secrets)} secrets found)"
        )
        return True
    except AzureError as e:
        print(f"❌ Key Vault connectivity failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error accessing Key Vault: {e}")
        return False


def validate_secret(
    secret_client: SecretClient, secret_name: str, description: str
) -> Dict[str, Any]:
    """
    Validate a specific secret in Key Vault.

    Args:
        secret_client: Azure Key Vault SecretClient
        secret_name: Name of the secret to validate
        description: Human-readable description of the secret

    Returns:
        Dict containing validation results
    """
    try:
        secret = secret_client.get_secret(secret_name)

        if secret.value and len(secret.value.strip()) > 0:
            # Mask the secret value for security
            masked_value = (
                secret.value[:8] + "..."
                if len(secret.value) > 8
                else "[HIDDEN]"
            )
            print(f"✅ {description}: {masked_value}")

            # Additional validation based on secret type
            validate_secret_format(secret_name, secret.value)

            return {
                "status": "success",
                "value_length": len(secret.value),
                "created_on": (
                    secret.properties.created_on.isoformat()
                    if secret.properties.created_on
                    else None
                ),
            }
        else:
            print(f"❌ {description}: Empty or invalid value")
            return {"status": "empty"}

    except AzureError as e:
        print(f"❌ {description}: Access denied or not found - {e}")
        return {"status": "access_denied", "error": str(e)}
    except Exception as e:
        print(f"❌ {description}: Unexpected error - {e}")
        return {"status": "error", "error": str(e)}


def validate_secret_format(secret_name: str, secret_value: str) -> None:
    """
    Validate secret format based on secret type.

    Args:
        secret_name: Name of the secret
        secret_value: Value of the secret
    """
    validators = {
        "ai-services-endpoint": _validate_ai_services_endpoint,
        "ai-services-key": _validate_ai_services_key,
        "cognitive-search-key": _validate_search_key,
        "cognitive-search-endpoint": _validate_search_endpoint,
    }

    validator = validators.get(secret_name)
    if validator:
        validator(secret_value)


def _validate_ai_services_endpoint(secret_value: str) -> None:
    """Validate AI Services endpoint format."""
    if secret_value.startswith("https://"):
        print("   ✅ Endpoint format valid")
    else:
        print(
            "   ⚠️ Endpoint format may be invalid "
            "(doesn't start with https://)"
        )


def _validate_ai_services_key(secret_value: str) -> None:
    """Validate AI Services key format."""
    # AI Services keys are typically 32+ chars
    if len(secret_value) >= 32:
        print("   ✅ Key format appears valid")
    else:
        print("   ⚠️ Key format may be invalid (too short)")


def _validate_search_key(secret_value: str) -> None:
    """Validate Cognitive Search key format."""
    # Cognitive Search keys are typically 32+ chars
    if len(secret_value) >= 32:
        print("   ✅ Search key format appears valid")
    else:
        print("   ⚠️ Search key format may be invalid (too short)")


def _validate_search_endpoint(secret_value: str) -> None:
    """Validate Cognitive Search endpoint format."""
    if (
        secret_value.startswith("https://")
        and ".search.windows.net" in secret_value
    ):
        print("   ✅ Search endpoint format valid")
    else:
        print("   ⚠️ Search endpoint format may be invalid")


def validate_expected_secrets(
    secret_client: SecretClient,
) -> Tuple[Dict[str, Dict[str, Any]], bool]:
    """
    Validate all expected secrets for AI Foundry.

    Args:
        secret_client: Azure Key Vault SecretClient

    Returns:
        Tuple of (validation_results, all_secrets_valid)
    """
    expected_secrets = {
        "ai-services-key": "AI Services API Key",
        "ai-services-endpoint": "AI Services Endpoint URL",
        "cognitive-search-admin-key": "Cognitive Search Admin API Key",
        "cognitive-search-query-key": "Cognitive Search Query API Key",
        "cognitive-search-endpoint": "Cognitive Search Endpoint URL",
        "speechtotext-endpoint": "Speech to Text Service Endpoint",
        "texttospeech-endpoint": "Text to Speech Service Endpoint",
        "translator-endpoint": "Text Translation Service Endpoint",
    }

    print("\n🔑 Validating Expected Secrets:")
    print("-" * 40)

    validation_results: Dict[str, Dict[str, Any]] = {}
    all_secrets_valid = True

    for secret_name, description in expected_secrets.items():
        result = validate_secret(secret_client, secret_name, description)
        validation_results[secret_name] = result

        if result["status"] not in ["success"]:
            all_secrets_valid = False

    return validation_results, all_secrets_valid


def test_write_permissions(secret_client: SecretClient) -> None:
    """
    Test Key Vault write permissions.

    Args:
        secret_client: Azure Key Vault SecretClient
    """
    print("\n🧪 Testing Secret Write Permissions:")
    print("-" * 40)

    # Generate a unique test secret name to avoid conflicts
    test_secret_name = f"ai-foundry-test-secret-{uuid.uuid4().hex[:8]}"
    test_secret_value = f"test-value-{uuid.uuid4().hex[:8]}"

    try:
        # Try to create a test secret
        secret_client.set_secret(test_secret_name, test_secret_value)
        print("✅ Write permission verified (created test secret)")

        # Try to read it back
        retrieved_secret = secret_client.get_secret(test_secret_name)
        if retrieved_secret.value == test_secret_value:
            print("✅ Read-after-write verified")
        else:
            print("⚠️ Read-after-write mismatch")

        # Clean up test secret
        secret_client.begin_delete_secret(test_secret_name)
        print("✅ Test secret cleaned up")

    except AzureError as e:
        print(f"⚠️ Write permission test failed: {e}")
        print("   (This is normal if you only have read permissions)")
    except Exception as e:
        print(f"❌ Write permission test error: {e}")


def print_validation_summary(all_secrets_valid: bool) -> bool:
    """
    Print validation summary and next steps.

    Args:
        all_secrets_valid: Whether all secrets validation passed

    Returns:
        bool: Overall validation result
    """
    print("\n📊 Validation Summary:")
    print("=" * 60)

    if all_secrets_valid:
        print("✅ All expected secrets are accessible and valid")
        print("✅ Key Vault access is working correctly")
        print("✅ AI Foundry secrets are ready for use")

        print("\n🚀 Next Steps:")
        print("• Your AI Services credentials are securely stored")
        print("• Your Cognitive Search credentials are securely stored")
        print("• You can now use these secrets in your AI applications")
        print("• Consider setting up monitoring for Key Vault access")

        return True
    else:
        print("❌ Some secrets are missing or inaccessible")
        print("❌ Key Vault configuration needs attention")

        print("\n🔧 Troubleshooting:")
        print("• Check that the AI Foundry deployment completed successfully")
        print("• Verify your Azure permissions for the Key Vault")
        print("• Ensure the AI Services account was created properly")
        print("• Ensure the Cognitive Search service was created properly")
        print("• Check the deployment logs for any errors")

        return False


def validate_keyvault_access() -> bool:
    """
    Validate Key Vault access and secret retrieval.

    Returns:
        bool: True if all validations pass, False otherwise
    """
    print("🔐 Azure AI Foundry Key Vault Access Validation")
    print("=" * 60)

    # Load environment variables
    load_dotenv(override=True)

    keyvault_name = os.getenv("KEYVAULT_NAME")
    if not keyvault_name:
        print("❌ KEYVAULT_NAME environment variable not set")
        return False

    print(f"📋 Key Vault: {keyvault_name}")

    # Initialize Key Vault client
    secret_client, success = initialize_keyvault_client(keyvault_name)
    if not success or secret_client is None:
        return False

    # Test Key Vault connectivity
    if not test_keyvault_connectivity(secret_client):
        return False

    # Validate expected secrets
    _, all_secrets_valid = validate_expected_secrets(secret_client)

    # Test write permissions
    test_write_permissions(secret_client)

    # Print summary and return result
    return print_validation_summary(all_secrets_valid)


def main() -> None:
    """Main validation function."""
    try:
        success = validate_keyvault_access()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
