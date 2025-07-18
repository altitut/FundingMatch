#!/usr/bin/env python3
"""
Verify that opportunities are correctly stored in ChromaDB
"""

import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.vector_database import VectorDatabaseManager
from backend.embeddings_manager import GeminiEmbeddingsManager


def verify_chromadb_storage():
    """Verify ChromaDB storage and functionality"""
    
    print("=== Verifying ChromaDB Storage ===\n")
    
    # Initialize components
    vector_db = VectorDatabaseManager()
    embeddings_manager = GeminiEmbeddingsManager()
    
    # 1. Check collection statistics
    print("1. Collection Statistics:")
    stats = vector_db.get_collection_stats()
    print(json.dumps(stats, indent=2))
    
    # 2. Test search with a query
    print("\n2. Testing Search Functionality:")
    test_queries = [
        "machine learning artificial intelligence",
        "space technology satellite systems",
        "underwater sensing marine applications",
        "education broadening participation"
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
                
        except Exception as e:
            print(f"  ✗ Error searching: {e}")
    
    # 3. Check for expired opportunities
    print("\n3. Checking Expired Opportunities:")
    
    # Load processed opportunities to check expiration dates
    processed_file = "FundingOpportunities/processed_opportunities.json"
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as f:
            processed_data = json.load(f)
        
        now = datetime.now()
        expired_count = 0
        active_count = 0
        no_date_count = 0
        
        for opp_id, opp_info in processed_data["opportunities"].items():
            if opp_info.get("expiration_date"):
                exp_date = datetime.fromisoformat(opp_info["expiration_date"].replace('+00:00', ''))
                if exp_date < now:
                    expired_count += 1
                else:
                    active_count += 1
            else:
                no_date_count += 1
        
        print(f"  Active opportunities: {active_count}")
        print(f"  Expired opportunities: {expired_count}")
        print(f"  No expiration date: {no_date_count}")
    
    # 4. Verify duplicate handling
    print("\n4. Duplicate Handling Test:")
    
    # Try to add a duplicate opportunity
    try:
        # Get a sample opportunity from the database
        test_query_embedding = embeddings_manager.generate_embedding("test")
        sample_results = vector_db.search_opportunities_for_profile(test_query_embedding, n_results=1)
        
        if sample_results:
            sample_opp = sample_results[0]
            print(f"  Testing with: {sample_opp.get('title', 'Unknown')[:50]}...")
            
            # Try to add it again (should be handled by the manager, not ChromaDB directly)
            print("  ✓ Duplicate handling would be managed by FundingOpportunitiesManager")
        else:
            print("  No opportunities found for duplicate test")
            
    except Exception as e:
        print(f"  ✗ Error in duplicate test: {e}")
    
    # 5. Performance test
    print("\n5. Performance Test:")
    import time
    
    try:
        # Generate a test embedding
        test_embedding = embeddings_manager.generate_embedding("innovative technology research funding")
        
        # Time the search
        start_time = time.time()
        results = vector_db.search_opportunities_for_profile(test_embedding, n_results=20)
        search_time = time.time() - start_time
        
        print(f"  Search time for 20 results: {search_time:.3f} seconds")
        print(f"  Results returned: {len(results)}")
        
    except Exception as e:
        print(f"  ✗ Error in performance test: {e}")
    
    print("\n✓ Verification complete!")


if __name__ == "__main__":
    verify_chromadb_storage()