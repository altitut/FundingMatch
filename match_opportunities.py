#!/usr/bin/env python3
"""
Match user profile with funding opportunities
"""

import os
import sys
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from user_profile_manager import UserProfileManager
from vector_database import VectorDatabaseManager


def main():
    """Match user with funding opportunities"""
    
    print("=== Matching User with Funding Opportunities ===\n")
    
    # Check if user profile exists
    profile_file = "output_results/user_profile.json"
    if not os.path.exists(profile_file):
        print("❌ No user profile found. Please run create_user_profile.py first")
        return
    
    # Load profile summary
    with open(profile_file, 'r') as f:
        profile_summary = json.load(f)
    
    print(f"Matching opportunities for: {profile_summary['name']}")
    
    # Initialize components
    manager = UserProfileManager()
    vector_db = VectorDatabaseManager()
    
    # Check database
    stats = vector_db.get_collection_stats()
    print(f"Database contains {stats.get('opportunities', 0)} funding opportunities")
    
    if stats.get('opportunities', 0) == 0:
        print("❌ No opportunities in database. Please run process_csv_to_embeddings.py first")
        return
    
    # Recreate full profile for matching
    print("\nLoading user profile for matching...")
    
    # Find user JSON
    json_files = [f for f in os.listdir("input_documents") if f.endswith('.json')]
    if not json_files:
        print("❌ User JSON file not found")
        return
    
    user_json_path = os.path.join("input_documents", json_files[0])
    
    # Find PDFs
    pdf_paths = []
    for root, dirs, files in os.walk("input_documents"):
        for file in files:
            if file.endswith('.pdf'):
                pdf_paths.append(os.path.join(root, file))
    
    # Create profile
    profile = manager.create_user_profile(user_json_path, pdf_paths)
    
    # Match with opportunities
    print("\nSearching for matches...")
    matches = manager.match_user_to_opportunities(profile, n_results=20)
    
    if matches:
        print(f"\n✓ Found {len(matches)} matching opportunities")
        
        # Display top matches
        print("\nTop 10 Matches:")
        print("-" * 80)
        
        for i, opp in enumerate(matches[:10], 1):
            print(f"\n{i}. {opp['title']}")
            print(f"   Confidence: {opp['confidence_score']}%")
            print(f"   Agency: {opp['agency']}")
            print(f"   Deadline: {opp['deadline']}")
            if opp['url']:
                print(f"   URL: {opp['url']}")
        
        # Save results
        results = {
            'user': {
                'name': profile['name'],
                'research_interests': profile['research_interests'][:10]
            },
            'matches': matches,
            'summary': {
                'total_matches': len(matches),
                'high_confidence': len([m for m in matches if m['confidence_score'] >= 70]),
                'medium_confidence': len([m for m in matches if 40 <= m['confidence_score'] < 70]),
                'low_confidence': len([m for m in matches if m['confidence_score'] < 40])
            },
            'generated_at': datetime.now().isoformat()
        }
        
        output_file = "output_results/user_funding_matches.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results saved to {output_file}")
        
        # Summary
        print("\nMatching Summary:")
        print(f"  High confidence (≥70%): {results['summary']['high_confidence']}")
        print(f"  Medium confidence (40-69%): {results['summary']['medium_confidence']}")
        print(f"  Low confidence (<40%): {results['summary']['low_confidence']}")
        
    else:
        print("❌ No matches found")


if __name__ == "__main__":
    main()