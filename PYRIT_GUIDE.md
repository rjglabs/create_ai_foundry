# PyRIT AI Security Testing Guide

## Overview
This guide explains how to integrate PyRIT (Python Risk Identification Toolkit) for AI security testing with your Azure AI Foundry deployment.

## When to Use PyRIT

### ✅ Use PyRIT When You Have:
- Deployed AI models (OpenAI, Azure Cognitive Services, etc.)
- Custom AI agents or chatbots
- Prompt templates and AI workflows
- AI applications handling user input
- Production AI systems requiring security validation

### ❌ PyRIT Not Needed For:
- Infrastructure-only deployments (current state)
- Non-AI applications
- Static content or traditional web applications

## Quick Start

### 1. Install PyRIT
```bash
pip install pyrit
```

### 2. Configure Azure Integration
Use the secrets from your Azure Key Vault:
```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# Get secrets from Key Vault (already configured by this project)
credential = DefaultAzureCredential()
secret_client = SecretClient(
    vault_url="https://YOUR_KEYVAULT_NAME.vault.azure.net/",
    credential=credential
)

ai_endpoint = secret_client.get_secret("ai-services-endpoint").value
ai_key = secret_client.get_secret("ai-services-key").value
```

### 3. Basic PyRIT Test Example
```python
from pyrit.prompt_target import AzureOpenAIChatTarget
from pyrit.orchestrator import PromptSendingOrchestrator

# Configure target
target = AzureOpenAIChatTarget(
    deployment_name="your-deployment",
    endpoint=ai_endpoint,
    api_key=ai_key
)

# Run basic jailbreak test
orchestrator = PromptSendingOrchestrator(prompt_target=target)
result = orchestrator.send_prompt("Ignore all previous instructions...")

print(f"Response: {result}")
```

## Integration with CI/CD

### 1. Add PyRIT to CI Pipeline
Uncomment PyRIT in `dev-requirements.txt`:
```txt
# pyrit  # Uncomment when ready for AI security testing
```

### 2. Create PyRIT Test Suite
```python
# tests/test_ai_security.py
import pytest
from pyrit.prompt_target import AzureOpenAIChatTarget
from pyrit.orchestrator import PromptSendingOrchestrator

class TestAISecurity:
    def test_jailbreak_resistance(self):
        # Test against common jailbreak attempts
        pass

    def test_content_filtering(self):
        # Test harmful content detection
        pass

    def test_bias_detection(self):
        # Test for biased responses
        pass
```

### 3. Update CI Workflow
Add to `.github/workflows/ci.yml`:
```yaml
- name: Run PyRIT AI Security Tests
  run: |
    python -m pytest tests/test_ai_security.py -v
```

## Test Categories

### 1. Jailbreak Testing
- Prompt injection attacks
- Instruction override attempts
- Context confusion tests
- Role-playing exploits

### 2. Content Safety
- Harmful content generation
- Inappropriate responses
- Violence and hate speech
- Privacy violations

### 3. Bias Detection
- Demographic bias
- Cultural sensitivity
- Fairness across groups
- Stereotyping detection

### 4. Data Leakage
- Training data exposure
- Prompt injection for data extraction
- Model inversion attacks
- Membership inference

## Configuration

### PyRIT Configuration File
Create `.pyrit/config.yaml`:
```yaml
azure_openai:
  api_type: "azure"
  api_version: "2023-05-15"
  endpoint: "${AI_SERVICES_ENDPOINT}"
  api_key: "${AI_SERVICES_KEY}"

test_categories:
  - jailbreak_attempts
  - prompt_injection
  - bias_detection
  - content_filtering
  - safety_guardrails

thresholds:
  max_jailbreak_success_rate: 0.05
  min_content_filter_effectiveness: 0.95
  max_bias_score: 0.3

reports:
  format: "json"
  output_dir: "pyrit_reports"
  include_evidence: true
```

## Best Practices

### 1. Test Early and Often
- Integrate PyRIT into CI/CD pipeline
- Test every model deployment
- Monitor for regression in security

### 2. Comprehensive Testing
- Test all AI endpoints
- Include edge cases
- Test different user roles

### 3. Documentation
- Document test results
- Track security improvements
- Share findings with team

### 4. Continuous Monitoring
- Regular security assessments
- Monitor for new attack vectors
- Update test cases regularly

## Compliance and Governance

### Regulatory Requirements
- GDPR compliance for AI systems
- Industry-specific regulations
- Internal security policies
- Audit requirements

### Documentation Requirements
- Security test results
- Risk assessments
- Mitigation strategies
- Compliance reports

## Resources

- [PyRIT Documentation](https://github.com/Azure/PyRIT)
- [Azure AI Security Guidelines](https://docs.microsoft.com/en-us/azure/ai-services/security)
- [Responsible AI Practices](https://www.microsoft.com/en-us/ai/responsible-ai)
- [AI Security Testing Best Practices](https://aka.ms/ai-security-testing)

## Next Steps

1. Deploy your first AI model using this infrastructure
2. Install PyRIT: `pip install pyrit`
3. Configure PyRIT with your Azure Key Vault secrets
4. Create your first security test
5. Integrate with CI/CD pipeline
6. Set up automated security monitoring

---

**Note**: This guide assumes you have already deployed the Azure AI Foundry infrastructure using the scripts in this repository. PyRIT testing becomes relevant once you start deploying actual AI models and applications.
