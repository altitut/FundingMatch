#!/usr/bin/env python3
"""
Process CSV funding opportunities and generate embeddings
"""

import os
import csv
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any
from tqdm import tqdm
from backend.embeddings_matcher import EmbeddingsEnhancedMatcher


def process_nsf_csv(csv_path: str) -> List[Dict[str, Any]]:
    """
    Process NSF funding CSV file
    
    Args:
        csv_path: Path to NSF CSV file
        
    Returns:
        List of opportunity dictionaries
    """
    opportunities = []
    
    # Read CSV with standard csv module
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader):
            opportunity = {
                "id": f"nsf_{idx}_{datetime.now().strftime('%Y%m%d')}",
                "title": row.get("Title", ""),
                "description": row.get("Synopsis", ""),
                "agency": "NSF",
                "program_id": row.get("Program ID", ""),
                "award_type": row.get("Award Type", ""),
                "close_date": row.get("Next due date (Y-m-d)", ""),
                "posted_date": row.get("Posted date (Y-m-d)", ""),
                "url": row.get("URL", ""),
                "solicitation_url": row.get("Solicitation URL", ""),
                "status": row.get("Status", ""),
                "accepts_anytime": row.get("Proposals accepted anytime", "False") == "True",
                "keywords": [],  # Will be extracted from description
                "topics": []  # Will be extracted from description
            }
            
            # Clean and validate data
            opportunity = {k: v if v else "" for k, v in opportunity.items()}
            opportunities.append(opportunity)
        
    return opportunities


def process_sbir_csv(csv_path: str) -> List[Dict[str, Any]]:
    """
    Process SBIR topics CSV file
    
    Args:
        csv_path: Path to SBIR CSV file
        
    Returns:
        List of opportunity dictionaries
    """
    opportunities = []
    
    # Read CSV with standard csv module
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader):
            opportunity = {
                "id": f"sbir_{row.get('Topic Number', idx)}_{datetime.now().strftime('%Y%m%d')}",
                "title": row.get("Topic Title", ""),
                "description": row.get("Topic Description", ""),
                "agency": row.get("Agency", ""),
                "branch": row.get("Branch", ""),
                "program": row.get("Program", "SBIR"),
                "phase": row.get("Phase", ""),
                "topic_number": row.get("Topic Number", ""),
                "close_date": row.get("Close Date", ""),
                "release_date": row.get("Release Date", ""),
                "open_date": row.get("Open Date", ""),
                "url": row.get("Solicitation Agency URL", ""),
                "sbir_topic_link": row.get("SBIRTopicLink", ""),
                "status": row.get("Solicitation Status", ""),
                "year": row.get("Solicitation Year", ""),
                "keywords": [],  # Will be extracted from description
                "topics": []  # Will be extracted from description
            }
            
            # Clean and validate data
            opportunity = {k: v if v else "" for k, v in opportunity.items()}
            opportunities.append(opportunity)
        
    return opportunities


def extract_keywords_from_text(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text (simple implementation)
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords
        
    Returns:
        List of keywords
    """
    # Simple keyword extraction - in production, use NLP library
    import re
    
    # Common stopwords to exclude
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    
    # Count frequencies
    word_freq = {}
    for word in words:
        if word not in stopwords:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, freq in sorted_words[:max_keywords]]
    
    return keywords


def main():
    """Main execution function"""
    
    parser = argparse.ArgumentParser(description='Process CSV files to embeddings')
    parser.add_argument('--nsf-csv', type=str, help='Path to NSF CSV file')
    parser.add_argument('--sbir-csv', type=str, help='Path to SBIR CSV file')
    parser.add_argument('--output-dir', type=str, default='./csv_embeddings_output', 
                       help='Output directory for processed data')
    parser.add_argument('--batch-size', type=int, default=20, 
                       help='Batch size for embedding generation')
    
    args = parser.parse_args()
    
    if not args.nsf_csv and not args.sbir_csv:
        print("Error: Please provide at least one CSV file (--nsf-csv or --sbir-csv)")
        return
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize matcher
    print("Initializing embeddings matcher...")
    matcher = EmbeddingsEnhancedMatcher()
    
    all_opportunities = []
    
    # Process NSF CSV
    if args.nsf_csv:
        print(f"\nProcessing NSF CSV: {args.nsf_csv}")
        nsf_opportunities = process_nsf_csv(args.nsf_csv)
        print(f"Found {len(nsf_opportunities)} NSF opportunities")
        
        # Extract keywords for each opportunity
        for opp in nsf_opportunities:
            text = f"{opp['title']} {opp['description']}"
            opp['keywords'] = extract_keywords_from_text(text)
            
        all_opportunities.extend(nsf_opportunities)
    
    # Process SBIR CSV
    if args.sbir_csv:
        print(f"\nProcessing SBIR CSV: {args.sbir_csv}")
        sbir_opportunities = process_sbir_csv(args.sbir_csv)
        print(f"Found {len(sbir_opportunities)} SBIR opportunities")
        
        # Extract keywords for each opportunity
        for opp in sbir_opportunities:
            text = f"{opp['title']} {opp['description']}"
            opp['keywords'] = extract_keywords_from_text(text)
            
        all_opportunities.extend(sbir_opportunities)
    
    # Save opportunities to JSON
    opportunities_json_path = os.path.join(args.output_dir, 'csv_opportunities.json')
    with open(opportunities_json_path, 'w') as f:
        json.dump(all_opportunities, f, indent=2)
    print(f"\nSaved {len(all_opportunities)} opportunities to {opportunities_json_path}")
    
    # Generate embeddings and add to vector database
    print(f"\nGenerating embeddings for {len(all_opportunities)} opportunities...")
    print(f"Batch size: {args.batch_size}")
    
    # Process in batches
    for i in tqdm(range(0, len(all_opportunities), args.batch_size)):
        batch = all_opportunities[i:i + args.batch_size]
        batch_data = []
        
        for opp in batch:
            try:
                # Generate embedding
                opp_with_embedding = matcher.embeddings_manager.embed_funding_opportunity(opp)
                
                # Create opportunity ID if not present
                if 'id' not in opp:
                    opp['id'] = f"opp_{int(datetime.now().timestamp() * 1000)}"
                
                batch_data.append((opp['id'], opp, opp_with_embedding['embedding']))
                
            except Exception as e:
                print(f"Error processing opportunity '{opp.get('title', 'Unknown')}': {e}")
                continue
        
        # Batch add to database
        if batch_data:
            matcher.vector_db.batch_add_opportunities(batch_data)
    
    # Print final statistics
    stats = matcher.vector_db.get_collection_stats()
    print(f"\n=== Processing Complete ===")
    print(f"Opportunities in vector DB: {stats['opportunities']}")
    print(f"Output saved to: {args.output_dir}")
    
    # Save a summary report
    summary_path = os.path.join(args.output_dir, 'processing_summary.json')
    summary = {
        "timestamp": datetime.now().isoformat(),
        "nsf_csv": args.nsf_csv,
        "sbir_csv": args.sbir_csv,
        "total_opportunities": len(all_opportunities),
        "nsf_opportunities": len([o for o in all_opportunities if o['agency'] == 'NSF']),
        "sbir_opportunities": len([o for o in all_opportunities if 'sbir' in o['id']]),
        "vector_db_stats": stats
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary saved to: {summary_path}")


if __name__ == "__main__":
    main()