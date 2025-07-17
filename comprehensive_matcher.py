#!/usr/bin/env python3
"""
NSF Comprehensive Opportunity Matcher V6
=======================================

Simplified and improved semantic matching system with:
- Gemini 2.5 Pro for comprehensive analysis
- Processes 50 opportunities at a time (no token restrictions)
- Detailed Results table at the top of the report
- Saves high-scoring opportunities (≥70%) to separate JSON file
- Better formatted output with proper analysis summaries
- Enhanced semantic NSF funding opportunities data

Features:
- Uses FundingOpportunitiesManual/nsf_funding_semantic.json
- Deep semantic analysis with Alfredo's comprehensive profile
- Saves selected opportunities to nsf_funding_semantic_SELECTED.json
- Clean, user-friendly report format
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from pathlib import Path
import logging
from dotenv import load_dotenv
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class HighPerformanceRateLimiter:
    """
    Thread-safe rate limiter for Gemini 2.5 Pro API compliance.
    
    Implements a sliding window rate limiting algorithm to ensure we don't exceed
    the 60 requests per minute limit for Gemini 2.5 Pro. This is critical for
    batch processing multiple opportunities without hitting API rate limits.
    """
    
    def __init__(self, max_requests_per_minute=60):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests_per_minute (int): Maximum requests allowed per minute (default: 60 for Gemini 2.5 Pro)
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.min_interval = 60.0 / max_requests_per_minute
        self.request_times = []
        self.lock = threading.Lock()
    
    def acquire(self):
        """
        Acquire permission to make a request with rate limiting.
        
        This method implements a sliding window rate limiting algorithm:
        1. Removes old requests outside the 60-second window
        2. Checks if we can make the request without exceeding rate limit
        3. If at limit, waits until we can make the request
        4. Records the current request timestamp
        
        Thread-safe implementation using locks for concurrent batch processing.
        """
        with self.lock:
            now = time.time()
            
            # Remove old requests outside the 60-second window
            cutoff = now - 60
            self.request_times = [t for t in self.request_times if t > cutoff]
            
            # Check if we can make the request
            if len(self.request_times) >= self.max_requests_per_minute:
                # Wait until we can make the request
                oldest_request = self.request_times[0]
                wait_time = 60 - (now - oldest_request)
                if wait_time > 0:
                    time.sleep(wait_time)
                    # Re-filter after waiting
                    now = time.time()
                    cutoff = now - 60
                    self.request_times = [t for t in self.request_times if t > cutoff]
            
            # Record this request
            self.request_times.append(now)

class ComprehensiveFundingMatcher:
    """
    Advanced funding opportunity matcher using Gemini 2.5 Pro for semantic analysis.
    
    This class provides comprehensive matching capabilities between researcher profiles
    and funding opportunities using pre-processed semantic data. Key features:
    
    - Batch processing of opportunities (50 per batch with 3 workers each)
    - Rate-limited API calls to comply with Gemini 2.5 Pro limits (60 RPM)
    - Deep semantic analysis of opportunity-profile compatibility
    - Proposal matching recommendations from successful/unsuccessful submissions
    - Detailed reporting with ranked results and strategic recommendations
    - Export of high-scoring opportunities (≥70%) for follow-up
    """
    
    def __init__(self, gemini_api_key: str):
        """
        Initialize the NSF Semantic Matcher with Gemini 2.5 Pro integration.
        
        Args:
            gemini_api_key (str): API key for Google Gemini 2.5 Pro model
            
        Raises:
            Exception: If Gemini API configuration fails
        """
        self.gemini_api_key = gemini_api_key
        self.rate_limiter = HighPerformanceRateLimiter(max_requests_per_minute=60)
        
        # Initialize Gemini 2.5 Pro
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-2.5-pro")
            logger.info("✅ Gemini 2.5 Pro configured for enhanced semantic matching")
        except Exception as e:
            logger.error(f"❌ Gemini configuration failed: {e}")
            raise
    
    def load_semantic_profile(self, profile_path: str) -> Dict[str, Any]:
        """
        Load and parse comprehensive semantic profile generated by the portfolio analysis system.
        
        This method loads a researcher's semantic profile containing analyzed documents including:
        - CV and biographical information
        - Successful and unsuccessful proposals with detailed analysis
        - Research papers and publications
        - Technical expertise and research domains
        - Funding history and track record
        
        Args:
            profile_path (str): Path to the semantic profile JSON file
            
        Returns:
            Dict[str, Any]: Complete semantic profile data structure
            
        Raises:
            Exception: If profile file cannot be loaded or parsed
        """
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            researcher_name = profile.get('profile_metadata', {}).get('primary_researcher', 'Unknown')
            total_docs = profile.get('profile_metadata', {}).get('total_documents', 0)
            logger.info(f"✅ Loaded comprehensive semantic profile for {researcher_name} ({total_docs} documents)")
            return profile
        except Exception as e:
            logger.error(f"❌ Failed to load semantic profile: {e}")
            raise
    
    def load_semantic_opportunities(self, opportunities_path: str) -> List[Dict[str, Any]]:
        """
        Load enhanced semantic funding opportunities dataset.
        
        This method loads the pre-processed funding opportunities containing:
        - Basic opportunity information (title, program ID, dates, etc.)
        - Detailed opportunity requirements and research areas
        - Enhanced semantic analysis of opportunity content
        - Program and solicitation URLs for direct access
        - Categorization and research domain classifications
        
        Args:
            opportunities_path (str): Path to the semantic opportunities JSON file
            
        Returns:
            List[Dict[str, Any]]: List of enhanced opportunity dictionaries
            
        Raises:
            Exception: If opportunities file cannot be loaded or parsed
        """
        try:
            with open(opportunities_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            opportunities = data.get('funding_opportunities_semantic', {}).get('opportunities', [])
            metadata = data.get('funding_opportunities_semantic', {}).get('metadata', {})
            
            successful_analyses = metadata.get('semantic_enhancement', {}).get('successful_analyses', 0)
            total_opportunities = len(opportunities)
            
            logger.info(f"✅ Loaded {total_opportunities} semantic opportunities ({successful_analyses} with full analysis)")
            return opportunities
        except Exception as e:
            logger.error(f"❌ Failed to load semantic opportunities: {e}")
            raise
    
    def extract_profile_summary(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract comprehensive profile summary optimized for opportunity matching.
        
        This method processes the full semantic profile to create a structured summary
        that's optimized for matching against funding opportunities. It extracts:
        
        - Researcher biographical and career information
        - Technical expertise and areas of specialization
        - Research domains and publication metrics
        - Successful proposals with funding amounts and innovations
        - Unsuccessful proposals with reusable components
        - Funding history and track record
        
        Args:
            profile (Dict[str, Any]): Complete semantic profile from load_semantic_profile
            
        Returns:
            Dict[str, Any]: Structured summary containing:
                - researcher_info: Basic researcher information and metrics
                - technical_expertise: List of technical areas and specializations
                - research_domains: Primary research domains
                - successful_proposals: List of funded proposals with details
                - unsuccessful_proposals: List of unfunded proposals for reuse analysis
                - publication_record: Publication metrics and impact
        """
        summary = {
            'researcher_info': {},
            'technical_expertise': [],
            'research_domains': [],
            'successful_proposals': [],
            'unsuccessful_proposals': [],
            'funding_history': [],
            'key_innovations': [],
            'collaboration_experience': [],
            'publication_record': {}
        }
        
        try:
            # Basic researcher info
            metadata = profile.get('profile_metadata', {})
            portfolio = profile.get('portfolio_summary', {})
            
            summary['researcher_info'] = {
                'name': metadata.get('primary_researcher', 'Unknown'),
                'career_stage': portfolio.get('career_stage', 'Unknown'),
                'total_funding': portfolio.get('funding_track_record', {}).get('total_secured', 0),
                'successful_proposals_count': portfolio.get('funding_track_record', {}).get('successful_proposals', 0)
            }
            
            summary['research_domains'] = portfolio.get('research_domains', [])
            summary['publication_record'] = portfolio.get('publication_metrics', {})
            
            # Extract from documents
            documents = profile.get('documents', [])
            for doc in documents:
                source_file = doc.get('source_file', 'Unknown')
                doc_type = doc.get('document_type', 'Unknown')
                analysis = doc.get('analysis', {})
                
                if doc_type == 'Curriculum Vitae':
                    cv_analysis = analysis.get('CurriculumVitae', {})
                    
                    # Technical expertise
                    tech_expertise = cv_analysis.get('research_technical_expertise', {})
                    summary['technical_expertise'].extend(tech_expertise.get('areas_of_specialization', []))
                    summary['technical_expertise'].extend(tech_expertise.get('domain_expertise', []))
                    
                elif doc_type == 'Successful Proposal':
                    proposal_analysis = analysis.get('successfulProposalAnalysis', {})
                    summary['successful_proposals'].append({
                        'source_file': source_file,
                        'title': proposal_analysis.get('project_overview', {}).get('title', 'Unknown'),
                        'agency': proposal_analysis.get('project_overview', {}).get('target_agency', 'Unknown'),
                        'amount': proposal_analysis.get('project_overview', {}).get('award_amount', 0),
                        'innovation_claims': proposal_analysis.get('innovation_and_impact', {}).get('innovation_claims', ''),
                        'technical_approach': proposal_analysis.get('technical_approach', {}).get('novel_methodologies', ''),
                        'abstract': proposal_analysis.get('comprehensive_abstract', '')
                    })
                    
                elif doc_type == 'Unsuccessful Proposal':
                    proposal_analysis = analysis.get('unsuccessfulProposalAnalysis', {})
                    summary['unsuccessful_proposals'].append({
                        'source_file': source_file,
                        'title': proposal_analysis.get('project_details', {}).get('title', 'Unknown'),
                        'agency': proposal_analysis.get('project_details', {}).get('target_agency', 'Unknown'),
                        'amount': proposal_analysis.get('project_details', {}).get('requested_amount', 0),
                        'technical_approach': proposal_analysis.get('technical_approach', {}).get('core_technical_approach', ''),
                        'reusable_components': proposal_analysis.get('reusable_components', {}),
                        'abstract': proposal_analysis.get('comprehensive_abstract', '')
                    })
            
            # Remove duplicates and clean up
            summary['technical_expertise'] = list(set(filter(None, summary['technical_expertise'])))
            
            logger.info(f"✅ Extracted profile summary: {len(summary['successful_proposals'])} successful, {len(summary['unsuccessful_proposals'])} unsuccessful proposals")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error extracting profile summary: {e}")
            return summary
    
    def create_comprehensive_matching_prompt(self, opportunity: Dict[str, Any], profile_summary: Dict[str, Any]) -> str:
        """Create comprehensive matching prompt for Gemini 2.5 Pro"""
        
        # Extract opportunity details
        basic_info = opportunity.get('basic_info', {})
        opportunity_details = opportunity.get('opportunity_details', {})
        semantic_analysis = opportunity.get('semantic_analysis', {})
        urls = opportunity.get('urls', {})
        
        # Create a concise but comprehensive prompt
        prompt = f"""
        COMPREHENSIVE NSF FUNDING OPPORTUNITY MATCHING ANALYSIS
        
        OPPORTUNITY DETAILS:
        Title: {basic_info.get('title', 'Unknown')}
        Program ID: {basic_info.get('program_id', 'Unknown')}
        NSF Program Number: {basic_info.get('nsf_program_number', 'Unknown')}
        Status: {basic_info.get('status', 'Unknown')}
        Posted Date: {basic_info.get('posted_date', 'Unknown')}
        
        Program URL: {urls.get('program_url', 'Not available')}
        Solicitation URL: {urls.get('solicitation_url', 'Not available')}
        
        Synopsis: {opportunity_details.get('synopsis', 'Not available')[:2000]}
        
        Key Requirements: {opportunity_details.get('key_requirements', [])}
        Research Areas: {opportunity.get('categorization', {}).get('research_areas', [])}
        Award Types: {opportunity_details.get('award_types', [])}
        Due Dates: {opportunity_details.get('due_dates', [])}
        
        ENHANCED SEMANTIC ANALYSIS (if available):
        {json.dumps(semantic_analysis.get('enhanced_opportunity_profile', {}), indent=1) if semantic_analysis else 'No enhanced analysis available'}
        
        RESEARCHER PROFILE:
        Name: {profile_summary['researcher_info']['name']}
        Career Stage: {profile_summary['researcher_info']['career_stage']}
        Total Funding Secured: ${profile_summary['researcher_info']['total_funding']:,}
        Successful Proposals: {profile_summary['researcher_info']['successful_proposals_count']}
        
        Research Domains: {', '.join(profile_summary['research_domains'])}
        Key Technical Expertise: {', '.join(profile_summary['technical_expertise'][:15])}
        
        SUCCESSFUL PROPOSALS (for adaptation reference):
        {json.dumps([{'file': p['source_file'].split('/')[-1], 'title': p['title'], 'agency': p['agency'], 'amount': p['amount']} for p in profile_summary['successful_proposals'][:5]], indent=1)}
        
        UNSUCCESSFUL PROPOSALS (for learning/adaptation):
        {json.dumps([{'file': p['source_file'].split('/')[-1], 'title': p['title'], 'agency': p['agency']} for p in profile_summary['unsuccessful_proposals'][:10]], indent=1)}
        
        ANALYSIS REQUIREMENTS:
        
        Please provide a comprehensive JSON response with the following structure:
        {{
            "compatibility_score": <integer from 0-100>,
            "one_sentence_summary": "<concise explanation of why this is or isn't a match>",
            "detailed_analysis": {{
                "technical_alignment": "<how researcher's technical skills match opportunity requirements>",
                "research_domain_match": "<alignment between researcher's domains and opportunity focus>",
                "experience_relevance": "<relevance of previous work and funding success>",
                "innovation_potential": "<potential for innovative contributions to this opportunity>"
            }},
            "proposal_matching": {{
                "best_adaptable_proposals": [
                    {{
                        "proposal_file": "<filename>",
                        "adaptation_strategy": "<how to adapt this proposal>",
                        "reusable_elements": "<what can be reused>"
                    }}
                ],
                "strategic_positioning": "<overall strategy for competitive proposal>"
            }},
            "success_factors": [
                "<key factor 1>",
                "<key factor 2>",
                "<key factor 3>"
            ],
            "challenges_and_gaps": [
                "<challenge 1>",
                "<challenge 2>"
            ]
        }}
        
        Focus on actionable insights and specific recommendations.
        """
        
        return prompt
    
    def analyze_opportunity_match(self, opportunity: Dict[str, Any], profile_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze opportunity match using Gemini 2.5 Pro"""
        
        basic_info = opportunity.get('basic_info', {})
        title = basic_info.get('title', 'Unknown Opportunity')
        urls = opportunity.get('urls', {})
        
        try:
            # Create comprehensive prompt
            prompt = self.create_comprehensive_matching_prompt(opportunity, profile_summary)
            
            # Apply rate limiting
            self.rate_limiter.acquire()
            
            # Make API call
            start_time = time.time()
            response = self.gemini_model.generate_content(prompt)
            analysis_time = time.time() - start_time
            
            # Parse response
            response_text = response.text
            
            # Extract JSON from response
            json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            elif response_text.strip().startswith('{'):
                pass  # Already JSON
            else:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    response_text = response_text[json_start:json_end]
            
            try:
                analysis_result = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed for {title}: {e}")
                analysis_result = {
                    'compatibility_score': 0,
                    'one_sentence_summary': 'Analysis failed due to response parsing error',
                    'detailed_analysis': {
                        'error': f'JSON parsing failed: {str(e)}'
                    },
                    'raw_response': response_text[:1000]
                }
            
            # Ensure required fields and add metadata
            result = {
                'opportunity_id': basic_info.get('program_id', 'Unknown'),
                'title': title,
                'program_url': urls.get('program_url', ''),
                'solicitation_url': urls.get('solicitation_url', ''),
                'compatibility_score': analysis_result.get('compatibility_score', 0),
                'one_sentence_summary': analysis_result.get('one_sentence_summary', 'No summary available'),
                'detailed_analysis': analysis_result.get('detailed_analysis', {}),
                'proposal_matching': analysis_result.get('proposal_matching', {}),
                'success_factors': analysis_result.get('success_factors', []),
                'challenges_and_gaps': analysis_result.get('challenges_and_gaps', []),
                'analysis_time': analysis_time,
                'original_opportunity': opportunity  # Store for selected opportunities
            }
            
            logger.info(f"✅ Analyzed {title} (Score: {result['compatibility_score']}, Time: {analysis_time:.1f}s)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing {title}: {e}")
            return {
                'opportunity_id': basic_info.get('program_id', 'Unknown'),
                'title': title,
                'program_url': urls.get('program_url', ''),
                'solicitation_url': urls.get('solicitation_url', ''),
                'compatibility_score': 0,
                'one_sentence_summary': f'Analysis failed: {str(e)}',
                'detailed_analysis': {'error': str(e)},
                'proposal_matching': {},
                'success_factors': [],
                'challenges_and_gaps': [],
                'analysis_time': 0,
                'original_opportunity': opportunity
            }
    
    def process_opportunities_batch(self, opportunities: List[Dict[str, Any]], 
                                   profile_summary: Dict[str, Any], 
                                   batch_size: int = 50) -> List[Dict[str, Any]]:
        """Process opportunities in batches of specified size"""
        
        all_results = []
        total_opportunities = len(opportunities)
        
        # Process in batches
        for batch_start in range(0, total_opportunities, batch_size):
            batch_end = min(batch_start + batch_size, total_opportunities)
            batch = opportunities[batch_start:batch_end]
            
            logger.info(f"🔄 Processing batch {batch_start//batch_size + 1}: opportunities {batch_start+1}-{batch_end} of {total_opportunities}")
            
            batch_results = []
            
            # Process batch with parallel workers
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_opportunity = {
                    executor.submit(self.analyze_opportunity_match, opportunity, profile_summary): opportunity
                    for opportunity in batch
                }
                
                for future in as_completed(future_to_opportunity):
                    try:
                        result = future.result()
                        batch_results.append(result)
                    except Exception as e:
                        logger.error(f"❌ Batch processing error: {e}")
            
            all_results.extend(batch_results)
            logger.info(f"✅ Completed batch {batch_start//batch_size + 1}: {len(batch_results)} opportunities analyzed")
        
        # Sort by compatibility score
        def get_score(result):
            score = result.get('compatibility_score', 0)
            if isinstance(score, dict):
                return score.get('overall_score', 0)
            return score
        
        all_results.sort(key=get_score, reverse=True)
        
        logger.info(f"✅ Completed processing all {len(all_results)} opportunities")
        return all_results
    
    def save_selected_opportunities(self, results: List[Dict[str, Any]], output_path: str):
        """
        Save high-scoring opportunities (≥70%) to separate JSON file for follow-up.
        
        This method filters the analysis results to identify the most promising opportunities
        and saves them to a separate JSON file. These selected opportunities represent
        the best matches for immediate proposal development consideration.
        
        Args:
            results (List[Dict[str, Any]]): Complete list of analyzed opportunities
            output_path (str): Path where selected opportunities JSON file will be saved
            
        The saved file includes:
        - Original opportunity data with enhanced semantic analysis
        - Compatibility scores and detailed analysis results
        - Proposal matching recommendations
        - Strategic positioning advice
        - Analysis timestamps for tracking
        """
        
        # Filter high-scoring opportunities
        def get_score(result):
            score = result.get('compatibility_score', 0)
            if isinstance(score, dict):
                return score.get('overall_score', 0)
            return score
        
        selected_opportunities = []
        for result in results:
            if get_score(result) >= 70:
                # Add the analysis results to the original opportunity
                original_opp = result.get('original_opportunity', {})
                enhanced_opp = {
                    **original_opp,
                    'matching_analysis': {
                        'compatibility_score': result['compatibility_score'],
                        'one_sentence_summary': result['one_sentence_summary'],
                        'detailed_analysis': result['detailed_analysis'],
                        'proposal_matching': result['proposal_matching'],
                        'success_factors': result['success_factors'],
                        'challenges_and_gaps': result['challenges_and_gaps'],
                        'analysis_time': result['analysis_time'],
                        'analysis_date': datetime.now().isoformat()
                    }
                }
                selected_opportunities.append(enhanced_opp)
        
        if selected_opportunities:
            # Create output structure
            output_data = {
                "nsf_funding_opportunities_selected": {
                    "metadata": {
                        "selection_criteria": "Compatibility score >= 70%",
                        "selection_date": datetime.now().isoformat(),
                        "total_selected": len(selected_opportunities),
                        "analysis_model": "gemini-2.5-pro",
                        "researcher": "Alfredo Costilla Reyes"
                    },
                    "opportunities": selected_opportunities
                }
            }
            
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                logger.info(f"💾 Saved {len(selected_opportunities)} high-scoring opportunities to: {output_path}")
            except Exception as e:
                logger.error(f"❌ Error saving selected opportunities: {e}")
        else:
            logger.info("ℹ️ No opportunities scored ≥70%, no selected opportunities file created")
    
    def generate_comprehensive_report(self, results: List[Dict[str, Any]], 
                                    profile_summary: Dict[str, Any], 
                                    output_path: str):
        """
        Generate comprehensive matching report with detailed analysis and formatting.
        
        This method creates a comprehensive markdown report containing:
        - Executive summary with key statistics
        - Detailed results table with all opportunities ranked by score
        - Matching statistics by score ranges
        - Researcher profile summary
        - Detailed analysis for high-scoring opportunities (≥70%)
        - Proposal matching recommendations
        - Strategic positioning advice
        - Processing summary and technical details
        
        Args:
            results (List[Dict[str, Any]]): Complete list of analyzed opportunities
            profile_summary (Dict[str, Any]): Researcher profile summary
            output_path (str): Path where the markdown report will be saved
            
        The report is saved to the opportunity_matches folder with timestamp.
        """
        
        # Helper function to get numeric score
        def get_numeric_score(result):
            score = result.get('compatibility_score', 0)
            if isinstance(score, dict):
                return score.get('overall_score', 0)
            return score
        
        # Filter opportunities by score
        high_scoring = [r for r in results if get_numeric_score(r) >= 70]
        medium_scoring = [r for r in results if 50 <= get_numeric_score(r) < 70]
        low_scoring = [r for r in results if get_numeric_score(r) < 50]
        
        # Generate report
        report_content = f"""# Comprehensive Funding Opportunities Semantic Matching Report

## Executive Summary

**Researcher:** {profile_summary['researcher_info']['name']}  
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Opportunities Analyzed:** {len(results)}  
**Analysis Model:** Gemini 2.5 Pro  
**Processing Mode:** Batch processing (50 opportunities per batch)

## Detailed Results

| Rank | Score | Program ID | Title | One Sentence Summary | Analysis Time (s) | Program URL | Solicitation URL |
|------|-------|------------|-------|---------------------|-------------------|-------------|------------------|"""
        
        # Add all results to the detailed table
        for i, result in enumerate(results, 1):
            score = get_numeric_score(result)
            program_id = result.get('opportunity_id', 'Unknown')
            title = result.get('title', 'Unknown')[:50] + ('...' if len(result.get('title', '')) > 50 else '')
            summary = result.get('one_sentence_summary', 'No summary available')[:100] + ('...' if len(result.get('one_sentence_summary', '')) > 100 else '')
            analysis_time = result.get('analysis_time', 0)
            program_url = result.get('program_url', 'Not available')
            solicitation_url = result.get('solicitation_url', 'Not available')
            
            # Create clickable links if URLs are available
            program_link = f"[Link]({program_url})" if program_url and program_url != 'Not available' else 'Not available'
            solicitation_link = f"[Link]({solicitation_url})" if solicitation_url and solicitation_url != 'Not available' else 'Not available'
            
            report_content += f"\n| {i} | {score} | {program_id} | {title} | {summary} | {analysis_time:.1f} | {program_link} | {solicitation_link} |"
        
        report_content += f"""

## Matching Statistics

| Score Range | Count | Percentage |
|-------------|-------|------------|
| **High (≥70)** | {len(high_scoring)} | {len(high_scoring)/len(results)*100:.1f}% |
| **Medium (50-69)** | {len(medium_scoring)} | {len(medium_scoring)/len(results)*100:.1f}% |
| **Low (<50)** | {len(low_scoring)} | {len(low_scoring)/len(results)*100:.1f}% |

## Researcher Profile Summary

- **Career Stage:** {profile_summary['researcher_info']['career_stage']}
- **Total Funding Secured:** ${profile_summary['researcher_info']['total_funding']:,}
- **Successful Proposals:** {profile_summary['researcher_info']['successful_proposals_count']}
- **Research Domains:** {', '.join(profile_summary['research_domains'])}
- **Key Technical Areas:** {', '.join(profile_summary['technical_expertise'][:10])}

## High-Scoring Opportunities (≥70) - Detailed Analysis

"""
        
        # Add detailed analysis for high-scoring opportunities
        for i, result in enumerate(high_scoring, 1):
            score = get_numeric_score(result)
            title = result.get('title', 'Unknown')
            program_id = result.get('opportunity_id', 'Unknown')
            detailed_analysis = result.get('detailed_analysis', {})
            proposal_matching = result.get('proposal_matching', {})
            success_factors = result.get('success_factors', [])
            challenges_and_gaps = result.get('challenges_and_gaps', [])
            
            report_content += f"""
### {i}. {title} (Score: {score})

**Program ID:** {program_id}  
**Compatibility Score:** {score}/100  
**Summary:** {result.get('one_sentence_summary', 'No summary available')}

#### Detailed Analysis
"""
            
            if detailed_analysis:
                for key, value in detailed_analysis.items():
                    if key != 'error':
                        formatted_key = key.replace('_', ' ').title()
                        report_content += f"- **{formatted_key}:** {value}\n"
            
            report_content += """
#### Proposal Matching Recommendations
"""
            
            if proposal_matching.get('best_adaptable_proposals'):
                report_content += "\n**Best Adaptable Proposals:**\n"
                for proposal in proposal_matching['best_adaptable_proposals']:
                    report_content += f"- **{proposal.get('proposal_file', 'Unknown')}**\n"
                    report_content += f"  - Adaptation Strategy: {proposal.get('adaptation_strategy', 'Not specified')}\n"
                    report_content += f"  - Reusable Elements: {proposal.get('reusable_elements', 'Not specified')}\n"
            
            if proposal_matching.get('strategic_positioning'):
                report_content += f"\n**Strategic Positioning:** {proposal_matching['strategic_positioning']}\n"
            
            if success_factors:
                report_content += "\n#### Success Factors\n"
                for factor in success_factors:
                    report_content += f"- {factor}\n"
            
            if challenges_and_gaps:
                report_content += "\n#### Challenges and Gaps\n"
                for challenge in challenges_and_gaps:
                    report_content += f"- {challenge}\n"
            
            report_content += "\n---\n"
        
        report_content += f"""
## Processing Summary

### Technical Details
- **Analysis Model:** Gemini 2.5 Pro
- **Processing Method:** Batch processing (50 opportunities per batch)
- **Total Processing Time:** Approximately {len(results) * 30 / 60:.1f} minutes
- **High-Scoring Opportunities Saved:** {len(high_scoring)} opportunities saved to COMPLETE_funding_semantic_SELECTED.json

### Key Recommendations
1. **Immediately pursue high-scoring opportunities** (≥70%) for proposal development
2. **Review medium-scoring opportunities** (50-69%) for potential with additional partnerships
3. **Leverage specific proposal adaptations** as identified in the matching recommendations
4. **Address challenges and gaps** mentioned in the detailed analyses

---

*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} using Gemini 2.5 Pro*
"""
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"📋 Comprehensive report saved to: {output_path}")
        except Exception as e:
            logger.error(f"❌ Error saving report: {e}")
    
    def run_comprehensive_analysis(self, profile_path: str, opportunities_path: str, 
                                 output_path: str, selected_output_path: str,
                                 max_opportunities: Optional[int] = None):
        """
        Run comprehensive semantic matching analysis between researcher profile and funding opportunities.
        
        This is the main orchestration method that:
        1. Loads researcher semantic profile and funding opportunities data
        2. Extracts and optimizes profile summary for matching
        3. Processes opportunities in batches with parallel workers
        4. Applies rate limiting to comply with Gemini 2.5 Pro API limits
        5. Generates comprehensive analysis report
        6. Saves high-scoring opportunities for follow-up
        
        Args:
            profile_path (str): Path to researcher's semantic profile JSON
            opportunities_path (str): Path to funding opportunities semantic dataset
            output_path (str): Path for the comprehensive markdown report
            selected_output_path (str): Path for high-scoring opportunities JSON
            max_opportunities (Optional[int]): Limit number of opportunities for quick mode
            
        Returns:
            List[Dict[str, Any]]: Complete list of analyzed opportunities with results
            
        The method processes opportunities in batches of 50 with 3 workers each,
        ensuring efficient processing while respecting API rate limits.
        """
        
        logger.info("🚀 Starting Comprehensive Funding Opportunity Matching Analysis")
        
        # Load data
        profile = self.load_semantic_profile(profile_path)
        opportunities = self.load_semantic_opportunities(opportunities_path)
        
        # Limit opportunities if specified
        if max_opportunities:
            opportunities = opportunities[:max_opportunities]
            logger.info(f"⚡ Limited to {max_opportunities} opportunities for analysis")
        
        # Extract profile summary
        profile_summary = self.extract_profile_summary(profile)
        
        # Process opportunities in batches
        results = self.process_opportunities_batch(opportunities, profile_summary, batch_size=50)
        
        # Save selected opportunities (≥70%)
        self.save_selected_opportunities(results, selected_output_path)
        
        # Generate report
        self.generate_comprehensive_report(results, profile_summary, output_path)
        
        # Print summary
        def get_score_value(result):
            score = result.get('compatibility_score', 0)
            if isinstance(score, dict):
                return score.get('overall_score', 0)
            return score
        
        high_scoring = [r for r in results if get_score_value(r) >= 70]
        medium_scoring = [r for r in results if 50 <= get_score_value(r) < 70]
        
        logger.info(f"🎉 Analysis Complete!")
        logger.info(f"📊 Total Opportunities: {len(results)}")
        logger.info(f"🎯 High-Scoring (≥70): {len(high_scoring)}")
        logger.info(f"🔶 Medium-Scoring (50-69): {len(medium_scoring)}")
        logger.info(f"📋 Report: {output_path}")
        logger.info(f"💾 Selected Opportunities: {selected_output_path}")
        
        return results

def main():
    """
    Main function for comprehensive NSF semantic matching analysis.
    
    This function serves as the entry point for the NSF Comprehensive Matcher system.
    It handles:
    - Environment setup and API key validation
    - Command-line argument parsing (--quick mode)
    - Path configuration for input and output files
    - Initialization of the matching system
    - Execution of the complete analysis workflow
    - Summary reporting of results
    
    Command-line options:
    - --quick: Process only first 100 opportunities for faster testing
    - (default): Process all 478+ opportunities for complete analysis
    
    Output files:
    - opportunity_matches/NSF_Semantic_Matching_Report_[timestamp].md
    - FundingOpportunitiesManual/nsf_funding_semantic_SELECTED.json
    """
    
    print("🚀 COMPREHENSIVE FUNDING OPPORTUNITY MATCHER")
    print("=" * 80)
    print("📊 Complete Analysis with Gemini 2.5 Pro")
    print("🎯 Batch Processing (50 opportunities at a time)")
    print("💾 Saves High-Scoring Opportunities to Separate File")
    print("📋 Improved Report Format with Detailed Results Table")
    print()
    
    # Check for Gemini API key
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        logger.error("❌ GEMINI_API_KEY not found in environment variables")
        logger.error("💡 Make sure .env file contains GEMINI_API_KEY")
        return
    
    logger.info(f"🔧 Using Gemini 2.5 Pro with batch processing")
    
    # Define paths
    profile_path = "semantic_profiles/alfredo_costilla_reyes_COMPREHENSIVE_semantic_profile_20250710_114302.json"
    opportunities_path = "FundingOpportunities/funding_semantic.json"
    
    # Create opportunity_matches folder if it doesn't exist
    os.makedirs("opportunity_matches", exist_ok=True)
    
    output_path = f"opportunity_matches/COMPLETE_Funding_Semantic_Matching_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    selected_output_path = "opportunity_matches/COMPLETE_funding_semantic_SELECTED.json"
    
    logger.info("🔄 Complete analysis mode: Processing all opportunities")
    
    try:
        # Initialize matcher
        matcher = ComprehensiveFundingMatcher(gemini_api_key)
        
        # Run analysis
        results = matcher.run_comprehensive_analysis(
            profile_path=profile_path,
            opportunities_path=opportunities_path,
            output_path=output_path,
            selected_output_path=selected_output_path,
            max_opportunities=None
        )
        
        print(f"\n✅ COMPREHENSIVE SEMANTIC MATCHING COMPLETE!")
        print(f"📋 Report saved to: {output_path}")
        print(f"💾 Selected opportunities saved to: {selected_output_path}")
        
        # Helper function for score checking
        def get_final_score(result):
            score = result.get('compatibility_score', 0)
            if isinstance(score, dict):
                return score.get('overall_score', 0)
            return score
        
        high_scoring_count = len([r for r in results if get_final_score(r) >= 70])
        print(f"🎯 High-scoring opportunities: {high_scoring_count}")
        print(f"📊 Total analyzed: {len(results)}")
        
    except Exception as e:
        logger.error(f"❌ Error in main execution: {e}")
        return

if __name__ == "__main__":
    main() 