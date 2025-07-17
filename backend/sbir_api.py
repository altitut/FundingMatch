import requests
import json
from datetime import datetime, timedelta

class SbirAPI:
    def __init__(self):
        # Real SBIR API endpoints  
        self.solicitations_url = "https://api.www.sbir.gov/public/api/solicitations"
        self.awards_url = "https://api.www.sbir.gov/public/api/awards"
        self.base_search_url = "https://www.sbir.gov/api/topics"
        
    def search_open_solicitations(self, keywords=None, agency=None, limit=100):
        """
        Search for open SBIR/STTR solicitations using multiple API approaches
        """
        print(f"🔍 SBIR.gov Real API Request: {self.solicitations_url}")
        
        all_opportunities = []
        
        # Try Method 1: Solicitations API
        opportunities = self._try_solicitations_api(keywords, agency, limit)
        if opportunities:
            all_opportunities.extend(opportunities)
        
        # Try Method 2: Alternative parameters  
        opportunities = self._try_alternative_api(keywords, agency, limit)
        if opportunities:
            all_opportunities.extend(opportunities)
        
        # Method 3: Always get current opportunities (includes NSF SBIR)
        current_opportunities = self._get_current_real_opportunities(keywords, agency, limit)
        if current_opportunities:
            all_opportunities.extend(current_opportunities)
        
        if all_opportunities:
            # Remove duplicates based on opportunity ID
            seen_ids = set()
            unique_opportunities = []
            for opp in all_opportunities:
                opp_id = opp.get('id', '')
                if opp_id not in seen_ids:
                    seen_ids.add(opp_id)
                    unique_opportunities.append(opp)
            
            return unique_opportunities[:limit]
        
        print(f"   ❌ All SBIR API methods failed - no real opportunities available")
        return []
    
    def _try_solicitations_api(self, keywords, agency, limit):
        """Try the main solicitations API endpoint"""
        try:
            # Use simple parameters based on API documentation examples
            params = {
                'open': '1'  # Only open solicitations
                # Note: API doesn't support date filtering or pagination parameters
            }
            
            # Remove keyword requirement - search ALL open opportunities
            # if keywords:
            #     params['keyword'] = ' '.join(keywords)
            
            if agency:
                agency_mapping = {
                    'department of defense': 'DOD',
                    'department of health and human services': 'HHS',
                    'national aeronautics and space administration': 'NASA',
                    'national science foundation': 'NSF',
                    'department of energy': 'DOE'
                }
                agency_lower = agency.lower()
                agency_code = agency_mapping.get(agency_lower, agency.upper())
                params['agency'] = agency_code
            
            print(f"   📊 Parameters: {params}")
            
            response = requests.get(self.solicitations_url, params=params, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   📄 API Response sample: {str(data)[:200]}...")
                    opportunities = self._process_api_response(data, keywords)
                    if opportunities:
                        print(f"   ✅ Found {len(opportunities)} real SBIR opportunities from solicitations API")
                        return opportunities[:limit]
                    else:
                        print(f"   ⚠️ API returned data but no opportunities extracted from response")
                except json.JSONDecodeError as e:
                    print(f"   ⚠️ Could not parse JSON response: {e}")
                    print(f"   📄 Raw response: {response.text[:200]}...")
            
            print(f"   ⚠️ Solicitations API failed: {response.status_code}")
            return []
            
        except Exception as e:
            print(f"   ⚠️ Solicitations API exception: {e}")
            return []
    
    def _try_alternative_api(self, keywords, agency, limit):
        """Try alternative API endpoints and parameters"""
        try:
            # Try different parameter combinations based on API documentation
            alt_params_list = [
                {'open': '1'},
                {'format': 'json', 'open': '1'},
                {'format': 'json'},
                {'open': 'true'},
                {}
            ]
            
            for params in alt_params_list:
                # Remove keyword requirement - search ALL open opportunities
                # if keywords:
                #     params['q'] = ' '.join(keywords)
                
                response = requests.get(self.solicitations_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        opportunities = self._process_api_response(data, keywords)
                        if opportunities:
                            print(f"   ✅ Found {len(opportunities)} opportunities with alternative parameters")
                            return opportunities[:limit]
                    except json.JSONDecodeError:
                        continue
            
            return []
            
        except Exception as e:
            print(f"   ⚠️ Alternative API exception: {e}")
            return []
    
    def _get_current_real_opportunities(self, keywords, agency, limit):
        """
        DEPRECATED: This method previously contained hardcoded data.
        All opportunities must come from real APIs only.
        """
        print(f"   ⚠️ No hardcoded opportunities available - using real API data only")
        return []
    
    def _process_api_response(self, data, keywords):
        """Process API response data into opportunities"""
        try:
            # Handle different response formats
            if isinstance(data, list):
                solicitations = data
            elif isinstance(data, dict):
                solicitations = data.get('solicitations', data.get('data', data.get('results', [])))
            else:
                return []
            
            opportunities = []
            current_date = datetime.now()
            
            # Apply 6-month window filter (3 months before to 3 months after)
            date_from = current_date - timedelta(days=90)
            date_to = current_date + timedelta(days=90)
            
            for sol in solicitations:
                try:
                    title = sol.get('solicitation_title', sol.get('title', ''))
                    if not title or len(title) < 5:
                        continue
                    
                    agency_name = sol.get('agency', '')
                    program = sol.get('program', 'SBIR')
                    phase = sol.get('phase', 'I')
                    
                    # Parse deadline - try multiple field names based on API response
                    close_date = None
                    close_date_str = sol.get('close_date', sol.get('application_due_date', sol.get('solicitation_close_date', '')))
                    
                    if close_date_str:
                        try:
                            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                                try:
                                    date_str = str(close_date_str).split("T")[0].split(" ")[0]
                                    close_date = datetime.strptime(date_str, fmt)
                                    break
                                except ValueError:
                                    continue
                        except:
                            pass
                    
                    # Apply 6-month window filter: only include opportunities with deadlines in the range
                    if close_date:
                        if close_date < date_from or close_date > date_to:
                            continue
                    else:
                        # If no deadline found, include it anyway (some opportunities might not have parsed deadlines)
                        pass
                    
                    opportunity = {
                        "id": sol.get('solicitation_number', f"sbir-{len(opportunities)+1}"),
                        "title": title,
                        "agency": agency_name,
                        "program": f"{program} Phase {phase}",
                        "description": sol.get('description', f"{program} Phase {phase} opportunity from {agency_name}"),
                        "deadline": close_date.strftime("%Y-%m-%d") if close_date else "",
                        "award_amount": 275000 if phase == 'I' else 1750000,
                        "technical_focus": keywords or [],
                        "phase": phase,
                        "url": sol.get('solicitation_agency_url', f"https://www.sbir.gov/node/{sol.get('solicitation_number', '')}"),
                        "solicitation_year": sol.get('solicitation_year', ''),
                        "current_status": sol.get('current_status', 'Open')
                    }
                    
                    opportunities.append(opportunity)
                    
                except Exception as e:
                    continue
            
            return opportunities
            
        except Exception as e:
            return []
    
    def format_opportunity(self, opp_data):
        """
        Format SBIR opportunity data for consistent structure
        """
        return {
            "id": opp_data.get("id", ""),
            "title": opp_data.get("title", ""),
            "description": opp_data.get("description", ""),
            "agency": opp_data.get("agency", ""),
            "program": opp_data.get("program", "SBIR"),
            "deadline": opp_data.get("deadline", ""),
            "award_amount": opp_data.get("award_amount", 0),
            "technical_focus": opp_data.get("technical_focus", []),
            "phase": opp_data.get("phase", "Unknown"),
            "url": opp_data.get("url", "https://www.sbir.gov/topics"),
            "solicitation_year": opp_data.get("solicitation_year", ""),
            "release_date": opp_data.get("release_date", ""),
            "open_date": opp_data.get("open_date", ""),
            "current_status": opp_data.get("current_status", "Open")
        }

# Usage example
if __name__ == "__main__":
    sbir = SbirAPI()
    
    # Test real SBIR API
    print("Testing Real SBIR API...")
    open_solicitations = sbir.search_open_solicitations(keywords=None, limit=50)
    print(f"Found {len(open_solicitations)} real open solicitations")
    
    for i, sol in enumerate(open_solicitations[:5], 1):
        print(f"{i}. {sol['title'][:80]}... - {sol['agency']}")
        print(f"   Program: {sol['program']}")
        print(f"   URL: {sol['url']}")
        print(f"   Deadline: {sol['deadline']}")
        print(f"   Amount: ${sol['award_amount']:,}")
        print() 