#!/usr/bin/env python3
"""
Test script for Betfair login only
"""
import sys
import os
from pathlib import Path

# Add modules to path
sys.path.append(str(Path(__file__).parent))

import betfairlightweight
from modules.scrap import _load_betfair_credentials

def test_login_only():
    """Test only the login process"""
    print("🔍 Testing Betfair login only...")

    try:
        username, password, app_key = _load_betfair_credentials()
        print(f"✅ Credentials loaded: {username}")

        # Test without certs first (interactive login)
        print("🔄 Testing interactive login (no certs)...")
        client = betfairlightweight.APIClient(
            username=username,
            password=password,
            app_key=app_key,
        )

        try:
            client.login_interactive()
            print("✅ Interactive login successful!")
            return True
        except Exception as e:
            print(f"❌ Interactive login failed: {e}")

        # Test with certs (non-interactive login)
        print("🔄 Testing non-interactive login (with certs)...")
        certs_path = Path(__file__).resolve().parent / "certs"
        client_cert = betfairlightweight.APIClient(
            username=username,
            password=password,
            app_key=app_key,
            certs=str(certs_path),
        )

        try:
            client_cert.login()
            print("✅ Non-interactive login successful!")
            return True
        except Exception as e:
            print(f"❌ Non-interactive login failed: {e}")

        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🟢 Testing Betfair Login Only")
    print("=" * 40)

    success = test_login_only()
    if success:
        print("\n✅ Login test passed!")
    else:
        print("\n❌ Login test failed!")
        print("\n🔧 Possible solutions:")
        print("1. Check if your Betfair account has API access enabled")
        print("2. Verify your app key is correct and active")
        print("3. Ensure SSL certificates are valid (if using non-interactive login)")
        print("4. Contact Betfair support about account restrictions")
        print("5. Try creating a new app key in Betfair developer portal")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)