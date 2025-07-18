#!/usr/bin/env python3
"""
Limited test of enriched processing - processes only first few opportunities
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.funding_opportunities_manager import FundingOpportunitiesManager
from backend.vector_database import VectorDatabaseManager


def process_limited_opportunities():
    """Process limited number of opportunities for testing"""
    
    print("=== Limited Test of Enriched Processing ===")
    print("Processing only first 5 opportunities from each CSV file...\n")
    
    # Initialize manager
    manager = FundingOpportunitiesManager()
    
    # Process NSF funding CSV
    nsf_csv = Path("FundingOpportunities/nsf_funding.csv")
    if nsf_csv.exists():
        print(f"Processing {nsf_csv.name}...")
        opportunities = manager._process_nsf_csv(nsf_csv)[:5]  # Only first 5
        
        print(f"  Found {len(opportunities)} opportunities to process")
        
        # Process them
        summary = manager._process_opportunities(opportunities, batch_size=2)
        print(f"  Processed: New={summary['new']}, Expired={summary['expired']}, Duplicates={summary['duplicates']}")
    
    # Save processed IDs
    manager._save_processed_ids()
    
    # Check results
    print("\n=== Results ===")
    
    # Database stats
    vector_db = VectorDatabaseManager()
    stats = vector_db.get_collection_stats()
    print(f"Opportunities in vector DB: {stats['opportunities']}")
    
    # Check a processed opportunity
    if manager.processed_ids['opportunities']:
        sample_id = list(manager.processed_ids['opportunities'].keys())[0]
        sample_info = manager.processed_ids['opportunities'][sample_id]
        print(f"\nSample processed opportunity:")
        print(f"  Title: {sample_info['title'][:60]}...")
        print(f"  Processed: {sample_info['processed_date']}")
        print(f"  Expires: {sample_info.get('expiration_date', 'No date')}")
    
    print("\n✓ Limited test completed!")


if __name__ == "__main__":
    process_limited_opportunities()