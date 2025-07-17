#!/usr/bin/env python3
"""
Enhanced Matcher for FundingMatch v2.0
Advanced opportunity matching using comprehensive semantic profiles
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from google import genai
from google.genai import types

class EnhancedMatcher:
    """
    Enhanced matching engine that uses comprehensive semantic profiles
    to provide evidence-based opportunity matching with detailed justifications
    """
    
    def __init__(self, gemini_api_key: str):
        """Initialize the enhanced matcher with Gemini client"""
        self.client = genai.Client(api_key=gemini_api_key)
        self.model = 'gemini-2.5-pro'
        self.min_match_score = 75  # Minimum score for high-quality matches
        
    def find_matches(self, semantic_profile: Dict[str, Any], opportunities: List[Dict[str, Any]], 
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Find and analyze matches between semantic profile and opportunities
        
        Args:
            semantic_profile: Complete researcher portfolio analysis
            opportunities: List of funding opportunities
            filters: Optional filtering criteria
            
        Returns:
            List of match analyses sorted by score
        """
        matches = []
        total_opportunities = len(opportunities)
        print(f"🔍 Analyzing {total_opportunities} opportunities with Gemini 2.5 Pro...")
        print("-" * 60)
        
        for i, opportunity in enumerate(opportunities, 1):
            try:
                title = opportunity.get('title', 'Unknown')[:50]
                agency = opportunity.get('agency', 'Unknown')
                source = opportunity.get('source', 'Unknown')
                
                print(f"  {i:2d}/{total_opportunities}. Analyzing: {title}...")
                print(f"           Agency: {agency} | Source: {source}")
                
                # Display complete URL for verification
                url = opportunity.get('url', 'No URL available')
                print(f"           🔗 URL: {url}")
                
                match_analysis = self._analyze_match(semantic_profile, opportunity)
                score = match_analysis.get('score', 0)
                
                if score >= self.min_match_score:
                    matches.append(match_analysis)
                    print(f"           ✅ HIGH MATCH: {score}/100 (Added to results)")
                else:
                    print(f"           ❌ Low match: {score}/100 (Below threshold)")
                    
            except Exception as e:
                print(f"           ❌ ERROR: {str(e)[:50]}...")
                continue
        
        # Sort by score (highest first)
        sorted_matches = sorted(matches, key=lambda x: x['score'], reverse=True)
        
        print("-" * 60)
        print(f"🎯 ANALYSIS COMPLETE:")
        print(f"   • Total Opportunities Analyzed: {total_opportunities}")
        print(f"   • High-Quality Matches Found: {len(sorted_matches)}")
        print(f"   • Success Rate: {len(sorted_matches)/total_opportunities*100:.1f}%")
        if sorted_matches:
            scores = [m.get('score', 0) for m in sorted_matches]
            print(f"   • Score Range: {min(scores)}-{max(scores)}")
            print(f"   • Average Score: {sum(scores)/len(scores):.1f}")
        print()
        
        return sorted_matches
    
    def _analyze_match(self, profile: Dict[str, Any], opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform deep match analysis using Gemini AI
        
        Args:
            profile: Semantic profile from Phase 1
            opportunity: Funding opportunity details
            
        Returns:
            Detailed match analysis with evidence and recommendations
        """
        prompt = self._build_matching_prompt(profile, opportunity)
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )
        
        # Parse the JSON response
        analysis_text = response.text
        
        # Extract JSON from response (handle potential markdown formatting)
        import re
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
            match_analysis = json.loads(analysis_text)
            
            # Add metadata
            match_analysis['opportunity'] = opportunity
            match_analysis['analysis_date'] = datetime.now().isoformat()
            match_analysis['profile_version'] = profile.get('profile_metadata', {}).get('processing_version', '2.0')
            
            return match_analysis
            
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse match analysis JSON: {e}")
            # Fallback analysis
            return {
                "score": 50,
                "confidence_level": "Low",
                "primary_justification": "Analysis parsing error - manual review required",
                "supporting_evidence": [],
                "competitive_advantages": [],
                "strategic_recommendations": [],
                "risk_assessment": "Unknown - parsing error",
                "effort_estimate": "Unknown",
                "opportunity": opportunity,
                "analysis_date": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _build_matching_prompt(self, profile: Dict[str, Any], opportunity: Dict[str, Any]) -> str:
        """
        Build sophisticated matching prompt with full context
        
        Args:
            profile: Complete semantic profile
            opportunity: Funding opportunity details
            
        Returns:
            Comprehensive prompt for Gemini analysis
        """
        # Extract key profile information
        portfolio_summary = profile.get('portfolio_summary', {})
        synthesis = profile.get('synthesis', {})
        documents = profile.get('documents', [])
        
        # Build context about researcher's capabilities
        researcher_context = f"""
RESEARCHER PROFILE SUMMARY:
• Primary Researcher: {profile.get('profile_metadata', {}).get('primary_researcher', 'Unknown')}
• Career Stage: {portfolio_summary.get('career_stage', 'Unknown')}
• Research Domains: {', '.join(portfolio_summary.get('research_domains', []))}
• Total Documents Analyzed: {len(documents)}
• Funding Track Record: ${portfolio_summary.get('funding_track_record', {}).get('total_secured', 0):,}
• Successful Proposals: {portfolio_summary.get('funding_track_record', {}).get('successful_proposals', 0)}
• Publications: {portfolio_summary.get('publication_metrics', {}).get('total_publications', 0)}

CORE COMPETENCIES:
"""
        
        # Add competencies
        for comp in synthesis.get('core_competencies', []):
            researcher_context += f"• {comp.get('domain', 'Unknown')}: {comp.get('evidence_strength', 'Unknown')} evidence\n"
        
        researcher_context += f"""
STRATEGIC ADVANTAGES:
"""
        for advantage in synthesis.get('strategic_advantages', []):
            researcher_context += f"• {advantage}\n"
        
        # Build document evidence context
        documents_context = "\n\nKEY SUPPORTING DOCUMENTS:\n"
        for i, doc in enumerate(documents[:10], 1):  # Limit to first 10 documents
            doc_analysis = doc.get('analysis', {})
            documents_context += f"{i}. {doc.get('document_type', 'Unknown')} - {doc.get('source_file', 'Unknown')}\n"
            
            # Add key details based on document type
            if 'title' in doc_analysis:
                documents_context += f"   Title: {doc_analysis['title']}\n"
            if 'award_amount' in doc_analysis:
                documents_context += f"   Award: ${doc_analysis['award_amount']:,}\n"
            if 'agency' in doc_analysis:
                documents_context += f"   Agency: {doc_analysis['agency']}\n"
            if 'summary' in doc_analysis:
                documents_context += f"   Summary: {doc_analysis['summary'][:200]}...\n"
            
            documents_context += "\n"
        
        # Build opportunity context
        opportunity_context = f"""
FUNDING OPPORTUNITY:
• Title: {opportunity.get('title', 'Unknown')}
• Agency: {opportunity.get('agency', 'Unknown')}
• Program: {opportunity.get('program', 'Unknown')}
• Description: {opportunity.get('description', 'No description available')[:1000]}
• Award Amount: ${opportunity.get('award_amount', 0):,}
• Deadline: {opportunity.get('deadline', 'Unknown')}
"""
        
        # Build the complete prompt
        prompt = f"""
You are an expert funding strategist analyzing opportunities for a researcher.

{researcher_context}

{documents_context}

{opportunity_context}

CRITICAL ANALYSIS INSTRUCTIONS:
⚠️ **ACCURACY REQUIREMENTS:**
- Only cite documents that are explicitly listed in the "KEY SUPPORTING DOCUMENTS" section above
- Only reference achievements, awards, or capabilities that are explicitly mentioned in the profile
- Do NOT make assumptions about connections between the researcher's work and the opportunity
- Do NOT cite or reference any documents, awards, or achievements not explicitly listed above
- Be conservative in scoring - only high scores (80+) if there is clear, explicit evidence of alignment

ANALYSIS TASK:
Perform a comprehensive match analysis considering:

1. TECHNICAL ALIGNMENT
   - Compare the opportunity requirements with the researcher's EXPLICITLY DOCUMENTED capabilities
   - Only reference documents that are actually listed in the profile above
   - If no clear technical alignment exists, score low and state this explicitly

2. STRATEGIC FIT
   - Base analysis only on the documented career trajectory and funding history
   - Do not assume connections that are not explicitly stated

3. EVIDENCE-BASED JUSTIFICATION
   - Reference ONLY documents that appear in the "KEY SUPPORTING DOCUMENTS" section
   - Use ONLY achievements and capabilities explicitly mentioned in the profile
   - If there's insufficient evidence, state this clearly and score low

4. CONSERVATIVE SCORING
   - Score 90+: Exceptional alignment with multiple explicit connections
   - Score 80-89: Good alignment with some clear connections
   - Score 70-79: Moderate alignment with limited connections
   - Score <70: Poor alignment or insufficient evidence

RESPONSE FORMAT (JSON):
{{
  "score": 75,
  "confidence_level": "Medium",
  "primary_justification": "Based on the documented research domains and past proposals, there is [specific evidence from profile]",
  "supporting_evidence": [
    {{
      "source": "EXACT_FILENAME_FROM_PROFILE_ABOVE",
      "document_type": "Type listed in profile",
      "relevance": "Specific relevance based on documented analysis",
      "specific_alignment": "Exact alignment based on documented capabilities"
    }}
  ],
  "competitive_advantages": [
    "Advantage based on documented achievements",
    "Strength based on explicitly listed capabilities"
  ],
  "strategic_recommendations": [
    "Recommendation based on documented strengths",
    "Action based on explicitly mentioned capabilities"
  ],
  "reusability_analysis": [
    {{
      "source_proposal": "EXACT_FILENAME_FROM_PROFILE_ABOVE",
      "reusable_sections": ["Sections mentioned in profile"],
      "adaptation_needed": "Changes needed based on documented content",
      "effort_estimate": "Conservative estimate"
    }}
  ],
  "risk_assessment": "Assessment based on documented track record",
  "effort_estimate": "Conservative estimate based on documented capabilities"
}}

**IMPORTANT**: If you cannot find clear, explicit evidence of alignment in the provided profile, score the opportunity low (< 70) and explain why. Do not create connections that are not explicitly documented.
"""
        
        return prompt
    
    def batch_analyze_matches(self, semantic_profile: Dict[str, Any], 
                            opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch process multiple opportunities for efficiency
        
        Args:
            semantic_profile: Complete researcher portfolio
            opportunities: List of funding opportunities
            
        Returns:
            List of high-quality matches
        """
        print(f"🔍 Analyzing {len(opportunities)} opportunities...")
        
        high_quality_matches = []
        
        for i, opportunity in enumerate(opportunities, 1):
            print(f"   {i}/{len(opportunities)}: {opportunity.get('title', 'Unknown')[:50]}...")
            
            try:
                match = self._analyze_match(semantic_profile, opportunity)
                if match['score'] >= self.min_match_score:
                    high_quality_matches.append(match)
                    print(f"      ✅ Match found (Score: {match['score']})")
                else:
                    print(f"      ❌ Low match (Score: {match['score']})")
            except Exception as e:
                print(f"      ⚠️  Error: {str(e)[:50]}...")
                continue
        
        print(f"✅ Found {len(high_quality_matches)} high-quality matches")
        return sorted(high_quality_matches, key=lambda x: x['score'], reverse=True)
    
    def get_match_summary(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for matches
        
        Args:
            matches: List of match analyses
            
        Returns:
            Summary statistics
        """
        if not matches:
            return {
                "total_matches": 0,
                "average_score": 0,
                "top_score": 0,
                "agencies": [],
                "total_potential_funding": 0
            }
        
        scores = [match['score'] for match in matches]
        agencies = list(set(match['opportunity'].get('agency', 'Unknown') for match in matches))
        total_funding = sum(match['opportunity'].get('award_amount', 0) for match in matches)
        
        return {
            "total_matches": len(matches),
            "average_score": sum(scores) / len(scores),
            "top_score": max(scores),
            "score_distribution": {
                "90+": len([s for s in scores if s >= 90]),
                "80-89": len([s for s in scores if 80 <= s < 90]),
                "75-79": len([s for s in scores if 75 <= s < 80])
            },
            "agencies": agencies,
            "total_potential_funding": total_funding,
            "top_opportunities": [
                {
                    "title": match['opportunity'].get('title', 'Unknown'),
                    "agency": match['opportunity'].get('agency', 'Unknown'),
                    "score": match['score']
                }
                for match in matches[:5]  # Top 5
            ]
        } 