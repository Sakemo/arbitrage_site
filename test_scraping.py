#!/usr/bin/env python3
"""
Test script for scraping functionality
"""
import asyncio
import sys
from pathlib import Path

# Add modules to path
sys.path.append(str(Path(__file__).parent))

from modules import create_app
from modules.scrap import start_scraping

async def test_scraping():
    """Test the scraping functionality"""
    print("🟢 Testing Scraping Functionality")
    print("=" * 50)

    try:
        # Create Flask app
        app, config = create_app()
        print("✅ Flask app created successfully")

        # Test scraping
        with app.app_context():
            print("🔄 Starting scraping test...")
            await start_scraping(app)
            print("✅ Scraping completed successfully")

    except Exception as e:
        print(f"❌ Error during scraping test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_scraping())
    sys.exit(0 if success else 1)