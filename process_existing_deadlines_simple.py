#!/usr/bin/env python3
"""
Process existing funding opportunities to remove those without deadlines
Simple version without Gemini API calls
"""

import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from vector_database import VectorDatabaseManager

def process_existing_opportunities():
    """Remove all opportunities without explicit deadlines"""
    print("Starting deadline processing for existing opportunities...")
    
    # Initialize managers
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
        
        opportunities_to_remove = []
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
                if not deadline or deadline == 'Not specified' or deadline == '':
                    opportunities_to_remove.append({
                        'id': opp_id,
                        'title': opportunity.get('title', 'Unknown'),
                        'agency': opportunity.get('agency', 'Unknown')
                    })
                else:
                    opportunities_with_deadline.append({
                        'id': opp_id,
                        'deadline': deadline
                    })
                    
            except Exception as e:
                print(f"Error processing opportunity {opp_id}: {e}")
        
        print(f"\nOpportunities with deadlines: {len(opportunities_with_deadline)}")
        print(f"Opportunities to remove (no deadlines): {len(opportunities_to_remove)}")
        
        if opportunities_to_remove:
            print(f"\nRemoving {len(opportunities_to_remove)} opportunities without deadlines...")
            
            # Remove in batches of 50
            batch_size = 50
            removed = 0
            
            for i in range(0, len(opportunities_to_remove), batch_size):
                batch = opportunities_to_remove[i:i+batch_size]
                batch_ids = [opp['id'] for opp in batch]
                
                try:
                    vector_db.opportunities.delete(ids=batch_ids)
                    removed += len(batch_ids)
                    print(f"  Removed batch of {len(batch_ids)} opportunities ({removed}/{len(opportunities_to_remove)})")
                    
                    # Log some examples
                    for opp in batch[:3]:
                        print(f"    - {opp['title'][:60]}...")
                        
                except Exception as e:
                    print(f"  Error removing batch: {e}")
            
            print(f"\nRemoval complete: {removed} opportunities removed")
            
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