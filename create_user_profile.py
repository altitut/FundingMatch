#!/usr/bin/env python3
"""
Create user profile from JSON and PDF documents
"""

import os
import sys
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from user_profile_manager import UserProfileManager


def main():
    """Create user profile from documents"""
    
    print("=== Creating User Profile ===\n")
    
    # Initialize manager
    manager = UserProfileManager()
    
    # Find user JSON file
    input_dir = "input_documents"
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    
    if not json_files:
        print("❌ No JSON file found in input_documents/")
        print("   Please add a user profile JSON file")
        return
    
    # Use first JSON file found
    user_json_path = os.path.join(input_dir, json_files[0])
    print(f"Found user profile: {json_files[0]}")
    
    # Find PDF documents
    pdf_paths = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.pdf'):
                pdf_paths.append(os.path.join(root, file))
    
    print(f"Found {len(pdf_paths)} PDF documents")
    
    # Create profile
    try:
        profile = manager.create_user_profile(user_json_path, pdf_paths)
        
        print(f"\n✓ User Profile Created:")
        print(f"  Name: {profile['name']}")
        print(f"  Research Interests: {len(profile['research_interests'])} areas")
        print(f"  Documents processed: {len(profile['extracted_pdfs'])}")
        print(f"  Combined text length: {len(profile['combined_text'])} characters")
        
        # Store profile
        print("\nStoring profile with embeddings...")
        success = manager.store_user_profile(profile)
        
        if success:
            print("✓ Profile stored successfully in vector database")
            
            # Save profile to output
            output_file = os.path.join("output_results", "user_profile.json")
            os.makedirs("output_results", exist_ok=True)
            
            # Save a summary version
            profile_summary = {
                'name': profile['name'],
                'research_interests': profile['research_interests'],
                'education': profile['education'],
                'awards': profile['awards'],
                'documents_processed': list(profile['extracted_pdfs'].keys()),
                'urls_processed': len(profile['urls'])
            }
            
            with open(output_file, 'w') as f:
                json.dump(profile_summary, f, indent=2)
            
            print(f"✓ Profile summary saved to {output_file}")
        else:
            print("❌ Failed to store profile")
            
    except Exception as e:
        print(f"❌ Error creating profile: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()