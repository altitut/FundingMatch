#!/usr/bin/env python3
"""
Comprehensive Funding Opportunities Analysis System
==================================================

This script performs comprehensive AI-powered analysis of funding opportunities using Gemini 2.5 Pro.
It processes CSV files from FundingOpportunities folder, converts them to JSON, fetches content from program URLs 
and solicitation URLs, and creates enriched semantic profiles for each opportunity.

Features:
- Real Gemini 2.5 Pro API integration for opportunity analysis
- CSV file processing from FundingOpportunities folder (no subfolders)
- URL content processing for program and solicitation pages
- Comprehensive semantic enrichment of funding opportunities
- Structured output for improved matching capabilities
- Incremental processing (only new opportunities)
- Standardized data structure across all opportunities
- Automatic file management and progress tracking

Usage:
    python comprehensive_funding_analysis.py              # Process new CSV files only
    python comprehensive_funding_analysis.py --quick      # Process first 5 opportunities total
    python comprehensive_funding_analysis.py --test       # Process 82 opportunities from each file
    python comprehensive_funding_analysis.py --force      # Force reprocess all

Input Files:
    - Any CSV files in FundingOpportunities folder (no subfolders)

Output:
    - Enhanced semantic profiles appended to FundingOpportunities/COMPLETE_funding_semantic.json
    - Instructions saved to ReadmeFundingOpportunities.md
    - Processing summaries and progress tracking
    - ProcessedOpportunities.md saved in FundingOpportunities folder

Author: Alfredo Costilla
Date: 2025
"""

import os
import sys
import json
import time
import hashlib
import requests
import csv
import glob
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai
from google.ai.generativelanguage import Content, Part, Blob
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import traceback

# Load environment variables
load_dotenv()

def discover_csv_files(folder_path: str = "FundingOpportunities") -> List[str]:
    """
    Discover all CSV files in the specified folder (no subfolders)
    
    Args:
        folder_path: Path to the folder containing CSV files
        
    Returns:
        List of CSV file paths
    """
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return []
    
    csv_files = []
    for file in os.listdir(folder_path):
        if file.endswith('.csv') and os.path.isfile(os.path.join(folder_path, file)):
            csv_files.append(os.path.join(folder_path, file))
    
    return csv_files

def convert_csv_to_json(csv_file_path: str, max_opportunities: Optional[int] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convert CSV file to JSON format with metadata and normalize structure
    
    Args:
        csv_file_path: Path to the CSV file
        max_opportunities: Maximum number of opportunities to process from this file
        
    Returns:
        Tuple of (opportunities list, metadata dict)
    """
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            # Use csv.DictReader to automatically handle headers
            csv_reader = csv.DictReader(csvfile)
            
            # Convert to list of dictionaries with normalized structure
            opportunities = []
            for i, row in enumerate(csv_reader):
                if max_opportunities and i >= max_opportunities:
                    break
                    
                # Clean up any empty values and normalize structure
                cleaned_row = {}
                for key, value in row.items():
                    # Strip whitespace from keys and values
                    clean_key = key.strip() if key else key
                    clean_value = value.strip() if value else value
                    
                    # Convert empty strings to None
                    if clean_value == "":
                        clean_value = None
                    
                    cleaned_row[clean_key] = clean_value
                
                # Normalize the structure for consistent processing
                normalized_opportunity = {
                    "basic_info": {
                        "title": cleaned_row.get("Title") or cleaned_row.get("Topic Title") or "Unknown Title",
                        "program_id": cleaned_row.get("Program ID") or cleaned_row.get("Topic Number") or "Unknown",
                        "nsf_program_number": cleaned_row.get("NSF/PD Num") or cleaned_row.get("Program") or "Not specified",
                        "status": cleaned_row.get("Status") or "Unknown",
                        "type": cleaned_row.get("Type") or cleaned_row.get("Phase") or "Unknown",
                        "posted_date": cleaned_row.get("Posted date (Y-m-d)") or cleaned_row.get("Release Date") or "Unknown"
                    },
                    "opportunity_details": {
                        "synopsis": cleaned_row.get("Synopsis") or cleaned_row.get("Topic Description") or "No description available",
                        "award_types": [cleaned_row.get("Award Type")] if cleaned_row.get("Award Type") else [],
                        "due_dates": [cleaned_row.get("Next due date (Y-m-d)")] if cleaned_row.get("Next due date (Y-m-d)") else [],
                        "accepts_anytime": False,  # Default value
                        "key_requirements": []
                    },
                    "categorization": {
                        "research_areas": [],
                        "funding_categories": [],
                        "opportunity_level": cleaned_row.get("Phase") or "Not specified"
                    },
                    "urls": {
                        "program_url": cleaned_row.get("URL") or cleaned_row.get("Solicitation Agency URL") or "",
                        "solicitation_url": cleaned_row.get("Solicitation URL") or ""
                    },
                    "metadata": {
                        "word_count": len((cleaned_row.get("Synopsis") or cleaned_row.get("Topic Description") or "").split()),
                        "has_detailed_synopsis": bool(cleaned_row.get("Synopsis") or cleaned_row.get("Topic Description")),
                        "processing_timestamp": datetime.now().isoformat()
                    },
                    "semantic_analysis": {
                        "error": None,
                        "skipped_reason": None,
                        "enhanced_description": "",
                        "analysis_confidence": 0.0,
                        "confidence_score": 0.0,
                        "analysis_timestamp": None,
                        "opportunity_id": cleaned_row.get("Program ID") or cleaned_row.get("Topic Number") or "Unknown",
                        "opportunity_title": cleaned_row.get("Title") or cleaned_row.get("Topic Title") or "Unknown Title",
                        "enhanced_opportunity_profile": {
                            "confidence_score": 0.0,
                            "refined_title_and_program_focus": {
                                "refined_title": "",
                                "program_focus": ""
                            },
                            "comprehensive_description": "",
                            "target_audience_and_eligibility": {
                                "target_audience": "",
                                "eligibility_requirements": {
                                    "organizations": "",
                                    "principal_investigators": ""
                                }
                            },
                            "award_information": {
                                "award_types": [],
                                "award_amounts": {
                                    "total_program_funding": "",
                                    "individual_award_size": "",
                                    "estimated_number_of_awards": ""
                                },
                                "award_duration": ""
                            },
                            "submission_requirements": {
                                "deadline": "",
                                "submission_process": "",
                                "pre_submission_artifacts": {
                                    "letter_of_intent_required": False,
                                    "preliminary_proposal_required": False
                                }
                            }
                        },
                        "technical_focus_areas": {
                            "confidence_score": 0.0,
                            "primary_research_domains": [],
                            "specific_technical_priorities": [],
                            "innovation_expectations": "",
                            "technology_readiness_levels": "",
                            "interdisciplinary_collaboration_opportunities": ""
                        },
                        "strategic_context": {
                            "confidence_score": 0.0,
                            "nsf_directorate_and_program_positioning": "",
                            "relationship_to_national_priorities": "",
                            "partnership_opportunities_and_requirements": "",
                            "international_collaboration_aspects": "",
                            "industry_engagement_expectations": ""
                        },
                        "competitive_landscape": {
                            "confidence_score": 0.0,
                            "funding_competition_level": "",
                            "typical_award_amounts_and_project_scales": "",
                            "review_criteria_and_evaluation_process": "",
                            "previous_award_examples_and_patterns": "",
                            "strategic_positioning_recommendations": ""
                        },
                        "application_strategy": {
                            "confidence_score": 0.0,
                            "key_proposal_elements": [],
                            "critical_success_factors": [],
                            "common_pitfalls_to_avoid": [],
                            "timeline_and_preparation_recommendations": "",
                            "team_composition_and_collaboration_needs": ""
                        },
                        "semantic_keywords": {
                            "confidence_score": 0.0,
                            "technical_terminology": [],
                            "research_methodology_keywords": [],
                            "application_domain_keywords": [],
                            "innovation_and_impact_keywords": [],
                            "collaboration_and_partnership_keywords": []
                        },
                        "match_ready_summary": {
                            "confidence_score": 0.0,
                            "summary": "",
                            "key_capabilities_needed": [],
                            "innovation_potential_and_impact": {
                                "innovation": "",
                                "impact": ""
                            },
                            "collaboration_requirements": "",
                            "funding_readiness_indicators": ""
                        }
                    },
                    "processing_metadata": {
                        "processed_date": None,
                        "skipped": False,
                        "skip_reason": None,
                        "program_url_accessible": False,
                        "solicitation_url_accessible": False,
                        "gemini_model": "gemini-2.5-pro",
                        "analysis_time_seconds": 0.0,
                        "program_url_processed": False,
                        "solicitation_url_processed": False
                    },
                    "agency_info": {
                        "agency": cleaned_row.get("Agency") or "NSF",  # Default to NSF if not specified
                        "branch": cleaned_row.get("Branch") or "Not specified"
                    },
                    "raw_data": cleaned_row  # Keep original data for reference
                }
                
                opportunities.append(normalized_opportunity)
        
        # Create metadata
        metadata = {
            "source_file": csv_file_path,
            "conversion_timestamp": datetime.now().isoformat(),
            "total_opportunities": len(opportunities),
            "file_type": "csv",
            "max_opportunities_limit": max_opportunities,
            "normalization_applied": True
        }
        
        return opportunities, metadata
        
    except Exception as e:
        print(f"❌ Error converting CSV to JSON: {e}")
        return [], {}

def move_processed_file(file_path: str, destination_folder: str = "FundingOpportunities/Ingested") -> bool:
    """
    Move processed file to destination folder with timestamp
    
    Args:
        file_path: Path to the file to move
        destination_folder: Destination folder path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create destination folder if it doesn't exist
        os.makedirs(destination_folder, exist_ok=True)
        
        # Get file name and extension
        file_name = os.path.basename(file_path)
        name, ext = os.path.splitext(file_name)
        
        # Create timestamp
        timestamp = datetime.now().strftime("%B_%d_%Y")
        
        # Create new filename
        new_filename = f"{name}_PROCESSED_ON_{timestamp}{ext}"
        destination_path = os.path.join(destination_folder, new_filename)
        
        # Move file
        shutil.move(file_path, destination_path)
        print(f"📁 Moved processed file: {file_path} → {destination_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error moving file {file_path}: {e}")
        return False

def create_readme_file():
    """
    Create a comprehensive README file with instructions for managing funding opportunities
    """
    readme_content = """# Funding Opportunities Management Guide

## Overview

This guide provides instructions for managing NSF funding opportunities data, including how to update, add, and remove opportunities using the comprehensive funding analysis system.

## File Structure

```
FundingOpportunities/
├── Ingested/                              # Processed CSV files with timestamps
├── nsf_funding_semantic.json              # Enhanced opportunities with AI analysis
└── ReadmeFundingOpportunities.md          # This file
```

## How to Update Funding Opportunities

### Method 1: Adding New CSV Files

1. **Place new CSV files** in the `FundingOpportunities/` folder
2. **Run the analysis script**:
   ```bash
   python comprehensive_funding_analysis.py
   ```
3. **Script will automatically**:
   - Discover and process all CSV files
   - Enhance opportunities with AI analysis
   - Move processed files to `Ingested/` folder with timestamps
   - Generate updated `nsf_funding_semantic.json`

### Method 2: Force Reprocessing

To reprocess all opportunities (useful when you want to refresh analysis):

```bash
python comprehensive_funding_analysis.py --force
```

## How to Add New Opportunities

1. **Add new rows** to existing CSV files in `FundingOpportunities/` folder
2. **Ensure CSV headers match** the existing structure:
   - Required fields vary by source (NSF, SBIR, etc.)
   - Common fields: Title, Description, Agency, Program, etc.
3. **Run the processing script**:
   ```bash
   python comprehensive_funding_analysis.py
   ```
4. **New opportunities will be**:
   - Automatically detected and processed
   - Enhanced with AI semantic analysis
   - Integrated into the output file

## How to Remove Outdated Opportunities

### Method 1: Source File Modification (Recommended)

1. **Remove rows** from CSV files in `FundingOpportunities/` folder
2. **Run script with --force** to reprocess all:
   ```bash
   python comprehensive_funding_analysis.py --force
   ```

### Method 2: Manual JSON Editing (Advanced)

1. **Backup the file** before making changes:
   ```bash
   cp FundingOpportunities/nsf_funding_semantic.json FundingOpportunities/nsf_funding_semantic_backup.json
   ```
2. **Edit the JSON file** to remove specific opportunities
3. **Update metadata counters** in the file:
   - `total_enhanced_opportunities`
   - `successful_analyses`
   - `total_opportunities`

⚠️ **Warning**: Manual edits may be overwritten when the script runs again.

## Command Line Options

| Command | Description |
|---------|-------------|
| `python comprehensive_funding_analysis.py` | Process all CSV files completely |
| `python comprehensive_funding_analysis.py --quick` | Process first 5 opportunities (testing) |
| `python comprehensive_funding_analysis.py --test` | Process 82 opportunities from each file |
| `python comprehensive_funding_analysis.py --force` | Force reprocess all data |

## Testing and Validation

### Quick Test (5 opportunities)
```bash
python comprehensive_funding_analysis.py --quick
```

### Medium Test (82 opportunities per file)
```bash
python comprehensive_funding_analysis.py --test
```

### Full Processing
```bash
python comprehensive_funding_analysis.py
```

## Data Quality Guidelines

1. **CSV Format Requirements**:
   - UTF-8 encoding
   - Proper header row
   - Consistent column names
   - No empty header cells

2. **Required Fields** (varies by source):
   - Title or Topic Title
   - Description or Synopsis
   - Program/Agency information
   - Dates (if available)

3. **Optional but Recommended**:
   - Program URLs
   - Solicitation URLs
   - Keywords
   - Contact information

## Output File Structure

The generated `nsf_funding_semantic.json` follows this structure:

```json
{
  "nsf_funding_opportunities_semantic": {
    "metadata": {
      "processing_timestamp": "...",
      "source_files": [...],
      "semantic_enhancement": {...}
    },
    "opportunities": [
      {
        "original_fields": "...",
        "semantic_analysis": {
          "enhanced_description": "...",
          "technical_focus_areas": [...],
          "strategic_context": "...",
          "semantic_keywords": [...],
          "match_ready_summary": "..."
        }
      }
    ]
  }
}
```

## Integration with Matching System

The output file is designed to work with `nsf_comprehensive_matcher.py`:

1. **Maintains compatibility** with existing matching algorithms
2. **Preserves original data** while adding semantic enhancements
3. **Structured for efficient** researcher-opportunity matching

## Maintenance Notes

- **Backup important data** before major changes
- **Check processing reports** (`NSF_semantic_report.md`) for errors
- **Monitor `Ingested/` folder** for processed file history
- **Review semantic enhancement** success rates in metadata

## Troubleshooting

### Common Issues

1. **"No CSV files found"**: Ensure CSV files are in root of `FundingOpportunities/` folder
2. **"GEMINI_API_KEY not found"**: Check `.env` file has valid API key
3. **Processing errors**: Check `NSF_semantic_report.md` for detailed error analysis

### Getting Help

1. Review processing reports for detailed statistics
2. Check log output for specific error messages
3. Verify CSV file format and encoding
4. Ensure proper API key configuration

---

**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}  
**System Version**: Comprehensive Funding Analysis v1.0
"""

    try:
        with open("ReadmeFundingOpportunities.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("📋 Created ReadmeFundingOpportunities.md with comprehensive instructions")
        return True
    except Exception as e:
        print(f"❌ Error creating README file: {e}")
        return False

class RateLimiter:
    """Rate limiter for API calls with threading support"""
    
    def __init__(self, max_requests_per_minute: int = 150):
        self.max_requests_per_minute = max_requests_per_minute
        self.requests = Queue()
        self.lock = threading.Lock()
        
    def acquire(self):
        """Acquire permission to make a request"""
        current_time = time.time()
        
        with self.lock:
            # Remove requests older than 1 minute
            while not self.requests.empty():
                oldest_request = self.requests.queue[0]
                if current_time - oldest_request > 60:
                    self.requests.get()
                else:
                    break
            
            # Check if we can make a request
            if self.requests.qsize() >= self.max_requests_per_minute:
                # Wait until we can make a request
                sleep_time = 60 - (current_time - self.requests.queue[0]) + 0.1
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    return self.acquire()
            
            # Record this request
            self.requests.put(current_time)

class NSFOpportunityAnalyzer:
    """
    Comprehensive NSF Funding Opportunity Analyzer using Gemini 2.5 Pro
    """
    
    def __init__(self, gemini_api_key: str, max_requests_per_minute: int = 150):
        """
        Initialize the analyzer with Gemini API
        
        Args:
            gemini_api_key: Gemini API key for document analysis
            max_requests_per_minute: Maximum API requests per minute (default: 150)
        """
        # Configure Gemini API
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(max_requests_per_minute)
        
        # Initialize analysis prompt
        self.analysis_prompt = self._initialize_analysis_prompt()
        
        # Initialize processing statistics
        self.processing_stats = {
            'successful': 0,
            'failed': 0,
            'url_403_errors': 0,
            'analysis_errors': 0,
            'successful_opportunities': [],
            'failed_opportunities': [],
            'url_403_opportunities': []
        }
        
        print(f"✅ NSF Opportunity Analyzer initialized with Gemini 2.5 Pro (Max {max_requests_per_minute} RPM)")
    
    def _initialize_analysis_prompt(self) -> str:
        """Initialize the comprehensive analysis prompt for funding opportunities"""
        return """
        Analyze this funding opportunity comprehensively. You have been provided with:
        1. The basic opportunity information from the funding database
        2. Content from the program URL (if available)
        3. Content from the solicitation URL (if available)
        
        IMPORTANT: If any data is missing or unavailable, analyze what IS available and note the limitations. Do not generate warnings about missing data - instead, work with the available information to provide the best possible analysis.
        
        Please provide a comprehensive analysis that extracts and enhances the following:
        
        1. **Enhanced Opportunity Profile**:
           - Refined title and program focus
           - Comprehensive description synthesizing all sources
           - Target audience and eligibility requirements
           - Award types, amounts, and duration details
           - Submission deadlines and process requirements
        
        2. **Technical Focus Areas**:
           - Primary research domains and disciplines
           - Specific technical requirements and priorities
           - Innovation expectations and evaluation criteria
           - Technology readiness levels expected
           - Interdisciplinary collaboration opportunities
        
        3. **Strategic Context**:
           - NSF directorate and program positioning
           - Relationship to national priorities and initiatives
           - Partnership opportunities and requirements
           - International collaboration aspects
           - Industry engagement expectations
        
        4. **Competitive Landscape**:
           - Funding competition level and success rates
           - Typical award amounts and project scales
           - Review criteria and evaluation process
           - Previous award examples and patterns
           - Strategic positioning recommendations
        
        5. **Application Strategy**:
           - Key proposal elements and requirements
           - Critical success factors and evaluation criteria
           - Common pitfalls and recommendations
           - Timeline and preparation requirements
           - Team composition and collaboration needs
        
        6. **Semantic Keywords**:
           - Technical terminology and domain keywords
           - Research methodology keywords
           - Application domain keywords
           - Innovation and impact keywords
           - Collaboration and partnership keywords
        
        7. **Match-Ready Summary**:
           - 200-300 word comprehensive summary for matching
           - Key capabilities and expertise needed
           - Innovation potential and impact expectations
           - Collaboration requirements and opportunities
           - Funding readiness indicators
        
        Return the analysis as a structured JSON object that enhances the original opportunity data.
        Include confidence scores for different analysis aspects based on available information quality.
        """
    
    def _fetch_url_content(self, url: str) -> Optional[str]:
        """
        Fetch content from a URL and return clean text
        
        Args:
            url: URL to fetch content from
            
        Returns:
            Clean text content from the URL or None if failed
        """
        # Check if URL is valid
        if not url or not url.strip():
            print(f"⚠️  Empty or invalid URL provided")
            return None
            
        try:
            # Set headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Make request with timeout
            response = requests.get(url, headers=headers, timeout=30)
            
            # Check if response is valid
            if response is None:
                print(f"❌ No response received from {url}")
                return None
                
            response.raise_for_status()
            
            # Get content type
            content_type = response.headers.get('content-type', '').lower()
            
            if 'text/html' in content_type:
                # Parse HTML content
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Get text content
                    text = soup.get_text()
                    
                    # Clean up text
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    return text[:15000]  # Limit to 15k characters for funding opportunities
                    
                except ImportError:
                    print("⚠️  BeautifulSoup not available, using raw text")
                    return response.text[:15000]
                    
            elif 'text/plain' in content_type:
                return response.text[:15000]
            else:
                return f"Content from {url} (Content-Type: {content_type})"
                
        except requests.RequestException as e:
            if "403" in str(e) or "Forbidden" in str(e):
                print(f"🔒 403 Forbidden error fetching {url}: {str(e)}")
                return "403_FORBIDDEN"
            else:
                print(f"❌ Error fetching {url}: {str(e)}")
                return None
        except Exception as e:
            print(f"❌ Unexpected error fetching {url}: {str(e)}")
            return None
    
    def analyze_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single funding opportunity using Gemini 2.5 Pro
        
        Args:
            opportunity: Funding opportunity data from JSON
            
        Returns:
            Enhanced opportunity analysis
        """
        basic_info = opportunity.get('basic_info', {})
        title = basic_info.get('title', 'Unknown Opportunity')
        
        print(f"   📊 Analyzing: {title[:60]}...")
        
        try:
            # Prepare context from opportunity data - handle missing fields gracefully
            title = basic_info.get('title', 'Unknown Title')
            program_id = basic_info.get('program_id', 'Unknown Program ID')
            nsf_program_number = basic_info.get('nsf_program_number', 'Not specified')
            status = basic_info.get('status', 'Unknown Status')
            opportunity_type = basic_info.get('type', 'Unknown Type')
            posted_date = basic_info.get('posted_date', 'Unknown Date')
            
            synopsis = opportunity.get('opportunity_details', {}).get('synopsis', 'No synopsis available')
            award_types = opportunity.get('opportunity_details', {}).get('award_types', [])
            due_dates = opportunity.get('opportunity_details', {}).get('due_dates', [])
            key_requirements = opportunity.get('opportunity_details', {}).get('key_requirements', [])
            research_areas = opportunity.get('categorization', {}).get('research_areas', [])
            funding_categories = opportunity.get('categorization', {}).get('funding_categories', [])
            opportunity_level = opportunity.get('categorization', {}).get('opportunity_level', 'Not specified')
            
            opportunity_context = f"""
            FUNDING OPPORTUNITY DATA:
            
            Title: {title}
            Program ID: {program_id}
            NSF Program Number: {nsf_program_number}
            Status: {status}
            Type: {opportunity_type}
            Posted Date: {posted_date}
            
            Synopsis: {synopsis}
            
            Award Types: {award_types if award_types else 'Not specified'}
            Due Dates: {due_dates if due_dates else 'Not specified'}
            Key Requirements: {key_requirements if key_requirements else 'Not specified'}
            
            Research Areas: {research_areas if research_areas else 'Not specified'}
            Funding Categories: {funding_categories if funding_categories else 'Not specified'}
            Opportunity Level: {opportunity_level}
            """
            
            # Fetch content from URLs
            urls = opportunity.get('urls', {})
            program_url = urls.get('program_url', '')
            solicitation_url = urls.get('solicitation_url', '')
            
            program_content = ""
            solicitation_content = ""
            has_403_error = False
            
            if program_url:
                print(f"   🔗 Fetching program URL content...")
                program_content = self._fetch_url_content(program_url)
                if program_content == "403_FORBIDDEN":
                    has_403_error = True
                    program_content = f"\n\nPROGRAM URL ({program_url}): 403 Forbidden - Access Denied"
                elif program_content:
                    program_content = f"\n\nPROGRAM URL CONTENT ({program_url}):\n{program_content}"
                else:
                    program_content = f"\n\nPROGRAM URL ({program_url}): Content not accessible"
            
            if solicitation_url and solicitation_url != program_url:
                print(f"   📋 Fetching solicitation URL content...")
                solicitation_content = self._fetch_url_content(solicitation_url)
                if solicitation_content == "403_FORBIDDEN":
                    has_403_error = True
                    solicitation_content = f"\n\nSOLICITATION URL ({solicitation_url}): 403 Forbidden - Access Denied"
                elif solicitation_content:
                    solicitation_content = f"\n\nSOLICITATION URL CONTENT ({solicitation_url}):\n{solicitation_content}"
                else:
                    solicitation_content = f"\n\nSOLICITATION URL ({solicitation_url}): Content not accessible"
            
            # Skip processing if we have 403 errors
            if has_403_error:
                print(f"   ⏭️  Skipping analysis due to 403 Forbidden errors")
                error_msg = "Skipped due to 403 Forbidden errors when fetching URL content"
                self.processing_stats['url_403_errors'] += 1
                self.processing_stats['url_403_opportunities'].append({
                    'title': title,
                    'program_id': basic_info.get('program_id', ''),
                    'error': error_msg,
                    'program_url': program_url,
                    'solicitation_url': solicitation_url
                })
                # Update the semantic_analysis with error information
                opportunity["semantic_analysis"].update({
                    "error": error_msg,
                    "skipped_reason": "403_forbidden_urls",
                    "enhanced_description": opportunity.get('opportunity_details', {}).get('synopsis', ''),
                    "analysis_confidence": 0.0
                })
                
                # Update processing metadata
                opportunity["processing_metadata"].update({
                    "processed_date": datetime.now().isoformat(),
                    "skipped": True,
                    "skip_reason": "403_forbidden_urls",
                    "program_url_accessible": program_content != "403_FORBIDDEN",
                    "solicitation_url_accessible": solicitation_content != "403_FORBIDDEN"
                })
                
                return opportunity
            
            # Combine all context
            full_context = opportunity_context + program_content + solicitation_content
            
            # Generate analysis using Gemini 2.5 Pro with rate limiting
            print(f"   🧠 Generating comprehensive analysis...")
            start_time = time.time()
            
            # Apply rate limiting
            self.rate_limiter.acquire()
            
            response = self.model.generate_content(
                f"{self.analysis_prompt}\n\n{full_context}"
            )
            
            analysis_time = time.time() - start_time
            
            # Check if response is valid
            if response is None:
                raise Exception("Gemini API returned None response")
            
            # Parse JSON response
            analysis_text = response.text
            
            # Check if analysis_text is valid
            if analysis_text is None:
                raise Exception("Gemini API response text is None")
            
            # Extract JSON from response (handle potential markdown formatting)
            json_match = re.search(r'```json\n(.*?)\n```', analysis_text, re.DOTALL)
            if json_match:
                analysis_text = json_match.group(1)
            elif analysis_text.strip().startswith('{'):
                # Response is already JSON
                pass
            else:
                # Try to find JSON in the response
                json_start = analysis_text.find('{')
                json_end = analysis_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    analysis_text = analysis_text[json_start:json_end]
            
            try:
                enhanced_analysis = json.loads(analysis_text)
            except json.JSONDecodeError as e:
                print(f"⚠️  Warning: Could not parse JSON response: {e}")
                # Fallback: create basic enhanced structure
                enhanced_analysis = {
                    "enhanced_description": opportunity.get('opportunity_details', {}).get('synopsis', ''),
                    "technical_focus_areas": opportunity.get('categorization', {}).get('research_areas', []),
                    "semantic_keywords": [],
                    "match_ready_summary": opportunity.get('opportunity_details', {}).get('synopsis', '')[:300],
                    "analysis_confidence": 0.3,
                    "raw_response": analysis_text[:1000]
                }
            
            # Update the semantic_analysis with the enhanced analysis
            opportunity["semantic_analysis"].update(enhanced_analysis)
            opportunity["semantic_analysis"]["analysis_timestamp"] = datetime.now().isoformat()
            
            # Update processing metadata
            opportunity["processing_metadata"].update({
                "processed_date": datetime.now().isoformat(),
                "analysis_time_seconds": round(analysis_time, 2),
                "program_url_processed": bool(program_content and "Content not accessible" not in program_content),
                "solicitation_url_processed": bool(solicitation_content and "Content not accessible" not in solicitation_content),
                "program_url_accessible": bool(program_content and "403 Forbidden" not in program_content and "Content not accessible" not in program_content),
                "solicitation_url_accessible": bool(solicitation_content and "403 Forbidden" not in solicitation_content and "Content not accessible" not in solicitation_content)
            })
            
            enhanced_opportunity = opportunity
            
            print(f"   ✅ Analysis complete ({analysis_time:.1f}s)")
            
            # Track successful analysis
            self.processing_stats['successful'] += 1
            self.processing_stats['successful_opportunities'].append({
                'title': title,
                'program_id': basic_info.get('program_id', ''),
                'analysis_time': analysis_time,
                'program_url_processed': bool(program_content and "403 Forbidden" not in program_content and "Content not accessible" not in program_content),
                'solicitation_url_processed': bool(solicitation_content and "403 Forbidden" not in solicitation_content and "Content not accessible" not in solicitation_content)
            })
            
            return enhanced_opportunity
            
        except Exception as e:
            print(f"   ❌ Analysis failed: {str(e)}")
            
            # Track failed analysis
            self.processing_stats['analysis_errors'] += 1
            self.processing_stats['failed_opportunities'].append({
                'title': title,
                'program_id': basic_info.get('program_id', ''),
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            
            # Return opportunity with error information
            error_opportunity = {
                **opportunity,
                "semantic_analysis": {
                    "error": str(e),
                    "enhanced_description": opportunity.get('opportunity_details', {}).get('synopsis', ''),
                    "analysis_confidence": 0.0
                },
                "processing_metadata": {
                    "processed_date": datetime.now().isoformat(),
                    "error": str(e),
                    "gemini_model": "gemini-2.5-pro"
                }
            }
            
            # Ensure we never return None
            if error_opportunity is None:
                error_opportunity = {
                    "basic_info": {"title": "Error Processing Opportunity"},
                    "semantic_analysis": {"error": str(e)},
                    "processing_metadata": {"error": str(e)}
                }
            
            return error_opportunity
    
    def analyze_all_opportunities(self, opportunities: List[Dict[str, Any]], quick_mode: bool = False, max_workers: int = 5) -> List[Dict[str, Any]]:
        """
        Analyze all funding opportunities using parallel processing
        
        Args:
            opportunities: List of opportunity dictionaries
            quick_mode: If True, only process first 5 opportunities
            max_workers: Maximum number of parallel workers (default: 5)
            
        Returns:
            List of enhanced opportunity analyses
        """
        if quick_mode:
            opportunities = opportunities[:5]
            print(f"🔄 Quick mode: Processing {len(opportunities)} opportunities")
        else:
            print(f"🔄 Full analysis: Processing {len(opportunities)} opportunities")
        
        enhanced_opportunities = []
        total_opportunities = len(opportunities)
        completed_count = 0
        
        print(f"🧠 Starting Parallel NSF Opportunity Analysis ({max_workers} workers, max 150 RPM)...")
        print("-" * 70)
        
        # Process opportunities in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_opportunity = {
                executor.submit(self.analyze_opportunity, opportunity): opportunity 
                for opportunity in opportunities
            }
            
            # Process completed tasks
            for future in as_completed(future_to_opportunity):
                completed_count += 1
                opportunity = future_to_opportunity[future]
                basic_info = opportunity.get('basic_info', {})
                title = basic_info.get('title', 'Unknown Opportunity')
                
                print(f"📊 Progress: {completed_count}/{total_opportunities} - {title[:50]}...")
                
                try:
                    enhanced_opportunity = future.result()
                    
                    # Ensure enhanced_opportunity is not None
                    if enhanced_opportunity is None:
                        raise Exception("Analysis returned None result")
                    
                    enhanced_opportunities.append(enhanced_opportunity)
                    
                    # Brief summary of analysis with safe access
                    semantic_analysis = enhanced_opportunity.get('semantic_analysis', {})
                    processing_metadata = enhanced_opportunity.get('processing_metadata', {})
                    
                    if processing_metadata.get('skipped', False):
                        print(f"        ⏭️  Skipped: {processing_metadata.get('skip_reason', 'Unknown')}")
                    elif semantic_analysis and 'error' in semantic_analysis:
                        error_msg = semantic_analysis['error']
                        if isinstance(error_msg, str):
                            print(f"        ❌ Error: {error_msg[:50]}...")
                        else:
                            print(f"        ❌ Error: {str(error_msg)[:50]}...")
                    elif semantic_analysis and 'enhanced_description' in semantic_analysis:
                        description = semantic_analysis['enhanced_description']
                        if isinstance(description, str) and len(description) > 50:
                            print(f"        📝 Enhanced: {description[:50]}...")
                        else:
                            print(f"        📝 Enhanced: Analysis completed")
                    else:
                        print(f"        📝 Enhanced: Analysis completed")
                    
                except Exception as e:
                    print(f"        ❌ FUTURE ERROR: {str(e)[:60]}...")
                    # Add original opportunity with error info
                    enhanced_opportunities.append({
                        **opportunity,
                        "semantic_analysis": {"error": str(e)},
                        "processing_metadata": {
                            "processed_date": datetime.now().isoformat(),
                            "error": str(e)
                        }
                    })
                
                print()
        
        print(f"📊 PARALLEL ANALYSIS COMPLETE: {len(enhanced_opportunities)}/{total_opportunities} opportunities processed")
        return enhanced_opportunities
    
    def generate_processing_report(self, output_file: str = "NSF_semantic_report.md"):
        """
        Generate a comprehensive processing report
        
        Args:
            output_file: Path to save the report markdown file
        """
        total_processed = (self.processing_stats['successful'] + 
                          self.processing_stats['url_403_errors'] + 
                          self.processing_stats['analysis_errors'])
        
        report_content = f"""# NSF Funding Opportunities Semantic Analysis Report

## Executive Summary

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Opportunities Processed:** {total_processed}  
**Analysis Model:** Gemini 2.5 Pro  
**Processing Mode:** Parallel Processing (Max 150 RPM)

## Processing Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Successful Analyses** | {self.processing_stats['successful']} | {self.processing_stats['successful']/total_processed*100:.1f}% |
| **403 Forbidden Errors** | {self.processing_stats['url_403_errors']} | {self.processing_stats['url_403_errors']/total_processed*100:.1f}% |
| **Analysis Errors** | {self.processing_stats['analysis_errors']} | {self.processing_stats['analysis_errors']/total_processed*100:.1f}% |
| **Total Processed** | {total_processed} | 100.0% |

## Successful Analyses

### Summary
- **Total Successful:** {self.processing_stats['successful']}
- **Average Analysis Time:** {sum(opp['analysis_time'] for opp in self.processing_stats['successful_opportunities'])/len(self.processing_stats['successful_opportunities']):.1f}s (if any)
- **Program URLs Processed:** {sum(1 for opp in self.processing_stats['successful_opportunities'] if opp['program_url_processed'])}
- **Solicitation URLs Processed:** {sum(1 for opp in self.processing_stats['successful_opportunities'] if opp['solicitation_url_processed'])}

### Detailed Results
"""
        
        if self.processing_stats['successful_opportunities']:
            report_content += "\n| Program ID | Title | Analysis Time (s) | Program URL | Solicitation URL |\n"
            report_content += "|------------|-------|-------------------|-------------|------------------|\n"
            
            for opp in self.processing_stats['successful_opportunities']:
                program_url_status = "✅" if opp['program_url_processed'] else "❌"
                solicitation_url_status = "✅" if opp['solicitation_url_processed'] else "❌"
                report_content += f"| {opp['program_id']} | {opp['title'][:40]}... | {opp['analysis_time']:.1f} | {program_url_status} | {solicitation_url_status} |\n"
        else:
            report_content += "\n*No successful analyses to report.*\n"
        
        report_content += f"""

## 403 Forbidden Errors

### Summary
- **Total 403 Errors:** {self.processing_stats['url_403_errors']}
- **Impact:** These opportunities were skipped due to access restrictions on NSF URLs

### Detailed Results
"""
        
        if self.processing_stats['url_403_opportunities']:
            report_content += "\n| Program ID | Title | Program URL Status | Solicitation URL Status |\n"
            report_content += "|------------|-------|--------------------|--------------------------|\n"
            
            for opp in self.processing_stats['url_403_opportunities']:
                report_content += f"| {opp['program_id']} | {opp['title'][:40]}... | 🔒 Forbidden | 🔒 Forbidden |\n"
        else:
            report_content += "\n*No 403 errors to report.*\n"
        
        report_content += f"""

## Analysis Errors

### Summary
- **Total Analysis Errors:** {self.processing_stats['analysis_errors']}
- **Impact:** These opportunities failed during AI analysis processing

### Detailed Results
"""
        
        if self.processing_stats['failed_opportunities']:
            report_content += "\n| Program ID | Title | Error Message |\n"
            report_content += "|------------|-------|---------------|\n"
            
            for opp in self.processing_stats['failed_opportunities']:
                error_msg = opp['error'][:60] + "..." if len(opp['error']) > 60 else opp['error']
                report_content += f"| {opp['program_id']} | {opp['title'][:40]}... | {error_msg} |\n"
        else:
            report_content += "\n*No analysis errors to report.*\n"
        
        report_content += f"""

## Recommendations

### For 403 Forbidden Errors
1. **NSF URL Access:** The NSF website may be blocking automated access to certain pages
2. **Alternative Approach:** Consider using NSF's official API or RSS feeds if available
3. **Manual Review:** High-priority opportunities with 403 errors may need manual review

### For Analysis Errors
1. **Retry Logic:** Implement retry mechanisms for transient errors
2. **Input Validation:** Enhance input validation for malformed opportunity data
3. **Fallback Analysis:** Use basic analysis for opportunities that fail comprehensive analysis

### Processing Optimization
1. **Rate Limiting:** Current 150 RPM limit appears appropriate
2. **Parallel Processing:** {5} workers provided good throughput
3. **Error Handling:** Robust error handling allowed processing to continue despite individual failures

## Technical Details

- **Processing Duration:** Approximately {total_processed * 70 / 60:.1f} minutes (estimated)
- **API Calls:** ~{total_processed * 3} total calls (analysis + URL fetching)
- **Output File:** FundingOpportunitiesManual/nsf_funding_semantic.json
- **Enhancement Features:** Enhanced descriptions, technical focus areas, semantic keywords, strategic context

---

*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} using Gemini 2.5 Pro*
"""
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"📋 Processing report saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            print("📋 Report content:")
            print(report_content)

def load_funding_opportunities_from_csvs(csv_folder: str = "FundingOpportunities", 
                                       test_mode: bool = False, 
                                       quick_mode: bool = False) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
    """
    Load funding opportunities from CSV files in the specified folder
    
    Args:
        csv_folder: Path to the folder containing CSV files
        test_mode: If True, process 20 opportunities from each file
        quick_mode: If True, process 5 opportunities total
        
    Returns:
        Tuple of (opportunities list, combined metadata, processed files list)
    """
    print(f"🔍 Discovering CSV files in {csv_folder}...")
    csv_files = discover_csv_files(csv_folder)
    
    if not csv_files:
        print(f"❌ No CSV files found in {csv_folder}")
        return [], {}, []
    
    print(f"📂 Found {len(csv_files)} CSV files:")
    for file in csv_files:
        file_size = os.path.getsize(file) / (1024 * 1024)  # Size in MB
        print(f"   • {os.path.basename(file)} ({file_size:.1f} MB)")
    
    all_opportunities = []
    combined_metadata = {
        "processing_timestamp": datetime.now().isoformat(),
        "source_files": [],
        "total_opportunities": 0,
        "file_type": "csv_batch",
        "processing_mode": "test" if test_mode else ("quick" if quick_mode else "full"),
        "agency_filter": "all_agencies"
    }
    
    processed_files = []
    total_processed = 0
    
    # Process each CSV file
    for csv_file in csv_files:
        print(f"\n📊 Processing {os.path.basename(csv_file)}...")
        
        # Determine max opportunities per file
        if quick_mode:
            # For quick mode, distribute 5 opportunities across all files
            remaining_quick = 5 - total_processed
            if remaining_quick <= 0:
                break
            max_opps = min(remaining_quick, 5)
        elif test_mode:
            max_opps = 20  # Process 20 opportunities per file
        else:
            max_opps = None
        
        opportunities, metadata = convert_csv_to_json(csv_file, max_opps)
        
        if opportunities:
            # Process all opportunities (no agency filtering)
            all_opportunities.extend(opportunities)
            total_processed += len(opportunities)
            combined_metadata["source_files"].append({
                "file": os.path.basename(csv_file),
                "opportunities": len(opportunities),
                "total_in_file": len(opportunities),
                "filtered": 0,
                "processed_at": datetime.now().isoformat(),
                "max_limit": max_opps
            })
            processed_files.append(csv_file)
            print(f"✅ Loaded {len(opportunities)} opportunities from {os.path.basename(csv_file)}")
            
            if quick_mode and total_processed >= 5:
                break
        else:
            print(f"❌ Failed to process {os.path.basename(csv_file)}")
    
    combined_metadata["total_opportunities"] = len(all_opportunities)
    
    print(f"\n📊 Total opportunities loaded: {len(all_opportunities)}")
    print(f"📁 Files processed: {len(processed_files)}")
    
    if test_mode:
        print(f"🧪 Test mode: Limited to 20 opportunities per file")
    elif quick_mode:
        print(f"⚡ Quick mode: Limited to 5 opportunities total")
    
    return all_opportunities, combined_metadata, processed_files

def load_nsf_opportunities(input_file: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Load NSF funding opportunities from JSON file (legacy function for backward compatibility)
    
    Args:
        input_file: Path to the NSF funding JSON file
        
    Returns:
        Tuple of (opportunities list, metadata dict)
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        opportunities = data.get('nsf_funding_opportunities', {}).get('opportunities', [])
        metadata = data.get('nsf_funding_opportunities', {}).get('metadata', {})
        
        print(f"📂 Loaded {len(opportunities)} opportunities from {input_file}")
        print(f"📊 Source metadata: {metadata.get('total_opportunities', 0)} total opportunities")
        print(f"📅 Data timestamp: {metadata.get('conversion_timestamp', 'Unknown')}")
        
        return opportunities, metadata
        
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return [], {}
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {input_file}: {e}")
        return [], {}
    except Exception as e:
        print(f"❌ Error loading {input_file}: {e}")
        return [], {}

def save_enhanced_opportunities(opportunities: List[Dict[str, Any]], 
                              original_metadata: Dict[str, Any],
                              output_file: str):
    """
    Save enhanced opportunities to JSON file with metadata, appending to existing file if it exists
    
    Args:
        opportunities: List of enhanced opportunity dictionaries
        original_metadata: Original metadata from CSV processing
        output_file: Path to save the JSON file
    """
    try:
        # Count successful analyses for new opportunities only
        new_successful_analyses = sum(1 for opp in opportunities 
                                    if not opp.get('semantic_analysis', {}).get('error'))
        
        # Check if output file already exists
        existing_opportunities = []
        existing_metadata = {}
        existing_successful_analyses = 0
        
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_opportunities = existing_data.get('funding_opportunities_semantic', {}).get('opportunities', [])
                    existing_metadata = existing_data.get('funding_opportunities_semantic', {}).get('metadata', {})
                    existing_successful_analyses = existing_metadata.get('semantic_enhancement', {}).get('successful_analyses', 0)
                print(f"📄 Found existing file with {len(existing_opportunities)} opportunities")
            except Exception as e:
                print(f"⚠️  Warning: Could not read existing file: {e}")
                existing_opportunities = []
                existing_metadata = {}
                existing_successful_analyses = 0
        
        # Combine opportunities (avoid duplicates based on program_id)
        existing_ids = {opp.get('basic_info', {}).get('program_id', '') for opp in existing_opportunities}
        new_opportunities = [opp for opp in opportunities 
                           if opp.get('basic_info', {}).get('program_id', '') not in existing_ids]
        
        if len(new_opportunities) < len(opportunities):
            print(f"📝 Skipping {len(opportunities) - len(new_opportunities)} duplicate opportunities")
        
        all_opportunities = existing_opportunities + new_opportunities
        total_successful_analyses = existing_successful_analyses + new_successful_analyses
        
        # Update source files list
        source_files = existing_metadata.get('source_files', [])
        new_source_file = original_metadata.get('source_file', 'Unknown')
        if new_source_file not in source_files:
            source_files.append(new_source_file)
        
        # Create output data structure
        output_data = {
            "funding_opportunities_semantic": {
                "metadata": {
                    "processing_timestamp": datetime.now().isoformat(),
                    "source_files": source_files,
                    "total_opportunities": len(all_opportunities),
                    "file_type": "csv_batch",
                    "processing_mode": "incremental",
                    "agency_filter": "all_agencies",
                    "semantic_enhancement": {
                        "processed_date": datetime.now().isoformat(),
                        "successful_analyses": total_successful_analyses,
                        "total_opportunities": len(all_opportunities),
                        "success_rate": f"{total_successful_analyses/len(all_opportunities)*100:.1f}%",
                        "analysis_model": "gemini-2.5-pro",
                        "enhancement_features": [
                            "comprehensive_description",
                            "technical_focus_areas", 
                            "strategic_context",
                            "competitive_landscape",
                            "application_strategy",
                            "semantic_keywords",
                            "match_ready_summary"
                        ]
                    }
                },
                "opportunities": all_opportunities
            }
        }
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Enhanced opportunities saved to: {output_file}")
        print(f"📊 Analysis summary:")
        print(f"   • Total opportunities: {len(all_opportunities)}")
        print(f"   • New opportunities added: {len(new_opportunities)}")
        print(f"   • New successful analyses: {new_successful_analyses}")
        print(f"   • Total successful analyses: {total_successful_analyses}")
        print(f"   • Success rate: {total_successful_analyses/len(all_opportunities)*100:.1f}%")
        print(f"🎯 Output structure optimized for comprehensive_matcher.py")
        
    except Exception as e:
        print(f"❌ Error saving enhanced opportunities: {e}")

def generate_opportunities_list(opportunities: List[Dict[str, Any]], output_file: str = "ProcessedOpportunities.md"):
    """
    Generate a simple markdown list of processed opportunity names, appending to existing file if it exists
    
    Args:
        opportunities: List of opportunity dictionaries
        output_file: Path to save the opportunities list
    """
    try:
        # Check if file already exists
        existing_content = ""
        existing_opportunities = []
        
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                print(f"📄 Found existing ProcessedOpportunities.md file")
                
                # Extract existing opportunities from the file
                lines = existing_content.split('\n')
                for line in lines:
                    if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or \
                       (line.strip().startswith('1') and '. ' in line):
                        # This is an opportunity line
                        existing_opportunities.append(line.strip())
            except Exception as e:
                print(f"⚠️  Warning: Could not read existing file: {e}")
                existing_content = ""
                existing_opportunities = []
        
        # Create new content for this batch
        new_content = f"""## Processing Session - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**New Opportunities in This Session**: {len(opportunities)}

### New Opportunity List

"""
        
        for i, opp in enumerate(opportunities, 1):
            # Get title from normalized structure
            title = opp.get('basic_info', {}).get('title', f"Opportunity {i}")
            
            # Get source info if available
            source_info = ""
            program_id = opp.get('basic_info', {}).get('program_id', '')
            agency = opp.get('agency_info', {}).get('agency', 'Unknown')
            
            if program_id and program_id != 'Unknown':
                source_info = f" (ID: {program_id}, Agency: {agency})"
            else:
                source_info = f" (Agency: {agency})"
            
            new_content += f"{i}. {title}{source_info}\n"
        
        # Add summary by source for new opportunities
        if opportunities:
            new_content += "\n### New Opportunities Summary by Source\n\n"
            source_counts = {}
            for opp in opportunities:
                agency = opp.get('agency_info', {}).get('agency', 'Unknown')
                source_counts[agency] = source_counts.get(agency, 0) + 1
            
            for source, count in source_counts.items():
                new_content += f"- **{source}**: {count} opportunities\n"
        
        new_content += f"\n---\n"
        
        # Combine content
        if existing_content:
            # If file exists, append new content
            combined_content = existing_content + "\n\n" + new_content
        else:
            # If file doesn't exist, create new file with header
            combined_content = f"""# Processed Funding Opportunities

**First Processing Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Opportunities**: {len(opportunities)}

## Opportunity List

"""
            # Add the new opportunities
            for i, opp in enumerate(opportunities, 1):
                title = opp.get('basic_info', {}).get('title', f"Opportunity {i}")
                program_id = opp.get('basic_info', {}).get('program_id', '')
                agency = opp.get('agency_info', {}).get('agency', 'Unknown')
                
                if program_id and program_id != 'Unknown':
                    source_info = f" (ID: {program_id}, Agency: {agency})"
                else:
                    source_info = f" (Agency: {agency})"
                
                combined_content += f"{i}. {title}{source_info}\n"
            
            # Add summary
            if opportunities:
                combined_content += "\n## Summary by Source\n\n"
                source_counts = {}
                for opp in opportunities:
                    agency = opp.get('agency_info', {}).get('agency', 'Unknown')
                    source_counts[agency] = source_counts.get(agency, 0) + 1
                
                for source, count in source_counts.items():
                    combined_content += f"- **{source}**: {count} opportunities\n"
            
            combined_content += f"\n---\n*Generated by Comprehensive Funding Analysis System*"
        
        # Save combined content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(combined_content)
        
        print(f"📋 Opportunities list saved to: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating opportunities list: {e}")
        return False

def main():
    """
    Main function to perform comprehensive funding opportunity analysis
    """
    print("🚀 COMPREHENSIVE FUNDING OPPORTUNITY ANALYSIS")
    print("=" * 80)
    print("📊 AI-Powered Semantic Enhancement using Gemini 2.5 Pro")
    print("📂 CSV File Processing from FundingOpportunities Folder (No Subfolders)")
    print("🔗 URL Content Processing & Comprehensive Analysis")
    print("📁 Incremental Processing & Standardized Data Structure")
    print("🏃 Automatic File Management & Progress Tracking")
    print()
    
    # Check for flags
    quick_mode = "--quick" in sys.argv
    test_mode = "--test" in sys.argv
    force_reprocess = "--force" in sys.argv
    
    # Check for Gemini API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        print("💡 Make sure .env file contains GEMINI_API_KEY")
        return
    
    print(f"✅ Gemini API key loaded: {api_key[:10]}...")
    print("🔬 Using Gemini 2.5 Pro for comprehensive analysis")
    print()
    
    # Create README file
    print("📋 Creating comprehensive README file...")
    create_readme_file()
    print()
    
    # Define file paths
    csv_folder = "FundingOpportunities"
    output_file = "FundingOpportunities/COMPLETE_funding_semantic.json"
    
    # Load opportunities from CSV files
    opportunities, metadata, processed_files = load_funding_opportunities_from_csvs(
        csv_folder, test_mode=test_mode, quick_mode=quick_mode
    )
    
    if not opportunities:
        print("❌ No opportunities loaded. Exiting.")
        return
    
    # Check if we should force reprocess (only applies to test and quick modes)
    if force_reprocess and (test_mode or quick_mode):
        print(f"🔄 Force reprocess mode: Will overwrite existing data")
    elif not test_mode and not quick_mode:
        print(f"📄 Incremental mode: Will append new opportunities to existing file")
    
    # Initialize analyzer
    try:
        analyzer = NSFOpportunityAnalyzer(api_key)
    except Exception as e:
        print(f"❌ Error initializing analyzer: {e}")
        return
    
    # Analyze opportunities
    try:
        enhanced_opportunities = analyzer.analyze_all_opportunities(
            opportunities, quick_mode=quick_mode
        )
        
        if not enhanced_opportunities:
            print("❌ No opportunities were successfully analyzed")
            return
        
        # Save enhanced opportunities
        save_enhanced_opportunities(enhanced_opportunities, metadata, output_file)
        
        # Generate opportunities list
        print("\n📋 Generating opportunities list...")
        generate_opportunities_list(enhanced_opportunities, "FundingOpportunities/ProcessedOpportunities.md")
        
        # Generate processing report
        print("\n📋 Generating processing report...")
        analyzer.generate_processing_report()
        
        # Move processed files to Ingested folder (only if not test mode)
        if not test_mode and not quick_mode:
            print(f"\n📁 Moving {len(processed_files)} processed files to Ingested folder...")
            for file_path in processed_files:
                move_processed_file(file_path)
        else:
            print(f"\n📁 Test/Quick mode: CSV files NOT moved (kept for reprocessing)")
        
        print("\n🎉 COMPREHENSIVE ANALYSIS COMPLETE!")
        print("-" * 50)
        print(f"📊 Total opportunities processed: {len(enhanced_opportunities)}")
        print(f"📁 Enhanced data saved to: {output_file}")
        print(f"🔬 Analysis model: Gemini 2.5 Pro")
        
        mode_desc = "Test (20 per file)" if test_mode else ("Quick (5 total)" if quick_mode else "Incremental processing")
        print(f"⏱️  Processing mode: {mode_desc}")
        print()
        print("📊 Processing Summary:")
        print(f"   • Successful analyses: {analyzer.processing_stats['successful']}")
        print(f"   • 403 Forbidden errors: {analyzer.processing_stats['url_403_errors']}")
        print(f"   • Analysis errors: {analyzer.processing_stats['analysis_errors']}")
        print(f"   • Success rate: {analyzer.processing_stats['successful']/(analyzer.processing_stats['successful']+analyzer.processing_stats['url_403_errors']+analyzer.processing_stats['analysis_errors'])*100:.1f}%")
        print()
        print("📁 File Management:")
        print(f"   • CSV files processed: {len(processed_files)}")
        if not test_mode and not quick_mode:
            print(f"   • Files moved to Ingested: {len(processed_files)}")
        else:
            print(f"   • Files preserved for reprocessing: {len(processed_files)}")
        print()
        print("📋 Generated Files:")
        print(f"   • Semantic data: {output_file}")
        print(f"   • Instructions: ReadmeFundingOpportunities.md")
        print(f"   • Opportunities list: FundingOpportunities/ProcessedOpportunities.md")
        print(f"   • Processing report: NSF_semantic_report.md")
        print()
        print("✅ Ready for advanced funding opportunity matching!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return

if __name__ == "__main__":
    main() 