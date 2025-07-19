#!/usr/bin/env python3
"""
Test the impact of adding documents on embeddings and matching
"""

import os
import sys
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from vector_database import VectorDatabaseManager
from embeddings_manager import GeminiEmbeddingsManager


def test_document_impact():
    """Test how document changes affect embeddings"""
    print("📊 Testing Document Impact on Embeddings")
    print("=" * 80)
    
    vector_db = VectorDatabaseManager()
    embeddings_manager = GeminiEmbeddingsManager()
    
    # Get current researcher embedding
    researchers = vector_db.get_all_researchers()
    if not researchers:
        print("No researchers found!")
        return
    
    researcher = researchers[0]
    print(f"\nResearcher: {researcher.get('name', 'Unknown')}")
    
    # Get current embedding
    result = vector_db.researchers.get(ids=[researcher['id']], include=['embeddings', 'metadatas'])
    if not result or not result.get('embeddings') or not result['embeddings'][0]:
        print("No embedding found!")
        return
    
    current_embedding = np.array(result['embeddings'][0])
    metadata = result['metadatas'][0] if result.get('metadatas') else {}
    
    print(f"\nCurrent profile metadata:")
    print(f"  - Total documents: {metadata.get('total_documents', 'Unknown')}")
    print(f"  - Research interests: {metadata.get('research_interests_count', 'Unknown')}")
    print(f"  - Embedding timestamp: {metadata.get('timestamp', 'Unknown')}")
    
    # Test embeddings for different content
    test_contents = [
        "Machine learning and artificial intelligence for healthcare diagnostics using deep neural networks",
        "Quantum computing applications in cryptography and secure communications",
        "Environmental sustainability through renewable energy and carbon capture technologies",
        researcher.get('summary', '') + " " + " ".join(researcher.get('research_interests', []))
    ]
    
    print("\n\n🧪 Testing embedding sensitivity to content:")
    print("-" * 60)
    
    for i, content in enumerate(test_contents):
        print(f"\nTest {i+1}: {content[:60]}...")
        
        # Generate embedding
        test_embedding = embeddings_manager.generate_embedding(content)
        test_embedding = np.array(test_embedding)
        
        # Calculate similarity with current profile
        similarity = embeddings_manager.calculate_similarity(
            current_embedding.tolist(),
            test_embedding.tolist()
        )
        
        # Calculate L2 distance
        l2_distance = np.linalg.norm(current_embedding - test_embedding)
        
        print(f"  - Cosine similarity: {similarity:.4f}")
        print(f"  - L2 distance: {l2_distance:.4f}")
        
        if i == 3:  # Last one is similar content
            print(f"  ✓ This is similar to the current profile (high similarity expected)")
        else:
            print(f"  → Different domain (lower similarity expected)")
    
    # Show how this affects matching
    print("\n\n🎯 Impact on Matching:")
    print("-" * 60)
    
    # Get top opportunities with current embedding
    matches = vector_db.search_opportunities_for_profile(
        current_embedding.tolist(),
        n_results=5
    )
    
    print("\nTop 5 matches with current profile:")
    for i, match in enumerate(matches):
        print(f"{i+1}. {match.get('title', 'Unknown')[:60]}... (Score: {match.get('similarity_score', 0):.4f})")


if __name__ == "__main__":
    test_document_impact()