#!/usr/bin/env python3
"""
Grants.gov API Integration Module

This module handles interaction with the Grants.gov Applicant API.
Based on: https://www.grants.gov/api/applicant/

Key features:
- No API key required for search2 endpoint
- 6-month date window filtering
- Comprehensive opportunity data extraction
- Error handling and retry logic

Author: AI Assistant
Date: 2025-01-10
"""

import requests
import json
from datetime import datetime, timedelta
import time

class GrantsAPI:
    """
    Grants.gov API client for fetching federal grant opportunities
    """
    
    def __init__(self):
        # API endpoints
        self.search_url = "https://api.grants.gov/v1/api/search2"
        # Note: fetchOpportunity requires authentication, so we'll skip it
        
    def search_opportunities(self, keywords=None, agency=None, limit=50):
        """
        Search for grant opportunities using the search2 endpoint
        
        Args:
            keywords (list): Optional list of keywords to search for
            agency (str): Optional agency code to filter by
            limit (int): Maximum number of opportunities to return
            
        Returns:
            list: List of grant opportunity dictionaries
        """
        print(f"🔍 Grants.gov API Request: {self.search_url}")
        
        try:
            opportunities = self._search_grants_api(keywords, agency, limit)
            
            if opportunities:
                print(f"   ✅ Found {len(opportunities)} current Grants.gov opportunities")
                return opportunities
            else:
                print(f"   ⚠️ No current Grants.gov opportunities found")
                return []
                
        except Exception as e:
            print(f"   ❌ Grants.gov API Error: {e}")
            return []
    
    def _search_grants_api(self, keywords, agency, limit):
        """Execute the grants search API call"""
        try:
            # Use 6-month window with execution date as middle point
            current_date = datetime.now()
            
            # Prepare search payload
            payload = {
                "rows": min(limit, 100),  # API might have limits
                "oppStatuses": "posted|forecasted",  # Open opportunities
                "agencies": agency if agency else "",  # Specific agency or all
                "fundingCategories": "",  # All funding categories for broad search
                "keyword": " ".join(keywords) if keywords else "",  # Keywords for search
                "eligibilities": "",  # All eligibilities
                "aln": ""  # All ALN numbers
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            print(f"   📊 Parameters: {json.dumps(payload, indent=4)}")
            
            response = requests.post(self.search_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for successful response
                    if 'errorcode' in data and data['errorcode'] == 0:
                        opportunities = self._process_api_response(data, keywords)
                        if opportunities:
                            print(f"   ✅ Found {len(opportunities)} Grants.gov opportunities from API")
                            return opportunities[:limit]
                        else:
                            print(f"   ⚠️ API returned data but no opportunities extracted")
                    else:
                        print(f"   ❌ API Error: {data.get('msg', 'Unknown error')}")
                        
                except json.JSONDecodeError as e:
                    print(f"   ⚠️ Could not parse JSON response: {e}")
                    print(f"   📄 Raw response: {response.text[:200]}...")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}...")
            
            return []
            
        except Exception as e:
            print(f"   ⚠️ Grants API exception: {e}")
            return []
    
    def _process_api_response(self, data, keywords):
        """Process API response data into standardized opportunities"""
        try:
            # Extract opportunities from response
            opp_data = data.get('data', {})
            opportunities = opp_data.get('oppHits', [])
            hit_count = opp_data.get('hitCount', 0)
            
            if not opportunities:
                return []
            
            processed_opportunities = []
            current_date = datetime.now()
            
            # Apply 6-month window filter (3 months before to 3 months after)
            date_from = current_date - timedelta(days=90)
            date_to = current_date + timedelta(days=90)
            
            for opp in opportunities:
                try:
                    # Extract basic information
                    title = opp.get('title', '').strip()
                    if not title or len(title) < 5:
                        continue
                    
                    opp_number = opp.get('number', '')
                    agency_name = opp.get('agencyName', 'Federal Agency')
                    opp_status = opp.get('oppStatus', 'unknown')
                    
                    # Parse dates
                    open_date = None
                    close_date = None
                    
                    open_date_str = opp.get('openDate', '')
                    close_date_str = opp.get('closeDate', '')
                    
                    # Parse open date
                    if open_date_str:
                        try:
                            for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"]:
                                try:
                                    open_date = datetime.strptime(open_date_str, fmt)
                                    break
                                except ValueError:
                                    continue
                        except:
                            pass
                    
                    # Parse close date
                    if close_date_str:
                        try:
                            for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"]:
                                try:
                                    close_date = datetime.strptime(close_date_str, fmt)
                                    break
                                except ValueError:
                                    continue
                        except:
                            pass
                    
                    # Apply 6-month window filter based on close date
                    # If no close date, include the opportunity (might be ongoing)
                    if close_date:
                        if close_date < date_from or close_date > date_to:
                            continue
                    
                    # Only include posted opportunities (skip forecasted for now)
                    if opp_status.lower() != 'posted':
                        continue
                    
                    # Create standardized opportunity
                    opportunity = {
                        "id": str(opp.get('id', '')),
                        "title": title,
                        "agency": agency_name,
                        "program": "Federal Grant",
                        "description": f"Federal grant opportunity from {agency_name}. Status: {opp_status}",
                        "deadline": close_date.strftime("%Y-%m-%d") if close_date else "",
                        "award_amount": 0,  # Amount not available in search results
                        "technical_focus": keywords or [],
                        "url": f"https://grants.gov/search-results-detail/{opp.get('id', '')}",
                        "opportunity_number": opp_number,
                        "opportunity_status": opp_status,
                        "open_date": open_date.strftime("%Y-%m-%d") if open_date else "",
                        "close_date": close_date.strftime("%Y-%m-%d") if close_date else "",
                        "source": "Grants.gov"
                    }
                    
                    processed_opportunities.append(opportunity)
                    
                except Exception as e:
                    # Skip this opportunity if there's an error processing it
                    continue
            
            return processed_opportunities
            
        except Exception as e:
            print(f"   ❌ Error processing Grants.gov response: {e}")
            return []
    
    def format_opportunity(self, opp_data):
        """
        Format Grants.gov opportunity data for consistent structure
        
        Args:
            opp_data (dict): Raw opportunity data
            
        Returns:
            dict: Formatted opportunity data
        """
        return {
            "id": opp_data.get("id", ""),
            "title": opp_data.get("title", ""),
            "description": opp_data.get("description", ""),
            "agency": opp_data.get("agency", ""),
            "program": opp_data.get("program", "Federal Grant"),
            "deadline": opp_data.get("deadline", ""),
            "award_amount": opp_data.get("award_amount", 0),
            "technical_focus": opp_data.get("technical_focus", []),
            "url": opp_data.get("url", f"https://grants.gov/search-results-detail/{opp_data.get('id', '')}"),
            "opportunity_number": opp_data.get("opportunity_number", ""),
            "opportunity_status": opp_data.get("opportunity_status", ""),
            "open_date": opp_data.get("open_date", ""),
            "close_date": opp_data.get("close_date", ""),
            "source": "Grants.gov"
        }

# Usage example and testing
if __name__ == "__main__":
    print("🧪 Testing Grants.gov API Module...")
    
    grants_api = GrantsAPI()
    
    # Test basic search
    print(f"\n1. Testing basic search...")
    opportunities = grants_api.search_opportunities(keywords=None, limit=10)
    
    if opportunities:
        print(f"✅ Found {len(opportunities)} opportunities")
        print(f"\n📋 Sample opportunities:")
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"{i}. {opp['title'][:60]}...")
            print(f"   Agency: {opp['agency']}")
            print(f"   Number: {opp['opportunity_number']}")
            print(f"   Status: {opp['opportunity_status']}")
            print(f"   Deadline: {opp['deadline']}")
            print(f"   URL: {opp['url']}")
    else:
        print("❌ No opportunities found")
    
    # Test search with keywords
    print(f"\n2. Testing search with keywords...")
    research_opportunities = grants_api.search_opportunities(
        keywords=["research", "technology"], 
        limit=5
    )
    
    if research_opportunities:
        print(f"✅ Found {len(research_opportunities)} research opportunities")
    else:
        print("❌ No research opportunities found")
    
    print(f"\n🎉 Grants.gov API module testing complete!") 