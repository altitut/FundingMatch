#!/usr/bin/env python3
"""
Reset and Initialize the FundingMatch System
Clears all data and starts fresh with proper duplicate checking
"""

import os
import sys
import shutil
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from vector_database import VectorDatabaseManager
from user_profile_manager import UserProfileManager
from funding_opportunities_manager import FundingOpportunitiesManager


def clear_all_data():
    """Clear all existing data"""
    print("🧹 Clearing all data...")
    
    # 1. Clear ChromaDB
    chroma_dir = Path("./chroma_db")
    if chroma_dir.exists():
        try:
            shutil.rmtree(chroma_dir)
            print("✓ Cleared ChromaDB")
        except Exception as e:
            print(f"⚠️  Error clearing ChromaDB: {e}")
    
    # 2. Clear processed IDs file
    processed_file = Path("./FundingOpportunities/processed_opportunities.json")
    if processed_file.exists():
        processed_file.unlink()
        print("✓ Cleared processed opportunities tracking")
    
    # 3. Clear uploads (optional - comment out if you want to keep uploaded files)
    # uploads_dir = Path("./uploads")
    # if uploads_dir.exists():
    #     shutil.rmtree(uploads_dir)
    #     uploads_dir.mkdir()
    #     print("✓ Cleared uploads directory")
    
    print("✅ All data cleared\n")


def initialize_user_profile():
    """Initialize user profile from CV"""
    print("👤 Creating user profile...")
    
    user_manager = UserProfileManager()
    
    # Check if CV exists
    cv_path = "input_documents/CV PI Alfredo Costilla Reyes 04-2025.pdf"
    if not os.path.exists(cv_path):
        print(f"❌ CV not found at: {cv_path}")
        return False
    
    # Create basic user JSON
    user_json = {
        "person": {
            "name": "Alfredo Costilla Reyes",
            "summary": "Principal Investigator",
            "biographical_information": {
                "research_interests": [
                    "Machine Learning",
                    "Artificial Intelligence",
                    "Data Science"
                ],
                "education": [],
                "awards": []
            },
            "links": []
        }
    }
    
    # Save user JSON temporarily
    json_path = "uploads/temp_user_profile.json"
    os.makedirs("uploads", exist_ok=True)
    import json
    with open(json_path, 'w') as f:
        json.dump(user_json, f)
    
    # Create profile
    try:
        profile = user_manager.create_user_profile(json_path, [cv_path])
        success = user_manager.store_user_profile(profile)
        
        if success:
            print(f"✓ Created profile for: {profile['name']}")
            print(f"  ID: {profile['id']}")
            print(f"  Research Interests: {', '.join(profile['research_interests'][:3])}")
            return profile['id']
        else:
            print("❌ Failed to store user profile")
            return None
    except Exception as e:
        print(f"❌ Error creating profile: {e}")
        return None


def load_test_opportunities():
    """Load test opportunities with duplicate checking"""
    print("\n📄 Loading test opportunities...")
    
    funding_manager = FundingOpportunitiesManager()
    
    # Check if test CSV exists
    test_csv = "test_opportunities.csv"
    if not os.path.exists(test_csv):
        print(f"❌ Test CSV not found: {test_csv}")
        return False
    
    # Copy to FundingOpportunities directory
    dest_path = f"FundingOpportunities/{test_csv}"
    shutil.copy2(test_csv, dest_path)
    
    # Process the CSV
    try:
        def progress_callback(data):
            if data.get('current'):
                print(f"  Processing: {data['current']}/{data['total']} - {data.get('title', 'Unknown')[:50]}...")
        
        summary = funding_manager.process_single_csv_file(test_csv, progress_callback=progress_callback)
        
        print(f"\n✓ Processed opportunities:")
        print(f"  Total: {summary.get('total_rows', 0)}")
        print(f"  New: {summary.get('new_opportunities', 0)}")
        print(f"  Duplicates skipped: {summary.get('duplicate_skipped', 0)}")
        print(f"  Errors: {len(summary.get('errors', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading opportunities: {e}")
        return False


def verify_setup():
    """Verify the system is set up correctly"""
    print("\n🔍 Verifying setup...")
    
    vector_db = VectorDatabaseManager()
    stats = vector_db.get_collection_stats()
    
    print(f"✓ Database statistics:")
    print(f"  Researchers: {stats['researchers']}")
    print(f"  Opportunities: {stats['opportunities']}")
    print(f"  Proposals: {stats['proposals']}")
    
    if stats['researchers'] == 0:
        print("⚠️  No researchers found - user profile may not have been created")
    
    if stats['opportunities'] == 0:
        print("⚠️  No opportunities found - CSV may not have been processed")
    
    return stats['researchers'] > 0 and stats['opportunities'] > 0


def test_matching(user_id):
    """Test the matching functionality"""
    print("\n🔍 Testing matching functionality...")
    
    user_manager = UserProfileManager()
    vector_db = VectorDatabaseManager()
    
    try:
        # Get user profile embedding
        result = vector_db.researchers.get(ids=[user_id])
        if not result or not result.get('embeddings') or not result.get('embeddings')[0]:
            print("❌ User embedding not found in database")
            return False
        
        # Search for matches
        user_embedding = result['embeddings'][0]
        matches = vector_db.search_opportunities_for_profile(user_embedding, n_results=5)
        
        print(f"✓ Found {len(matches)} matches:")
        for i, match in enumerate(matches[:3]):
            print(f"\n  {i+1}. {match.get('title', 'Unknown')[:60]}...")
            print(f"     Agency: {match.get('agency', 'Unknown')}")
            print(f"     Similarity: {match.get('similarity_score', 0):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing matches: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution"""
    print("🚀 FundingMatch Reset and Initialize\n")
    
    # Step 1: Clear all data
    clear_all_data()
    
    # Step 2: Initialize user profile
    user_id = initialize_user_profile()
    if not user_id:
        print("\n❌ Failed to create user profile. Exiting.")
        return
    
    # Step 3: Load test opportunities
    if not load_test_opportunities():
        print("\n❌ Failed to load opportunities. Exiting.")
        return
    
    # Step 4: Verify setup
    if not verify_setup():
        print("\n⚠️  Setup verification failed")
    
    # Step 5: Test matching
    test_matching(user_id)
    
    print("\n✅ System reset and initialized successfully!")
    print(f"\n📌 User ID for testing: {user_id}")
    print("\nYou can now use the web interface to:")
    print("  1. View the user profile")
    print("  2. Browse loaded opportunities")
    print("  3. Run matching to find relevant opportunities")


if __name__ == "__main__":
    main()