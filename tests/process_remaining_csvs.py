#!/usr/bin/env python3
"""
Process any remaining CSV files in FundingOpportunities folder
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.funding_opportunities_manager import FundingOpportunitiesManager


def main():
    """Process remaining CSV files"""
    
    print("=== Processing Remaining CSV Files ===\n")
    
    # Initialize manager
    manager = FundingOpportunitiesManager()
    
    # Process all CSV files
    processed = manager.process_csv_files()
    
    print(f"\nProcessing complete!")
    print(f"Files processed: {processed}")
    
    # Show current state
    print("\nFiles in FundingOpportunities:")
    for item in os.listdir("FundingOpportunities"):
        if item.endswith('.csv'):
            print(f"  - {item}")
    
    print("\nFiles in FundingOpportunities/Ingested:")
    ingested_path = "FundingOpportunities/Ingested"
    if os.path.exists(ingested_path):
        for item in os.listdir(ingested_path):
            if item.endswith('.csv'):
                print(f"  - {item}")


if __name__ == "__main__":
    main()