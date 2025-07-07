#!/usr/bin/env python3
"""
Test script to verify that secrets are properly consolidated and accessible.
"""

import streamlit as st
import sys
import os

def main():
    print("🔧 Testing NatureTrace Secrets Configuration")
    print("=" * 50)
    
    try:
        # Load secrets
        st.secrets.load_if_toml_exists()
        print("✅ Secrets file loaded successfully")
        
        # Test critical secrets
        critical_secrets = [
            "groq_api_key",
            "google_maps_key", 
            "AZURE_COMPUTER_VISION_ENDPOINT",
            "AZURE_COMPUTER_VISION_KEY",
            "snowflake_account",
            "snowflake_user",
            "freesound_api_key"
        ]
        
        print("\n📋 Checking critical secrets:")
        missing_secrets = []
        
        for secret in critical_secrets:
            value = st.secrets.get(secret)
            if value:
                print(f"✅ {secret}: {'*' * min(10, len(str(value)))}...")
            else:
                print(f"❌ {secret}: NOT FOUND")
                missing_secrets.append(secret)
        
        # Test optional secrets
        optional_secrets = ["macaulay_api_key", "freesound_api_key", "hf_token"]
        print("\n📋 Checking optional secrets:")
        
        for secret in optional_secrets:
            value = st.secrets.get(secret)
            if value:
                print(f"✅ {secret}: {'*' * min(10, len(str(value)))}...")
            else:
                print(f"⚠️  {secret}: Not configured (optional)")
        
        # Summary
        print("\n" + "=" * 50)
        if missing_secrets:
            print(f"❌ Missing {len(missing_secrets)} critical secrets: {missing_secrets}")
            return False
        else:
            print("✅ All critical secrets are properly configured!")
            print("🎉 Secrets consolidation completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
