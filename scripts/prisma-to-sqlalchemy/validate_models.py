#!/usr/bin/env python3
"""
Validate that the generated SQLAlchemy models can be imported and are syntactically correct.
"""

import sys
import importlib.util
from pathlib import Path


def validate_models(models_path: Path) -> bool:
    """Validate that the models can be imported."""
    print(f"Validating models at: {models_path}")
    
    # Load the module
    spec = importlib.util.spec_from_file_location("generated_models", models_path)
    if not spec or not spec.loader:
        print("❌ Failed to load module spec")
        return False
    
    module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(module)
        print("✅ Models imported successfully")
    except Exception as e:
        print(f"❌ Failed to import models: {e}")
        return False
    
    # Check for expected classes
    expected_models = [
        "Base", "Agent", "Organization", "User", "PaymentLink", "PaymentOrder",
        "Customer", "Product", "Price", "Wallet", "Provider"
    ]
    
    missing = []
    for model in expected_models:
        if not hasattr(module, model):
            missing.append(model)
    
    if missing:
        print(f"❌ Missing models: {', '.join(missing)}")
        return False
    
    print(f"✅ Found all expected models")
    
    # Check enums
    expected_enums = [
        "AgentType", "AuthProvider", "PaymentOrderStatus", "ComplianceStatus"
    ]
    
    missing_enums = []
    for enum in expected_enums:
        if not hasattr(module, enum):
            missing_enums.append(enum)
    
    if missing_enums:
        print(f"❌ Missing enums: {', '.join(missing_enums)}")
        return False
    
    print(f"✅ Found all expected enums")
    
    return True


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python validate_models.py <models_path>")
        sys.exit(1)
    
    models_path = Path(sys.argv[1])
    
    if not models_path.exists():
        print(f"Error: Models file not found: {models_path}")
        sys.exit(1)
    
    if validate_models(models_path):
        print("\n✅ Validation successful!")
        sys.exit(0)
    else:
        print("\n❌ Validation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 