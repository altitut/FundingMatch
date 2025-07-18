#!/usr/bin/env python3
"""
Main script for running the enhanced embeddings-based matching system
"""

import os
import sys
import argparse
import json
from datetime import datetime
from backend.embeddings_matcher import EmbeddingsEnhancedMatcher


def main():
    """Main execution function"""
    
    parser = argparse.ArgumentParser(description='Run enhanced embeddings-based funding matching')
    parser.add_argument('--profile', type=str, help='Path to researcher profile JSON')
    parser.add_argument('--opportunities', type=str, help='Path to funding opportunities JSON')
    parser.add_argument('--top-k', type=int, default=20, help='Number of top matches to return')
    parser.add_argument('--min-score', type=float, default=0.7, help='Minimum similarity score')
    parser.add_argument('--skip-migration', action='store_true', help='Skip data migration')
    
    args = parser.parse_args()
    
    print("=== FundingMatch Enhanced Embeddings System ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Initialize matcher
    print("Initializing enhanced matcher...")
    matcher = EmbeddingsEnhancedMatcher()
    
    # Check if migration is needed
    stats = matcher.vector_db.get_collection_stats()
    if stats['researchers'] == 0 and not args.skip_migration:
        print("\nNo data in vector database. Running migration...")
        from migrate_to_embeddings import migrate_existing_data
        profile_id, _ = migrate_existing_data()
    else:
        profile_id = None
    
    # Process new profile if provided
    if args.profile:
        print(f"\nProcessing profile: {args.profile}")
        profile_id = matcher.process_researcher_profile(args.profile)
    
    # Process new opportunities if provided
    if args.opportunities:
        print(f"\nProcessing opportunities: {args.opportunities}")
        matcher.process_funding_opportunities(args.opportunities)
    
    # Get profile ID if not set
    if not profile_id:
        # Try to get from database
        stats = matcher.vector_db.get_collection_stats()
        if stats['researchers'] > 0:
            print("\nUsing existing researcher profile from database")
            # For now, we'll need to implement a method to list profiles
            # Using a placeholder approach
            profile_id = input("Enter profile ID (or press Enter to skip matching): ").strip()
            if not profile_id:
                print("No profile selected. Exiting.")
                return
    
    # Run matching
    print(f"\n=== Running Enhanced Matching ===")
    print(f"Profile ID: {profile_id}")
    print(f"Top K: {args.top_k}")
    print(f"Minimum Score: {args.min_score}")
    
    try:
        matches = matcher.match_researcher_to_opportunities(
            profile_id,
            top_k=args.top_k,
            min_score=args.min_score
        )
        
        print(f"\nFound {len(matches)} high-quality matches!")
        
        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = "opportunity_matches"
        os.makedirs(report_dir, exist_ok=True)
        
        report_path = os.path.join(report_dir, f"EMBEDDINGS_Enhanced_Report_{timestamp}.md")
        matcher.generate_match_report(profile_id, matches, report_path)
        
        # Save matched opportunities JSON
        matches_json_path = os.path.join(report_dir, f"EMBEDDINGS_matches_{timestamp}.json")
        with open(matches_json_path, 'w') as f:
            json.dump(matches, f, indent=2)
        
        print(f"\nResults saved:")
        print(f"- Report: {report_path}")
        print(f"- JSON: {matches_json_path}")
        
        # Display top 5 matches
        print("\n=== Top 5 Matches ===")
        for i, match in enumerate(matches[:5], 1):
            print(f"\n{i}. {match.get('title', 'Unknown')}")
            print(f"   Agency: {match.get('agency', 'Unknown')}")
            print(f"   Score: {match['similarity_score']*100:.1f}%")
            print(f"   Deadline: {match.get('close_date', 'N/A')}")
            
            if match['retrofitting_potential']['has_retrofit_candidate']:
                print(f"   ✓ Can retrofit: {match['retrofitting_potential']['best_candidate']}")
                
    except Exception as e:
        print(f"\nError during matching: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n=== Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")


if __name__ == "__main__":
    main()