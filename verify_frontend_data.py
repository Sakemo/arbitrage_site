#!/usr/bin/env python3
"""
Quick verification that frontend will display correct data.
"""

import sys
sys.path.insert(0, '')

from modules import create_app


def verify_api_data():
    """Check if API is returning correct URLs and data."""
    app = create_app()[0] if isinstance(create_app(), tuple) else create_app()
    
    with app.test_client() as client:
        print("=" * 70)
        print("API Data Verification - Frontend Display Check")
        print("=" * 70)
        
        # Get all opportunities
        response = client.get('/api/opportunities?per_page=20')
        data = response.get_json()
        items = data.get('items', [])
        
        print(f"\n📊 Found {data['total']} opportunities in database\n")
        
        if not items:
            print("❌ No items found!")
            return False
        
        # Check each item for old SureBet references
        issues = 0
        
        for i, item in enumerate(items, 1):
            print(f"🔍 Opportunity #{i}: {item['event1']}")
            print(f"   League: {item['league1']}")
            print(f"   Profit: {item['profit']}%")
            print(f"   Age: {item['age']}")
            print(f"   Bookmakers: {item['bookmaker1']}, {item['bookmaker2']}, {item['bookmaker3']}")
            
            # Check event_link
            for j in range(1, 4):
                link_field = f'event_link{j}'
                link = item.get(link_field)
                
                if link and 'surebet.com' in link.lower():
                    print(f"   ❌ ISSUE: {link_field} still points to SureBet!")
                    issues += 1
                elif link and ('placeholder.local' in link or 'betfair.com' in link):
                    print(f"   ✅ {link_field}: {link[:50]}...")
                else:
                    print(f"   ⚠️  {link_field}: {link}")
            
            print()
        
        print("=" * 70)
        if issues == 0:
            print("✅ SUCCESS: No SureBet.com references found!")
            print("   Frontend will display placeholder/Betfair links instead")
        else:
            print(f"⚠️  WARNING: Found {issues} references to SureBet.com")
            print("   These should be replaced before production use")
        print("=" * 70)
        
        return issues == 0


if __name__ == '__main__':
    success = verify_api_data()
    sys.exit(0 if success else 1)
