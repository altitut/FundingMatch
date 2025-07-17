#!/usr/bin/env python3
"""
Simple test of CSV processing and embeddings without ChromaDB
"""

import os
import csv
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

load_dotenv()

from embeddings_manager import GeminiEmbeddingsManager


def test_csv_embeddings():
    """Test CSV processing and embeddings generation"""
    
    print("=== Testing CSV to Embeddings ===")
    
    # Initialize embeddings manager
    try:
        manager = GeminiEmbeddingsManager()
        print("✓ Initialized embeddings manager")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return
    
    # Process NSF CSV
    nsf_csv = "FundingOpportunities/nsf_funding.csv"
    print(f"\n1. Processing NSF CSV: {nsf_csv}")
    
    opportunities = []
    
    try:
        with open(nsf_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Process first 3 entries
            for idx, row in enumerate(reader):
                if idx >= 3:
                    break
                    
                opportunity = {
                    "id": f"nsf_{idx}",
                    "title": row.get("Title", ""),
                    "description": row.get("Synopsis", "")[:500],  # Limit description length
                    "agency": "NSF"
                }
                
                opportunities.append(opportunity)
                print(f"  - Read opportunity: {opportunity['title'][:60]}...")
                
    except Exception as e:
        print(f"✗ Failed to read CSV: {e}")
        return
    
    # Generate embeddings
    print(f"\n2. Generating embeddings for {len(opportunities)} opportunities...")
    
    embeddings_data = []
    
    for opp in opportunities:
        try:
            # Create text for embedding
            text = f"{opp['title']} {opp['description']}"
            
            print(f"\n  Processing: {opp['title'][:50]}...")
            embedding = manager.generate_embedding(text)
            
            print(f"  ✓ Generated embedding with {len(embedding)} dimensions")
            print(f"    First 5 values: {embedding[:5]}")
            
            embeddings_data.append({
                "opportunity": opp,
                "embedding": embedding
            })
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Test similarity between opportunities
    if len(embeddings_data) >= 2:
        print("\n3. Testing similarity between opportunities...")
        
        emb1 = embeddings_data[0]["embedding"]
        emb2 = embeddings_data[1]["embedding"]
        
        similarity = manager.calculate_similarity(emb1, emb2)
        print(f"  Similarity between first two opportunities: {similarity:.3f}")
    
    # Save results
    output_file = "test_embeddings_output.json"
    with open(output_file, 'w') as f:
        # Convert embeddings to lists for JSON serialization
        output_data = []
        for item in embeddings_data:
            output_data.append({
                "opportunity": item["opportunity"],
                "embedding_length": len(item["embedding"]),
                "embedding_sample": item["embedding"][:5]  # Just save first 5 values
            })
        
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")
    
    # Test SBIR CSV
    print("\n4. Testing SBIR CSV...")
    sbir_csv = "FundingOpportunities/topics_search_1752507977.csv"
    
    try:
        with open(sbir_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)  # Read first row
            
            sbir_opportunity = {
                "title": row.get("Topic Title", ""),
                "description": row.get("Topic Description", "")[:500]
            }
            
            print(f"  SBIR Title: {sbir_opportunity['title'][:60]}...")
            
            # Generate embedding
            text = f"{sbir_opportunity['title']} {sbir_opportunity['description']}"
            embedding = manager.generate_embedding(text)
            
            print(f"  ✓ Generated SBIR embedding with {len(embedding)} dimensions")
            
    except Exception as e:
        print(f"  ✗ Error processing SBIR: {e}")


if __name__ == "__main__":
    test_csv_embeddings()