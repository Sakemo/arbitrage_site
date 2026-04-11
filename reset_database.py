#!/usr/bin/env python3
"""
Reset database and initialize with fresh scraping data.
This script:
1. Removes old SureBet data
2. Seeds fresh Betfair data
3. Verifies API endpoints
"""

import asyncio
import sys
sys.path.insert(0, '')

from modules import create_app
from modules.models import BettingOpportunity, db
from modules.scrap import (
    seed_bet_data,
    get_table_data_from_page,
)


def reset_database():
    """Delete all records from BettingOpportunity."""
    app = create_app()[0] if isinstance(create_app(), tuple) else create_app()
    
    with app.app_context():
        try:
            count = BettingOpportunity.query.delete()
            db.session.commit()
            print(f"✅ Deleted {count} old records from database")
            return True
        except Exception as e:
            print(f"❌ Failed to delete records: {e}")
            db.session.rollback()
            return False


async def populate_with_fresh_data():
    """Populate database with fresh Betfair data."""
    app = create_app()[0] if isinstance(create_app(), tuple) else create_app()
    
    with app.app_context():
        try:
            print("\n📥 Fetching fresh data...")
            bets = await get_table_data_from_page()
            
            if not bets:
                print("❌ No data returned from scraper")
                return False
            
            print(f"📊 Got {len(bets)} betting opportunities")
            
            stored = await seed_bet_data(app, bets)
            print(f"✅ Stored {stored} records in database")
            
            # Verify data
            total = BettingOpportunity.query.count()
            print(f"📈 Total records in database: {total}")
            
            # Show sample data
            sample = BettingOpportunity.query.first()
            if sample:
                print(f"\n📋 Sample record:")
                print(f"   Event: {sample.event1}")
                print(f"   Bookmaker 1: {sample.bookmaker1}")
                print(f"   Event Link 1: {sample.event_link1}")
                print(f"   Profit: {sample.profit}%")
                print(f"   Age: {sample.age}")
            
            return total > 0
            
        except Exception as e:
            print(f"❌ Failed to populate data: {e}")
            import traceback
            traceback.print_exc()
            return False


async def check_api():
    """Verify API endpoints are working."""
    app = create_app()[0] if isinstance(create_app(), tuple) else create_app()
    
    with app.test_client() as client:
        try:
            print("\n🔍 Checking API endpoints...")
            
            # Test /api/filters
            response = client.get('/api/filters')
            if response.status_code == 200:
                data = response.get_json()
                print(f"✅ /api/filters OK")
                print(f"   Bookmakers: {data.get('bookmakers', [])[:3]}...")
                print(f"   Sports: {data.get('sports', [])[:3]}...")
            else:
                print(f"❌ /api/filters returned {response.status_code}")
            
            # Test /api/opportunities
            response = client.get('/api/opportunities?per_page=5')
            if response.status_code == 200:
                data = response.get_json()
                total = data.get('total', 0)
                items = data.get('items', [])
                print(f"✅ /api/opportunities OK (total: {total})")
                
                if items:
                    item = items[0]
                    print(f"   Sample item:")
                    print(f"      Event: {item.get('event1')}")
                    print(f"      Bookmaker: {item.get('bookmaker1')}")
                    print(f"      Event Link: {item.get('event_link1')}")
                    print(f"      Profit: {item.get('profit')}%")
            else:
                print(f"❌ /api/opportunities returned {response.status_code}")
            
        except Exception as e:
            print(f"❌ API check failed: {e}")


async def main():
    print("=" * 60)
    print("Database Reset & Verification Script")
    print("=" * 60)
    
    # Step 1: Reset
    if not reset_database():
        print("Cannot continue without clean database")
        return 1
    
    # Step 2: Populate with fresh data
    if not await populate_with_fresh_data():
        print("Failed to populate data")
        return 1
    
    # Step 3: Verify API
    await check_api()
    
    print("\n" + "=" * 60)
    print("✅ Database reset and verification complete!")
    print("=" * 60)
    print("\n📌 Next steps:")
    print("   1. Go to http://localhost:5000/ (if running locally)")
    print("   2. Check if cards show:")
    print("      - event_link pointing to 'betfair.com' or Betfair landing pages")
    print("      - NOT to 'pt.surebet.com'")
    print("   3. Profit values should be realistic Betfair odds ratios")
    print("   4. Age field should show 'betfair-api' for Betfair-sourced data")
    
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
