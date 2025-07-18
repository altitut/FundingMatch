#!/usr/bin/env python3
"""
Verify that enriched embeddings are correctly stored
"""

import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.vector_database import VectorDatabaseManager
from backend.embeddings_manager import GeminiEmbeddingsManager


def verify_enriched_storage():
    """Verify enriched embeddings storage"""
    
    print("=== Verifying Enriched Embeddings Storage ===\n")
    
    # Initialize components
    vector_db = VectorDatabaseManager()
    embeddings_manager = GeminiEmbeddingsManager()
    
    # 1. Check database statistics
    print("1. Database Statistics:")
    stats = vector_db.get_collection_stats()
    print(f"   Total opportunities stored: {stats['opportunities']}")
    
    # 2. Sample search to check enriched content
    print("\n2. Sample Search Results:")
    
    try:
        # Search for a specific topic
        query = "network systems intelligent technology"
        query_embedding = embeddings_manager.generate_embedding(query, task_type="RETRIEVAL_QUERY")
        
        matches = vector_db.search_opportunities_for_profile(
            query_embedding,
            n_results=2
        )
        
        for i, match in enumerate(matches, 1):
            print(f"\n   Match {i}:")
            print(f"   Title: {match.get('title', 'Unknown')}")
            print(f"   Score: {match.get('similarity_score', 0):.3f}")
            print(f"   Agency: {match.get('agency', 'Unknown')}")
            print(f"   Deadline: {match.get('close_date', 'Not specified')}")
            
            # Check for enriched content
            if 'url_content' in match:
                print("   ✓ URL content present")
                url_content = match['url_content']
                if url_content.get('keywords'):
                    print(f"   Keywords from URL: {', '.join(url_content['keywords'][:5])}")
            else:
                print("   ✗ No URL content")
                
            if 'keywords' in match and match['keywords']:
                print(f"   Keywords: {match['keywords'][:5] if isinstance(match['keywords'], list) else 'Present'}")
                
            # Show snippet of description to verify enrichment
            desc = match.get('description', '')
            if desc:
                print(f"   Description preview: {desc[:150]}...")
                if "From URL:" in desc:
                    print("   ✓ Description enriched from URL")
                    
    except Exception as e:
        print(f"   ✗ Error during search: {e}")
    
    # 3. Check processed opportunities file
    print("\n3. Processed Opportunities Summary:")
    processed_file = "FundingOpportunities/processed_opportunities.json"
    
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as f:
            processed_data = json.load(f)
        
        total = len(processed_data['opportunities'])
        with_dates = sum(1 for opp in processed_data['opportunities'].values() 
                        if opp.get('expiration_date'))
        
        print(f"   Total tracked: {total}")
        print(f"   With expiration dates: {with_dates}")
        print(f"   Without expiration dates: {total - with_dates}")
        
        # Show sample
        if processed_data['opportunities']:
            sample_id, sample = list(processed_data['opportunities'].items())[0]
            print(f"\n   Sample tracked opportunity:")
            print(f"   ID: {sample_id}")
            print(f"   Title: {sample['title'][:60]}...")
            print(f"   Expiration: {sample.get('expiration_date', 'None')}")
    
    print("\n✓ Verification complete!")


if __name__ == "__main__":
    verify_enriched_storage()