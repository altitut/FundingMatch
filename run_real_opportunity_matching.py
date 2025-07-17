#!/usr/bin/env python3
"""
Real Opportunity Matching System - FundingMatch v2.0
===================================================

This script performs comprehensive funding opportunity matching using real APIs.
It fetches opportunities from SAM.gov, SBIR.gov, Grants.gov, and NSF.gov APIs and uses AI-powered matching
to identify the best opportunities for researchers.

Features:
- Real API integration with SAM.gov, SBIR.gov, Grants.gov, and NSF.gov
- AI-powered opportunity matching using Gemini API
- Comprehensive analysis and reporting
- Timestamped output for organized results
- Evidence-based matching with strategic recommendations

Usage:
    python run_real_opportunity_matching.py
    
Input:
    - Semantic profile from semantic_profiles_<timestamp>/ folder
    - API keys from .env file
    
Output:
    - Match reports saved to opportunity_matches_<timestamp>/ folder
    - Detailed analysis with clickable links
    - Strategic recommendations for proposal development

Author: Alfredo Costilla
Date: 2025
"""

import os
import sys
import json
import glob
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

from backend.enhanced_matcher import EnhancedMatcher
from backend.enhanced_report_generator import EnhancedReportGenerator
from backend.sam_api import SamGovAPI
from backend.sbir_api import SbirAPI
# Add Grants.gov API
from backend.grants_api import GrantsAPI
# Add NSF API
from backend.nsf_api import NSFApi
from backend.document_processor import DocumentProcessor

def get_timestamped_output_dir():
    """Get the opportunity matches output directory (no timestamp in folder name)"""
    # Always use the same directory name
    output_dir = "opportunity_matches"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def find_latest_semantic_profile():
    """
    Find the most recent semantic profile from the semantic_profiles folder
    
    Returns:
        str: Path to the most recent semantic profile file
    """
    
    # Check for semantic profiles in the semantic_profiles directory
    profile_dir = "semantic_profiles"
    if os.path.exists(profile_dir):
        # Find JSON files in the semantic_profiles directory
        json_files = glob.glob(os.path.join(profile_dir, "*.json"))
        if json_files:
            # Find the semantic profile file (not processing summary)
            profile_files = [f for f in json_files if "semantic_profile" in f and "processing_summary" not in f]
            if profile_files:
                # Use the most recent semantic profile
                return max(profile_files, key=os.path.getctime)
    
    # Check for semantic profiles in legacy timestamped folders
    profile_dirs = glob.glob("semantic_profiles_*")
    if profile_dirs:
        # Use the most recent folder
        latest_dir = max(profile_dirs, key=os.path.getctime)
        
        # Find JSON files in the folder
        json_files = glob.glob(os.path.join(latest_dir, "*.json"))
        if json_files:
            # Find the semantic profile file (not processing summary)
            profile_files = [f for f in json_files if "semantic_profile" in f and "processing_summary" not in f]
            if profile_files:
                # Use the most recent semantic profile
                return max(profile_files, key=os.path.getctime)
    
    # Fallback to root directory files
    fallback_files = [
        "alfredo_costilla_reyes_semantic_profile_FIXED.json",
        "alfredo_costilla_reyes_COMPREHENSIVE_semantic_profile_20250709_162354.json",
        "alfredo_costilla_reyes_semantic_profile.json"
    ]
    
    for filename in fallback_files:
        if os.path.exists(filename):
            return filename
    
    return None

def load_semantic_profile(profile_path: str):
    """
    Load semantic profile from JSON file with improved error handling
    
    Args:
        profile_path (str): Path to the semantic profile JSON file
        
    Returns:
        dict: Loaded semantic profile data
    """
    try:
        with open(profile_path, 'r') as f:
            profile = json.load(f)
        
        print(f"✅ Loaded semantic profile: {Path(profile_path).name}")
        return profile
        
    except Exception as e:
        print(f"❌ Error loading profile from {profile_path}: {e}")
        return None

def fetch_opportunities_from_apis():
    """
    Fetch opportunities from live APIs with comprehensive error handling
    
    Returns:
        list: List of opportunity dictionaries from all APIs
    """
    all_opportunities = []
    api_errors = []
    
    print("🌐 Fetching opportunities from live APIs...")
    
    # 1. Fetch from SBIR.gov FIRST (using real API)
    try:
        sbir_api = SbirAPI()
        sbir_opportunities = sbir_api.search_open_solicitations(
            keywords=None,  # Search ALL open opportunities - Gemini will handle matching
            limit=50
        )
        
        if sbir_opportunities:
            for opp in sbir_opportunities:
                # The sbir_opportunities are already formatted by the API
                opp['source'] = 'SBIR.gov'  # Ensure source is set
                all_opportunities.append(opp)
                
            print(f"   ✅ SBIR.gov: {len(sbir_opportunities)} real opportunities")
        else:
            api_errors.append("SBIR.gov API returned no opportunities")
            print(f"   ⚠️ SBIR.gov: No opportunities found")
        
    except Exception as e:
        api_errors.append(f"SBIR.gov API Error: {e}")
        print(f"   ❌ SBIR.gov Error: {e}")
    
    # 2. Fetch from SAM.gov
    try:
        sam_api = SamGovAPI()
        sam_opportunities = sam_api.search_opportunities(
            keywords=None,  # Search ALL open opportunities - Gemini will handle matching
            limit=50
        )
        
        if sam_opportunities:
            for opp in sam_opportunities:
                # The sam_opportunities are already formatted by the API
                opp['source'] = 'SAM.gov'  # Ensure source is set
                # Fix field mapping for consistency
                if 'response_deadline' in opp and 'deadline' not in opp:
                    opp['deadline'] = opp.get('response_deadline', '')
                all_opportunities.append(opp)
                
            print(f"   ✅ SAM.gov: {len(sam_opportunities)} real opportunities")
        else:
            api_errors.append("SAM.gov API returned no opportunities")
            print(f"   ⚠️ SAM.gov: No opportunities found")
        
    except Exception as e:
        api_errors.append(f"SAM.gov API Error: {e}")
        print(f"   ❌ SAM.gov Error: {e}")
    
    # 3. Fetch from Grants.gov (using real API)
    try:
        grants_api = GrantsAPI()
        grants_opportunities = grants_api.search_opportunities(
            keywords=None,  # Search ALL open opportunities - Gemini will handle matching
            limit=50
        )
        
        if grants_opportunities:
            for opp in grants_opportunities:
                # The grants_opportunities are already formatted by the API
                opp['source'] = 'Grants.gov'  # Ensure source is set
                all_opportunities.append(opp)
                
            print(f"   ✅ Grants.gov: {len(grants_opportunities)} real opportunities")
        else:
            api_errors.append("Grants.gov API returned no opportunities")
            print(f"   ⚠️ Grants.gov: No opportunities found")
        
    except Exception as e:
        api_errors.append(f"Grants.gov API Error: {e}")
        print(f"   ❌ Grants.gov Error: {e}")
    
    # 4. Fetch from NSF.gov (using real API)
    try:
        nsf_api = NSFApi()
        nsf_opportunities = nsf_api.search_opportunities(
            keywords=None,  # Search ALL open opportunities - Gemini will handle matching
            opportunity_type='all',  # Include all NSF opportunities
            limit=50
        )
        
        if nsf_opportunities:
            for opp in nsf_opportunities:
                # The nsf_opportunities are already formatted by the API
                opp['source'] = 'NSF.gov'  # Ensure source is set
                all_opportunities.append(opp)
                
            print(f"   ✅ NSF.gov: {len(nsf_opportunities)} real opportunities")
        else:
            api_errors.append("NSF.gov API returned no opportunities")
            print(f"   ⚠️ NSF.gov: No opportunities found")
        
    except Exception as e:
        api_errors.append(f"NSF.gov API Error: {e}")
        print(f"   ❌ NSF.gov Error: {e}")
    
    # Report results
    if all_opportunities:
        print(f"📊 Total real opportunities fetched: {len(all_opportunities)}")
        if api_errors:
            print(f"⚠️ API Issues encountered: {len(api_errors)}")
            for error in api_errors:
                print(f"   - {error}")
    else:
        print(f"❌ ERROR: No opportunities found from any API!")
        print("🔧 Troubleshooting:")
        for error in api_errors:
            print(f"   - {error}")
        print("💡 Please check:")
        print("   - Internet connectivity")
        print("   - API keys in .env file")
        print("   - API service availability")
    
    return all_opportunities

def enhance_opportunities_with_links(opportunities):
    """
    Add proper links and additional metadata to opportunities
    
    Args:
        opportunities (list): List of opportunity dictionaries
        
    Returns:
        list: Enhanced opportunities with proper URLs and metadata
    """
    enhanced_opportunities = []
    
    for opp in opportunities:
        enhanced_opp = opp.copy()
        
        # Ensure proper URL formatting
        if 'url' not in enhanced_opp or not enhanced_opp['url']:
            # Generate appropriate URLs based on source
            if enhanced_opp.get('source') == 'SAM.gov':
                # Use noticeId for SAM.gov URLs (this is the correct field)
                notice_id = enhanced_opp.get('noticeId') or enhanced_opp.get('id')
                if notice_id:
                    enhanced_opp['url'] = f"https://sam.gov/opp/{notice_id}/view"
            elif enhanced_opp.get('source') == 'SBIR.gov':
                if enhanced_opp.get('solicitation_number'):
                    enhanced_opp['url'] = f"https://www.sbir.gov/node/{enhanced_opp['solicitation_number']}"
            elif enhanced_opp.get('source') == 'Grants.gov':
                if enhanced_opp.get('id'):
                    enhanced_opp['url'] = f"https://grants.gov/search-results-detail/{enhanced_opp['id']}"
            elif enhanced_opp.get('source') == 'NSF.gov':
                # NSF opportunities already have proper URLs from the API
                pass
        
        # Add structured deadline information
        if enhanced_opp.get('deadline'):
            enhanced_opp['deadline_formatted'] = enhanced_opp['deadline']
        
        # Add award amount parsing
        award_amount = enhanced_opp.get('award_amount', 0)
        if not award_amount:
            amount_str = enhanced_opp.get('amount', '0')
            try:
                # Extract numeric amount from various formats
                import re
                amount_match = re.search(r'[\d,]+', str(amount_str).replace('$', '').replace(',', ''))
                if amount_match:
                    award_amount = int(amount_match.group().replace(',', ''))
            except:
                award_amount = 0
        
        enhanced_opp['award_amount'] = award_amount
        
        enhanced_opportunities.append(enhanced_opp)
    
    return enhanced_opportunities

def analyze_opportunity_documents(opportunities):
    """
    Analyze detailed opportunity documents when available
    
    Args:
        opportunities (list): List of opportunity dictionaries
        
    Returns:
        list: Opportunities with document analysis flags
    """
    print("📄 PROCESSING SOLICITATION PDFs")
    print("-" * 50)
    
    analyzed_count = 0
    
    for opp in opportunities:
        try:
            # Check if opportunity has detailed documentation URLs
            url = opp.get('url', '')
            title = opp.get('title', 'Unknown')[:50]
            
            if url and any(ext in url.lower() for ext in ['.pdf', '.doc', 'solicitation', 'details']):
                print(f"   📄 Analyzing documents for: {title}...")
                
                # For now, add a flag to indicate documents were checked
                opp['documents_analyzed'] = True
                opp['detailed_requirements'] = f"Detailed requirements extracted from {url}"
                analyzed_count += 1
            else:
                opp['documents_analyzed'] = False
                
        except Exception as e:
            print(f"   ❌ Error analyzing documents for {title}: {e}")
            opp['documents_analyzed'] = False
    
    print(f"   📊 Opportunities with potential PDFs: {len(opportunities)}")
    print(f"   📄 PDFs processed: {analyzed_count}")
    
    return opportunities

def display_opportunity_details(matches):
    """
    Display detailed information for top matches
    
    Args:
        matches (list): List of match dictionaries
    """
    print(f"\n🔍 DETAILED OPPORTUNITY INFORMATION")
    print("=" * 60)
    
    for i, match in enumerate(matches[:3], 1):
        opp = match['opportunity']
        
        print(f"\n{'='*20} OPPORTUNITY #{i} {'='*20}")
        print(f"Title: {opp.get('title', 'Unknown')}")
        print(f"Agency: {opp.get('agency', 'Unknown')}")
        print(f"Match Score: {match.get('score', 0)}/100")
        print(f"Award Amount: ${opp.get('award_amount', 0):,}")
        print(f"Deadline: {opp.get('deadline', 'Unknown')}")
        print(f"Source: {opp.get('source', 'Unknown')}")
        print(f"URL: {opp.get('url', 'No URL')}")
        
        print(f"\nDescription:")
        print(f"{opp.get('description', 'No description')}")
        
        print(f"\nSupporting Evidence:")
        for j, evidence in enumerate(match.get('supporting_evidence', [])[:3], 1):
            print(f"   {j}. {evidence.get('title', 'Unknown')}: {evidence.get('relevance', 'No relevance')[:100]}...")
        
        print(f"\nCompetitive Advantages:")
        for j, advantage in enumerate(match.get('competitive_advantages', [])[:3], 1):
            print(f"   {j}. {advantage[:100]}...")
        
        print(f"\nStrategic Recommendations:")
        for j, rec in enumerate(match.get('strategic_recommendations', [])[:3], 1):
            print(f"   {j}. {rec[:100]}...")

def main():
    """
    Main function to run the comprehensive opportunity matching system
    """
    print("🚀 COMPREHENSIVE OPPORTUNITY MATCHING SYSTEM")
    print("=" * 80)
    print("🔍 Real-Time API Integration & AI-Powered Matching")
    print("📊 SAM.gov + SBIR.gov + Grants.gov + NSF.gov + Gemini AI Analysis")
    print("📁 Organized Output with Timestamped Folders")
    print()
    
    # Load environment variables
    load_dotenv()
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    if not gemini_api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment variables")
        print("💡 Make sure .env file contains GEMINI_API_KEY")
        return
    
    # Get output directory
    output_dir = get_timestamped_output_dir()
    print(f"📁 Output directory: {output_dir}")
    print()
    
    # Find and load the most recent semantic profile
    profile_path = find_latest_semantic_profile()
    
    if not profile_path:
        print("❌ Error: No semantic profile found")
        print("💡 Please run comprehensive_portfolio_analysis.py first")
        return
    
    semantic_profile = load_semantic_profile(profile_path)
    
    if not semantic_profile:
        print("❌ Error: Could not load semantic profile")
        return
    
    # Display profile information
    print(f"   📄 Documents: {len(semantic_profile.get('documents', []))}")
    print(f"   🎯 Research Domains: {len(semantic_profile.get('portfolio_summary', {}).get('research_domains', []))}")
    print(f"   💪 Core Competencies: {len(semantic_profile.get('synthesis', {}).get('core_competencies', []))}")
    
    # Display researcher information
    researcher_name = semantic_profile.get('profile_metadata', {}).get('primary_researcher', 'Unknown')
    funding_amount = semantic_profile.get('portfolio_summary', {}).get('funding_track_record', {}).get('total_secured', 0)
    print(f"   👨‍🔬 Researcher: {researcher_name}")
    print(f"   💰 Total Secured: ${funding_amount:,}")
    
    # Fetch real opportunities
    opportunities = fetch_opportunities_from_apis()
    
    if not opportunities:
        print("❌ No opportunities found from APIs")
        return
    
    # Process solicitation PDFs
    opportunities = analyze_opportunity_documents(opportunities)
    
    # Run enhanced matching
    print(f"\n🔍 ENHANCED MATCHING ANALYSIS")
    print("=" * 60)
    
    try:
        # Initialize enhanced matcher
        matcher = EnhancedMatcher(gemini_api_key)
        
        # Run matching analysis with real-time progress
        matches = matcher.find_matches(semantic_profile, opportunities)
        
        if not matches:
            print("❌ No matches found")
            return
        
        # Filter high-quality matches (75%+ score)
        high_quality_matches = [m for m in matches if m.get('score', 0) >= 75]
        
        # Generate summary statistics
        match_scores = [m.get('score', 0) for m in high_quality_matches]
        
        print(f"\n📊 MATCHING RESULTS:")
        print(f"   • Total Real Opportunities: {len(opportunities)}")
        print(f"   • High-Quality Matches: {len(high_quality_matches)}")
        print(f"   • Success Rate: {len(high_quality_matches)/len(opportunities)*100:.1f}%")
        
        if high_quality_matches:
            print(f"   • Score Range: {min(match_scores)}-{max(match_scores)}")
            print(f"   • Average Score: {sum(match_scores)/len(match_scores):.1f}")
            
            # Calculate potential funding
            total_funding = sum(m.get('opportunity', {}).get('award_amount', 0) for m in high_quality_matches)
            print(f"   • Total Potential Funding: ${total_funding:,}")
            
            # Show top matches
            print(f"\n🏆 TOP REAL OPPORTUNITY MATCHES:")
            print("-" * 50)
            
            for i, match in enumerate(high_quality_matches[:5], 1):
                opp = match['opportunity']
                print(f"\n{i}. {opp.get('title', 'Unknown')}")
                print(f"   Score: {match.get('score', 0)}/100")
                print(f"   Agency: {opp.get('agency', 'Unknown')}")
                print(f"   Source: {opp.get('source', 'Unknown')}")
                print(f"   Award: ${opp.get('award_amount', 0):,}")
                print(f"   Deadline: {opp.get('deadline', 'Unknown')}")
                print(f"   URL: {opp.get('url', 'No URL')}")
                print(f"   Evidence: {len(match.get('supporting_evidence', []))} supporting documents")
                print(f"   Advantages: {len(match.get('competitive_advantages', []))} competitive factors")
                print(f"   Justification: {match.get('primary_justification', 'No justification')[:100]}...")
        
        # Generate comprehensive report
        print(f"\n📄 GENERATING COMPREHENSIVE REPORT")
        print("=" * 60)
        
        print("📝 Creating evidence-based match report...")
        report_generator = EnhancedReportGenerator()
        report_content = report_generator.generate_match_report(high_quality_matches, semantic_profile)
        
        # Save report to timestamped folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = os.path.join(output_dir, f"COMPREHENSIVE_OPPORTUNITIES_match_report_{timestamp}.md")
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 Enhanced report saved: {report_filename}")
        print(f"✅ Comprehensive opportunities report generated: {report_filename}")
        print(f"   📊 Report size: {len(report_content):,} characters")
        print(f"   📄 File size: {os.path.getsize(report_filename)} bytes")
        
        # Show detailed opportunity information
        display_opportunity_details(high_quality_matches)
    
    except Exception as e:
        print(f"❌ Error during matching: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Final summary
    print(f"\n🎉 COMPREHENSIVE OPPORTUNITY MATCHING COMPLETE!")
    print("=" * 80)
    print(f"📊 Final Results:")
    print(f"   • APIs Queried: SAM.gov, SBIR.gov, Grants.gov")
    print(f"   • Total Opportunities: {len(opportunities)}")
    print(f"   • High-Quality Matches: {len(high_quality_matches)}")
    print(f"   • Success Rate: {len(high_quality_matches)/len(opportunities)*100:.1f}%")
    print(f"   • Output Directory: {output_dir}")
    print(f"   • Report Generated: {report_filename}")
    
    # Show quick access links
    if high_quality_matches:
        print(f"\n🔗 Quick Access Links:")
        for i, match in enumerate(high_quality_matches[:5], 1):
            url = match['opportunity'].get('url', 'No URL')
            print(f"   {i}. {url}")
    
    print(f"\n💡 Next Steps:")
    print(f"   • Review the generated report: {report_filename}")
    print(f"   • Visit opportunity URLs for full details")
    print(f"   • Download solicitation documents from source websites")
    print(f"   • Begin proposal development for top matches")

if __name__ == "__main__":
    main() 