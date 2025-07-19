#!/usr/bin/env python3
"""Pipeline validation script to test CI/CD requirements."""

import os
import sys


def main() -> int:
    """Validate all pipeline requirements."""
    print("=== CI Pipeline Validation ===")

    # Test 1: Check if all required modules can be imported
    modules_to_test = ["toml", "subprocess", "sys", "os", "json"]
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ Module {module} available")
        except ImportError as e:
            print(f"✗ Module {module} missing: {e}")
            return 1

    # Test 2: Check pyproject.toml parsing
    try:
        import toml

        with open("pyproject.toml", "r", encoding="utf-8") as f:
            toml.load(f)  # Just validate parsing, don't store result
        print("✓ pyproject.toml parsing successful")
    except Exception as e:
        print(f"✗ pyproject.toml parsing failed: {e}")
        return 1

    # Test 3: Verify README sections
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        sections = ["Resources Created", "Security Features"]
        for section in sections:
            if section in content:
                print(f'✓ README section "{section}" found')
            else:
                print(f'✗ README section "{section}" missing')
                return 1
    except Exception as e:
        print(f"✗ README validation failed: {e}")
        return 1

    # Test 4: Check main scripts exist
    scripts = [
        "create-ai-foundry-project.py",
        "validate-ai-foundry-deployment.py",
    ]
    for script in scripts:
        if os.path.exists(script):
            print(f"✓ Script {script} exists")
        else:
            print(f"✗ Script {script} missing")
            return 1

    print("\n=== Pipeline Requirements Check Complete ===")
    print("✓ All tests passed! Pipeline should work correctly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
