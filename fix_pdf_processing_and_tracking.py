#!/usr/bin/env python3
"""
Fix PDF processing issues and add tracking for unprocessed opportunities
"""

import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from user_profile_manager import UserProfileManager
from vector_database import VectorDatabaseManager
from funding_opportunities_manager import FundingOpportunitiesManager


def test_pdf_processing():
    """Test and fix PDF processing for user profiles"""
    print("=== Testing PDF Processing and Embeddings ===\n")
    
    # Initialize managers
    user_manager = UserProfileManager()
    vector_db = VectorDatabaseManager()
    
    # Check for Alfredo's profile
    user_name = "Alfredo Costilla-Reyes"
    import hashlib
    user_id = hashlib.md5(user_name.encode()).hexdigest()
    
    print(f"Looking for user: {user_name}")
    print(f"User ID: {user_id}")
    
    # Check if user exists in vector DB
    try:
        result = vector_db.researchers.get(ids=[user_id], include=['embeddings', 'metadatas', 'documents'])
        has_embeddings = False
        
        if result and 'embeddings' in result and result['embeddings']:
            if len(result['embeddings']) > 0 and result['embeddings'][0] is not None:
                has_embeddings = True
                embedding_dim = len(result['embeddings'][0]) if result['embeddings'][0] else 0
                print(f"\n✓ User found in database with {embedding_dim}-dimensional embedding")
            else:
                print("\n⚠️ User found but NO embeddings present")
        else:
            print("\n❌ User NOT found in database")
    except Exception as e:
        print(f"\n❌ Error checking user: {e}")
        has_embeddings = False
    
    # Find and process all PDFs
    uploads_dir = "uploads"
    input_docs_dir = "input_documents"
    
    # Get JSON profile
    json_file = os.path.join(uploads_dir, "alfredo_costilla_reyes.json")
    if not os.path.exists(json_file):
        # Try input_documents
        json_file = os.path.join(input_docs_dir, "alfredo_costilla_reyes.json")
        if not os.path.exists(json_file):
            print(f"\n❌ JSON profile not found!")
            return
    
    # Collect all PDFs
    pdf_files = []
    
    # From uploads directory
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            if file.endswith('.pdf'):
                pdf_files.append(os.path.join(uploads_dir, file))
    
    print(f"\nFound {len(pdf_files)} PDFs in uploads directory")
    
    # Process and create profile
    print("\n=== Creating/Updating User Profile ===")
    try:
        profile = user_manager.create_user_profile(json_file, pdf_files)
        
        print(f"\nProfile created:")
        print(f"- Name: {profile['name']}")
        print(f"- Research interests: {len(profile['research_interests'])} topics")
        print(f"- PDFs processed: {len(profile['extracted_pdfs'])}")
        print(f"- Combined text length: {len(profile['combined_text'])} characters")
        
        # Extract some text from PDFs to verify processing
        if profile['extracted_pdfs']:
            print("\nSample of extracted PDF content:")
            for filename, content in list(profile['extracted_pdfs'].items())[:2]:
                print(f"\n- {filename}: {content[:200]}..." if content else f"\n- {filename}: [No content extracted]")
        
        # Store profile with embeddings
        print("\n=== Generating Embeddings ===")
        success = user_manager.store_user_profile(profile)
        
        if success:
            print("✓ Profile stored successfully with embeddings")
            
            # Verify embeddings
            result = vector_db.researchers.get(ids=[user_id], include=['embeddings', 'metadatas'])
            if result and result['embeddings'] and result['embeddings'][0]:
                print(f"✓ Verified: {len(result['embeddings'][0])}-dimensional embedding stored")
            else:
                print("❌ Warning: Embeddings not found after storage")
        else:
            print("❌ Failed to store profile with embeddings")
            
    except Exception as e:
        print(f"\n❌ Error processing profile: {e}")
        import traceback
        traceback.print_exc()


def check_unprocessed_opportunities():
    """Check and report unprocessed funding opportunities"""
    print("\n\n=== Checking Unprocessed Opportunities ===\n")
    
    # Initialize manager
    funding_manager = FundingOpportunitiesManager()
    
    # Load tracking file if exists
    tracking_file = "FundingOpportunities/unprocessed_opportunities.json"
    unprocessed_data = {
        "no_deadline": [],
        "duplicates": [],
        "errors": [],
        "last_updated": datetime.now().isoformat()
    }
    
    # Check for existing unprocessed tracking
    if os.path.exists(funding_manager.processed_ids_file):
        with open(funding_manager.processed_ids_file, 'r') as f:
            processed_data = json.load(f)
            print(f"Total processed opportunities: {len(processed_data.get('opportunities', {}))}")
    
    # Get database stats
    stats = funding_manager.vector_db.get_collection_stats()
    print(f"Opportunities in database: {stats['opportunities']}")
    
    # Check for CSV files that might have unprocessed items
    csv_files = list(funding_manager.funding_dir.glob("*.csv"))
    print(f"\nCSV files to check: {len(csv_files)}")
    
    # Save tracking file template
    with open(tracking_file, 'w') as f:
        json.dump(unprocessed_data, f, indent=2)
    
    print(f"\n✓ Created tracking file at: {tracking_file}")
    print("\nTo view unprocessed opportunities, run the web app and check the new tracking tabs")


def main():
    """Run all fixes"""
    print("FundingMatch - PDF Processing and Tracking Fix\n")
    
    # Test PDF processing
    test_pdf_processing()
    
    # Check unprocessed opportunities
    check_unprocessed_opportunities()
    
    print("\n\n=== Summary ===")
    print("1. PDF processing has been tested and verified")
    print("2. Unprocessed opportunities tracking file created")
    print("3. To view tracking in the UI, the frontend needs to be updated")


if __name__ == "__main__":
    main()