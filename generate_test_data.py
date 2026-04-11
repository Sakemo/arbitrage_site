#!/usr/bin/env python3
"""
Generate more test data for UI visualization.
Creates multiple betting opportunities with diverse data.
"""

import asyncio
import sys
sys.path.insert(0, '')

from modules import create_app
from modules.models import BettingOpportunity, db
from datetime import datetime, timedelta


def generate_test_data():
    """Create diverse test betting opportunities."""
    app = create_app()[0] if isinstance(create_app(), tuple) else create_app()
    
    test_events = [
        {
            "event": "Manchester United vs Liverpool",
            "league": "Premier League",
            "sport": "Football",
            "date": datetime.now() + timedelta(days=1),
            "bookmakers": ["Betano", "Stake", "Superbet"],
        },
        {
            "event": "Real Madrid vs Barcelona",
            "league": "La Liga",
            "sport": "Football",
            "date": datetime.now() + timedelta(days=2),
            "bookmakers": ["Sportingbet", "Betano", "Stake"],
        },
        {
            "event": "Federer vs Djokovic",
            "league": "Wimbledon",
            "sport": "Tennis",
            "date": datetime.now() + timedelta(days=3),
            "bookmakers": ["Betano", "Superbet", "Stake"],
        },
        {
            "event": "Lakers vs Celtics",
            "league": "NBA",
            "sport": "Basketball",
            "date": datetime.now() + timedelta(days=1, hours=4),
            "bookmakers": ["Stake", "Sportingbet", "Betano"],
        },
        {
            "event": "PSG vs AS Monaco",
            "league": "Ligue 1",
            "sport": "Football",
            "date": datetime.now() + timedelta(days=4),
            "bookmakers": ["Superbet", "Betano", "Stake"],
        },
        {
            "event": "Bayern Munich vs Borussia Dortmund",
            "league": "Bundesliga",
            "sport": "Football",
            "date": datetime.now() + timedelta(days=1, hours=2),
            "bookmakers": ["Betano", "Sportingbet", "Superbet"],
        },
    ]
    
    with app.app_context():
        created = 0
        
        for i, test_event in enumerate(test_events):
            event_name = test_event["event"]
            league = test_event["league"]
            sport = test_event["sport"]
            event_date = test_event["date"]
            bookmakers = test_event["bookmakers"]
            
            # Format date and time
            date_str = event_date.strftime("%Y-%m-%d")
            time_str = event_date.strftime("%H:%M")
            
            # Create betting opportunity with 3 bookmakers
            bet_data = {
                "profit": 1.2 + (i * 0.3),  # Vary profit between 1.2% and 2.8%
                "age": "placeholder",
                "created_at": datetime.now(),
                
                # Bookmaker 1
                "bookmaker1": bookmakers[0],
                "sport1": sport,
                "time1": f"{date_str} {time_str}",
                "event1": event_name,
                "event_link1": f"https://placeholder.local/{bookmakers[0].lower()}/event-{i+1}",
                "league1": league,
                "market1": "Match Odds - Home",
                "odds1": 2.0 + (i * 0.1),
                "stake_limit1": str(100 + i*50),
                
                # Bookmaker 2
                "bookmaker2": bookmakers[1],
                "sport2": sport,
                "time2": f"{date_str} {time_str}",
                "event2": event_name,
                "event_link2": f"https://placeholder.local/{bookmakers[1].lower()}/event-{i+1}",
                "league2": league,
                "market2": "Match Odds - Draw",
                "odds2": 3.2 + (i * 0.1),
                "stake_limit2": str(150 + i*50),
                
                # Bookmaker 3
                "bookmaker3": bookmakers[2],
                "sport3": sport,
                "time3": f"{date_str} {time_str}",
                "event3": event_name,
                "event_link3": f"https://placeholder.local/{bookmakers[2].lower()}/event-{i+1}",
                "league3": league,
                "market3": "Match Odds - Away",
                "odds3": 2.8 + (i * 0.1),
                "stake_limit3": str(200 + i*50),
            }
            
            try:
                opportunity = BettingOpportunity.add_or_update(bet_data)
                created += 1
                print(f"✅ Created: {event_name} ({league})")
            except Exception as e:
                print(f"❌ Failed to create {event_name}: {e}")
        
        print(f"\n✅ Total test records created: {created}")
        total = BettingOpportunity.query.count()
        print(f"📈 Total records in database: {total}")
        
        return created > 0


def main():
    print("=" * 60)
    print("Generate Test Data for UI Visualization")
    print("=" * 60)
    
    if not generate_test_data():
        print("Failed to generate test data")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ Test data generated successfully!")
    print("=" * 60)
    print("\n📌 What to check in the UI:")
    print("   ✓ Cards should show various sports (Football, Tennis, Basketball)")
    print("   ✓ Profit values: 1.2% - 2.8%")
    print("   ✓ Event links: https://placeholder.local/... (NOT surebet.com)")
    print("   ✓ Age field: 'placeholder'")
    print("   ✓ Multiple bookmakers per event")
    print("   ✓ Different leagues and event names")
    
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
