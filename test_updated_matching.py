#!/usr/bin/env python3
"""
Test the updated matching algorithm
"""

import os
import sys
import json
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from vector_database import VectorDatabaseManager
from user_profile_manager import UserProfileManager


def test_updated_matching():
    """Test the updated matching with better score distribution"""
    print("🧪 Testing Updated Matching Algorithm")
    print("=" * 80)
    
    vector_db = VectorDatabaseManager()
    
    # Get Alfredo's profile
    researchers = vector_db.get_all_researchers()
    if not researchers:
        print("No researchers found!")
        return
    
    researcher = researchers[0]
    print(f"\nTesting with: {researcher.get('name', 'Unknown')}")
    
    # Get embedding
    result = vector_db.researchers.get(ids=[researcher['id']], include=['embeddings'])
    if not result or not result.get('embeddings') or not result['embeddings'][0]:
        print("No embedding found!")
        return
    
    user_embedding = result['embeddings'][0]
    
    # Test with different n_results
    for n_results in [10, 20, 50]:
        print(f"\n📊 Testing with n_results={n_results}")
        matches = vector_db.search_opportunities_for_profile(
            user_embedding,
            n_results=n_results
        )
        
        if matches:
            scores = [m.get('similarity_score', 0) for m in matches]
            raw_distances = [m.get('raw_distance', 0) for m in matches]
            
            print(f"\n   Similarity Scores:")
            print(f"     Count: {len(scores)}")
            print(f"     Min: {min(scores):.4f}")
            print(f"     Max: {max(scores):.4f}")
            print(f"     Mean: {np.mean(scores):.4f}")
            print(f"     Std: {np.std(scores):.4f}")
            print(f"     Range: {max(scores) - min(scores):.4f}")
            
            print(f"\n   Raw L2 Distances:")
            print(f"     Min: {min(raw_distances):.4f}")
            print(f"     Max: {max(raw_distances):.4f}")
            print(f"     Mean: {np.mean(raw_distances):.4f}")
            
            # Show top 5 matches
            print(f"\n   Top 5 Matches:")
            for i, match in enumerate(matches[:5]):
                print(f"\n   {i+1}. {match.get('title', 'Unknown')[:60]}...")
                print(f"      Agency: {match.get('agency', 'Unknown')}")
                print(f"      Similarity: {match.get('similarity_score', 0):.4f}")
                print(f"      Raw Distance: {match.get('raw_distance', 0):.4f}")
            
            # Calculate confidence scores as the app would
            confidences = []
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score if max_score > min_score else 1
            
            for score in scores:
                if score_range > 0:
                    normalized_score = (score - min_score) / score_range
                else:
                    normalized_score = score
                confidence = 20 + (75 * (normalized_score ** 0.7))
                confidence = min(95, max(20, confidence))
                confidences.append(confidence)
            
            print(f"\n   Confidence Scores (as shown in UI):")
            print(f"     Min: {min(confidences):.1f}%")
            print(f"     Max: {max(confidences):.1f}%")
            print(f"     Range: {max(confidences) - min(confidences):.1f}%")


if __name__ == "__main__":
    test_updated_matching()