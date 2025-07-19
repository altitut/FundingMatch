#!/usr/bin/env python3
"""
Diagnostic script to investigate embedding and matching issues
"""

import os
import sys
import json
import numpy as np
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from vector_database import VectorDatabaseManager
from embeddings_manager import GeminiEmbeddingsManager
from user_profile_manager import UserProfileManager


def analyze_embeddings():
    """Analyze the embeddings in the database"""
    print("🔍 Embedding Analysis")
    print("=" * 80)
    
    # Initialize managers
    vector_db = VectorDatabaseManager()
    embeddings_manager = GeminiEmbeddingsManager()
    
    # 1. Check researcher embeddings
    print("\n1. RESEARCHER EMBEDDINGS:")
    researchers = vector_db.get_all_researchers()
    print(f"   Total researchers in database: {len(researchers)}")
    
    # Get embeddings directly from ChromaDB
    try:
        researcher_data = vector_db.researchers.get(include=['embeddings', 'metadatas', 'documents'])
        if researcher_data and 'embeddings' in researcher_data:
            embeddings = researcher_data['embeddings']
            print(f"   Embeddings found: {len(embeddings)}")
            
            if embeddings:
                # Analyze embedding properties
                embedding_dims = [len(emb) if emb else 0 for emb in embeddings]
                print(f"   Embedding dimensions: {set(embedding_dims)}")
                
                # Check if embeddings are normalized
                for i, emb in enumerate(embeddings[:3]):  # Check first 3
                    if emb:
                        norm = np.linalg.norm(emb)
                        print(f"   Researcher {i} embedding norm: {norm:.4f}")
                        
                        # Check embedding statistics
                        emb_array = np.array(emb)
                        print(f"     - Min: {emb_array.min():.4f}, Max: {emb_array.max():.4f}")
                        print(f"     - Mean: {emb_array.mean():.4f}, Std: {emb_array.std():.4f}")
    except Exception as e:
        print(f"   Error getting researcher embeddings: {e}")
    
    # 2. Check opportunity embeddings
    print("\n2. OPPORTUNITY EMBEDDINGS:")
    opportunities = vector_db.get_all_opportunities()
    print(f"   Total opportunities in database: {len(opportunities)}")
    
    try:
        opp_data = vector_db.opportunities.get(include=['embeddings'], limit=10)
        if opp_data and 'embeddings' in opp_data:
            embeddings = opp_data['embeddings']
            print(f"   Sample embeddings retrieved: {len(embeddings)}")
            
            if embeddings:
                # Check if embeddings are normalized
                for i, emb in enumerate(embeddings[:3]):  # Check first 3
                    if emb:
                        norm = np.linalg.norm(emb)
                        print(f"   Opportunity {i} embedding norm: {norm:.4f}")
                        
                        # Check embedding statistics
                        emb_array = np.array(emb)
                        print(f"     - Min: {emb_array.min():.4f}, Max: {emb_array.max():.4f}")
                        print(f"     - Mean: {emb_array.mean():.4f}, Std: {emb_array.std():.4f}")
    except Exception as e:
        print(f"   Error getting opportunity embeddings: {e}")


def test_matching():
    """Test the matching process"""
    print("\n\n🎯 MATCHING TEST")
    print("=" * 80)
    
    vector_db = VectorDatabaseManager()
    
    # Get a researcher
    researchers = vector_db.get_all_researchers()
    if not researchers:
        print("   No researchers found in database")
        return
    
    researcher = researchers[0]
    print(f"\n   Testing with researcher: {researcher.get('name', 'Unknown')}")
    
    # Get researcher embedding
    try:
        result = vector_db.researchers.get(ids=[researcher['id']], include=['embeddings'])
        if result and result.get('embeddings') and result['embeddings'][0]:
            user_embedding = result['embeddings'][0]
            print(f"   Researcher embedding retrieved (dim: {len(user_embedding)})")
            
            # Search for matches
            matches = vector_db.search_opportunities_for_profile(
                user_embedding,
                n_results=10
            )
            
            print(f"\n   Found {len(matches)} matches:")
            for i, match in enumerate(matches[:5]):
                print(f"\n   Match {i+1}:")
                print(f"     Title: {match.get('title', 'Unknown')[:60]}...")
                print(f"     Agency: {match.get('agency', 'Unknown')}")
                print(f"     Similarity Score: {match.get('similarity_score', 0):.4f}")
                print(f"     Keywords: {match.get('keywords', [])[:3]}")
            
            # Check similarity score distribution
            if matches:
                scores = [m.get('similarity_score', 0) for m in matches]
                print(f"\n   Similarity Score Statistics:")
                print(f"     Min: {min(scores):.4f}")
                print(f"     Max: {max(scores):.4f}")
                print(f"     Mean: {np.mean(scores):.4f}")
                print(f"     Std: {np.std(scores):.4f}")
                print(f"     Range: {max(scores) - min(scores):.4f}")
                
    except Exception as e:
        print(f"   Error in matching test: {e}")


def check_profile_processing():
    """Check how profiles are being processed"""
    print("\n\n📁 PROFILE PROCESSING CHECK")
    print("=" * 80)
    
    upload_dir = 'uploads'
    
    # Count files
    pdf_files = [f for f in os.listdir(upload_dir) if f.endswith('.pdf')]
    json_files = [f for f in os.listdir(upload_dir) if f.endswith('.json')]
    
    print(f"\n   Files in uploads directory:")
    print(f"     PDF files: {len(pdf_files)}")
    print(f"     JSON files: {len(json_files)}")
    
    # Check a sample profile creation
    if json_files:
        user_manager = UserProfileManager()
        json_path = os.path.join(upload_dir, json_files[0])
        
        print(f"\n   Testing profile creation with: {json_files[0]}")
        
        # Create profile
        profile = user_manager.create_user_profile(json_path, [os.path.join(upload_dir, f) for f in pdf_files])
        
        print(f"\n   Profile created:")
        print(f"     Name: {profile.get('name', 'Unknown')}")
        print(f"     Research Interests: {len(profile.get('research_interests', []))}")
        print(f"     Extracted PDFs: {len(profile.get('extracted_pdfs', {}))}")
        print(f"     URLs: {len(profile.get('urls', []))}")
        print(f"     Combined text length: {len(profile.get('combined_text', ''))}")
        
        # Check what's in extracted_pdfs
        if profile.get('extracted_pdfs'):
            print(f"\n   Extracted PDF content samples:")
            for i, (filename, content) in enumerate(list(profile['extracted_pdfs'].items())[:3]):
                print(f"     {filename}: {len(content)} chars")


def test_new_embedding_generation():
    """Test generating new embeddings"""
    print("\n\n🔄 NEW EMBEDDING GENERATION TEST")
    print("=" * 80)
    
    embeddings_manager = GeminiEmbeddingsManager()
    
    # Test with different texts
    test_texts = [
        "Machine learning for healthcare applications using deep neural networks",
        "Funding opportunities for small business innovation research in biotechnology",
        "Artificial intelligence and data science for climate change research"
    ]
    
    print("\n   Generating test embeddings...")
    embeddings = []
    for text in test_texts:
        try:
            emb = embeddings_manager.generate_embedding(text)
            embeddings.append(emb)
            print(f"   ✓ Generated embedding for: '{text[:50]}...' (dim: {len(emb)})")
        except Exception as e:
            print(f"   ✗ Error generating embedding: {e}")
    
    # Calculate similarities between test embeddings
    if len(embeddings) >= 2:
        print("\n   Similarity matrix:")
        for i in range(len(embeddings)):
            for j in range(i+1, len(embeddings)):
                sim = embeddings_manager.calculate_similarity(embeddings[i], embeddings[j])
                print(f"     Text {i+1} vs Text {j+1}: {sim:.4f}")


if __name__ == "__main__":
    print("🚀 FundingMatch Embedding Diagnostics")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run diagnostics
    analyze_embeddings()
    test_matching()
    check_profile_processing()
    test_new_embedding_generation()
    
    print("\n\n✅ Diagnostics complete!")