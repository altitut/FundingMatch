#!/usr/bin/env python3
"""
Simple test of embeddings functionality
"""

import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

load_dotenv()

def test_embeddings():
    """Test basic embeddings functionality"""
    
    # Test imports
    try:
        from embeddings_manager import GeminiEmbeddingsManager
        print("✓ Successfully imported GeminiEmbeddingsManager")
    except Exception as e:
        print(f"✗ Failed to import GeminiEmbeddingsManager: {e}")
        return
    
    # Test initialization
    try:
        manager = GeminiEmbeddingsManager()
        print("✓ Successfully initialized embeddings manager")
    except Exception as e:
        print(f"✗ Failed to initialize embeddings manager: {e}")
        return
    
    # Test embedding generation
    try:
        test_text = "Machine learning for funding opportunity matching"
        print(f"\nGenerating embedding for: '{test_text}'")
        
        embedding = manager.generate_embedding(test_text)
        print(f"✓ Generated embedding with {len(embedding)} dimensions")
        print(f"  First 5 values: {embedding[:5]}")
        
    except Exception as e:
        print(f"✗ Failed to generate embedding: {e}")
        import traceback
        traceback.print_exc()
        
    # Test similarity calculation
    try:
        text2 = "AI-powered grant matching system"
        print(f"\nGenerating embedding for: '{text2}'")
        
        embedding2 = manager.generate_embedding(text2)
        similarity = manager.calculate_similarity(embedding, embedding2)
        
        print(f"✓ Similarity score: {similarity:.3f}")
        
    except Exception as e:
        print(f"✗ Failed to calculate similarity: {e}")


if __name__ == "__main__":
    print("=== Testing Embeddings System ===")
    test_embeddings()