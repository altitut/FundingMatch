#!/usr/bin/env python3
"""
Test script to process all documents in input_documents folder
and ensure embeddings are correctly produced for Alfredo Costilla-Reyes
"""

import os
import sys
import shutil
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from user_profile_manager import UserProfileManager
from vector_database import VectorDatabaseManager

def main():
    """Process all documents from input_documents folder"""
    
    # Initialize managers
    user_manager = UserProfileManager()
    vector_db = VectorDatabaseManager()
    
    # Paths
    input_docs_dir = "input_documents"
    uploads_dir = "uploads"
    
    # Get JSON profile
    json_file = os.path.join(input_docs_dir, "alfredo_costilla_reyes.json")
    if not os.path.exists(json_file):
        print(f"Error: JSON profile not found at {json_file}")
        return
    
    # Collect all PDF files from input_documents
    pdf_files = []
    
    # Add PDFs from root of input_documents
    for file in os.listdir(input_docs_dir):
        if file.endswith('.pdf'):
            pdf_files.append(os.path.join(input_docs_dir, file))
    
    # Add PDFs from subdirectories
    subdirs = ["ResearchPapers/First author journals", 
               "ResearchPapers/Co-author/Conferences",
               "ResearchPapers/Co-author/Journals",
               "ResearchPapers/Rice",
               "Proposals/Successful/NSF_SBIR",
               "Proposals/Successful/Rice_Business_Plan_Competition",
               "Proposals/NotSuccessful",
               "Proposals/Pending"]
    
    for subdir in subdirs:
        full_path = os.path.join(input_docs_dir, subdir)
        if os.path.exists(full_path):
            for file in os.listdir(full_path):
                if file.endswith('.pdf'):
                    pdf_files.append(os.path.join(full_path, file))
    
    print(f"\nFound {len(pdf_files)} PDF files to process")
    
    # Copy files to uploads directory if not already there
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Copy JSON file
    json_dest = os.path.join(uploads_dir, "alfredo_costilla_reyes.json")
    if not os.path.exists(json_dest):
        shutil.copy2(json_file, json_dest)
        print(f"Copied JSON profile to uploads")
    
    # Copy PDFs with sanitized names
    uploaded_pdfs = []
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        # Sanitize filename (remove special chars except underscore)
        safe_filename = filename.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
        dest_path = os.path.join(uploads_dir, safe_filename)
        
        if not os.path.exists(dest_path):
            shutil.copy2(pdf_path, dest_path)
            print(f"Copied: {filename} -> {safe_filename}")
        
        uploaded_pdfs.append(dest_path)
    
    print(f"\nTotal PDFs in uploads: {len(uploaded_pdfs)}")
    
    # Create user profile with all documents
    print("\n=== Creating comprehensive user profile ===")
    profile = user_manager.create_user_profile(json_dest, uploaded_pdfs)
    
    print(f"\nProfile created for: {profile['name']}")
    print(f"Research interests: {', '.join(profile['research_interests'][:5])}...")
    print(f"Extracted PDFs: {len(profile['extracted_pdfs'])}")
    print(f"Combined text length: {len(profile['combined_text'])} characters")
    
    # Store profile with embeddings
    print("\n=== Generating and storing embeddings ===")
    success = user_manager.store_user_profile(profile)
    
    if success:
        print("✓ Profile stored successfully with embeddings")
        
        # Verify in database
        stats = vector_db.get_collection_stats()
        print(f"\nDatabase stats: {stats}")
        
        # Test search
        print("\n=== Testing search functionality ===")
        test_matches = user_manager.match_user_to_opportunities(profile, n_results=5)
        
        if test_matches:
            print(f"\nFound {len(test_matches)} matching opportunities:")
            for i, match in enumerate(test_matches[:3]):
                print(f"\n{i+1}. {match['title']}")
                print(f"   Agency: {match['agency']}")
                print(f"   Confidence: {match['confidence_score']}%")
        else:
            print("\nNo matches found (this is OK if no opportunities are in database)")
    else:
        print("✗ Failed to store profile with embeddings")
        
    # Check if user exists in database
    user_id = profile['id']
    researchers = vector_db.get_all_researchers()
    user_found = any(r['id'] == user_id for r in researchers)
    
    if user_found:
        print(f"\n✓ User {profile['name']} (ID: {user_id}) confirmed in database")
    else:
        print(f"\n✗ User {profile['name']} (ID: {user_id}) NOT found in database")


if __name__ == "__main__":
    main()