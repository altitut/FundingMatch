#!/usr/bin/env python3
"""
Comprehensive test for user profile creation and funding opportunity matching
"""

import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.user_profile_manager import UserProfileManager


def main():
    """Test user profile creation and matching"""
    
    print("=== User Profile and Funding Opportunity Matching Test ===\n")
    
    # Initialize manager
    manager = UserProfileManager()
    
    # 1. Define user documents
    user_json_path = "input_documents/alfredo_costilla_reyes.json"
    pdf_paths = [
        "input_documents/CV PI Alfredo Costilla Reyes 04-2025.pdf",
        "input_documents/COSTILLAREYES-DISSERTATION-2020.pdf"
    ]
    
    # Add some successful proposal PDFs for better profile
    proposal_pdfs = [
        "input_documents/Proposals/Successful/NSF_SBIR/NSF21_SBIR_AutoML_OnDeviceAI.pdf",
        "input_documents/ResearchPapers/First author journals/A Time-Interleave-Based Power Management System with Maximum Power Extraction and Health Protection Algorithm for Multip.pdf"
    ]
    
    # Filter existing PDFs
    existing_pdfs = [pdf for pdf in pdf_paths + proposal_pdfs if os.path.exists(pdf)]
    
    print(f"1. Creating user profile from {len(existing_pdfs)} PDF documents and JSON data...")
    print(f"   PDFs found: {len(existing_pdfs)}")
    for pdf in existing_pdfs:
        print(f"   - {os.path.basename(pdf)}")
    
    # 2. Create user profile
    try:
        profile = manager.create_user_profile(user_json_path, existing_pdfs)
        
        print(f"\n2. User Profile Created:")
        print(f"   Name: {profile['name']}")
        print(f"   Research Interests: {len(profile['research_interests'])} areas")
        print(f"   First 3 interests: {profile['research_interests'][:3]}")
        print(f"   Education: {len(profile['education'])} entries")
        print(f"   Awards: {len(profile['awards'])} awards")
        print(f"   URLs processed: {len(profile['urls'])}")
        print(f"   Combined text length: {len(profile['combined_text'])} characters")
        
    except Exception as e:
        print(f"   ✗ Error creating profile: {e}")
        return
    
    # 3. Store user profile
    print("\n3. Storing user profile with embeddings...")
    try:
        success = manager.store_user_profile(profile)
        if success:
            print("   ✓ Profile stored successfully")
        else:
            print("   ✗ Failed to store profile")
            return
    except Exception as e:
        print(f"   ✗ Error storing profile: {e}")
        return
    
    # 4. Match with funding opportunities
    print("\n4. Matching user with funding opportunities...")
    try:
        matches = manager.match_user_to_opportunities(profile, n_results=15)
        
        if matches:
            print(f"   ✓ Found {len(matches)} matching opportunities\n")
            
            print("=== Top Ranked Funding Opportunities ===\n")
            
            for i, opp in enumerate(matches[:10], 1):
                print(f"{i}. {opp['title']}")
                print(f"   Confidence Score: {opp['confidence_score']}%")
                print(f"   Agency: {opp['agency']}")
                print(f"   Deadline: {opp['deadline']}")
                print(f"   Keywords: {', '.join(opp['keywords'][:3]) if opp['keywords'] else 'None'}")
                print(f"   Description: {opp['description']}")
                if opp['url']:
                    print(f"   URL: {opp['url']}")
                print()
            
            # 5. Summary statistics
            print("=== Matching Summary ===")
            print(f"Total opportunities matched: {len(matches)}")
            
            # Group by confidence levels
            high_conf = [m for m in matches if m['confidence_score'] >= 70]
            med_conf = [m for m in matches if 40 <= m['confidence_score'] < 70]
            low_conf = [m for m in matches if m['confidence_score'] < 40]
            
            print(f"High confidence (≥70%): {len(high_conf)} opportunities")
            print(f"Medium confidence (40-69%): {len(med_conf)} opportunities")
            print(f"Low confidence (<40%): {len(low_conf)} opportunities")
            
            # Save results
            results = {
                'user': {
                    'name': profile['name'],
                    'research_interests': profile['research_interests'][:10]
                },
                'matches': matches,
                'summary': {
                    'total_matches': len(matches),
                    'high_confidence': len(high_conf),
                    'medium_confidence': len(med_conf),
                    'low_confidence': len(low_conf)
                },
                'generated_at': datetime.now().isoformat()
            }
            
            output_file = 'user_funding_matches.json'
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n✓ Results saved to {output_file}")
            
        else:
            print("   ✗ No matches found")
            
    except Exception as e:
        print(f"   ✗ Error during matching: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✓ Test completed successfully!")


if __name__ == "__main__":
    main()