#!/usr/bin/env python3
"""
Remove test opportunities from the database
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from vector_database import VectorDatabaseManager

def remove_test_opportunities():
    """Remove opportunities with example.gov URLs"""
    db = VectorDatabaseManager()
    
    # Get all opportunities
    opportunities = db.get_all_opportunities()
    print(f"Total opportunities before removal: {len(opportunities)}")
    
    # Find test opportunities (those with example.gov URLs)
    test_opportunity_ids = []
    for opp in opportunities:
        url = opp.get('url', '')
        if 'example.gov' in url:
            test_opportunity_ids.append(opp['id'])
            print(f"Found test opportunity: {opp['title']} (ID: {opp['id']})")
    
    print(f"\nFound {len(test_opportunity_ids)} test opportunities to remove")
    
    if test_opportunity_ids:
        # Remove each test opportunity
        for opp_id in test_opportunity_ids:
            try:
                db.opportunities.delete(ids=[opp_id])
                print(f"✓ Removed opportunity ID: {opp_id}")
            except Exception as e:
                print(f"❌ Error removing opportunity {opp_id}: {e}")
        
        # Verify removal
        remaining_opportunities = db.get_all_opportunities()
        print(f"\nTotal opportunities after removal: {len(remaining_opportunities)}")
        
        # Check if any test opportunities remain
        remaining_test = [opp for opp in remaining_opportunities if 'example.gov' in opp.get('url', '')]
        if remaining_test:
            print(f"⚠️  Warning: {len(remaining_test)} test opportunities still remain")
        else:
            print("✅ All test opportunities successfully removed")
    else:
        print("No test opportunities found to remove")

if __name__ == "__main__":
    remove_test_opportunities()