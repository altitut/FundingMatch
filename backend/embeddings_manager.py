"""
Gemini Embeddings Manager for FundingMatch
Handles embedding generation using Google's gemini-embedding-001 model
"""

import os
import time
import json
from typing import List, Dict, Any, Optional
from google import genai
from dotenv import load_dotenv
import numpy as np

load_dotenv()


class GeminiEmbeddingsManager:
    """Manages embedding generation using Gemini API"""
    
    def __init__(self):
        """Initialize the Gemini embeddings client"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-embedding-001'  # Embedding model
        
    def generate_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            task_type: Type of task (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.)
            
        Returns:
            List of embedding values
        """
        try:
            response = self.client.models.embed(
                model=self.model,
                content=text
            )
            return response.embeddings[0].values
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            task_type: Type of task
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for i, text in enumerate(texts):
            try:
                embedding = self.generate_embedding(text, task_type)
                embeddings.append(embedding)
                
                # Rate limiting (60 RPM)
                if (i + 1) % 60 == 0:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Error processing text {i}: {e}")
                embeddings.append(None)
                
        return embeddings
    
    def embed_researcher_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate embeddings for researcher profile components
        
        Args:
            profile: Researcher semantic profile
            
        Returns:
            Profile with embeddings added
        """
        # Create comprehensive text representation
        profile_text = self._create_profile_text(profile)
        
        # Generate embedding
        embedding = self.generate_embedding(profile_text, "RETRIEVAL_DOCUMENT")
        
        # Add embedding to profile
        profile['embedding'] = embedding
        profile['embedding_model'] = self.model
        profile['embedding_timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        return profile
    
    def embed_funding_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate embeddings for funding opportunity
        
        Args:
            opportunity: Funding opportunity data
            
        Returns:
            Opportunity with embeddings added
        """
        # Create comprehensive text representation
        opp_text = self._create_opportunity_text(opportunity)
        
        # Generate embedding
        embedding = self.generate_embedding(opp_text, "RETRIEVAL_DOCUMENT")
        
        # Add embedding to opportunity
        opportunity['embedding'] = embedding
        opportunity['embedding_model'] = self.model
        opportunity['embedding_timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        return opportunity
    
    def _create_profile_text(self, profile: Dict[str, Any]) -> str:
        """Create text representation of researcher profile for embedding"""
        sections = []
        
        # Extract key information
        if 'portfolio_summary' in profile:
            summary = profile['portfolio_summary']
            if 'research_domains' in summary:
                sections.append(f"Research domains: {', '.join(summary['research_domains'])}")
            if 'key_expertise' in summary:
                sections.append(f"Expertise: {', '.join(summary['key_expertise'])}")
                
        if 'synthesis' in profile:
            synthesis = profile['synthesis']
            if 'core_competencies' in synthesis:
                sections.append(f"Core competencies: {' '.join(synthesis['core_competencies'])}")
            if 'research_focus' in synthesis:
                sections.append(f"Research focus: {synthesis['research_focus']}")
                
        # Add publication titles
        if 'publications' in profile:
            titles = [pub.get('title', '') for pub in profile['publications'] if pub.get('title')]
            if titles:
                sections.append(f"Publications: {' '.join(titles[:10])}")  # Limit to 10
                
        # Add proposal history
        if 'proposal_history' in profile:
            history = profile['proposal_history']
            if 'successful_programs' in history:
                sections.append(f"Successful programs: {', '.join(history['successful_programs'])}")
                
        return " ".join(sections)
    
    def _create_opportunity_text(self, opportunity: Dict[str, Any]) -> str:
        """Create text representation of funding opportunity for embedding"""
        sections = []
        
        # Basic information
        if 'title' in opportunity:
            sections.append(f"Title: {opportunity['title']}")
        if 'agency' in opportunity:
            sections.append(f"Agency: {opportunity['agency']}")
        if 'description' in opportunity:
            sections.append(f"Description: {opportunity['description'][:500]}")  # Limit length
            
        # Technical details
        if 'topics' in opportunity:
            sections.append(f"Topics: {', '.join(opportunity['topics'])}")
        if 'keywords' in opportunity:
            sections.append(f"Keywords: {', '.join(opportunity['keywords'])}")
        if 'eligibility' in opportunity:
            sections.append(f"Eligibility: {opportunity['eligibility'][:200]}")
            
        # Semantic analysis if available
        if 'semantic_analysis' in opportunity:
            analysis = opportunity['semantic_analysis']
            if 'technical_focus' in analysis:
                sections.append(f"Technical focus: {', '.join(analysis['technical_focus'])}")
            if 'research_areas' in analysis:
                sections.append(f"Research areas: {', '.join(analysis['research_areas'])}")
                
        return " ".join(sections)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        similarity = dot_product / (norm1 * norm2)
        
        # Ensure result is between 0 and 1
        return float(max(0, min(1, similarity)))


if __name__ == "__main__":
    # Test the embeddings manager
    manager = GeminiEmbeddingsManager()
    
    # Test embedding generation
    test_text = "Machine learning and artificial intelligence for healthcare applications"
    embedding = manager.generate_embedding(test_text)
    print(f"Generated embedding with {len(embedding)} dimensions")
    
    # Test similarity calculation
    text2 = "AI and ML in medical diagnostics"
    embedding2 = manager.generate_embedding(text2)
    similarity = manager.calculate_similarity(embedding, embedding2)
    print(f"Similarity between texts: {similarity:.3f}")