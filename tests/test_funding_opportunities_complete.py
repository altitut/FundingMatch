#!/usr/bin/env python3
"""
Comprehensive test of funding opportunities management system
Tests CSV processing, embeddings generation, ChromaDB storage, and expiration handling
"""

import os
import sys
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.funding_opportunities_manager import FundingOpportunitiesManager
from backend.vector_database import VectorDatabaseManager


def create_test_csv_with_dates():
    """Create a test CSV with various expiration dates for testing"""
    test_csv_content = """Title,Synopsis,Next due date (Y-m-d),Program ID,Status
"Active Opportunity 1","This is an active funding opportunity","{future_date}","NSF-001","Active"
"Active Opportunity 2","Another active opportunity","{future_date2}","NSF-002","Active"
"Expired Opportunity 1","This opportunity has expired","{past_date}","NSF-003","Closed"
"No Date Opportunity","This opportunity has no deadline","","NSF-004","Open"
"Soon to Expire","This expires tomorrow","{tomorrow}","NSF-005","Active"
"""
    
    # Calculate dates
    today = datetime.now()
    future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
    future_date2 = (today + timedelta(days=60)).strftime("%Y-%m-%d")
    past_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Format content
    content = test_csv_content.format(
        future_date=future_date,
        future_date2=future_date2,
        past_date=past_date,
        tomorrow=tomorrow
    )
    
    # Write test file
    test_file = Path("FundingOpportunities/test_opportunities.csv")
    with open(test_file, 'w') as f:
        f.write(content)
    
    print(f"Created test CSV: {test_file}")
    return test_file


def test_complete_workflow():
    """Test the complete funding opportunities workflow"""
    
    print("=== Testing Complete Funding Opportunities Workflow ===\n")
    
    # 1. Initialize manager
    print("1. Initializing Funding Opportunities Manager...")
    try:
        manager = FundingOpportunitiesManager()
        print("✓ Manager initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize manager: {e}")
        return
    
    # 2. Check initial statistics
    print("\n2. Initial Statistics:")
    initial_stats = manager.get_statistics()
    print(json.dumps(initial_stats, indent=2))
    
    # 3. Create test CSV if needed
    test_csv = create_test_csv_with_dates()
    
    # 4. Process CSV files
    print("\n3. Processing CSV files...")
    try:
        summary = manager.process_csv_files(batch_size=5)
        print("\nProcessing Summary:")
        print(f"  - Files processed: {summary['processed_files']}")
        print(f"  - New opportunities: {summary['new_opportunities']}")
        print(f"  - Expired skipped: {summary['expired_skipped']}")
        print(f"  - Duplicates skipped: {summary['duplicate_skipped']}")
        print(f"  - Expired removed: {summary.get('expired_removed', 0)}")
        if summary['errors']:
            print(f"  - Errors: {summary['errors']}")
    except Exception as e:
        print(f"✗ Error processing CSV files: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. Check if files were moved
    print("\n4. Checking file movement...")
    ingested_dir = Path("FundingOpportunities/Ingested")
    ingested_files = list(ingested_dir.glob("*.csv"))
    print(f"  Files in Ingested folder: {[f.name for f in ingested_files]}")
    
    # 6. Test duplicate handling
    print("\n5. Testing duplicate handling...")
    # Copy a file back to test duplicate detection
    if ingested_files:
        test_file = ingested_files[0]
        shutil.copy(test_file, Path("FundingOpportunities") / f"duplicate_{test_file.name}")
        print(f"  Created duplicate file: duplicate_{test_file.name}")
        
        # Process again
        summary2 = manager.process_csv_files()
        print(f"  Second processing - New: {summary2['new_opportunities']}, Duplicates: {summary2['duplicate_skipped']}")
    
    # 7. Final statistics
    print("\n6. Final Statistics:")
    final_stats = manager.get_statistics()
    print(json.dumps(final_stats, indent=2))
    
    # 8. Test vector database search
    print("\n7. Testing Vector Database Search...")
    vector_db = VectorDatabaseManager()
    
    # Get a sample profile embedding (mock)
    from backend.embeddings_manager import GeminiEmbeddingsManager
    embeddings_manager = GeminiEmbeddingsManager()
    
    try:
        # Create a test query
        test_query = "Machine learning and artificial intelligence research funding"
        query_embedding = embeddings_manager.generate_embedding(test_query)
        
        # Search for opportunities
        matches = vector_db.search_opportunities_for_profile(
            query_embedding,
            n_results=5
        )
        
        print(f"\nFound {len(matches)} matching opportunities:")
        for i, match in enumerate(matches, 1):
            print(f"\n  {i}. {match.get('title', 'Unknown')}")
            print(f"     Agency: {match.get('agency', 'Unknown')}")
            print(f"     Score: {match.get('similarity_score', 0):.3f}")
            print(f"     Deadline: {match.get('close_date', 'N/A')}")
            
    except Exception as e:
        print(f"✗ Error testing search: {e}")
    
    # 9. Clean up test files
    print("\n8. Cleaning up test files...")
    test_files_to_remove = [
        Path("FundingOpportunities") / f"duplicate_{f.name}" 
        for f in ingested_files 
        if (Path("FundingOpportunities") / f"duplicate_{f.name}").exists()
    ]
    
    for f in test_files_to_remove:
        os.remove(f)
        print(f"  Removed: {f.name}")
    
    print("\n✓ Test completed successfully!")


def test_specific_csv():
    """Test processing specific NSF and SBIR CSV files"""
    
    print("\n=== Testing Specific CSV Files ===\n")
    
    manager = FundingOpportunitiesManager()
    
    # Check for NSF funding CSV
    nsf_csv = Path("FundingOpportunities/nsf_funding.csv")
    if nsf_csv.exists():
        print(f"Processing {nsf_csv.name}...")
        
        # Process just this file
        opportunities = manager._process_nsf_csv(nsf_csv)
        print(f"  Found {len(opportunities)} opportunities")
        
        # Show sample
        if opportunities:
            opp = opportunities[0]
            print(f"\n  Sample opportunity:")
            print(f"    Title: {opp['title'][:60]}...")
            print(f"    Deadline: {opp.get('close_date', 'N/A')}")
            
            # Check expiration
            is_expired, exp_date = manager._is_expired(opp)
            print(f"    Expired: {is_expired} (Date: {exp_date})")
    
    # Check for SBIR CSV
    sbir_csv = Path("FundingOpportunities/topics_search_1752507977.csv")
    if sbir_csv.exists():
        print(f"\nProcessing {sbir_csv.name}...")
        
        opportunities = manager._process_sbir_csv(sbir_csv)
        print(f"  Found {len(opportunities)} opportunities")
        
        # Show sample
        if opportunities:
            opp = opportunities[0]
            print(f"\n  Sample opportunity:")
            print(f"    Title: {opp['title'][:60]}...")
            print(f"    Deadline: {opp.get('close_date', 'N/A')}")
            
            # Check expiration
            is_expired, exp_date = manager._is_expired(opp)
            print(f"    Expired: {is_expired} (Date: {exp_date})")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test funding opportunities management')
    parser.add_argument('--specific', action='store_true', 
                       help='Test specific CSV files without full processing')
    
    args = parser.parse_args()
    
    if args.specific:
        test_specific_csv()
    else:
        test_complete_workflow()