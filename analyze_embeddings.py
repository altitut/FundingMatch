#!/usr/bin/env python3
"""
Analyze embeddings and matching scores to understand clustering
"""

import json
import numpy as np
from pathlib import Path
from backend.isolated_vector_database import IsolatedVectorDatabaseManager
import matplotlib.pyplot as plt

def analyze_embeddings():
    """Analyze the distribution of embeddings and similarities"""
    print("🔍 Analyzing Embeddings and Matching Scores")
    print("=" * 60)
    
    # Initialize vector database
    vector_db = IsolatedVectorDatabaseManager()
    
    # Get user profile embeddings
    print("\n1. Checking User Profile Embeddings...")
    try:
        # Get Alfredo's profile
        user_results = vector_db.users_db.get(
            where={"$contains": {"name": "Alfredo"}},
            include=["embeddings", "metadatas"]
        )
        
        if user_results and user_results['embeddings']:
            user_embedding = np.array(user_results['embeddings'][0])
            print(f"   ✅ Found user embedding (dimension: {len(user_embedding)})")
            print(f"   Embedding norm: {np.linalg.norm(user_embedding):.4f}")
        else:
            print("   ❌ No user embeddings found")
            return
    except Exception as e:
        print(f"   ❌ Error getting user embeddings: {e}")
        return
    
    # Get opportunity embeddings sample
    print("\n2. Analyzing Opportunity Embeddings...")
    try:
        # Get a sample of opportunities
        opp_results = vector_db.opportunities_db.get(
            limit=100,
            include=["embeddings", "metadatas"]
        )
        
        if opp_results and opp_results['embeddings']:
            opp_embeddings = np.array(opp_results['embeddings'])
            print(f"   ✅ Found {len(opp_embeddings)} opportunity embeddings")
            
            # Calculate similarities
            similarities = []
            for opp_emb in opp_embeddings:
                sim = np.dot(user_embedding, opp_emb)
                similarities.append(sim)
            
            similarities = np.array(similarities)
            
            print(f"\n3. Similarity Distribution Analysis:")
            print(f"   - Min similarity: {similarities.min():.4f}")
            print(f"   - Max similarity: {similarities.max():.4f}")
            print(f"   - Mean similarity: {similarities.mean():.4f}")
            print(f"   - Std deviation: {similarities.std():.4f}")
            print(f"   - Range: {similarities.max() - similarities.min():.4f}")
            
            # Analyze clustering
            print(f"\n4. Clustering Analysis:")
            percentiles = [10, 25, 50, 75, 90]
            for p in percentiles:
                value = np.percentile(similarities, p)
                print(f"   - {p}th percentile: {value:.4f}")
            
            # Plot distribution
            plt.figure(figsize=(10, 6))
            plt.hist(similarities, bins=30, alpha=0.7, color='blue', edgecolor='black')
            plt.xlabel('Cosine Similarity')
            plt.ylabel('Count')
            plt.title('Distribution of Funding Opportunity Similarities')
            plt.axvline(similarities.mean(), color='red', linestyle='--', label=f'Mean: {similarities.mean():.3f}')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.savefig('similarity_distribution.png', dpi=150, bbox_inches='tight')
            print("\n   📊 Saved similarity distribution plot to 'similarity_distribution.png'")
            
            # Recommendations
            print("\n5. Recommendations for Better Score Distribution:")
            
            if similarities.std() < 0.05:
                print("   ⚠️  Very low variance in similarities - opportunities are too similar")
                print("   Recommendations:")
                print("   - Consider using more diverse funding sources")
                print("   - Apply keyword filtering before embedding search")
                print("   - Use hybrid search (keywords + embeddings)")
            
            narrow_range = similarities.max() - similarities.min()
            if narrow_range < 0.1:
                print(f"   ⚠️  Narrow similarity range ({narrow_range:.4f})")
                print("   The exponential transformation in vector_database.py should help spread these scores")
            
            # Show how transformation affects scores
            print("\n6. Score Transformation Effect:")
            sample_sims = [similarities.min(), np.percentile(similarities, 25), 
                          similarities.mean(), np.percentile(similarities, 75), similarities.max()]
            
            print("   Raw Similarity → Confidence Score:")
            for sim in sample_sims:
                # Simulate the transformation
                normalized = (sim - similarities.min()) / (similarities.max() - similarities.min() + 1e-10)
                transformed = 1 - np.exp(-3 * normalized)
                final_score = 20 + (transformed * 75)
                print(f"   {sim:.4f} → {final_score:.1f}%")
            
        else:
            print("   ❌ No opportunity embeddings found")
            
    except Exception as e:
        print(f"   ❌ Error analyzing opportunities: {e}")

if __name__ == "__main__":
    analyze_embeddings()