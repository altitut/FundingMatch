"""
Enhanced Funding Opportunities Manager with Unprocessed Tracking
"""

from typing import Dict, Any, List
import json
import os
from datetime import datetime


class UnprocessedTracker:
    """Tracks unprocessed opportunities with reasons"""
    
    def __init__(self, tracking_dir: str = "FundingOpportunities"):
        self.tracking_dir = tracking_dir
        self.tracking_file = os.path.join(tracking_dir, "unprocessed_tracking.json")
        self.data = self._load_tracking_data()
    
    def _load_tracking_data(self) -> Dict[str, Any]:
        """Load existing tracking data"""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default structure
        return {
            "no_deadline": [],
            "duplicates": [],
            "errors": [],
            "expired": [],
            "last_updated": None,
            "statistics": {
                "total_no_deadline": 0,
                "total_duplicates": 0,
                "total_errors": 0,
                "total_expired": 0
            }
        }
    
    def add_no_deadline(self, opportunity: Dict[str, Any], source_file: str = ""):
        """Add opportunity that has no deadline"""
        entry = {
            "title": opportunity.get('title', 'Unknown')[:200],
            "agency": opportunity.get('agency', 'Unknown'),
            "url": opportunity.get('url', ''),
            "source_file": source_file,
            "date_encountered": datetime.now().isoformat(),
            "topic_number": opportunity.get('topic_number', opportunity.get('Topic Number', ''))
        }
        
        # Check if already tracked
        existing = [e for e in self.data['no_deadline'] 
                   if e['title'] == entry['title'] and e['agency'] == entry['agency']]
        
        if not existing:
            self.data['no_deadline'].append(entry)
            self.data['statistics']['total_no_deadline'] += 1
    
    def add_duplicate(self, opportunity: Dict[str, Any], existing_id: str, source_file: str = ""):
        """Add duplicate opportunity"""
        entry = {
            "title": opportunity.get('title', 'Unknown')[:200],
            "agency": opportunity.get('agency', 'Unknown'),
            "existing_id": existing_id,
            "source_file": source_file,
            "date_encountered": datetime.now().isoformat(),
            "topic_number": opportunity.get('topic_number', opportunity.get('Topic Number', ''))
        }
        
        # Keep only last 100 duplicates to avoid file bloat
        self.data['duplicates'].append(entry)
        if len(self.data['duplicates']) > 100:
            self.data['duplicates'] = self.data['duplicates'][-100:]
        
        self.data['statistics']['total_duplicates'] += 1
    
    def add_error(self, opportunity: Dict[str, Any], error_msg: str, source_file: str = ""):
        """Add opportunity that had processing error"""
        entry = {
            "title": opportunity.get('title', 'Unknown')[:200],
            "agency": opportunity.get('agency', 'Unknown'),
            "error": error_msg[:500],
            "source_file": source_file,
            "date_encountered": datetime.now().isoformat()
        }
        
        self.data['errors'].append(entry)
        self.data['statistics']['total_errors'] += 1
    
    def add_expired(self, opportunity: Dict[str, Any], expiration_date: str, source_file: str = ""):
        """Add expired opportunity"""
        entry = {
            "title": opportunity.get('title', 'Unknown')[:200],
            "agency": opportunity.get('agency', 'Unknown'),
            "expiration_date": expiration_date,
            "source_file": source_file,
            "date_encountered": datetime.now().isoformat()
        }
        
        # Keep only last 50 expired to avoid file bloat
        self.data['expired'].append(entry)
        if len(self.data['expired']) > 50:
            self.data['expired'] = self.data['expired'][-50:]
            
        self.data['statistics']['total_expired'] += 1
    
    def save(self):
        """Save tracking data to file"""
        self.data['last_updated'] = datetime.now().isoformat()
        
        try:
            os.makedirs(self.tracking_dir, exist_ok=True)
            with open(self.tracking_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save tracking data: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of unprocessed opportunities"""
        return {
            "no_deadline_count": len(self.data['no_deadline']),
            "recent_duplicates": len(self.data['duplicates']),
            "recent_errors": len(self.data['errors']),
            "recent_expired": len(self.data['expired']),
            "total_statistics": self.data['statistics'],
            "last_updated": self.data['last_updated']
        }


def enhance_funding_manager():
    """
    Monkey patch the existing FundingOpportunitiesManager to add tracking
    """
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
    
    from funding_opportunities_manager import FundingOpportunitiesManager
    
    # Store original method
    original_process = FundingOpportunitiesManager._process_opportunities
    
    def _process_opportunities_with_tracking(self, opportunities: List[Dict[str, Any]], 
                                           batch_size: int = 20, 
                                           progress_callback=None) -> Dict[str, Any]:
        """Enhanced version that tracks unprocessed items"""
        
        # Initialize tracker
        tracker = UnprocessedTracker()
        
        # Call original method
        summary = original_process(self, opportunities, batch_size, progress_callback)
        
        # Save unprocessed items from summary
        if 'unprocessed' in summary:
            source_file = getattr(self, '_current_csv_file', 'unknown')
            
            for item in summary['unprocessed']:
                reason = item.get('reason', '')
                
                if 'no deadline' in reason.lower():
                    tracker.add_no_deadline(item, source_file)
                elif 'duplicate' in reason.lower():
                    tracker.add_duplicate(item, item.get('existing_id', ''), source_file)
                elif 'expired' in reason.lower():
                    tracker.add_expired(item, item.get('expiration_date', ''), source_file)
                elif 'error' in reason.lower():
                    tracker.add_error(item, reason, source_file)
            
            # Save tracking data
            tracker.save()
            
            # Add tracking summary to return value
            summary['tracking_saved'] = True
            summary['tracking_summary'] = tracker.get_summary()
        
        return summary
    
    # Replace method
    FundingOpportunitiesManager._process_opportunities = _process_opportunities_with_tracking
    
    print("✓ Enhanced FundingOpportunitiesManager with unprocessed tracking")


if __name__ == "__main__":
    # Test the tracker
    tracker = UnprocessedTracker()
    
    # Add some test data
    test_opp = {
        "title": "Test Opportunity",
        "agency": "NSF",
        "url": "https://example.com"
    }
    
    tracker.add_no_deadline(test_opp, "test.csv")
    tracker.save()
    
    print("Tracking summary:", tracker.get_summary())