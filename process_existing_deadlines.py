#!/usr/bin/env python3
"""
Process existing funding opportunities to extract and update deadlines
"""

import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from funding_opportunities_manager import FundingOpportunitiesManager
from vector_database import VectorDatabaseManager

def process_existing_opportunities():
    """Process all existing opportunities to ensure they have deadlines"""
    print("Starting deadline processing for existing opportunities...")
    
    # Initialize managers
    funding_manager = FundingOpportunitiesManager()
    vector_db = VectorDatabaseManager()
    
    # Get all opportunities from vector database
    try:
        # Query all opportunities
        collection_info = vector_db.opportunities.peek(limit=10000)
        total_opportunities = len(collection_info['ids'])
        print(f"\nFound {total_opportunities} opportunities in vector database")
        
        # Get all opportunities with their metadata
        all_opportunities = vector_db.opportunities.get(
            ids=collection_info['ids'],
            include=['metadatas', 'documents']
        )
        
        opportunities_without_deadline = []
        opportunities_with_deadline = []
        
        # Check each opportunity
        for i, (opp_id, metadata, doc) in enumerate(zip(
            all_opportunities['ids'], 
            all_opportunities['metadatas'], 
            all_opportunities['documents']
        )):
            try:
                # Parse the document JSON
                opportunity = json.loads(doc)
                
                # Check if it has a deadline
                deadline = metadata.get('deadline', '')
                if not deadline or deadline == 'Not specified':
                    opportunities_without_deadline.append({
                        'id': opp_id,
                        'title': opportunity.get('title', 'Unknown'),
                        'agency': opportunity.get('agency', 'Unknown'),
                        'opportunity': opportunity
                    })
                else:
                    opportunities_with_deadline.append({
                        'id': opp_id,
                        'deadline': deadline
                    })
                    
            except Exception as e:
                print(f"Error processing opportunity {opp_id}: {e}")
        
        print(f"\nOpportunities with deadlines: {len(opportunities_with_deadline)}")
        print(f"Opportunities without deadlines: {len(opportunities_without_deadline)}")
        
        if opportunities_without_deadline:
            print(f"\nProcessing {len(opportunities_without_deadline)} opportunities without deadlines...")
            
            processed = 0
            removed = 0
            api_calls = 0
            max_api_calls = 50  # Limit API calls to avoid rate limiting
            
            for i, opp_data in enumerate(opportunities_without_deadline):
                opportunity = opp_data['opportunity']
                
                # Skip API calls if we've hit the limit
                if api_calls >= max_api_calls:
                    print(f"\n  Reached API limit ({max_api_calls} calls). Removing remaining opportunities without deadlines...")
                    # Remove without API check
                    try:
                        vector_db.opportunities.delete(ids=[opp_data['id']])
                        removed += 1
                    except Exception as e:
                        print(f"    Error removing: {e}")
                    continue
                
                # Use funding manager to check if expired/extract deadline
                is_expired, exp_date = funding_manager._is_expired(opportunity)
                api_calls += 1
                
                if is_expired and exp_date is None:
                    # No deadline found - remove from database
                    print(f"  Removing '{opp_data['title'][:50]}...' - no deadline found")
                    try:
                        vector_db.opportunities.delete(ids=[opp_data['id']])
                        removed += 1
                    except Exception as e:
                        print(f"    Error removing: {e}")
                        
                elif exp_date:
                    # Deadline found - update metadata
                    new_deadline = opportunity.get('close_date', exp_date.strftime('%Y-%m-%d'))
                    print(f"  Updating '{opp_data['title'][:50]}...' - deadline: {new_deadline}")
                    
                    try:
                        # Update the metadata
                        vector_db.opportunities.update(
                            ids=[opp_data['id']],
                            metadatas=[{
                                **vector_db.opportunities.get(ids=[opp_data['id']])['metadatas'][0],
                                'deadline': new_deadline
                            }]
                        )
                        processed += 1
                    except Exception as e:
                        print(f"    Error updating: {e}")
                
                # Progress indicator
                if (processed + removed) % 10 == 0:
                    print(f"  Progress: {processed + removed}/{len(opportunities_without_deadline)}")
            
            print(f"\nProcessing complete:")
            print(f"  - Updated with deadlines: {processed}")
            print(f"  - Removed (no deadline): {removed}")
            
        else:
            print("\nAll opportunities already have deadlines!")
            
        # Final statistics
        remaining = vector_db.opportunities.count()
        print(f"\nFinal opportunity count: {remaining}")
        
    except Exception as e:
        print(f"Error processing opportunities: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = process_existing_opportunities()
    if success:
        print("\nDeadline processing completed successfully!")
    else:
        print("\nDeadline processing failed!")
        sys.exit(1)