import requests
from datetime import datetime, timedelta
from config import Config

class SamGovAPI:
    def __init__(self):
        self.base_url = "https://api.sam.gov/opportunities/v2/search"
        self.api_key = Config.SAM_GOV_API_KEY
        
    def search_opportunities(self, keywords=None, limit=100, posted_from=None, posted_to=None):
        """
        Search opportunities from SAM.gov using v2 API
        """
        if not self.api_key:
            print("Warning: No SAM.gov API key provided, cannot fetch opportunities")
            return []
        
        # SAM.gov API requires PostedFrom and PostedTo as mandatory parameters
        current_date = datetime.now()
        
        # Use 6-month range with execution date as middle point (3 months before and after)
        posted_from = (current_date - timedelta(days=90)).strftime("%m/%d/%Y")   # 3 months before
        posted_to = (current_date + timedelta(days=90)).strftime("%m/%d/%Y")     # 3 months after
        
        params = {
            "limit": limit,
            "api_key": self.api_key,
            "postedFrom": posted_from,
            "postedTo": posted_to,
            "active": "true"  # Only active opportunities
        }
        
        # Add response due date filter to ensure opportunities are not expired
        # Only include opportunities with due dates in the future
        future_date = (current_date + timedelta(days=1)).strftime("%m/%d/%Y")
        params["responseDeadLineFrom"] = future_date
        
        # Remove keyword requirement - search ALL open opportunities
        # if keywords:
        #     params["keywords"] = keywords
            
        try:
            print(f"🔍 SAM.gov API Request: {self.base_url}")
            print(f"   📊 Parameters: {params}")
            
            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get("opportunitiesData", [])
                
                # Additional filtering for future opportunities
                filtered_opportunities = []
                for opp in opportunities:
                    response_date = opp.get("responseDeadLine")
                    if response_date:
                        try:
                            # Parse different date formats
                            if "T" in response_date:
                                deadline = datetime.strptime(response_date.split("T")[0], "%Y-%m-%d")
                            else:
                                deadline = datetime.strptime(response_date, "%m/%d/%Y")
                            
                            # Only include opportunities with deadlines in the future
                            if deadline > current_date:
                                filtered_opportunities.append(opp)
                        except ValueError:
                            # If date parsing fails, include the opportunity
                            filtered_opportunities.append(opp)
                    else:
                        # If no deadline specified, include the opportunity
                        filtered_opportunities.append(opp)
                
                print(f"   ✅ Found {len(filtered_opportunities)} current/future opportunities")
                return filtered_opportunities
            else:
                print(f"   ❌ SAM.gov API Error: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"   ❌ SAM.gov API Exception: {e}")
            return []
    
    def get_opportunity_details(self, opportunity_id):
        """
        Get detailed information about a specific opportunity
        """
        if not self.api_key:
            return None
            
        detail_url = f"https://api.sam.gov/opportunities/v2/search?noticeid={opportunity_id}"
        
        try:
            params = {"api_key": self.api_key}
            response = requests.get(detail_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("opportunitiesData", [])
            else:
                print(f"Error fetching opportunity details: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching opportunity details: {e}")
            return None
    
    def format_opportunity(self, opp_data):
        """
        Format opportunity data for consistent structure
        """
        # Generate the correct SAM.gov URL format
        notice_id = opp_data.get("noticeId", "")
        sam_url = ""
        if notice_id:
            # Use the actual SAM.gov opportunity URL format
            sam_url = f"https://sam.gov/opp/{notice_id}/view"
        
        return {
            "id": notice_id,
            "title": opp_data.get("title", ""),
            "description": opp_data.get("description", ""),
            "agency": opp_data.get("departmentName", ""),
            "office": opp_data.get("subTier", ""),
            "posted_date": opp_data.get("postedDate", ""),
            "response_deadline": opp_data.get("responseDeadLine", ""),
            "award_amount": self._parse_award_amount(opp_data.get("awardAmount", "")),
            "solicitation_number": opp_data.get("solicitationNumber", ""),
            "opportunity_type": opp_data.get("typeOfNoticeDescription", ""),
            "place_of_performance": opp_data.get("placeOfPerformance", ""),
            "classification_code": opp_data.get("classificationCode", ""),
            "url": sam_url
        }
    
    def _parse_award_amount(self, amount_str):
        """
        Parse award amount from string
        """
        if not amount_str:
            return 0
        
        try:
            # Remove currency symbols and formatting
            cleaned = amount_str.replace('$', '').replace(',', '').strip()
            
            # Handle ranges (take the maximum)
            if '-' in cleaned:
                parts = cleaned.split('-')
                if len(parts) == 2:
                    return int(float(parts[1].strip()))
            
            # Handle single values
            return int(float(cleaned))
        except (ValueError, TypeError):
            return 0
    
    def _format_opportunity(self, raw_opp):
        """Format raw SAM.gov API response into consistent structure"""
        return {
            'id': raw_opp.get('noticeId', ''),
            'title': raw_opp.get('title', ''),
            'agency': self._extract_agency(raw_opp),
            'type': raw_opp.get('type', ''),
            'amount': self._extract_amount(raw_opp),
            'deadline': raw_opp.get('responseDeadLine', ''),
            'posted_date': raw_opp.get('postedDate', ''),
            'description': raw_opp.get('description', ''),
            'solicitation_number': raw_opp.get('solicitationNumber', ''),
            'naics_code': raw_opp.get('naicsCode', ''),
            'set_aside': raw_opp.get('setAside', ''),
            'place_of_performance': self._extract_place_of_performance(raw_opp),
            'point_of_contact': self._extract_point_of_contact(raw_opp),
            'url': raw_opp.get('uiLink', ''),
            'source': 'sam.gov'
        }
    
    def _extract_agency(self, opp):
        """Extract agency name from opportunity data"""
        if 'fullParentPathName' in opp and opp['fullParentPathName']:
            # Split on dots and take first part (department level)
            return opp['fullParentPathName'].split('.')[0]
        elif 'department' in opp:
            return opp['department']
        else:
            return 'Unknown Agency'
    
    def _extract_amount(self, opp):
        """Extract funding amount from opportunity data"""
        if 'award' in opp and opp['award'] and 'amount' in opp['award']:
            try:
                amount = float(opp['award']['amount'])
                return f"${amount:,.0f}"
            except (ValueError, TypeError):
                pass
        return "Not specified"
    
    def _extract_place_of_performance(self, opp):
        """Extract place of performance information"""
        if 'placeOfPerformance' in opp and opp['placeOfPerformance']:
            pop = opp['placeOfPerformance']
            location_parts = []
            
            if 'city' in pop and pop['city'] and 'name' in pop['city']:
                location_parts.append(pop['city']['name'])
            
            if 'state' in pop and pop['state'] and 'code' in pop['state']:
                location_parts.append(pop['state']['code'])
            
            return ', '.join(location_parts) if location_parts else 'Not specified'
        
        return 'Not specified'
    
    def _extract_point_of_contact(self, opp):
        """Extract point of contact information"""
        if 'pointOfContact' in opp and opp['pointOfContact'] and len(opp['pointOfContact']) > 0:
            contact = opp['pointOfContact'][0]  # Take first contact
            return {
                'name': contact.get('fullName', ''),
                'title': contact.get('title', ''),
                'email': contact.get('email', ''),
                'phone': contact.get('phone', '')
            }
        return None
    
    def search_opportunities_by_profile(self, profile_summary, limit=50):
        """
        Search opportunities based on user profile
        """
        # Extract keywords from profile for search
        profile_lower = profile_summary.lower()
        keywords = []
        
        # Research-related keywords
        if any(term in profile_lower for term in ['research', 'phd', 'scientist', 'academic']):
            keywords.extend(['research', 'development', 'innovation'])
        
        # Technology keywords
        if any(term in profile_lower for term in ['computer', 'software', 'technology', 'ai', 'data']):
            keywords.extend(['technology', 'information', 'systems'])
        
        # Engineering keywords
        if 'engineering' in profile_lower:
            keywords.extend(['engineering', 'technical'])
        
        # Business/consulting keywords
        if any(term in profile_lower for term in ['business', 'management', 'consulting']):
            keywords.extend(['consulting', 'management', 'business'])
        
        # Healthcare keywords
        if any(term in profile_lower for term in ['health', 'medical', 'clinical']):
            keywords.extend(['health', 'medical', 'healthcare'])
        
        # If no specific keywords found, use general terms
        if not keywords:
            keywords = ['research', 'services', 'consulting']
        
        return self.search_opportunities(keywords=keywords, limit=limit)


# Usage example
if __name__ == "__main__":
    sam_api = SamGovAPI()
    
    # Test simple search
    opportunities = sam_api.search_opportunities(keywords=['technology'])
    print(f"Found {len(opportunities)} opportunities")
    
    # Test profile-based search
    profile_summary = "PhD in Computer Science with experience in software development and AI"
    profile_opportunities = sam_api.search_opportunities_by_profile(profile_summary)
    print(f"Found {len(profile_opportunities)} opportunities for profile") 