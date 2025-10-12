#!/usr/bin/env python3
"""
Qwen 3 8B Q5 Test Preparation Script

This script prepares the system for testing Qwen 3 8B with reasoning disabled.
Run this once the model download is complete to set up the test configuration.
"""

import json
from pathlib import Path

def update_prompts_with_no_think():
    """Add /no_think to prompts to disable reasoning in Qwen 3 models"""
    
    # Update prepass prompt
    prepass_file = Path("prepass_prompt.txt")
    if prepass_file.exists():
        with open(prepass_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Add /no_think if not already present
        if not content.endswith('/no_think'):
            content += '\n\n/no_think'
            
        with open(prepass_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Updated prepass_prompt.txt with /no_think")
    
    # Update grammar prompt  
    grammar_file = Path("grammar_promt.txt")  # Note: intentional typo in filename
    if grammar_file.exists():
        with open(grammar_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Add /no_think if not already present
        if not content.endswith('/no_think'):
            content += '\n\n/no_think'
            
        with open(grammar_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Updated grammar_promt.txt with /no_think")

def update_stress_test_config():
    """Update stress test system for Qwen 3 8B model"""
    
    stress_test_file = Path("stress_test_system.py")
    if stress_test_file.exists():
        with open(stress_test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update the model configuration
        old_model_line = 'model="ibm/granite-3.1-8b"'
        new_model_line = 'model="qwen/qwen3-8b-instruct"'  # Adjust this to actual model name
        
        if old_model_line in content:
            content = content.replace(old_model_line, new_model_line)
            
            with open(stress_test_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated stress_test_system.py for Qwen 3 8B")
        else:
            print("⚠️ Manual update needed for stress_test_system.py model configuration")

def test_model_availability():
    """Test if Qwen 3 model is available on the server"""
    import requests
    
    try:
        response = requests.get("http://192.168.8.104:1234/v1/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            available_models = [model['id'] for model in models.get('data', [])]
            
            print("Available models:")
            for model in available_models:
                print(f"  - {model}")
            
            qwen3_models = [m for m in available_models if 'qwen3' in m.lower() or 'qwen-3' in m.lower()]
            if qwen3_models:
                print(f"\n✅ Qwen 3 models found: {qwen3_models}")
                return qwen3_models[0]  # Return first Qwen 3 model found
            else:
                print("\n❌ No Qwen 3 models found. Check if download is complete.")
                return None
        else:
            print(f"❌ Server error: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None

def main():
    """Main preparation function"""
    print("=== Qwen 3 8B Q5 Test Preparation ===")
    print()
    
    # Check model availability
    print("1. Checking model availability...")
    model_name = test_model_availability()
    
    if model_name:
        print(f"\n2. Preparing prompts with /no_think...")
        update_prompts_with_no_think()
        
        print(f"\n3. Updating test configuration...")
        update_stress_test_config()
        
        print(f"\n🎉 Preparation complete!")
        print(f"Model ready: {model_name}")
        print(f"Prompts updated with /no_think to disable reasoning")
        print(f"Ready to run: python stress_test_system.py")
        
        # Save model name for reference
        config = {"qwen3_model": model_name, "prepared_at": "2025-10-11"}
        with open("qwen3_test_config.json", "w") as f:
            json.dump(config, f, indent=2)
            
    else:
        print(f"\n⏳ Model not yet available. Run this script again after download completes.")
        print(f"Expected model patterns: qwen3, qwen-3, or similar")

if __name__ == "__main__":
    main()