"""
Vector Database Manager for FundingMatch
Uses ChromaDB for storing and searching embeddings
"""

import os
import json
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime


class VectorDatabaseManager:
    """Manages vector storage and retrieval using ChromaDB"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize ChromaDB client
        
        Args:
            persist_directory: Directory to persist the database
        """
        self.persist_directory = persist_directory
        
        # Create ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize collections
        self._init_collections()
        
    def _init_collections(self):
        """Initialize or get existing collections"""
        # Researcher profiles collection
        self.researchers = self.client.get_or_create_collection(
            name="researcher_profiles",
            metadata={"description": "Researcher semantic profiles with embeddings"}
        )
        
        # Funding opportunities collection
        self.opportunities = self.client.get_or_create_collection(
            name="funding_opportunities",
            metadata={"description": "Funding opportunities with embeddings"}
        )
        
        # Proposals collection (for retrofitting analysis)
        self.proposals = self.client.get_or_create_collection(
            name="proposals",
            metadata={"description": "Historical proposals for retrofitting analysis"}
        )
        
    def add_researcher_profile(self, profile_id: str, profile: Dict[str, Any], embedding: List[float]):
        """
        Add researcher profile to vector database
        
        Args:
            profile_id: Unique identifier for the profile
            profile: Profile data
            embedding: Profile embedding vector
        """
        # Prepare metadata (ChromaDB has limits on metadata)
        metadata = {
            "researcher_name": profile.get("profile_metadata", {}).get("primary_researcher", "Unknown"),
            "total_documents": str(profile.get("profile_metadata", {}).get("total_documents", 0)),
            "research_domains": json.dumps(profile.get("portfolio_summary", {}).get("research_domains", [])),
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in ChromaDB
        self.researchers.upsert(
            ids=[profile_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[json.dumps(profile)]  # Store full profile as document
        )
        
    def add_funding_opportunity(self, opp_id: str, opportunity: Dict[str, Any], embedding: List[float]):
        """
        Add funding opportunity to vector database
        
        Args:
            opp_id: Unique identifier for the opportunity
            opportunity: Opportunity data
            embedding: Opportunity embedding vector
        """
        # Prepare metadata
        metadata = {
            "title": opportunity.get("title", "")[:100],  # Limit length
            "agency": opportunity.get("agency", ""),
            "deadline": opportunity.get("close_date", ""),
            "award_amount": str(opportunity.get("award_amount", "")),
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in ChromaDB
        self.opportunities.upsert(
            ids=[opp_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[json.dumps(opportunity)]
        )
        
    def add_proposal(self, proposal_id: str, proposal: Dict[str, Any], embedding: List[float]):
        """
        Add proposal to vector database
        
        Args:
            proposal_id: Unique identifier for the proposal
            proposal: Proposal data
            embedding: Proposal embedding vector
        """
        # Prepare metadata
        metadata = {
            "title": proposal.get("title", "")[:100],
            "program": proposal.get("program", ""),
            "success": str(proposal.get("success", False)),
            "agency": proposal.get("agency", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in ChromaDB
        self.proposals.upsert(
            ids=[proposal_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[json.dumps(proposal)]
        )
        
    def search_opportunities_for_profile(self, 
                                       profile_embedding: List[float], 
                                       n_results: int = 20,
                                       filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for matching opportunities given a researcher profile embedding
        
        Args:
            profile_embedding: Researcher profile embedding
            n_results: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of matching opportunities with scores
        """
        # Query ChromaDB
        results = self.opportunities.query(
            query_embeddings=[profile_embedding],
            n_results=n_results,
            where=filter_dict
        )
        
        # Parse results
        opportunities = []
        for i in range(len(results['ids'][0])):
            opportunity = json.loads(results['documents'][0][i])
            opportunity['similarity_score'] = 1 - results['distances'][0][i]  # Convert distance to similarity
            opportunity['match_id'] = results['ids'][0][i]
            opportunities.append(opportunity)
            
        return opportunities
    
    def search_similar_proposals(self, 
                               opportunity_embedding: List[float], 
                               n_results: int = 5,
                               success_only: bool = False) -> List[Dict[str, Any]]:
        """
        Search for similar proposals given an opportunity embedding
        
        Args:
            opportunity_embedding: Opportunity embedding
            n_results: Number of results to return
            success_only: Only return successful proposals
            
        Returns:
            List of similar proposals with scores
        """
        # Build filter
        filter_dict = {"success": "True"} if success_only else None
        
        # Query ChromaDB
        results = self.proposals.query(
            query_embeddings=[opportunity_embedding],
            n_results=n_results,
            where=filter_dict
        )
        
        # Parse results
        proposals = []
        for i in range(len(results['ids'][0])):
            proposal = json.loads(results['documents'][0][i])
            proposal['similarity_score'] = 1 - results['distances'][0][i]
            proposal['match_id'] = results['ids'][0][i]
            proposals.append(proposal)
            
        return proposals
    
    def get_researcher_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get researcher profile by ID"""
        result = self.researchers.get(ids=[profile_id])
        if result['documents']:
            return json.loads(result['documents'][0])
        return None
    
    def get_opportunity(self, opp_id: str) -> Optional[Dict[str, Any]]:
        """Get opportunity by ID"""
        result = self.opportunities.get(ids=[opp_id])
        if result['documents']:
            return json.loads(result['documents'][0])
        return None
    
    def batch_add_opportunities(self, opportunities: List[Tuple[str, Dict[str, Any], List[float]]]):
        """
        Batch add multiple opportunities
        
        Args:
            opportunities: List of (id, opportunity_data, embedding) tuples
        """
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for opp_id, opportunity, embedding in opportunities:
            ids.append(opp_id)
            embeddings.append(embedding)
            
            # Prepare metadata
            metadata = {
                "title": opportunity.get("title", "")[:100],
                "agency": opportunity.get("agency", ""),
                "deadline": opportunity.get("close_date", ""),
                "award_amount": str(opportunity.get("award_amount", "")),
                "timestamp": datetime.now().isoformat()
            }
            metadatas.append(metadata)
            documents.append(json.dumps(opportunity))
        
        # Batch upsert
        self.opportunities.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about collections"""
        return {
            "researchers": self.researchers.count(),
            "opportunities": self.opportunities.count(),
            "proposals": self.proposals.count()
        }
    
    def clear_collection(self, collection_name: str):
        """Clear a specific collection"""
        if collection_name == "researchers":
            self.client.delete_collection("researcher_profiles")
            self._init_collections()
        elif collection_name == "opportunities":
            self.client.delete_collection("funding_opportunities")
            self._init_collections()
        elif collection_name == "proposals":
            self.client.delete_collection("proposals")
            self._init_collections()


if __name__ == "__main__":
    # Test the vector database
    db = VectorDatabaseManager()
    
    # Print collection stats
    stats = db.get_collection_stats()
    print(f"Collection stats: {stats}")
    
    # Test adding a dummy profile
    test_embedding = [0.1] * 768  # Dummy 768-dim embedding
    test_profile = {
        "profile_metadata": {"primary_researcher": "Test Researcher"},
        "portfolio_summary": {"research_domains": ["AI", "ML"]}
    }
    
    db.add_researcher_profile("test_001", test_profile, test_embedding)
    print("Added test profile to database")