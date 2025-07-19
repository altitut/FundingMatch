"""
URL Content Fetcher
Fetches and processes content from funding opportunity URLs
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, Any, Optional
import re


class URLContentFetcher:
    """Fetches and extracts content from URLs"""
    
    def __init__(self):
        """Initialize the URL content fetcher"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def fetch_url_content(self, url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Fetch and extract content from a URL
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with extracted content or None if failed
        """
        if not url or not url.startswith(('http://', 'https://')):
            return None
            
        try:
            # Add delay to be respectful
            time.sleep(0.5)
            
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content
            content = {
                'url': url,
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'main_content': self._extract_main_content(soup),
                'deadline_info': self._extract_deadline_info(soup),
                'eligibility_info': self._extract_eligibility_info(soup),
                'award_info': self._extract_award_info(soup),
                'contact_info': self._extract_contact_info(soup),
                'keywords': self._extract_keywords(soup)
            }
            
            return content
            
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  Error fetching URL {url}: {str(e)[:100]}")
            return None
        except Exception as e:
            print(f"  ⚠️  Unexpected error processing {url}: {str(e)[:100]}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from page"""
        # Try different title sources
        title = soup.find('title')
        if title:
            return title.get_text(strip=True)
        
        # Try h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
            
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract description/summary from page"""
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')
        
        # Try to find summary or abstract sections
        for tag in ['summary', 'abstract', 'overview']:
            section = soup.find(['div', 'section', 'p'], 
                              {'class': re.compile(tag, re.I)}) or \
                     soup.find(['div', 'section'], 
                              {'id': re.compile(tag, re.I)})
            if section:
                return section.get_text(strip=True)[:1000]
        
        return ""
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from page"""
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
        
        # Try to find main content area
        main = soup.find('main') or \
               soup.find('div', {'class': re.compile('content|main', re.I)}) or \
               soup.find('article')
        
        if main:
            text = main.get_text(separator=' ', strip=True)
            # Limit to reasonable length
            return ' '.join(text.split()[:500])
        
        # Fallback to body text
        body_text = soup.get_text(separator=' ', strip=True)
        return ' '.join(body_text.split()[:500])
    
    def _extract_deadline_info(self, soup: BeautifulSoup) -> str:
        """Extract deadline information"""
        deadline_keywords = ['deadline', 'due date', 'close date', 'closing date', 
                           'submission deadline', 'application deadline', 'proposal due',
                           'applications due', 'next deadline', 'upcoming deadline']
        
        # First try to find deadline in specific patterns
        for keyword in deadline_keywords:
            # Look for keyword followed by date
            pattern = re.compile(f'{keyword}[:\s]*([^<\n]+)', re.I)
            text = soup.get_text()
            matches = pattern.findall(text)
            
            for match in matches:
                # Look for dates in the matched text
                # Multiple date formats
                date_patterns = [
                    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
                    r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                    r'\b\d{4}-\d{2}-\d{2}\b',
                    r'\b\d{1,2}-\d{1,2}-\d{4}\b'
                ]
                
                for date_pattern in date_patterns:
                    date_match = re.search(date_pattern, match)
                    if date_match:
                        return date_match.group(0)
        
        # If no keyword match, look for standalone dates near deadline-related words
        deadline_section = None
        for keyword in deadline_keywords:
            elements = soup.find_all(text=re.compile(keyword, re.I))
            for elem in elements:
                parent = elem.parent
                if parent:
                    text = parent.get_text()[:500]
                    # Look for dates
                    date_pattern = re.compile(r'\b(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b')
                    dates = date_pattern.findall(text)
                    if dates:
                        return dates[0]  # Return first date found
        
        # Fallback: look for any date patterns in the page
        date_pattern = re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b')
        dates = date_pattern.findall(soup.get_text())
        if dates:
            # Filter out old dates if possible
            from datetime import datetime
            current_year = datetime.now().year
            future_dates = [d for d in dates if str(current_year) in d or str(current_year + 1) in d or str(current_year + 2) in d]
            if future_dates:
                return future_dates[0]
        
        return ""
    
    def _extract_eligibility_info(self, soup: BeautifulSoup) -> str:
        """Extract eligibility information"""
        eligibility_keywords = ['eligibility', 'eligible', 'qualification', 'who can apply']
        
        for keyword in eligibility_keywords:
            section = soup.find(['div', 'section', 'p'], 
                              text=re.compile(keyword, re.I))
            if section:
                parent = section.find_parent(['div', 'section'])
                if parent:
                    return parent.get_text(strip=True)[:500]
        
        return ""
    
    def _extract_award_info(self, soup: BeautifulSoup) -> str:
        """Extract award/funding amount information"""
        award_keywords = ['award', 'funding', 'grant amount', 'budget', r'\$[\d,]+']
        
        for keyword in award_keywords:
            pattern = re.compile(keyword, re.I)
            matches = soup.find_all(text=pattern)
            if matches:
                # Get context around the match
                for match in matches[:3]:
                    parent = match.parent
                    if parent:
                        text = parent.get_text(strip=True)
                        if '$' in text or 'award' in text.lower():
                            return text[:300]
        
        return ""
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> str:
        """Extract contact information"""
        contact_keywords = ['contact', 'email', 'phone', 'program officer']
        
        for keyword in contact_keywords:
            section = soup.find(['div', 'section', 'p'], 
                              text=re.compile(keyword, re.I))
            if section:
                parent = section.find_parent(['div', 'section'])
                if parent:
                    text = parent.get_text(strip=True)[:300]
                    # Look for email
                    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
                    emails = email_pattern.findall(text)
                    if emails:
                        return f"Contact: {emails[0]}"
                    return text
        
        return ""
    
    def _extract_keywords(self, soup: BeautifulSoup) -> list:
        """Extract keywords from page"""
        keywords = []
        
        # Try meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            content = meta_keywords.get('content', '')
            keywords.extend([k.strip() for k in content.split(',') if k.strip()])
        
        # Extract from headings
        for heading in soup.find_all(['h1', 'h2', 'h3'])[:10]:
            text = heading.get_text(strip=True)
            if len(text) < 50:  # Reasonable heading length
                keywords.append(text)
        
        return keywords[:20]  # Limit keywords