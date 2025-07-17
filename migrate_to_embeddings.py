"""
Migration script to convert existing data to embeddings-based system
"""

import os
import json
import glob
from datetime import datetime
from backend.embeddings_matcher import EmbeddingsEnhancedMatcher


def migrate_existing_data():
    """Migrate existing profiles and opportunities to vector database"""
    
    print("=== Starting Migration to Embeddings System ===")
    
    # Initialize matcher
    matcher = EmbeddingsEnhancedMatcher()
    
    # 1. Process existing researcher profiles
    print("\n1. Processing Researcher Profiles...")
    profile_files = glob.glob("semantic_profiles*/alfredo_*.json")
    
    if profile_files:
        # Get the most recent profile
        latest_profile = max(profile_files, key=os.path.getctime)
        print(f"Found profile: {latest_profile}")
        
        profile_id = matcher.process_researcher_profile(latest_profile)
        print(f"Profile processed with ID: {profile_id}")
    else:
        print("No researcher profiles found")
        profile_id = None
    
    # 2. Process funding opportunities
    print("\n2. Processing Funding Opportunities...")
    
    # Process complete funding semantic data
    if os.path.exists("FundingOpportunities/COMPLETE_funding_semantic.json"):
        print("Processing COMPLETE_funding_semantic.json...")
        matcher.process_funding_opportunities(
            "FundingOpportunities/COMPLETE_funding_semantic.json",
            batch_size=50
        )
    
    # Process NSF semantic data
    if os.path.exists("FundingOpportunitiesManual/nsf_funding_semantic.json"):
        print("\nProcessing NSF funding semantic data...")
        matcher.process_funding_opportunities(
            "FundingOpportunitiesManual/nsf_funding_semantic.json",
            batch_size=50
        )
    
    # 3. Process historical proposals (for retrofitting)
    print("\n3. Processing Historical Proposals...")
    proposal_count = process_historical_proposals(matcher)
    
    # 4. Print migration summary
    print("\n=== Migration Summary ===")
    stats = matcher.vector_db.get_collection_stats()
    print(f"Researchers in DB: {stats['researchers']}")
    print(f"Opportunities in DB: {stats['opportunities']}")
    print(f"Proposals in DB: {stats['proposals']}")
    
    return profile_id, matcher


def process_historical_proposals(matcher):
    """Process historical proposals from researcher profile"""
    
    # Load the latest profile to extract proposal information
    profile_files = glob.glob("semantic_profiles*/alfredo_*.json")
    if not profile_files:
        return 0
        
    latest_profile = max(profile_files, key=os.path.getctime)
    with open(latest_profile, 'r') as f:
        profile = json.load(f)
    
    proposal_count = 0
    
    # Extract proposals from document analysis
    if 'document_analyses' in profile:
        for doc in profile['document_analyses']:
            if doc.get('document_type') == 'Proposal':
                # Determine if successful based on path
                success = 'Successful' in doc.get('file_path', '')
                
                # Create proposal object
                proposal = {
                    "title": doc.get('title', 'Unknown Proposal'),
                    "abstract": doc.get('abstract', ''),
                    "program": doc.get('funding_agency', ''),
                    "agency": doc.get('funding_agency', ''),
                    "success": success,
                    "keywords": doc.get('technical_keywords', []),
                    "file_path": doc.get('file_path', '')
                }
                
                # Generate embedding
                proposal_text = f"{proposal['title']} {proposal['abstract']} {' '.join(proposal['keywords'])}"
                embedding = matcher.embeddings_manager.generate_embedding(proposal_text)
                
                # Add to database
                proposal_id = f"proposal_{proposal_count}_{int(datetime.now().timestamp())}"
                matcher.vector_db.add_proposal(proposal_id, proposal, embedding)
                
                proposal_count += 1
                
    print(f"Processed {proposal_count} historical proposals")
    return proposal_count


def test_matching(profile_id, matcher):
    """Test the matching system with migrated data"""
    
    if not profile_id:
        print("\nNo profile to test matching")
        return
        
    print("\n=== Testing Enhanced Matching ===")
    
    # Run matching
    matches = matcher.match_researcher_to_opportunities(
        profile_id,
        top_k=10,
        min_score=0.7
    )
    
    print(f"\nFound {len(matches)} high-quality matches")
    
    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"opportunity_matches/EMBEDDINGS_Enhanced_Report_{timestamp}.md"
    
    # Create directory if needed
    os.makedirs("opportunity_matches", exist_ok=True)
    
    matcher.generate_match_report(profile_id, matches, report_path)
    
    # Print top 3 matches
    print("\nTop 3 Matches:")
    for i, match in enumerate(matches[:3], 1):
        print(f"\n{i}. {match.get('title', 'Unknown')}")
        print(f"   Score: {match['similarity_score']*100:.1f}%")
        print(f"   Agency: {match.get('agency', 'Unknown')}")
        if match['retrofitting_potential']['has_retrofit_candidate']:
            print(f"   Retrofit: {match['retrofitting_potential']['best_candidate']}")


if __name__ == "__main__":
    # Run migration
    profile_id, matcher = migrate_existing_data()
    
    # Test the system
    if profile_id:
        test_matching(profile_id, matcher)
    
    print("\n=== Migration Complete ===")