#!/usr/bin/env python3
"""
User Profile Manager - Creates embeddings from user documents and matches with opportunities
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

from .pdf_extractor import PDFExtractor
from .url_content_fetcher import URLContentFetcher
from .embeddings_manager import GeminiEmbeddingsManager
from .vector_database import VectorDatabaseManager


class UserProfileManager:
    """Manages user profiles and matches them with funding opportunities"""
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.url_fetcher = URLContentFetcher()
        self.embeddings_manager = GeminiEmbeddingsManager()
        self.vector_db = VectorDatabaseManager()
        
    def create_user_profile(self, user_json_path: str, pdf_paths: List[str]) -> Dict[str, Any]:
        """
        Create a comprehensive user profile from JSON and PDF documents
        
        Args:
            user_json_path: Path to user JSON file
            pdf_paths: List of PDF document paths
            
        Returns:
            User profile dictionary
        """
        profile = {
            'id': '',
            'name': '',
            'summary': '',
            'research_interests': [],
            'education': [],
            'experience': '',
            'publications': '',
            'awards': [],
            'skills': '',
            'urls': [],
            'extracted_pdfs': {},
            'combined_text': ''
        }
        
        # 1. Load JSON data
        if os.path.exists(user_json_path):
            with open(user_json_path, 'r') as f:
                user_data = json.load(f)
            
            person = user_data.get('person', {})
            profile['name'] = person.get('name', '')
            profile['summary'] = person.get('summary', '')
            
            bio_info = person.get('biographical_information', {})
            profile['research_interests'] = bio_info.get('research_interests', [])
            profile['education'] = bio_info.get('education', [])
            profile['awards'] = bio_info.get('awards', [])
            
            # Store URLs for later processing
            profile['urls'] = person.get('links', [])
            
            print(f"✓ Loaded user data for {profile['name']}")
        
        # 2. Extract PDF content
        pdf_content = self.pdf_extractor.extract_from_multiple_pdfs(pdf_paths)
        profile['extracted_pdfs'] = pdf_content
        
        # 3. Extract key sections from PDFs
        all_pdf_text = "\n\n".join(pdf_content.values())
        if all_pdf_text:
            sections = self.pdf_extractor.extract_key_sections(all_pdf_text)
            profile['experience'] = sections.get('experience', '')
            profile['publications'] = sections.get('publications', '')
            profile['skills'] = sections.get('skills', '')
        
        # 4. Process URLs
        url_contents = []
        for link in profile['urls']:
            url = link.get('url', '')
            if url:
                print(f"Fetching content from: {url}")
                content = self.url_fetcher.fetch_url_content(url)
                if content:
                    url_contents.append(f"From {link.get('type', 'web')}: {content.get('text', '')[:500]}")
        
        # 5. Create combined text for embedding
        combined_parts = [
            f"Name: {profile['name']}",
            f"Summary: {profile['summary']}",
            f"Research Interests: {', '.join(profile['research_interests'])}",
            f"Education: {json.dumps(profile['education'])}",
            f"Awards: {json.dumps(profile['awards'])}",
            f"Experience: {profile['experience'][:1000]}",
            f"Publications: {profile['publications'][:1000]}",
            f"Skills: {profile['skills'][:500]}",
            "\n".join(url_contents),
            all_pdf_text[:3000]  # Include some PDF content
        ]
        
        profile['combined_text'] = "\n\n".join(filter(None, combined_parts))
        
        # Generate unique ID
        profile['id'] = hashlib.md5(profile['name'].encode()).hexdigest()
        
        return profile
    
    def store_user_profile(self, profile: Dict[str, Any]) -> bool:
        """
        Store user profile with embeddings
        
        Args:
            profile: User profile dictionary
            
        Returns:
            Success status
        """
        try:
            # Generate embedding for the profile
            embedding = self.embeddings_manager.generate_embedding(
                profile['combined_text'],
                task_type="RETRIEVAL_DOCUMENT"
            )
            
            if embedding is None:
                print("Failed to generate embedding for user profile")
                return False
            
            # Store in vector database
            self.vector_db.add_researcher_profile(
                profile_id=profile['id'],
                profile={
                    'name': profile['name'],
                    'research_interests': profile['research_interests'],
                    'education': json.dumps(profile['education']),
                    'awards': json.dumps(profile['awards']),
                    'experience': profile['experience'][:500],
                    'publications': profile['publications'][:500],
                    'skills': profile['skills'][:500],
                    'summary': profile['summary']
                },
                embedding=embedding
            )
            
            print(f"✓ Stored profile for {profile['name']} with embedding")
            return True
            
        except Exception as e:
            print(f"Error storing user profile: {e}")
            return False
    
    def match_user_to_opportunities(self, user_profile: Dict[str, Any], 
                                  n_results: int = 20) -> List[Dict[str, Any]]:
        """
        Match user profile to funding opportunities
        
        Args:
            user_profile: User profile dictionary
            n_results: Number of results to return
            
        Returns:
            List of matched opportunities with scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings_manager.generate_embedding(
                user_profile['combined_text'],
                task_type="RETRIEVAL_QUERY"
            )
            
            if query_embedding is None:
                print("Failed to generate query embedding")
                return []
            
            # Search for matching opportunities
            matches = self.vector_db.search_opportunities_for_profile(
                query_embedding,
                n_results=n_results
            )
            
            # Calculate confidence scores (0-100)
            ranked_opportunities = []
            for match in matches:
                # Similarity score from vector DB is typically 0-1 for cosine similarity
                # Convert to percentage confidence
                similarity = match.get('similarity_score', 0)
                confidence = min(100, max(0, similarity * 100))
                
                # Boost confidence based on keyword matches
                keywords_boost = self._calculate_keyword_boost(
                    user_profile['research_interests'],
                    match.get('keywords', [])
                )
                
                final_confidence = min(100, confidence + keywords_boost)
                
                ranked_opportunities.append({
                    'title': match.get('title', 'Unknown'),
                    'agency': match.get('agency', 'Unknown'),
                    'description': match.get('description', '')[:200] + '...',
                    'keywords': match.get('keywords', [])[:5],
                    'deadline': match.get('close_date', 'Not specified'),
                    'url': match.get('url', ''),
                    'confidence_score': round(final_confidence, 1),
                    'similarity_score': round(similarity, 3)
                })
            
            # Sort by confidence score
            ranked_opportunities.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            return ranked_opportunities
            
        except Exception as e:
            print(f"Error matching user to opportunities: {e}")
            return []
    
    def _calculate_keyword_boost(self, user_interests: List[str], 
                               opportunity_keywords: List[str]) -> float:
        """Calculate boost based on keyword matches"""
        if not user_interests or not opportunity_keywords:
            return 0.0
        
        # Convert to lowercase for comparison
        user_interests_lower = [i.lower() for i in user_interests]
        opp_keywords_lower = [k.lower() if isinstance(k, str) else str(k).lower() 
                             for k in opportunity_keywords]
        
        # Count matches
        matches = 0
        for interest in user_interests_lower:
            for keyword in opp_keywords_lower:
                if interest in keyword or keyword in interest:
                    matches += 1
        
        # Calculate boost (max 20 points)
        boost = min(20, matches * 5)
        return boost