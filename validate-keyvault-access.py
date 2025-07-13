#!/usr/bin/env python3
"""
Azure AI Foundry Key Vault Access Validator

This script specifically validates access to the Key Vault and verifies that
all expected secrets are accessible. It's designed to be run after the main
deployment to ensure the security configuration is working correctly.

VALIDATION CHECKS:
1. Key Vault accessibility
2. Secret retrieval (ai-services-key, ai-services-endpoint)
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

from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv


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

    # Initialize Azure credential
    try:
        credential = DefaultAzureCredential()
        print("✅ Azure credential initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Azure credential: {e}")
        return False

    # Create Key Vault client
    try:
        vault_url = f"https://{keyvault_name}.vault.azure.net/"
        secret_client = SecretClient(
            vault_url=vault_url, credential=credential
        )
        print(f"✅ Key Vault client created for: {vault_url}")
    except Exception as e:
        print(f"❌ Failed to create Key Vault client: {e}")
        return False

    # Test Key Vault connectivity
    try:
        # Try to list secrets to test basic connectivity
        secrets = list(secret_client.list_properties_of_secrets())
        print(
            f"✅ Key Vault connectivity verified ({len(secrets)} secrets found)"
        )
    except AzureError as e:
        print(f"❌ Key Vault connectivity failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error accessing Key Vault: {e}")
        return False

    # Expected secrets for AI Foundry
    expected_secrets = {
        "ai-services-key": "AI Services API Key",
        "ai-services-endpoint": "AI Services Endpoint URL",
    }

    print("\n🔑 Validating Expected Secrets:")
    print("-" * 40)

    validation_results = {}
    all_secrets_valid = True

    for secret_name, description in expected_secrets.items():
        try:
            secret = secret_client.get_secret(secret_name)

            # Basic validation
            if secret.value and len(secret.value.strip()) > 0:
                # Mask the secret value for security
                masked_value = (
                    secret.value[:8] + "..."
                    if len(secret.value) > 8
                    else "[HIDDEN]"
                )
                print(f"✅ {description}: {masked_value}")

                # Additional validation based on secret type
                if secret_name == "ai-services-endpoint":  # nosec B105
                    if secret.value.startswith("https://"):
                        print("   ✅ Endpoint format valid")
                    else:
                        print(
                            "   ⚠️ Endpoint format may be invalid "
                            "(doesn't start with https://)"
                        )

                elif secret_name == "ai-services-key":  # nosec B105
                    # AI Services keys are typically 32+ chars
                    if len(secret.value) >= 32:
                        print("   ✅ Key format appears valid")
                    else:
                        print("   ⚠️ Key format may be invalid (too short)")

                validation_results[secret_name] = {
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
                validation_results[secret_name] = {"status": "empty"}
                all_secrets_valid = False

        except AzureError as e:
            print(f"❌ {description}: Access denied or not found - {e}")
            validation_results[secret_name] = {
                "status": "access_denied",
                "error": str(e),
            }
            all_secrets_valid = False

        except Exception as e:
            print(f"❌ {description}: Unexpected error - {e}")
            validation_results[secret_name] = {
                "status": "error",
                "error": str(e),
            }
            all_secrets_valid = False

    # Test secret creation (if we have permissions)
    print("\n🧪 Testing Secret Write Permissions:")
    print("-" * 40)

    test_secret_name = "ai-foundry-test-secret"  # nosec B105
    test_secret_value = "test-value-12345"  # nosec B105

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

    # Summary
    print("\n📊 Validation Summary:")
    print("=" * 60)

    if all_secrets_valid:
        print("✅ All expected secrets are accessible and valid")
        print("✅ Key Vault access is working correctly")
        print("✅ AI Foundry secrets are ready for use")

        print("\n🚀 Next Steps:")
        print("• Your AI Services credentials are securely stored")
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
        print("• Check the deployment logs for any errors")

        return False


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
