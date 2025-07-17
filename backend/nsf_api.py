#!/usr/bin/env python3
"""
Enhanced NSF API Client
======================

Robust API client for automatically discovering and extracting NSF funding opportunities.
Uses dynamic discovery and comprehensive search across multiple NSF funding programs.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time


class NSFApi:
    """
    Enhanced NSF API client with dynamic opportunity discovery
    """
    
    def __init__(self):
        self.base_url = "https://www.nsf.gov"
        self.funding_base = f"{self.base_url}/funding"
        
        # Session setup with robust headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # Comprehensive NSF funding program categories
        self.funding_categories = [
            'opportunities',
            'smallbusiness',
            'education',
            'research',
            'international',
            'crosscutting',
            'careers',
            'grad',
            'postdoc',
            'fellowships'
        ]
        
        # Known NSF funding programs to search
        self.funding_programs = [
            'sbir',
            'sttr',
            'career',
            'eager',
            'rapid',
            'goali',
            'pfi',
            'i-corps',
            'nrt',
            'grfp',
            'postdoc',
            'international'
        ]
    
    def search_opportunities(self, keywords: Optional[List[str]] = None, 
                           opportunity_type: str = 'all', 
                           limit: int = 100) -> List[Dict]:
        """
        Robustly search for NSF funding opportunities using dynamic discovery
        
        Args:
            keywords: Keywords to search for (optional - will search all if None)
            opportunity_type: Type of opportunities ('sbir', 'sttr', 'all')
            limit: Maximum number of opportunities to return
            
        Returns:
            List of dynamically discovered NSF funding opportunities
        """
        print(f"🔍 Enhanced NSF Dynamic Discovery Started")
        print(f"   📊 Target: {limit} opportunities")
        print(f"   🔎 Type: {opportunity_type}")
        
        all_opportunities = []
        discovered_urls = set()
        
        try:
            # Phase 1: Discover funding opportunity pages
            print(f"   🌐 Phase 1: Discovering NSF funding pages...")
            funding_pages = self._discover_funding_pages()
            print(f"   ✅ Discovered {len(funding_pages)} funding pages")
            
            # Phase 2: Extract opportunities from each page
            print(f"   📄 Phase 2: Extracting opportunities from pages...")
            for page_url in funding_pages:
                try:
                    page_opportunities = self._extract_opportunities_from_page(
                        page_url, keywords, opportunity_type, discovered_urls
                    )
                    all_opportunities.extend(page_opportunities)
                    
                    # Rate limiting to be respectful
                    if len(funding_pages) > 5:
                        time.sleep(0.5)
                        
                except Exception as e:
                    print(f"   ⚠️ Error processing page {page_url}: {e}")
                    continue
            
            # Phase 3: Search-based discovery
            print(f"   🔍 Phase 3: Search-based opportunity discovery...")
            search_opportunities = self._search_based_discovery(keywords, opportunity_type, discovered_urls)
            all_opportunities.extend(search_opportunities)
            
            # Phase 4: Filter and enhance opportunities
            print(f"   🎯 Phase 4: Filtering and enhancing opportunities...")
            filtered_opportunities = self._filter_and_enhance_opportunities(
                all_opportunities, keywords, opportunity_type
            )
            
            # Apply date filtering (6-month window)
            current_opportunities = self._filter_by_date_range(filtered_opportunities)
            
            print(f"   ✅ NSF Dynamic Discovery Complete:")
            print(f"      📊 Raw opportunities found: {len(all_opportunities)}")
            print(f"      🎯 After filtering: {len(current_opportunities)}")
            print(f"      📅 Within 6 months: {len(current_opportunities)}")
            
            return current_opportunities[:limit]
            
        except Exception as e:
            print(f"   ❌ NSF Discovery Error: {e}")
            return []
    
    def _discover_funding_pages(self) -> List[str]:
        """Dynamically discover NSF funding opportunity pages"""
        discovered_pages = set()
        
        try:
            # Start with main funding pages
            main_pages = [
                f"{self.funding_base}/",
                f"{self.funding_base}/opportunities/",
                f"{self.base_url}/eng/iip/sbir/",
                f"{self.base_url}/funding/education/",
                f"{self.base_url}/funding/research/",
                f"{self.base_url}/funding/careers/",
                f"{self.base_url}/funding/smallbusiness/",
                f"{self.base_url}/funding/graduate-students/",
                f"{self.base_url}/funding/early-career-researchers/"
            ]
            
            for page_url in main_pages:
                try:
                    response = self.session.get(page_url, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Find all funding opportunity links
                        opportunity_links = self._find_opportunity_links(soup, page_url)
                        discovered_pages.update(opportunity_links)
                        
                        # Look for program-specific pages
                        program_links = self._find_program_links(soup, page_url)
                        discovered_pages.update(program_links)
                        
                        # Look for solicitation links specifically
                        solicitation_links = self._find_solicitation_links(soup, page_url)
                        discovered_pages.update(solicitation_links)
                        
                except Exception as e:
                    continue
            
            # Add category-specific discovery
            for category in self.funding_categories:
                category_url = f"{self.funding_base}/{category}/"
                try:
                    response = self.session.get(category_url, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        category_links = self._find_opportunity_links(soup, category_url)
                        discovered_pages.update(category_links)
                        
                        # Also look for solicitation links in category pages
                        solicitation_links = self._find_solicitation_links(soup, category_url)
                        discovered_pages.update(solicitation_links)
                except Exception:
                    continue
            
            # Enhanced discovery: Search for known NSF program numbers
            known_programs = [
                'nsf24-582',  # Fast-Track
                'nsf24-580',  # Regular SBIR
                'nsf24-581',  # STTR
                'nsf24-579',  # CAREER
                'nsf24-578',  # EAGER
                'nsf24-577'   # RAPID
            ]
            
            for program in known_programs:
                program_search_url = f"{self.base_url}/funding/opportunities/"
                try:
                    # Search for pages containing these program numbers
                    response = self.session.get(program_search_url, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Look for links containing program numbers
                        program_links = soup.find_all('a', href=re.compile(program, re.IGNORECASE))
                        for link in program_links:
                            full_url = urljoin(program_search_url, link.get('href'))
                            if self._is_valid_opportunity_url(full_url):
                                discovered_pages.add(full_url)
                        
                        # Also search page text for program numbers
                        page_text = soup.get_text()
                        if program in page_text:
                            # Look for any links on pages that mention this program
                            all_links = soup.find_all('a', href=True)
                            for link in all_links:
                                if 'solicitation' in link.get('href', '').lower():
                                    full_url = urljoin(program_search_url, link.get('href'))
                                    if self._is_valid_opportunity_url(full_url):
                                        discovered_pages.add(full_url)
                except Exception:
                    continue
            
            # Advanced discovery: Use search functionality
            search_terms = ['sbir', 'sttr', 'solicitation', 'funding opportunity']
            for term in search_terms:
                try:
                    search_url = f"{self.base_url}/search/?q={term}"
                    response = self.session.get(search_url, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Extract search result links
                        result_links = soup.find_all('a', href=True)
                        for link in result_links:
                            href = link.get('href')
                            if any(keyword in href.lower() for keyword in ['solicitation', 'opportunity', 'funding']):
                                full_url = urljoin(self.base_url, href)
                                if self._is_valid_opportunity_url(full_url):
                                    discovered_pages.add(full_url)
                except Exception:
                    continue
            
            # Specific Fast-Track discovery
            if len(discovered_pages) < 50:  # If we haven't found many pages, add known URLs
                known_opportunity_urls = [
                    f"{self.base_url}/funding/opportunities/sbir-sttr-fast-track-nsf-small-business-innovation-research-small-business/nsf24-582/solicitation",
                    f"{self.base_url}/funding/opportunities/nsf-ttp-national-science-foundation-translation-practice",
                    f"{self.base_url}/funding/opportunities/career-faculty-early-career-development-program",
                    f"{self.base_url}/funding/opportunities/nrt-national-science-foundation-research-traineeship-program"
                ]
                
                for url in known_opportunity_urls:
                    try:
                        # Verify the URL is accessible
                        response = self.session.get(url, timeout=30)
                        if response.status_code == 200:
                            discovered_pages.add(url)
                    except Exception:
                        continue
            
            return list(discovered_pages)
            
        except Exception as e:
            print(f"   ⚠️ Discovery error: {e}")
            # Return known URLs as fallback
            return [
                f"{self.funding_base}/opportunities/",
                f"{self.base_url}/funding/opportunities/sbir-sttr-fast-track-nsf-small-business-innovation-research-small-business/nsf24-582/solicitation"
            ]
    
    def _find_opportunity_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Find opportunity links from a page"""
        links = set()
        
        # Look for common opportunity link patterns
        opportunity_patterns = [
            r'solicitation',
            r'opportunity',
            r'funding',
            r'nsf\d{2}-\d{3}',  # NSF program numbers like nsf24-582
            r'sbir',
            r'sttr',
            r'career',
            r'eager',
            r'rapid'
        ]
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            link_text = link.get_text(strip=True).lower()
            
            # Check if link matches opportunity patterns
            for pattern in opportunity_patterns:
                if (re.search(pattern, href, re.IGNORECASE) or 
                    re.search(pattern, link_text, re.IGNORECASE)):
                    
                    full_url = urljoin(base_url, href)
                    if self._is_valid_opportunity_url(full_url):
                        links.add(full_url)
                        break
        
        return links
    
    def _find_program_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Find program-specific pages that might contain opportunities"""
        links = set()
        
        for program in self.funding_programs:
            # Look for program-specific links
            program_links = soup.find_all('a', href=re.compile(program, re.IGNORECASE))
            for link in program_links:
                href = link.get('href')
                full_url = urljoin(base_url, href)
                if self._is_valid_program_url(full_url):
                    links.add(full_url)
        
        return links
    
    def _is_valid_opportunity_url(self, url: str) -> bool:
        """Check if URL is a valid NSF opportunity URL"""
        if not url.startswith(self.base_url):
            return False
        
        # Exclude common non-opportunity URLs
        exclude_patterns = [
            r'/about/',
            r'/contact/',
            r'/help/',
            r'/search/',
            r'/news/',
            r'/events/',
            r'\.pdf$',
            r'\.doc$',
            r'mailto:',
            r'tel:',
            r'#'
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        return True
    
    def _is_valid_program_url(self, url: str) -> bool:
        """Check if URL is a valid NSF program URL"""
        return (self._is_valid_opportunity_url(url) and 
                any(program in url.lower() for program in self.funding_programs))
    
    def _extract_opportunities_from_page(self, page_url: str, keywords: Optional[List[str]], 
                                       opportunity_type: str, discovered_urls: Set[str]) -> List[Dict]:
        """Extract opportunities from a specific page"""
        opportunities = []
        
        try:
            if page_url in discovered_urls:
                return []
            
            discovered_urls.add(page_url)
            
            response = self.session.get(page_url, timeout=30)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try different extraction methods based on page type
            if 'solicitation' in page_url.lower():
                opportunity = self._extract_solicitation_opportunity(soup, page_url)
                if opportunity:
                    opportunities.append(opportunity)
            
            elif any(program in page_url.lower() for program in self.funding_programs):
                program_opportunities = self._extract_program_opportunities(soup, page_url)
                opportunities.extend(program_opportunities)
            
            else:
                # General opportunity extraction
                general_opportunities = self._extract_general_opportunities(soup, page_url)
                opportunities.extend(general_opportunities)
            
            # Filter by opportunity type
            if opportunity_type != 'all':
                opportunities = [opp for opp in opportunities 
                               if opportunity_type.lower() in opp.get('title', '').lower() or
                                  opportunity_type.lower() in opp.get('description', '').lower()]
            
            return opportunities
            
        except Exception as e:
            return []
    
    def _extract_solicitation_opportunity(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Extract opportunity from a solicitation page"""
        try:
            # Extract title
            title = "NSF Funding Opportunity"
            title_selectors = ['h1', 'h2', '.title', '#title', '.page-title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text(strip=True):
                    title = title_elem.get_text(strip=True)
                    break
            
            # Extract description
            description = ""
            desc_selectors = [
                '.field-name-body',
                '.body',
                '.description',
                '.summary',
                '.abstract',
                '#summary'
            ]
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)[:1000]
                    break
            
            # Extract deadline
            deadline = None
            deadline_patterns = [
                r'deadline[:\s]+([^\n\r]+)',
                r'due[:\s]+([^\n\r]+)',
                r'submission[:\s]+([^\n\r]+)',
                r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'(\w+\s+\d{1,2},\s+\d{4})'
            ]
            
            page_text = soup.get_text()
            for pattern in deadline_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    deadline = match.group(1).strip()
                    break
            
            # Extract award amount
            award_amount = 0
            amount_patterns = [
                r'\$[\d,]+(?:\.\d{2})?',
                r'award[:\s]+\$?([\d,]+)',
                r'funding[:\s]+\$?([\d,]+)'
            ]
            
            for pattern in amount_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group().replace('$', '').replace(',', '')
                        award_amount = int(re.search(r'\d+', amount_str).group())
                        break
                    except:
                        continue
            
            # Extract program number
            program_number = ""
            program_match = re.search(r'nsf\d{2}-\d{3}', url, re.IGNORECASE)
            if program_match:
                program_number = program_match.group().upper()
            
            opportunity = {
                'title': title,
                'description': description or "NSF funding opportunity details available on solicitation page",
                'deadline': deadline,
                'award_amount': award_amount,
                'agency': 'NSF',
                'program_number': program_number,
                'url': url,
                'source': 'NSF.gov',
                'opportunity_type': self._classify_opportunity_type(title, description)
            }
            
            return opportunity
            
        except Exception as e:
            return None
    
    def _extract_program_opportunities(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract opportunities from a program page"""
        opportunities = []
        
        try:
            # Look for multiple opportunities on the page
            opportunity_sections = soup.find_all(['div', 'section', 'article'], 
                                                class_=re.compile(r'opportunity|funding|solicitation', re.IGNORECASE))
            
            for section in opportunity_sections:
                try:
                    title_elem = section.find(['h1', 'h2', 'h3', 'h4'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    description = section.get_text(strip=True)[:500]
                    
                    # Look for specific opportunity links
                    links = section.find_all('a', href=True)
                    for link in links:
                        if any(keyword in link.get_text().lower() for keyword in ['solicitation', 'opportunity', 'apply']):
                            opp_url = urljoin(url, link.get('href'))
                            
                            opportunity = {
                                'title': title,
                                'description': description,
                                'url': opp_url,
                                'agency': 'NSF',
                                'source': 'NSF.gov',
                                'opportunity_type': self._classify_opportunity_type(title, description)
                            }
                            
                            opportunities.append(opportunity)
                
                except Exception:
                    continue
            
            # If no specific opportunities found, create one for the program
            if not opportunities:
                title = soup.find('h1')
                if title:
                    opportunity = {
                        'title': title.get_text(strip=True),
                        'description': soup.get_text(strip=True)[:500],
                        'url': url,
                        'agency': 'NSF',
                        'source': 'NSF.gov',
                        'opportunity_type': self._classify_opportunity_type(title.get_text(), "")
                    }
                    opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            return []
    
    def _extract_general_opportunities(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract opportunities from general NSF pages"""
        opportunities = []
        
        try:
            # Look for opportunity listings
            opportunity_links = soup.find_all('a', href=True)
            
            for link in opportunity_links:
                link_text = link.get_text(strip=True).lower()
                href = link.get('href')
                
                # Check if this looks like an opportunity
                if any(keyword in link_text for keyword in ['solicitation', 'opportunity', 'funding', 'apply']):
                    if any(keyword in href.lower() for keyword in ['solicitation', 'opportunity', 'funding']):
                        
                        opp_url = urljoin(url, href)
                        
                        opportunity = {
                            'title': link.get_text(strip=True),
                            'description': f"NSF funding opportunity: {link.get_text(strip=True)}",
                            'url': opp_url,
                            'agency': 'NSF',
                            'source': 'NSF.gov',
                            'opportunity_type': self._classify_opportunity_type(link.get_text(), "")
                        }
                        
                        opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            return []
    
    def _search_based_discovery(self, keywords: Optional[List[str]], 
                              opportunity_type: str, discovered_urls: Set[str]) -> List[Dict]:
        """Search-based opportunity discovery"""
        opportunities = []
        
        try:
            # Search for specific NSF programs
            search_terms = []
            
            if opportunity_type == 'sbir' or opportunity_type == 'all':
                search_terms.extend(['sbir', 'small business innovation research'])
            
            if opportunity_type == 'sttr' or opportunity_type == 'all':
                search_terms.extend(['sttr', 'small business technology transfer'])
            
            if opportunity_type == 'all':
                search_terms.extend(['career', 'eager', 'rapid', 'goali', 'pfi', 'i-corps'])
            
            # Add user keywords
            if keywords:
                search_terms.extend(keywords)
            
            # Search NSF site for each term
            for term in search_terms:
                try:
                    search_url = f"{self.base_url}/search/"
                    search_opportunities = self._search_nsf_site(term, search_url, discovered_urls)
                    opportunities.extend(search_opportunities)
                except Exception:
                    continue
            
            return opportunities
            
        except Exception as e:
            return []
    
    def _search_nsf_site(self, term: str, search_url: str, discovered_urls: Set[str]) -> List[Dict]:
        """Search NSF site for a specific term"""
        opportunities = []
        
        try:
            # Try different search approaches
            search_params = {'q': term, 'type': 'funding'}
            
            response = self.session.get(search_url, params=search_params, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract search results
                search_results = soup.find_all('a', href=True)
                
                for result in search_results:
                    href = result.get('href')
                    if href and 'funding' in href.lower():
                        full_url = urljoin(self.base_url, href)
                        
                        if full_url not in discovered_urls and self._is_valid_opportunity_url(full_url):
                            discovered_urls.add(full_url)
                            
                            opportunity = {
                                'title': result.get_text(strip=True),
                                'description': f"NSF funding opportunity related to {term}",
                                'url': full_url,
                                'agency': 'NSF',
                                'source': 'NSF.gov',
                                'opportunity_type': self._classify_opportunity_type(result.get_text(), term)
                            }
                            
                            opportunities.append(opportunity)
        
        except Exception:
            pass
        
        return opportunities
    
    def _classify_opportunity_type(self, title: str, description: str) -> str:
        """Classify the type of opportunity"""
        text = f"{title} {description}".lower()
        
        if any(keyword in text for keyword in ['sbir', 'small business innovation']):
            return 'SBIR'
        elif any(keyword in text for keyword in ['sttr', 'small business technology']):
            return 'STTR'
        elif any(keyword in text for keyword in ['career', 'faculty early career']):
            return 'CAREER'
        elif any(keyword in text for keyword in ['education', 'graduate', 'undergraduate']):
            return 'Education'
        elif any(keyword in text for keyword in ['research', 'science', 'engineering']):
            return 'Research'
        else:
            return 'General'
    
    def _filter_and_enhance_opportunities(self, opportunities: List[Dict], 
                                        keywords: Optional[List[str]], 
                                        opportunity_type: str) -> List[Dict]:
        """Filter and enhance opportunities"""
        enhanced_opportunities = []
        seen_urls = set()
        
        for opp in opportunities:
            # Remove duplicates
            url = opp.get('url', '')
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Enhance opportunity data
            enhanced_opp = opp.copy()
            
            # Ensure required fields
            if not enhanced_opp.get('title'):
                enhanced_opp['title'] = 'NSF Funding Opportunity'
            
            if not enhanced_opp.get('description'):
                enhanced_opp['description'] = 'NSF funding opportunity details available'
            
            # Add metadata
            enhanced_opp['discovered_date'] = datetime.now().isoformat()
            enhanced_opp['search_keywords'] = keywords or []
            
            # Score relevance if keywords provided
            if keywords:
                relevance_score = self._calculate_relevance_score(enhanced_opp, keywords)
                enhanced_opp['relevance_score'] = relevance_score
            
            enhanced_opportunities.append(enhanced_opp)
        
        # Sort by relevance score if available
        if keywords:
            enhanced_opportunities.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return enhanced_opportunities
    
    def _calculate_relevance_score(self, opportunity: Dict, keywords: List[str]) -> float:
        """Calculate relevance score for an opportunity"""
        score = 0
        
        text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}".lower()
        
        for keyword in keywords:
            if keyword.lower() in text:
                score += 1
        
        return score / len(keywords) if keywords else 0
    
    def _filter_by_date_range(self, opportunities: List[Dict]) -> List[Dict]:
        """Filter opportunities by date range (6 months)"""
        current_date = datetime.now()
        six_months_later = current_date + timedelta(days=180)
        
        filtered_opportunities = []
        
        for opp in opportunities:
            deadline = opp.get('deadline')
            if not deadline:
                # If no deadline, assume it's current
                filtered_opportunities.append(opp)
                continue
            
            try:
                # Try to parse deadline
                deadline_date = self._parse_deadline(deadline)
                if deadline_date and deadline_date <= six_months_later:
                    filtered_opportunities.append(opp)
                else:
                    # If can't parse, include it
                    filtered_opportunities.append(opp)
            except:
                # If parsing fails, include it
                filtered_opportunities.append(opp)
        
        return filtered_opportunities
    
    def _parse_deadline(self, deadline_str: str) -> Optional[datetime]:
        """Parse deadline string to datetime"""
        try:
            # Try different date formats
            date_formats = [
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%m-%d-%Y",
                "%B %d, %Y",
                "%b %d, %Y",
                "%d %B %Y",
                "%d %b %Y"
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(deadline_str.strip(), fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def format_opportunity(self, opp_data: Dict) -> Dict:
        """Format opportunity data for output"""
        return {
            'title': opp_data.get('title', 'Unknown NSF Opportunity'),
            'description': opp_data.get('description', 'No description available'),
            'deadline': opp_data.get('deadline', 'No deadline specified'),
            'award_amount': opp_data.get('award_amount', 0),
            'agency': 'NSF',
            'program_number': opp_data.get('program_number', ''),
            'opportunity_type': opp_data.get('opportunity_type', 'General'),
            'url': opp_data.get('url', ''),
            'source': 'NSF.gov',
            'relevance_score': opp_data.get('relevance_score', 0),
            'discovered_date': opp_data.get('discovered_date', datetime.now().isoformat())
        }

    def _find_solicitation_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Find solicitation-specific links from a page"""
        links = set()
        
        # Look for solicitation-specific patterns
        solicitation_patterns = [
            r'solicitation',
            r'nsf\d{2}-\d{3}',  # NSF program numbers
            r'funding/opportunities/[^/]+/nsf\d{2}-\d{3}',  # Full solicitation paths
            r'proposal-guide',
            r'program-description'
        ]
        
        # Search for direct solicitation links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            link_text = link.get_text(strip=True).lower()
            
            # Check if link matches solicitation patterns
            for pattern in solicitation_patterns:
                if (re.search(pattern, href, re.IGNORECASE) or 
                    re.search(pattern, link_text, re.IGNORECASE)):
                    
                    full_url = urljoin(base_url, href)
                    if self._is_valid_opportunity_url(full_url):
                        links.add(full_url)
                        break
        
        # Also look for div/section elements containing solicitation info
        solicitation_containers = soup.find_all(['div', 'section', 'article'], 
                                              class_=re.compile(r'solicitation|opportunity|funding', re.IGNORECASE))
        
        for container in solicitation_containers:
            container_links = container.find_all('a', href=True)
            for link in container_links:
                href = link.get('href')
                if href and any(keyword in href.lower() for keyword in ['solicitation', 'opportunity']):
                    full_url = urljoin(base_url, href)
                    if self._is_valid_opportunity_url(full_url):
                        links.add(full_url)
        
        return links


# Usage example
if __name__ == "__main__":
    nsf = NSFApi()
    
    # Test NSF API
    print("Testing Real NSF API...")
    opportunities = nsf.search_opportunities(keywords=["artificial intelligence", "machine learning"], 
                                           opportunity_type='all', limit=10)
    
    print(f"Found {len(opportunities)} NSF opportunities")
    
    for i, opp in enumerate(opportunities[:5], 1):
        print(f"{i}. {opp['title']}")
        print(f"   Program: {opp['program_number']}")
        print(f"   URL: {opp['url']}")
        print(f"   Deadline: {opp['deadline']}")
        print(f"   Amount: ${opp['award_amount']:,}")
        print() 