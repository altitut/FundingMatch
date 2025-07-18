#!/usr/bin/env python3
"""
RAG Explainer - Uses Gemini 2.0 Pro to explain funding opportunity matches
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from google import genai
from google.genai.types import GenerateContentConfig, Tool


class RAGExplainer:
    """Explains funding opportunity matches using Retrieval Augmented Generation"""
    
    def __init__(self):
        """Initialize Gemini client"""
        # Get API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            # Try alternative name
            api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        # Initialize client with new genai library
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash-exp"  # Using Gemini 2.0
        
    def explain_match(self, 
                     user_profile: Dict[str, Any],
                     opportunity: Dict[str, Any],
                     user_documents: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate explanation for why an opportunity matches the user
        
        Args:
            user_profile: User profile with research interests, experience, etc.
            opportunity: Funding opportunity details
            user_documents: Dictionary of user's documents (proposals, papers)
            
        Returns:
            Explanation with match reasons, reusable content, and next steps
        """
        try:
            # Prepare context for RAG
            context = self._prepare_context(user_profile, opportunity, user_documents)
            
            # Generate explanation
            prompt = self._create_explanation_prompt(context)
            
            # Use Gemini to generate response
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1000
                )
            )
            
            # Parse response
            explanation_text = response.text
            
            # Extract structured information
            explanation = self._parse_explanation(explanation_text, user_documents)
            
            return explanation
            
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return {
                'summary': 'Unable to generate detailed explanation',
                'alignment_reasons': ['This opportunity matches your research area'],
                'reusable_content': [],
                'next_steps': ['Review the opportunity details', 'Check eligibility requirements'],
                'error': str(e)
            }
    
    def _prepare_context(self, 
                        user_profile: Dict[str, Any],
                        opportunity: Dict[str, Any],
                        user_documents: Dict[str, str]) -> Dict[str, Any]:
        """Prepare context for RAG"""
        
        # Extract key user information
        user_context = {
            'name': user_profile.get('name', ''),
            'research_interests': user_profile.get('research_interests', []),
            'experience': user_profile.get('experience', '')[:500],
            'publications': user_profile.get('publications', '')[:500],
            'awards': [award['name'] for award in user_profile.get('awards', [])],
            'skills': user_profile.get('skills', '')[:300]
        }
        
        # Extract opportunity details
        opp_context = {
            'title': opportunity.get('title', ''),
            'agency': opportunity.get('agency', ''),
            'description': opportunity.get('description', ''),
            'keywords': opportunity.get('keywords', []),
            'deadline': opportunity.get('deadline', ''),
            'url': opportunity.get('url', ''),
            'eligibility': opportunity.get('eligibility', ''),
            'award_amount': opportunity.get('award_amount', '')
        }
        
        # Get document titles
        doc_titles = {
            'proposals': [],
            'papers': [],
            'other': []
        }
        
        for doc_name in user_documents.keys():
            doc_lower = doc_name.lower()
            if 'proposal' in doc_lower or 'sbir' in doc_lower or 'nsf' in doc_lower:
                doc_titles['proposals'].append(doc_name)
            elif 'paper' in doc_lower or 'journal' in doc_lower or '.pdf' in doc_lower:
                doc_titles['papers'].append(doc_name)
            else:
                doc_titles['other'].append(doc_name)
        
        return {
            'user': user_context,
            'opportunity': opp_context,
            'documents': doc_titles
        }
    
    def _create_explanation_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for Gemini"""
        
        prompt = f"""You are an expert grant consultant helping researchers match with funding opportunities.

USER PROFILE:
- Name: {context['user']['name']}
- Research Interests: {', '.join(context['user']['research_interests'][:10])}
- Awards: {', '.join(context['user']['awards'][:3])}
- Experience Summary: {context['user']['experience'][:300]}...
- Key Skills: {context['user']['skills'][:200]}...

FUNDING OPPORTUNITY:
- Title: {context['opportunity']['title']}
- Agency: {context['opportunity']['agency']}
- Description: {context['opportunity']['description']}
- Keywords: {', '.join(context['opportunity']['keywords'][:10])}
- Deadline: {context['opportunity']['deadline']}
- URL: {context['opportunity']['url']}

USER'S AVAILABLE DOCUMENTS:
- Proposals: {', '.join(context['documents']['proposals'][:5]) if context['documents']['proposals'] else 'None'}
- Research Papers: {', '.join(context['documents']['papers'][:5]) if context['documents']['papers'] else 'None'}
- Other Documents: {', '.join(context['documents']['other'][:5]) if context['documents']['other'] else 'None'}

Please provide:
1. A brief explanation (2-3 sentences) of why this funding opportunity is a good match for the user's profile
2. List 2-3 specific documents from the user's portfolio that could be reused, explaining exactly how each document's content relates to this opportunity
3. Concrete next steps the user should take to apply

Format your response EXACTLY as follows:
MATCH EXPLANATION:
[Your 2-3 sentence explanation here]

REUSABLE CONTENT:
- [Exact document filename from the list above]: [Specific explanation of how this document's research/methods/results can be adapted for this opportunity]
- [Another exact document filename]: [Specific explanation of relevant sections or content that applies]

NEXT STEPS:
1. Review solicitation requirements: [Specific action]
2. Prepare application materials: [Specific action]
3. Submit proposal: [Specific action with timeline if mentioned]
"""
        
        return prompt
    
    def _parse_explanation(self, 
                          explanation_text: str,
                          user_documents: Dict[str, str]) -> Dict[str, Any]:
        """Parse explanation into structured format"""
        
        result = {
            'summary': '',  # Changed from match_explanation to summary for frontend compatibility
            'alignment_reasons': [],
            'reusable_content': [],
            'next_steps': [],
            'raw_explanation': explanation_text
        }
        
        # Split by sections
        sections = explanation_text.split('\n\n')
        
        current_section = None
        for section in sections:
            section = section.strip()
            
            if section.startswith('MATCH EXPLANATION:'):
                explanation = section.replace('MATCH EXPLANATION:', '').strip()
                result['summary'] = explanation
                # Extract alignment reasons from the explanation
                sentences = explanation.split('. ')
                for sentence in sentences:
                    if sentence.strip():
                        result['alignment_reasons'].append(sentence.strip() + ('.' if not sentence.endswith('.') else ''))
                current_section = 'explanation'
            
            elif section.startswith('REUSABLE CONTENT:'):
                current_section = 'reusable'
                content_lines = section.split('\n')[1:]  # Skip header
                for line in content_lines:
                    if line.strip().startswith('-'):
                        # Parse "- Document: How to reuse"
                        parts = line.strip('- ').split(':', 1)
                        if len(parts) == 2:
                            doc_name = parts[0].strip()
                            reuse_info = parts[1].strip()
                            
                            # Match with actual document names
                            matched_doc = self._match_document_name(doc_name, user_documents)
                            if matched_doc:
                                # Extract snippet from the document
                                snippet = self._extract_relevant_snippet(matched_doc, user_documents)
                                result['reusable_content'].append({
                                    'source': matched_doc,
                                    'content': snippet,
                                    'relevance': reuse_info
                                })
            
            elif section.startswith('NEXT STEPS:'):
                current_section = 'steps'
                steps_lines = section.split('\n')[1:]  # Skip header
                for line in steps_lines:
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-')):
                        # Remove numbering or bullets
                        step_text = line.lstrip('0123456789.-) ').strip()
                        if step_text:
                            # Check if this step has a title (text before colon)
                            if '**' in step_text:
                                # Parse markdown-style bold text
                                step_text = step_text.replace('**', '')
                            result['next_steps'].append(step_text)
            
            elif current_section == 'explanation' and section:
                result['summary'] += ' ' + section
                # Also add to alignment reasons
                sentences = section.split('. ')
                for sentence in sentences:
                    if sentence.strip():
                        result['alignment_reasons'].append(sentence.strip() + ('.' if not sentence.endswith('.') else ''))
            
        # Clean up summary
        result['summary'] = result['summary'].strip()
        
        # Ensure we have at least some content
        if not result['summary']:
            result['summary'] = "This opportunity aligns with your research profile."
            result['alignment_reasons'] = ["Your expertise matches the technical requirements.", "Your research background is relevant to this solicitation."]
        
        if not result['next_steps']:
            result['next_steps'] = [
                "Review the full solicitation at the provided URL",
                "Check eligibility requirements",
                "Contact the program officer with questions"
            ]
        
        # If no reusable content was parsed, try to add some based on available documents
        if not result['reusable_content'] and user_documents:
            # Add at least one document reference with generic relevance
            doc_names = list(user_documents.keys())[:2]  # Take first 2 documents
            for doc_name in doc_names:
                snippet = self._extract_relevant_snippet(doc_name, user_documents)
                result['reusable_content'].append({
                    'source': doc_name,
                    'content': snippet,
                    'relevance': 'This document contains relevant research experience and methodologies that could strengthen your proposal.'
                })
        
        return result
    
    def _match_document_name(self, 
                            mentioned_name: str,
                            user_documents: Dict[str, str]) -> Optional[str]:
        """Match mentioned document name with actual document"""
        
        mentioned_lower = mentioned_name.lower()
        
        # Try exact match first
        for doc_name in user_documents.keys():
            if mentioned_lower in doc_name.lower() or doc_name.lower() in mentioned_lower:
                return doc_name
        
        # Try partial matches
        keywords = mentioned_lower.split()
        for doc_name in user_documents.keys():
            doc_lower = doc_name.lower()
            if any(keyword in doc_lower for keyword in keywords if len(keyword) > 3):
                return doc_name
        
        return None
    
    def _extract_relevant_snippet(self, 
                                 doc_name: str, 
                                 user_documents: Dict[str, str]) -> str:
        """Extract a relevant snippet from the document"""
        if doc_name not in user_documents:
            return f"Content from {doc_name}"
        
        # Get document content
        content = user_documents[doc_name]
        if not content:
            return f"Content from {doc_name}"
        
        # Try to extract a meaningful snippet
        # Look for key sections like abstract, summary, objectives
        content_lower = content.lower()
        
        # Common section headers to look for
        sections = ['abstract', 'summary', 'executive summary', 'objectives', 'overview', 'introduction']
        
        for section in sections:
            if section in content_lower:
                # Find the section
                start_idx = content_lower.find(section)
                # Extract next 200-300 characters after the section header
                snippet_start = start_idx
                snippet = content[snippet_start:snippet_start + 300]
                
                # Clean up the snippet
                if len(snippet) > 250:
                    # Find a good break point (period, newline)
                    for i in range(250, len(snippet)):
                        if snippet[i] in '.!?\n':
                            snippet = snippet[:i+1]
                            break
                
                return snippet.strip()
        
        # If no section found, return first 200 characters
        snippet = content[:250]
        if len(content) > 250:
            # Find a good break point
            for i in range(200, 250):
                if snippet[i] in '.!?\n ':
                    snippet = snippet[:i+1]
                    break
        
        return snippet.strip() + "..."
    
    def generate_batch_explanations(self,
                                   user_profile: Dict[str, Any],
                                   opportunities: List[Dict[str, Any]],
                                   user_documents: Dict[str, str],
                                   top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Generate explanations for top N opportunities
        
        Args:
            user_profile: User profile
            opportunities: List of matched opportunities
            user_documents: User's documents
            top_n: Number of opportunities to explain
            
        Returns:
            List of opportunities with explanations
        """
        explained_opportunities = []
        
        # Take top N opportunities
        for i, opportunity in enumerate(opportunities[:top_n]):
            print(f"Generating explanation for opportunity {i+1}/{top_n}...")
            
            # Generate explanation
            explanation = self.explain_match(user_profile, opportunity, user_documents)
            
            # Add explanation to opportunity
            opportunity_with_explanation = opportunity.copy()
            opportunity_with_explanation['explanation'] = explanation
            
            explained_opportunities.append(opportunity_with_explanation)
        
        return explained_opportunities