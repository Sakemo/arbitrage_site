#!/usr/bin/env python3
"""
Test script for Betfair API integration
"""
import sys
import os
import json
from pathlib import Path

# Add modules to path
sys.path.append(str(Path(__file__).parent))

from modules.scrap import _load_betfair_credentials, aggregate_betfair_bets

def test_betfair_credentials():
    """Test loading Betfair credentials"""
    print("🔍 Testing Betfair credentials loading...")
    try:
        creds = _load_betfair_credentials()
        print("✅ Credentials loaded successfully:")
        print(f"   Username: {creds[0]}")
        print(f"   App Key: {creds[2]}")
        print(f"   Password: {'*' * len(creds[1]) if creds[1] else 'NOT FOUND'}")
        return True
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return False

def test_betfair_api():
    """Test Betfair API connection"""
    print("\n🔍 Testing Betfair API connection...")
    try:
        result = aggregate_betfair_bets()
        if result:
            print("✅ Betfair API call successful!")
            print(f"   Returned {len(result)} betting opportunities")
            if result:
                first_opp = result[0]
                print(f"   Sample opportunity: {first_opp.event1} vs {first_opp.event2}")
                print(f"   Profit: {first_opp.profit}%")
                print(f"   Bookmakers: {first_opp.bookmaker1}, {first_opp.bookmaker2}, {first_opp.bookmaker3}")
            return True
        else:
            print("❌ Betfair API returned no data")
            return False
    except Exception as e:
        print(f"❌ Error calling Betfair API: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🟢 Testing Betfair Integration")
    print("=" * 50)

    # Test credentials
    creds_ok = test_betfair_credentials()
    if not creds_ok:
        print("\n❌ Cannot proceed without valid credentials")
        return False

    # Test API
    api_ok = test_betfair_api()
    if api_ok:
        print("\n✅ Betfair integration is working!")
        return True
    else:
        print("\n❌ Betfair integration failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)