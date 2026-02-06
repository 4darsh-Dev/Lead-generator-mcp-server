#!/usr/bin/env python3
"""
Test script to verify resume with increased max_results works correctly.
"""

import json
from pathlib import Path

state_file = Path(".scraping_state/state_1229173287d1.json")

print("Current State Analysis")
print("=" * 80)

if state_file.exists():
    with state_file.open('r') as f:
        state = json.load(f)
    
    print(f"Query: {state['query']}")
    print(f"Current max_results: {state['max_results']}")
    print(f"Total URLs in state: {len(state['business_urls'])}")
    print(f"Processed: {len(state['processed_indices'])}")
    print(f"Pending: {len(state['business_urls']) - len(state['processed_indices'])}")
    print(f"Completed: {state['completed']}")
    
    print("\n" + "=" * 80)
    print("What will happen when you run with --max-results 1000:")
    print("=" * 80)
    
    if len(state['business_urls']) < 1000:
        print(f"✓ Will fetch MORE URLs ({len(state['business_urls'])} → 1000)")
        print(f"  - Already have: {len(state['business_urls'])} URLs")
        print(f"  - Already processed: {len(state['processed_indices'])} URLs")
        print(f"  - Will fetch: ~{1000 - len(state['business_urls'])} new URLs")
        print(f"  - Total to process: ~{1000 - len(state['processed_indices'])} URLs")
    else:
        print(f"✓ State already has enough URLs")
        print(f"  - Will resume from where it left off")
    
else:
    print("❌ No state file found at:", state_file)
    print("   Will start a fresh scraping session")

print("\n" + "=" * 80)
