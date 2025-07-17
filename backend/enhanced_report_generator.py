#!/usr/bin/env python3
"""
Enhanced Report Generator for FundingMatch v2.0
Generates comprehensive match reports with evidence-based justifications
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

class EnhancedReportGenerator:
    """
    Enhanced report generator that creates comprehensive match reports
    with evidence-based justifications and document citations
    """
    
    def __init__(self):
        """Initialize the report generator"""
        self.report_template = {
            "title": "FundingMatch Analysis Report v2.0",
            "subtitle": "Evidence-Based Opportunity Matching",
            "generated_date": datetime.now().isoformat(),
            "version": "2.0"
        }
    
    def generate_match_report(self, matches: List[Dict[str, Any]], 
                            semantic_profile: Dict[str, Any],
                            output_file: Optional[str] = None) -> str:
        """
        Generate comprehensive match report with evidence citations
        
        Args:
            matches: List of match analyses from Enhanced Matcher
            semantic_profile: Complete researcher portfolio
            output_file: Optional output filename
            
        Returns:
            Formatted markdown report
        """
        report_sections = []
        
        # Header
        report_sections.append(self._generate_header(semantic_profile))
        
        # Executive Summary
        report_sections.append(self._generate_executive_summary(matches, semantic_profile))
        
        # Portfolio Overview
        report_sections.append(self._generate_portfolio_overview(semantic_profile))
        
        # Top Matches (detailed analysis)
        report_sections.append(self._generate_detailed_matches(matches[:5]))  # Top 5
        
        # Strategic Analysis
        report_sections.append(self._generate_strategic_analysis(matches, semantic_profile))
        
        # Funding Landscape
        report_sections.append(self._generate_funding_landscape(matches))
        
        # Recommendations
        report_sections.append(self._generate_recommendations(matches, semantic_profile))
        
        # Appendices
        report_sections.append(self._generate_appendices(matches, semantic_profile))
        
        # Combine all sections
        full_report = "\n\n".join(report_sections)
        
        # Save report if filename provided
        if output_file:
            with open(output_file, 'w') as f:
                f.write(full_report)
            print(f"📄 Enhanced report saved: {output_file}")
        
        return full_report
    
    def _generate_header(self, semantic_profile: Dict[str, Any]) -> str:
        """Generate report header with metadata"""
        primary_researcher = semantic_profile.get('profile_metadata', {}).get('primary_researcher', 'Unknown Researcher')
        generation_date = datetime.now().strftime("%B %d, %Y")
        
        return f"""# {self.report_template['title']}
## {self.report_template['subtitle']}

**Researcher:** {primary_researcher}  
**Analysis Date:** {generation_date}  
**Report Version:** {self.report_template['version']}  
**Profile Version:** {semantic_profile.get('profile_metadata', {}).get('processing_version', 'Unknown')}

---"""
    
    def _generate_executive_summary(self, matches: List[Dict[str, Any]], 
                                   semantic_profile: Dict[str, Any]) -> str:
        """Generate executive summary with key insights"""
        portfolio_summary = semantic_profile.get('portfolio_summary', {})
        documents_count = len(semantic_profile.get('documents', []))
        total_funding = portfolio_summary.get('funding_track_record', {}).get('total_secured', 0)
        
        # Calculate match statistics
        if matches:
            avg_score = sum(match['score'] for match in matches) / len(matches)
            top_score = max(match['score'] for match in matches)
            total_potential = sum(match['opportunity'].get('award_amount', 0) for match in matches)
        else:
            avg_score = 0
            top_score = 0
            total_potential = 0
        
        return f"""## Executive Summary

Based on comprehensive analysis of your **{documents_count}-document portfolio**, including {portfolio_summary.get('funding_track_record', {}).get('successful_proposals', 0)} successful proposals and **${total_funding:,}** in secured funding, we've identified **{len(matches)} high-relevance funding opportunities**.

### Key Findings

🎯 **Match Quality**: {len(matches)} opportunities with 75%+ alignment  
📊 **Average Match Score**: {avg_score:.1f}/100  
🏆 **Top Match Score**: {top_score}/100  
💰 **Total Potential Funding**: ${total_potential:,}

### Your Strategic Advantages

{self._format_strategic_advantages(semantic_profile)}

### Recommendation Priority

{self._generate_priority_recommendations(matches)}"""
    
    def _generate_portfolio_overview(self, semantic_profile: Dict[str, Any]) -> str:
        """Generate portfolio overview section"""
        portfolio_summary = semantic_profile.get('portfolio_summary', {})
        synthesis = semantic_profile.get('synthesis', {})
        
        return f"""## Portfolio Overview

### Research Profile
- **Career Stage**: {portfolio_summary.get('career_stage', 'Unknown')}
- **Research Domains**: {', '.join(portfolio_summary.get('research_domains', []))}
- **Core Competencies**: {len(synthesis.get('core_competencies', []))} validated expertise areas

### Funding Track Record
- **Total Secured**: ${portfolio_summary.get('funding_track_record', {}).get('total_secured', 0):,}
- **Successful Proposals**: {portfolio_summary.get('funding_track_record', {}).get('successful_proposals', 0)}
- **Agencies Worked With**: {', '.join(portfolio_summary.get('funding_track_record', {}).get('agencies_worked_with', []))}

### Publication Metrics
- **Total Publications**: {portfolio_summary.get('publication_metrics', {}).get('total_publications', 0)}
- **First Author Papers**: {portfolio_summary.get('publication_metrics', {}).get('first_author_papers', 0)}

### Core Competencies Analysis

{self._format_core_competencies(synthesis)}"""
    
    def _generate_detailed_matches(self, top_matches: List[Dict[str, Any]]) -> str:
        """Generate detailed analysis of top matches"""
        sections = ["## Top Funding Opportunities"]
        
        for i, match in enumerate(top_matches, 1):
            opportunity = match['opportunity']
            
            # Get opportunity URL
            opp_url = opportunity.get('url', '')
            if not opp_url:
                # Generate URL based on opportunity source
                opp_id = opportunity.get('id', opportunity.get('noticeId', ''))
                if opp_id:
                    if 'sam.gov' in str(opportunity.get('source', '')).lower() or opportunity.get('agency', '').startswith('Department'):
                        opp_url = f"https://sam.gov/opp/{opp_id}"
                    elif 'sbir' in str(opportunity.get('program', '')).lower():
                        opp_url = f"https://www.sbir.gov/sbirsearch/detail/{opp_id}"
                    elif 'grants.gov' in str(opportunity.get('source', '')).lower():
                        opp_url = f"https://www.grants.gov/search-grants.html?cfda={opp_id}"
            
            # Format deadline
            deadline = opportunity.get('deadline', opportunity.get('response_deadline', 'Unknown'))
            
            # Format opportunity details with clickable link
            link_text = f"🔗 [**View Full Opportunity Details**]({opp_url})" if opp_url else "🔗 **View Full Opportunity Details**: *Link not available*"
            
            opportunity_section = f"""### {i}. {opportunity.get('title', 'Unknown Opportunity')}
**Match Score**: {match['score']}/100 | **Confidence**: {match.get('confidence_level', 'Unknown')}  
**Agency**: {opportunity.get('agency', 'Unknown')} | **Program**: {opportunity.get('program', 'Unknown')}  
**Award Amount**: ${opportunity.get('award_amount', 0):,} | **Deadline**: {deadline}

{link_text}

#### Why This Is Perfect For You
{match.get('primary_justification', 'No justification provided')}

#### Supporting Evidence
{self._format_supporting_evidence(match.get('supporting_evidence', []))}

#### Your Competitive Advantages
{self._format_competitive_advantages(match.get('competitive_advantages', []))}

#### Strategic Recommendations
{self._format_strategic_recommendations(match.get('strategic_recommendations', []))}

#### Proposal Reusability Analysis
{self._format_reusability_analysis(match.get('reusability_analysis', []))}

**Risk Assessment**: {match.get('risk_assessment', 'Unknown')}  
**Effort Estimate**: {match.get('effort_estimate', 'Unknown')}

---"""
            sections.append(opportunity_section)
        
        return "\n\n".join(sections)
    
    def _generate_strategic_analysis(self, matches: List[Dict[str, Any]], 
                                   semantic_profile: Dict[str, Any]) -> str:
        """Generate strategic analysis section"""
        # Analyze agency distribution
        agencies = {}
        for match in matches:
            agency = match['opportunity'].get('agency', 'Unknown')
            if agency not in agencies:
                agencies[agency] = []
            agencies[agency].append(match)
        
        # Analyze score distribution
        score_ranges = {
            '90-100': [m for m in matches if m['score'] >= 90],
            '80-89': [m for m in matches if 80 <= m['score'] < 90],
            '75-79': [m for m in matches if 75 <= m['score'] < 80]
        }
        
        return f"""## Strategic Analysis

### Agency Distribution
{self._format_agency_distribution(agencies)}

### Match Score Distribution
{self._format_score_distribution(score_ranges)}

### Funding Timeline Analysis
{self._generate_timeline_analysis(matches)}

### Competitive Positioning
{self._generate_competitive_positioning(matches, semantic_profile)}"""
    
    def _generate_funding_landscape(self, matches: List[Dict[str, Any]]) -> str:
        """Generate funding landscape overview"""
        total_potential = sum(match['opportunity'].get('award_amount', 0) for match in matches)
        
        # Group by program type
        program_types = {}
        for match in matches:
            program = match['opportunity'].get('program', 'Unknown')
            if program not in program_types:
                program_types[program] = []
            program_types[program].append(match)
        
        return f"""## Funding Landscape Overview

### Total Opportunity Value
**${total_potential:,}** across {len(matches)} high-quality opportunities

### Program Distribution
{self._format_program_distribution(program_types)}

### Deadline Analysis
{self._generate_deadline_analysis(matches)}

### Award Size Distribution
{self._generate_award_size_analysis(matches)}"""
    
    def _generate_recommendations(self, matches: List[Dict[str, Any]], 
                                semantic_profile: Dict[str, Any]) -> str:
        """Generate strategic recommendations"""
        return f"""## Strategic Recommendations

### Immediate Actions (Next 30 Days)
{self._generate_immediate_actions(matches)}

### Medium-Term Strategy (3-6 Months)
{self._generate_medium_term_strategy(matches, semantic_profile)}

### Long-Term Positioning (6+ Months)
{self._generate_long_term_strategy(matches, semantic_profile)}

### Proposal Development Priority
{self._generate_proposal_priority(matches)}"""
    
    def _generate_appendices(self, matches: List[Dict[str, Any]], 
                           semantic_profile: Dict[str, Any]) -> str:
        """Generate appendices with detailed data"""
        return f"""## Appendices

### Appendix A: Complete Match Summary
{self._format_complete_match_summary(matches)}

### Appendix B: Document Evidence Index
{self._format_document_evidence_index(semantic_profile)}

### Appendix C: Methodology
This analysis uses FundingMatch v2.0's Enhanced Matching Algorithm, which leverages:
- Comprehensive semantic profiling of researcher portfolios
- Evidence-based matching with document citations
            - AI-powered opportunity analysis using Gemini 2.5 Pro
- Strategic positioning assessment

### Appendix D: Contact Information
For questions about this analysis or to discuss proposal development strategies, please contact the FundingMatch team.

---
*Report generated by FundingMatch v2.0 on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}*"""
    
    # Helper methods for formatting
    def _format_strategic_advantages(self, semantic_profile: Dict[str, Any]) -> str:
        """Format strategic advantages list"""
        advantages = semantic_profile.get('synthesis', {}).get('strategic_advantages', [])
        if not advantages:
            return "- No strategic advantages identified"
        
        formatted = []
        for i, advantage in enumerate(advantages, 1):
            formatted.append(f"{i}. {advantage}")
        
        return "\n".join(formatted)
    
    def _format_core_competencies(self, synthesis: Dict[str, Any]) -> str:
        """Format core competencies section"""
        competencies = synthesis.get('core_competencies', [])
        if not competencies:
            return "No core competencies identified."
        
        formatted = []
        for comp in competencies:
            domain = comp.get('domain', 'Unknown')
            strength = comp.get('evidence_strength', 'Unknown')
            support_count = len(comp.get('supporting_documents', []))
            
            formatted.append(f"- **{domain}**: {strength} evidence ({support_count} supporting documents)")
        
        return "\n".join(formatted)
    
    def _format_supporting_evidence(self, evidence: List[Dict[str, Any]]) -> str:
        """Format supporting evidence list"""
        if not evidence:
            return "No supporting evidence provided."
        
        formatted = []
        for i, item in enumerate(evidence, 1):
            source = item.get('source', 'Unknown')
            doc_type = item.get('document_type', 'Unknown')
            relevance = item.get('relevance', 'No relevance provided')
            alignment = item.get('specific_alignment', 'No alignment details')
            
            formatted.append(f"{i}. **{source}** ({doc_type})\n   - Relevance: {relevance}\n   - Alignment: {alignment}")
        
        return "\n".join(formatted)
    
    def _format_competitive_advantages(self, advantages: List[str]) -> str:
        """Format competitive advantages list"""
        if not advantages:
            return "No competitive advantages identified."
        
        return "\n".join(f"- {advantage}" for advantage in advantages)
    
    def _format_strategic_recommendations(self, recommendations: List[str]) -> str:
        """Format strategic recommendations list"""
        if not recommendations:
            return "No strategic recommendations provided."
        
        return "\n".join(f"- {recommendation}" for recommendation in recommendations)
    
    def _format_reusability_analysis(self, reusability: List[Dict[str, Any]]) -> str:
        """Format reusability analysis"""
        if not reusability:
            return "No reusability analysis available."
        
        formatted = []
        for item in reusability:
            source = item.get('source_proposal', 'Unknown')
            reusable = ', '.join(item.get('reusable_sections', []))
            adaptation = item.get('adaptation_needed', 'Unknown')
            effort = item.get('effort_estimate', 'Unknown')
            
            formatted.append(f"**{source}**\n- Reusable: {reusable}\n- Adaptation: {adaptation}\n- Effort: {effort}")
        
        return "\n".join(formatted)
    
    def _generate_priority_recommendations(self, matches: List[Dict[str, Any]]) -> str:
        """Generate priority recommendations"""
        if not matches:
            return "No high-priority opportunities identified."
        
        top_match = matches[0]
        opportunity = top_match['opportunity']
        
        return f"""**Priority #1**: {opportunity.get('title', 'Unknown')} ({opportunity.get('agency', 'Unknown')})
- Score: {top_match['score']}/100
- Award: ${opportunity.get('award_amount', 0):,}
- Deadline: {opportunity.get('deadline', 'Unknown')}
- Action: Begin proposal development immediately"""
    
    def _format_agency_distribution(self, agencies: Dict[str, List]) -> str:
        """Format agency distribution"""
        if not agencies:
            return "No agencies identified."
        
        formatted = []
        for agency, matches in agencies.items():
            total_funding = sum(match['opportunity'].get('award_amount', 0) for match in matches)
            avg_score = sum(match['score'] for match in matches) / len(matches)
            
            formatted.append(f"- **{agency}**: {len(matches)} opportunities, ${total_funding:,} total, {avg_score:.1f} avg score")
        
        return "\n".join(formatted)
    
    def _format_score_distribution(self, score_ranges: Dict[str, List]) -> str:
        """Format score distribution"""
        formatted = []
        for range_name, matches in score_ranges.items():
            if matches:
                formatted.append(f"- **{range_name}**: {len(matches)} opportunities")
        
        return "\n".join(formatted) if formatted else "No score distribution available."
    
    def _generate_timeline_analysis(self, matches: List[Dict[str, Any]]) -> str:
        """Generate timeline analysis"""
        # Sort by deadline (if available)
        try:
            sorted_matches = sorted(matches, key=lambda x: x['opportunity'].get('deadline', 'Z'))
            upcoming = sorted_matches[:3]
            
            formatted = []
            for match in upcoming:
                opportunity = match['opportunity']
                formatted.append(f"- {opportunity.get('deadline', 'Unknown')}: {opportunity.get('title', 'Unknown')[:50]}...")
            
            return "\n".join(formatted)
        except:
            return "Timeline analysis not available."
    
    def _generate_competitive_positioning(self, matches: List[Dict[str, Any]], 
                                        semantic_profile: Dict[str, Any]) -> str:
        """Generate competitive positioning analysis"""
        advantages = semantic_profile.get('synthesis', {}).get('strategic_advantages', [])
        
        if not advantages:
            return "No competitive positioning data available."
        
        return f"""Your key differentiators across all opportunities:
{self._format_strategic_advantages(semantic_profile)}"""
    
    def _format_program_distribution(self, program_types: Dict[str, List]) -> str:
        """Format program distribution"""
        if not program_types:
            return "No program distribution available."
        
        formatted = []
        for program, matches in program_types.items():
            total_funding = sum(match['opportunity'].get('award_amount', 0) for match in matches)
            formatted.append(f"- **{program}**: {len(matches)} opportunities, ${total_funding:,}")
        
        return "\n".join(formatted)
    
    def _generate_deadline_analysis(self, matches: List[Dict[str, Any]]) -> str:
        """Generate deadline analysis"""
        return "Deadline analysis: Review individual opportunity deadlines above."
    
    def _generate_award_size_analysis(self, matches: List[Dict[str, Any]]) -> str:
        """Generate award size analysis"""
        if not matches:
            return "No award size data available."
        
        awards = [match['opportunity'].get('award_amount', 0) for match in matches]
        awards = [a for a in awards if a > 0]  # Filter out zero awards
        
        if not awards:
            return "No award amount data available."
        
        return f"""- **Range**: ${min(awards):,} - ${max(awards):,}
- **Average**: ${sum(awards) / len(awards):,.0f}
- **Total Potential**: ${sum(awards):,}"""
    
    def _generate_immediate_actions(self, matches: List[Dict[str, Any]]) -> str:
        """Generate immediate actions"""
        if not matches:
            return "No immediate actions identified."
        
        top_match = matches[0]
        opportunity = top_match['opportunity']
        
        return f"""1. **Begin {opportunity.get('title', 'top opportunity')} proposal development**
   - Deadline: {opportunity.get('deadline', 'Unknown')}
   - Focus on leveraging your proven track record
   
2. **Gather supporting documents and evidence**
   - Compile relevant publications and past proposals
   - Prepare budget and timeline estimates
   
3. **Engage with program officers**
   - Contact {opportunity.get('agency', 'agency')} program managers
   - Schedule informational meetings"""
    
    def _generate_medium_term_strategy(self, matches: List[Dict[str, Any]], 
                                     semantic_profile: Dict[str, Any]) -> str:
        """Generate medium-term strategy"""
        return f"""1. **Develop 3-5 high-quality proposals** from top-ranked opportunities
2. **Strengthen strategic partnerships** for collaborative proposals
3. **Expand research portfolio** in high-scoring domains
4. **Build industry connections** for commercial validation"""
    
    def _generate_long_term_strategy(self, matches: List[Dict[str, Any]], 
                                   semantic_profile: Dict[str, Any]) -> str:
        """Generate long-term strategy"""
        return f"""1. **Establish domain leadership** in your core competency areas
2. **Build multi-agency relationships** for sustained funding
3. **Develop proposal templates** for efficient reuse
4. **Create strategic research roadmap** aligned with funding priorities"""
    
    def _generate_proposal_priority(self, matches: List[Dict[str, Any]]) -> str:
        """Generate proposal priority ranking"""
        if not matches:
            return "No proposals to prioritize."
        
        formatted = []
        for i, match in enumerate(matches[:5], 1):  # Top 5
            opportunity = match['opportunity']
            formatted.append(f"{i}. **{opportunity.get('title', 'Unknown')}** (Score: {match['score']}/100)")
        
        return "\n".join(formatted)
    
    def _format_complete_match_summary(self, matches: List[Dict[str, Any]]) -> str:
        """Format complete match summary table"""
        if not matches:
            return "No matches to summarize."
        
        formatted = ["| Rank | Opportunity | Agency | Score | Award | Deadline |",
                    "|------|-------------|---------|-------|--------|----------|"]
        
        for i, match in enumerate(matches, 1):
            opportunity = match['opportunity']
            title = opportunity.get('title', 'Unknown')[:30] + "..."
            agency = opportunity.get('agency', 'Unknown')[:20]
            score = match['score']
            award = f"${opportunity.get('award_amount', 0):,}"
            deadline = opportunity.get('deadline', 'Unknown')
            
            formatted.append(f"| {i} | {title} | {agency} | {score} | {award} | {deadline} |")
        
        return "\n".join(formatted)
    
    def _format_document_evidence_index(self, semantic_profile: Dict[str, Any]) -> str:
        """Format document evidence index"""
        documents = semantic_profile.get('documents', [])
        if not documents:
            return "No documents available."
        
        formatted = []
        for i, doc in enumerate(documents, 1):
            doc_type = doc.get('document_type', 'Unknown')
            source = Path(doc.get('source_file', 'Unknown')).name
            formatted.append(f"{i}. **{source}** ({doc_type})")
        
        return "\n".join(formatted)
    
    def generate_summary_report(self, matches: List[Dict[str, Any]]) -> str:
        """Generate a shorter summary report"""
        if not matches:
            return "No matches found for summary report."
        
        summary = f"""# FundingMatch Summary Report
**Generated:** {datetime.now().strftime("%B %d, %Y")}

## Quick Stats
- **High-Quality Matches**: {len(matches)}
- **Total Potential Funding**: ${sum(match['opportunity'].get('award_amount', 0) for match in matches):,}
- **Average Match Score**: {sum(match['score'] for match in matches) / len(matches):.1f}/100

## Top 3 Opportunities
"""
        
        for i, match in enumerate(matches[:3], 1):
            opportunity = match['opportunity']
            summary += f"""
### {i}. {opportunity.get('title', 'Unknown')}
- **Score**: {match['score']}/100
- **Agency**: {opportunity.get('agency', 'Unknown')}
- **Award**: ${opportunity.get('award_amount', 0):,}
- **Deadline**: {opportunity.get('deadline', 'Unknown')}
"""
        
        return summary 