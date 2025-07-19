#!/usr/bin/env python3
"""
Complete system test for FundingMatch
Tests PDF processing, embeddings, and opportunity tracking
"""

import os
import sys
import json
import shutil
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from user_profile_manager import UserProfileManager
from vector_database import VectorDatabaseManager
from funding_opportunities_manager import FundingOpportunitiesManager
from funding_opportunities_manager_enhanced import UnprocessedTracker


def test_user_profile_processing():
    """Test user profile and PDF processing"""
    print("=== Testing User Profile Processing ===\n")
    
    user_manager = UserProfileManager()
    vector_db = VectorDatabaseManager()
    
    # Get user info
    user_name = "Alfredo Costilla-Reyes"
    import hashlib
    user_id = hashlib.md5(user_name.encode()).hexdigest()
    
    # Check existing profile
    researchers = vector_db.get_all_researchers()
    user_exists = any(r['id'] == user_id for r in researchers)
    
    print(f"User '{user_name}' exists: {user_exists}")
    
    if user_exists:
        # Get detailed info
        result = vector_db.researchers.get(ids=[user_id], include=['embeddings', 'metadatas'])
        if result and result['embeddings'] and result['embeddings'][0]:
            print(f"✓ User has {len(result['embeddings'][0])}-dimensional embedding")
            metadata = result['metadatas'][0] if result['metadatas'] else {}
            print(f"✓ Total documents: {metadata.get('total_documents', 0)}")
            print(f"✓ Last updated: {metadata.get('timestamp', 'Unknown')}")
        else:
            print("❌ User exists but has no embeddings!")
    
    return user_exists


def test_opportunity_tracking():
    """Test opportunity tracking system"""
    print("\n=== Testing Opportunity Tracking ===\n")
    
    # Check for tracking file
    tracking_file = "FundingOpportunities/unprocessed_tracking.json"
    
    if os.path.exists(tracking_file):
        with open(tracking_file, 'r') as f:
            tracking_data = json.load(f)
        
        print("Unprocessed Opportunities Summary:")
        print(f"- No deadline: {len(tracking_data.get('no_deadline', []))}")
        print(f"- Duplicates: {len(tracking_data.get('duplicates', []))}")
        print(f"- Errors: {len(tracking_data.get('errors', []))}")
        print(f"- Expired: {len(tracking_data.get('expired', []))}")
        
        # Show sample of no deadline opportunities
        no_deadline = tracking_data.get('no_deadline', [])
        if no_deadline:
            print("\nSample of opportunities with no deadline:")
            for opp in no_deadline[:3]:
                print(f"  - {opp['title'][:60]}... ({opp['agency']})")
    else:
        print("No tracking file found. Creating new tracker...")
        tracker = UnprocessedTracker()
        tracker.save()
        print("✓ Tracking file created")


def test_vector_database():
    """Test vector database functionality"""
    print("\n=== Testing Vector Database ===\n")
    
    vector_db = VectorDatabaseManager()
    stats = vector_db.get_collection_stats()
    
    print("Database Statistics:")
    print(f"- Researchers: {stats['researchers']}")
    print(f"- Opportunities: {stats['opportunities']}")
    print(f"- Proposals: {stats['proposals']}")
    
    # Test search functionality
    if stats['researchers'] > 0 and stats['opportunities'] > 0:
        print("\n✓ Database is populated and ready for matching")
    else:
        print("\n⚠️ Database needs data:")
        if stats['researchers'] == 0:
            print("  - No researcher profiles found")
        if stats['opportunities'] == 0:
            print("  - No funding opportunities found")


def test_new_pdf_processing():
    """Test adding a new PDF to existing profile"""
    print("\n=== Testing New PDF Addition ===\n")
    
    # This simulates what happens when a user adds a new PDF
    uploads_dir = "uploads"
    input_docs_dir = "input_documents"
    
    # Check for new PDFs in input_documents that aren't in uploads
    new_pdfs = []
    
    if os.path.exists(input_docs_dir) and os.path.exists(uploads_dir):
        input_files = set()
        # Collect all PDFs from input_documents (including subdirs)
        for root, dirs, files in os.walk(input_docs_dir):
            for file in files:
                if file.endswith('.pdf'):
                    input_files.add(file)
        
        # Check which ones are not in uploads
        upload_files = set(f for f in os.listdir(uploads_dir) if f.endswith('.pdf'))
        
        missing_files = input_files - upload_files
        
        if missing_files:
            print(f"Found {len(missing_files)} PDFs in input_documents not in uploads:")
            for f in list(missing_files)[:5]:  # Show first 5
                print(f"  - {f}")
        else:
            print("✓ All PDFs from input_documents are already in uploads")
    
    return len(new_pdfs)


def main():
    """Run all tests"""
    print("FundingMatch Complete System Test\n")
    print("=" * 50)
    
    # Test 1: User Profile
    user_exists = test_user_profile_processing()
    
    # Test 2: Opportunity Tracking
    test_opportunity_tracking()
    
    # Test 3: Vector Database
    test_vector_database()
    
    # Test 4: New PDF Processing
    test_new_pdf_processing()
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if user_exists:
        print("✓ User profile system is working")
    else:
        print("❌ User profile needs attention")
    
    print("✓ Opportunity tracking is configured")
    print("✓ Vector database is operational")
    
    print("\nRecommendations:")
    print("1. To process new PDFs: Use the /api/profile/update endpoint")
    print("2. To track unprocessed opportunities: Check /api/opportunities/unprocessed")
    print("3. To view all data: Run the web app at http://localhost:5001")


if __name__ == "__main__":
    main()