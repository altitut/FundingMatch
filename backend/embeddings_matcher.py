"""
Enhanced Matching System with Embeddings and RAG
Combines vector search with AI-powered explanations and proposal retrofitting
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from tqdm import tqdm

from .embeddings_manager import GeminiEmbeddingsManager
from .vector_database import VectorDatabaseManager
from google import genai
from dotenv import load_dotenv

load_dotenv()


class EmbeddingsEnhancedMatcher:
    """Enhanced matching system using embeddings and RAG"""
    
    def __init__(self):
        """Initialize the enhanced matcher"""
        # Initialize components
        self.embeddings_manager = GeminiEmbeddingsManager()
        self.vector_db = VectorDatabaseManager()
        
        # Initialize Gemini for RAG
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")
            
        self.gemini_client = genai.Client(api_key=api_key)
        self.rag_model = 'gemini-2.5-pro'
        
    def process_researcher_profile(self, profile_path: str) -> str:
        """
        Process researcher profile and add to vector database
        
        Args:
            profile_path: Path to researcher semantic profile JSON
            
        Returns:
            Profile ID
        """
        # Load profile
        with open(profile_path, 'r') as f:
            profile = json.load(f)
            
        # Generate embedding
        profile_with_embedding = self.embeddings_manager.embed_researcher_profile(profile)
        
        # Create profile ID
        researcher_name = profile.get("profile_metadata", {}).get("primary_researcher", "unknown")
        profile_id = f"{researcher_name.lower().replace(' ', '_')}_{int(time.time())}"
        
        # Add to vector database
        self.vector_db.add_researcher_profile(
            profile_id,
            profile,
            profile_with_embedding['embedding']
        )
        
        print(f"Processed researcher profile: {researcher_name}")
        return profile_id
    
    def process_funding_opportunities(self, opportunities_path: str, batch_size: int = 50):
        """
        Process funding opportunities and add to vector database
        
        Args:
            opportunities_path: Path to funding opportunities JSON
            batch_size: Number of opportunities to process in batch
        """
        # Load opportunities
        with open(opportunities_path, 'r') as f:
            opportunities = json.load(f)
            
        if isinstance(opportunities, dict):
            opportunities = list(opportunities.values())
            
        print(f"Processing {len(opportunities)} funding opportunities...")
        
        # Process in batches
        for i in tqdm(range(0, len(opportunities), batch_size)):
            batch = opportunities[i:i + batch_size]
            batch_data = []
            
            for opp in batch:
                try:
                    # Generate embedding
                    opp_with_embedding = self.embeddings_manager.embed_funding_opportunity(opp)
                    
                    # Create opportunity ID
                    opp_id = opp.get('id', f"opp_{int(time.time() * 1000)}")
                    
                    batch_data.append((opp_id, opp, opp_with_embedding['embedding']))
                    
                except Exception as e:
                    print(f"Error processing opportunity: {e}")
                    continue
                    
            # Batch add to database
            if batch_data:
                self.vector_db.batch_add_opportunities(batch_data)
                
            # Rate limiting
            time.sleep(1)
            
        print(f"Added {len(opportunities)} opportunities to vector database")
    
    def match_researcher_to_opportunities(self, 
                                        profile_id: str,
                                        top_k: int = 20,
                                        min_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Match researcher profile to funding opportunities
        
        Args:
            profile_id: Researcher profile ID
            top_k: Number of top matches to return
            min_score: Minimum similarity score threshold
            
        Returns:
            List of matched opportunities with scores and explanations
        """
        # Get researcher profile
        profile = self.vector_db.get_researcher_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")
            
        # Search for matching opportunities
        matches = self.vector_db.search_opportunities_for_profile(
            profile['embedding'],
            n_results=top_k * 2  # Get more to filter by score
        )
        
        # Filter by minimum score
        filtered_matches = [m for m in matches if m['similarity_score'] >= min_score][:top_k]
        
        print(f"Found {len(filtered_matches)} matches above {min_score} threshold")
        
        # Enhance matches with RAG explanations
        enhanced_matches = []
        for match in filtered_matches:
            enhanced_match = self._enhance_match_with_rag(profile, match)
            enhanced_matches.append(enhanced_match)
            
        return enhanced_matches
    
    def _enhance_match_with_rag(self, profile: Dict[str, Any], opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance match with RAG-powered explanation and retrofitting suggestions
        
        Args:
            profile: Researcher profile
            opportunity: Funding opportunity
            
        Returns:
            Enhanced match with explanations
        """
        # Find similar successful proposals
        similar_proposals = self.vector_db.search_similar_proposals(
            opportunity['embedding'],
            n_results=3,
            success_only=True
        )
        
        # Generate RAG prompt
        prompt = self._create_rag_prompt(profile, opportunity, similar_proposals)
        
        # Get AI explanation
        try:
            response = self.gemini_client.models.generate_content(
                model=self.rag_model,
                config={"temperature": 0.7, "max_output_tokens": 1000},
                contents=prompt
            )
            
            explanation = response.text
            
        except Exception as e:
            print(f"Error generating explanation: {e}")
            explanation = "Unable to generate detailed explanation."
            
        # Create enhanced match
        enhanced_match = {
            **opportunity,
            "match_explanation": explanation,
            "similar_successful_proposals": [
                {
                    "title": p.get("title", ""),
                    "program": p.get("program", ""),
                    "similarity": p.get("similarity_score", 0)
                }
                for p in similar_proposals
            ],
            "retrofitting_potential": self._assess_retrofitting_potential(profile, opportunity)
        }
        
        return enhanced_match
    
    def _create_rag_prompt(self, 
                          profile: Dict[str, Any], 
                          opportunity: Dict[str, Any],
                          similar_proposals: List[Dict[str, Any]]) -> str:
        """Create prompt for RAG explanation"""
        
        # Extract key information
        researcher_expertise = profile.get("portfolio_summary", {}).get("key_expertise", [])
        research_domains = profile.get("portfolio_summary", {}).get("research_domains", [])
        
        opp_title = opportunity.get("title", "Unknown")
        opp_description = opportunity.get("description", "")[:500]
        
        prompt = f"""
        As a funding expert, explain why this funding opportunity is a strong match for the researcher.
        
        RESEARCHER PROFILE:
        - Expertise: {', '.join(researcher_expertise[:5])}
        - Research Domains: {', '.join(research_domains[:5])}
        - Funding Track Record: ${profile.get('portfolio_summary', {}).get('funding_track_record', {}).get('total_secured', 0):,}
        
        FUNDING OPPORTUNITY:
        - Title: {opp_title}
        - Agency: {opportunity.get('agency', 'Unknown')}
        - Description: {opp_description}
        
        SIMILAR SUCCESSFUL PROPOSALS:
        """
        
        for i, proposal in enumerate(similar_proposals[:3], 1):
            prompt += f"\n{i}. {proposal.get('title', 'Unknown')} (Similarity: {proposal.get('similarity_score', 0):.2f})"
            
        prompt += """
        
        Please provide:
        1. Why this is a good match (2-3 key reasons)
        2. How the researcher's background aligns with the opportunity
        3. Specific suggestions for proposal development
        4. Which unsuccessful proposal could be retrofitted for this opportunity
        
        Keep the response concise and actionable.
        """
        
        return prompt
    
    def _assess_retrofitting_potential(self, 
                                     profile: Dict[str, Any], 
                                     opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess potential for retrofitting unsuccessful proposals
        
        Args:
            profile: Researcher profile
            opportunity: Funding opportunity
            
        Returns:
            Retrofitting assessment
        """
        # Get unsuccessful proposals from profile
        unsuccessful_proposals = []
        if 'proposal_history' in profile:
            history = profile['proposal_history']
            if 'unsuccessful_proposals' in history:
                unsuccessful_proposals = history['unsuccessful_proposals']
                
        # Find best retrofit candidate
        best_candidate = None
        max_overlap = 0
        
        for proposal in unsuccessful_proposals:
            # Simple keyword overlap for now
            proposal_keywords = set(proposal.get('keywords', []))
            opp_keywords = set(opportunity.get('keywords', []))
            
            overlap = len(proposal_keywords & opp_keywords)
            if overlap > max_overlap:
                max_overlap = overlap
                best_candidate = proposal
                
        return {
            "has_retrofit_candidate": best_candidate is not None,
            "best_candidate": best_candidate.get('title', '') if best_candidate else None,
            "keyword_overlap": max_overlap,
            "retrofit_score": min(max_overlap / 5.0, 1.0) if best_candidate else 0  # Normalize to 0-1
        }
    
    def generate_match_report(self, 
                            profile_id: str, 
                            matches: List[Dict[str, Any]],
                            output_path: str):
        """
        Generate comprehensive matching report
        
        Args:
            profile_id: Researcher profile ID
            matches: List of enhanced matches
            output_path: Path to save report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = f"""# Embeddings-Enhanced Funding Match Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary
- Total Matches: {len(matches)}
- High Confidence Matches (≥85%): {len([m for m in matches if m['similarity_score'] >= 0.85])}
- Retrofit Opportunities: {len([m for m in matches if m['retrofitting_potential']['has_retrofit_candidate']])}

## Top Funding Matches

"""
        
        for i, match in enumerate(matches[:10], 1):
            score_pct = match['similarity_score'] * 100
            
            report += f"""### {i}. {match.get('title', 'Unknown')}
**Agency:** {match.get('agency', 'Unknown')}  
**Deadline:** {match.get('close_date', 'N/A')}  
**Match Score:** {score_pct:.1f}%  
**Award Amount:** {match.get('award_amount', 'Not specified')}

#### Why This Match?
{match.get('match_explanation', 'No explanation available')}

#### Retrofitting Potential
"""
            
            if match['retrofitting_potential']['has_retrofit_candidate']:
                report += f"- **Recommended Proposal to Retrofit:** {match['retrofitting_potential']['best_candidate']}\n"
                report += f"- **Retrofit Score:** {match['retrofitting_potential']['retrofit_score']:.2f}\n"
            else:
                report += "- No suitable proposal for retrofitting identified\n"
                
            report += "\n---\n\n"
            
        # Save report
        with open(output_path, 'w') as f:
            f.write(report)
            
        print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    # Test the enhanced matcher
    matcher = EmbeddingsEnhancedMatcher()
    
    print("Enhanced Embeddings Matcher initialized successfully!")
    print(f"Vector DB stats: {matcher.vector_db.get_collection_stats()}")