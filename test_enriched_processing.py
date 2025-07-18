#!/usr/bin/env python3
"""
Test enriched processing of funding opportunities with URL content
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.funding_opportunities_manager import FundingOpportunitiesManager
from backend.vector_database import VectorDatabaseManager
from backend.embeddings_manager import GeminiEmbeddingsManager


def main():
    """Test enriched processing workflow"""
    
    print("=== Testing Enriched Funding Opportunities Processing ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Initialize manager
    print("1. Initializing Funding Opportunities Manager...")
    try:
        manager = FundingOpportunitiesManager()
        print("✓ Manager initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize manager: {e}")
        return
    
    # 2. Check CSV files
    print("\n2. Checking CSV files in FundingOpportunities folder...")
    csv_files = list(Path("FundingOpportunities").glob("*.csv"))
    print(f"Found {len(csv_files)} CSV files:")
    for csv_file in csv_files:
        print(f"  - {csv_file.name}")
    
    # 3. Process all CSV files with smaller batch size to handle rate limits
    print("\n3. Processing CSV files with URL enrichment...")
    print("Note: This will fetch content from URLs and may take some time...")
    
    try:
        # Use smaller batch size to manage API rate limits
        summary = manager.process_csv_files(batch_size=3)
        
        print("\n✅ Processing Summary:")
        print(f"  - Files processed: {summary['processed_files']}")
        print(f"  - New opportunities: {summary['new_opportunities']}")
        print(f"  - Expired skipped: {summary['expired_skipped']}")
        print(f"  - Duplicates skipped: {summary['duplicate_skipped']}")
        print(f"  - Expired removed: {summary.get('expired_removed', 0)}")
        
        if summary['errors']:
            print(f"\n⚠️  Errors encountered:")
            for error in summary['errors']:
                print(f"  - {error}")
                
    except Exception as e:
        print(f"✗ Error processing CSV files: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Verify database statistics
    print("\n4. Verifying Database Statistics...")
    vector_db = VectorDatabaseManager()
    stats = vector_db.get_collection_stats()
    print(f"  - Opportunities in vector DB: {stats['opportunities']}")
    
    # 5. Check processed opportunities
    print("\n5. Checking Processed Opportunities...")
    processed_file = Path("FundingOpportunities/processed_opportunities.json")
    if processed_file.exists():
        with open(processed_file, 'r') as f:
            processed_data = json.load(f)
        
        total_processed = len(processed_data['opportunities'])
        print(f"  - Total tracked opportunities: {total_processed}")
        
        # Count opportunities with expiration dates
        with_dates = 0
        without_dates = 0
        
        for opp_id, opp_info in processed_data['opportunities'].items():
            if opp_info.get('expiration_date'):
                with_dates += 1
            else:
                without_dates += 1
        
        print(f"  - With expiration dates: {with_dates}")
        print(f"  - Without expiration dates: {without_dates}")
    
    # 6. Test search with enriched embeddings
    print("\n6. Testing Search with Enriched Embeddings...")
    embeddings_manager = GeminiEmbeddingsManager()
    
    test_queries = [
        "machine learning artificial intelligence research",
        "space technology satellite launch systems",
        "photonic crystal laser systems"
    ]
    
    for query in test_queries:
        print(f"\n  Query: '{query}'")
        try:
            # Generate query embedding
            query_embedding = embeddings_manager.generate_embedding(query, task_type="RETRIEVAL_QUERY")
            
            # Search for opportunities
            matches = vector_db.search_opportunities_for_profile(
                query_embedding,
                n_results=3
            )
            
            print(f"  Found {len(matches)} matches:")
            for i, match in enumerate(matches, 1):
                print(f"    {i}. {match.get('title', 'Unknown')[:60]}...")
                print(f"       Score: {match.get('similarity_score', 0):.3f}")
                print(f"       Agency: {match.get('agency', 'Unknown')}")
                print(f"       Deadline: {match.get('close_date', 'N/A')}")
                
                # Check if URL content was included
                if 'url_content' in match:
                    print(f"       ✓ URL content enriched")
                
                # Add delay to avoid rate limits
                time.sleep(1)
                
        except Exception as e:
            print(f"  ✗ Error searching: {e}")
            # If rate limit, wait
            if "429" in str(e):
                print("  Waiting 30 seconds for rate limit...")
                time.sleep(30)
    
    # 7. Sample enriched opportunity
    print("\n7. Sample Enriched Opportunity:")
    try:
        sample_embedding = embeddings_manager.generate_embedding("sample test")
        sample_results = vector_db.search_opportunities_for_profile(sample_embedding, n_results=1)
        
        if sample_results:
            sample = sample_results[0]
            print(f"\n  Title: {sample.get('title', 'Unknown')}")
            print(f"  Agency: {sample.get('agency', 'Unknown')}")
            print(f"  Description: {sample.get('description', '')[:200]}...")
            
            if 'url_content' in sample:
                url_content = sample['url_content']
                print(f"\n  URL Content Enrichments:")
                if url_content.get('keywords'):
                    print(f"    Keywords: {', '.join(url_content['keywords'][:5])}")
                if url_content.get('deadline_info'):
                    print(f"    Deadline info: {url_content['deadline_info'][:100]}")
                if url_content.get('award_info'):
                    print(f"    Award info: {url_content['award_info'][:100]}")
                    
    except Exception as e:
        print(f"  ✗ Error getting sample: {e}")
    
    # 8. Check ingested folder
    print("\n8. Checking Ingested Folder...")
    ingested_files = list(Path("FundingOpportunities/Ingested").glob("*.csv"))
    print(f"  Files moved to Ingested: {len(ingested_files)}")
    for f in ingested_files[:5]:  # Show first 5
        print(f"    - {f.name}")
    
    print(f"\n✅ Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()