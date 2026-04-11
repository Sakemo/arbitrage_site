#!/usr/bin/env python3
"""Test Betfair data mapping and normalization."""

import sys
sys.path.insert(0, '')

from modules.scrap import (
    BetEntry,
    _normalize_sport_name,
    _format_betfair_time,
    _load_betfair_credentials,
    build_bet_data,
)
from datetime import datetime


def test_normalize_sport_name():
    """Teste normalização de nomes de esporte."""
    print("Testing sport name normalization...")
    
    tests = [
        ("Football", "Football"),
        ("football", "Football"),
        ("futebol", "Football"),
        ("Tennis", "Tennis"),
        ("tênis", "Tennis"),
        ("Horse Racing", "Horse Racing"),
        ("corrida de cavalo", "Horse Racing"),
        ("Basketball", "Basketball"),
        ("basquete", "Basketball"),
        ("", "Football"),
        (None, "Football"),
    ]
    
    for input_val, expected in tests:
        result = _normalize_sport_name(input_val)
        status = "PASS" if result == expected else "FAIL"
        print(f"  {status}: sport={input_val!r} -> {result!r} (expected {expected!r})")
        if result != expected:
            return False
    
    return True


def test_format_betfair_time():
    """Teste formatação de tempo Betfair."""
    print("Testing Betfair time formatting...")
    
    # Test with ISO format
    dt = datetime(2026, 4, 9, 14, 30, 45)
    result = _format_betfair_time(dt)
    expected = "2026-04-09 14:30"
    status = "PASS" if result == expected else "FAIL"
    print(f"  {status}: datetime -> {result!r} (expected {expected!r})")
    if result != expected:
        return False
    
    # Test with None
    result = _format_betfair_time(None)
    status = "PASS" if result == "" else "FAIL"
    print(f"  {status}: None -> {result!r} (expected '')")
    if result != "":
        return False
    
    return True


def test_load_credentials():
    """Teste carregamento de credenciais."""
    print("Testing credential loading...")
    
    try:
        username, password, app_key = _load_betfair_credentials()
        if username and password and app_key:
            print(f"  PASS: Credentials loaded - user={username[:10]}..., app_key={app_key[:5]}...")
            return True
        else:
            print("  FAIL: Credentials are empty")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def test_build_bet_data():
    """Teste construção de bet_data a partir de BetEntry."""
    print("Testing BetEntry to bet_data conversion...")
    
    bet_entry = BetEntry(
        profit="1.50%",
        age="betfair-api",
        bookmakers=["Betfair", "Betfair", "Betfair"],
        sports=["Football", "Football", "Football"],
        times=["2026-04-09 14:30", "2026-04-09 15:30", "2026-04-09 16:30"],
        events=["Team A vs Team B", "Team C vs Team D", "Team E vs Team F"],
        event_links=["https://betfair.com/1", "https://betfair.com/2", "https://betfair.com/3"],
        leagues=["League1", "League2", "League3"],
        markets=["Match Odds - Team A", "Match Odds - Team C", "Under/Over"],
        odds=["2.50", "3.25", "1.80"],
        stake_limits=["100", "200", "150"],
    )
    
    bet_data = build_bet_data(bet_entry)
    
    # Validate required fields exist
    required_fields = [
        'profit', 'age', 'created_at',
        'bookmaker1', 'sport1', 'time1', 'event1', 'league1', 'market1', 'odds1', 'stake_limit1',
        'bookmaker2', 'sport2', 'time2', 'event2', 'league2', 'market2', 'odds2', 'stake_limit2',
        'bookmaker3', 'sport3', 'time3', 'event3', 'league3', 'market3', 'odds3', 'stake_limit3',
    ]
    
    missing = [f for f in required_fields if f not in bet_data]
    if missing:
        print(f"  FAIL: Missing fields: {missing}")
        return False
    
    # Validate data types and values
    checks = [
        ('profit', float, 1.50),
        ('age', str, 'betfair-api'),
        ('bookmaker1', str, 'Betfair'),
        ('sport1', str, 'Football'),
        ('odds1', float, 2.50),
        ('stake_limit1', str, '100'),
    ]
    
    for field, expected_type, expected_value in checks:
        if field not in bet_data:
            print(f"  FAIL: Field {field} missing")
            return False
        value = bet_data[field]
        if not isinstance(value, expected_type):
            print(f"  FAIL: {field} type is {type(value).__name__}, expected {expected_type.__name__}")
            return False
        if value != expected_value:
            print(f"  FAIL: {field}={value!r}, expected {expected_value!r}")
            return False
    
    print(f"  PASS: All {len(required_fields)} required fields present and valid")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Betfair Data Mapping Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("Sport Normalization", test_normalize_sport_name()))
    print()
    
    results.append(("Time Formatting", test_format_betfair_time()))
    print()
    
    results.append(("Credential Loading", test_load_credentials()))
    print()
    
    results.append(("BetEntry to bet_data", test_build_bet_data()))
    print()
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {test_name}")
    
    print("=" * 60)
    print(f"Result: {passed}/{total} test groups passed")
    print("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
