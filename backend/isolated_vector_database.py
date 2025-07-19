"""
Isolated Vector Database Manager for FundingMatch
Uses separate ChromaDB instances for users and opportunities to prevent corruption
"""

import os
import json
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import shutil
import traceback


class IsolatedVectorDatabaseManager:
    """Manages vector storage with complete isolation between users and opportunities"""
    
    def __init__(self, 
                 users_db_path: str = "./chroma_db_users",
                 opportunities_db_path: str = "./chroma_db_opportunities",
                 proposals_db_path: str = "./chroma_db_proposals"):
        """
        Initialize separate ChromaDB instances for complete isolation
        
        Args:
            users_db_path: Directory for user profiles database
            opportunities_db_path: Directory for opportunities database
            proposals_db_path: Directory for proposals database
        """
        self.users_db_path = users_db_path
        self.opportunities_db_path = opportunities_db_path
        self.proposals_db_path = proposals_db_path
        
        # Initialize separate clients
        self.users_client = self._init_client(users_db_path, "users")
        self.opportunities_client = self._init_client(opportunities_db_path, "opportunities")
        self.proposals_client = self._init_client(proposals_db_path, "proposals")
        
        # Initialize collections
        self._init_collections()
        
    def _init_client(self, db_path: str, db_name: str) -> chromadb.PersistentClient:
        """Initialize a ChromaDB client with error recovery"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                client = chromadb.PersistentClient(
                    path=db_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                print(f"✓ Successfully initialized {db_name} database at {db_path}")
                return client
            except Exception as e:
                print(f"Error initializing {db_name} database (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    # Remove corrupted database and retry
                    if os.path.exists(db_path):
                        try:
                            shutil.rmtree(db_path)
                            print(f"Removed corrupted {db_name} database, retrying...")
                        except Exception as rm_err:
                            print(f"Failed to remove corrupted database: {rm_err}")
                else:
                    raise Exception(f"Failed to initialize {db_name} database after {max_retries} attempts")
    
    def _init_collections(self):
        """Initialize collections in separate databases"""
        try:
            # Users database - researcher profiles
            self.researchers = self.users_client.get_or_create_collection(
                name="researcher_profiles",
                metadata={"description": "Researcher semantic profiles with embeddings"}
            )
            print("✓ Initialized researcher profiles collection")
        except Exception as e:
            print(f"Error initializing researchers collection: {e}")
            self.researchers = None
            
        try:
            # Opportunities database - funding opportunities
            self.opportunities = self.opportunities_client.get_or_create_collection(
                name="funding_opportunities",
                metadata={"description": "Funding opportunities with embeddings"}
            )
            print("✓ Initialized funding opportunities collection")
        except Exception as e:
            print(f"Error initializing opportunities collection: {e}")
            self.opportunities = None
            
        try:
            # Proposals database - historical proposals
            self.proposals = self.proposals_client.get_or_create_collection(
                name="proposals",
                metadata={"description": "Historical proposals for retrofitting analysis"}
            )
            print("✓ Initialized proposals collection")
        except Exception as e:
            print(f"Error initializing proposals collection: {e}")
            self.proposals = None
    
    def _safe_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """Execute database operation with error isolation"""
        try:
            return operation_func(*args, **kwargs)
        except Exception as e:
            print(f"Error in {operation_name}: {e}")
            traceback.print_exc()
            
            # Check if it's a corruption error
            error_str = str(e).lower()
            if "no such column" in error_str or "database" in error_str or "corrupt" in error_str:
                print(f"Database corruption detected in {operation_name}")
                
                # Attempt recovery based on operation
                if "researcher" in operation_name.lower():
                    self._attempt_recovery("users")
                elif "opportunit" in operation_name.lower():
                    self._attempt_recovery("opportunities")
                elif "proposal" in operation_name.lower():
                    self._attempt_recovery("proposals")
            
            return None
    
    def _attempt_recovery(self, db_type: str):
        """Attempt to recover a corrupted database"""
        print(f"Attempting recovery for {db_type} database...")
        
        try:
            if db_type == "users":
                self.users_client = self._init_client(self.users_db_path, "users")
                self.researchers = self.users_client.get_or_create_collection(
                    name="researcher_profiles",
                    metadata={"description": "Researcher semantic profiles with embeddings"}
                )
            elif db_type == "opportunities":
                self.opportunities_client = self._init_client(self.opportunities_db_path, "opportunities")
                self.opportunities = self.opportunities_client.get_or_create_collection(
                    name="funding_opportunities",
                    metadata={"description": "Funding opportunities with embeddings"}
                )
            elif db_type == "proposals":
                self.proposals_client = self._init_client(self.proposals_db_path, "proposals")
                self.proposals = self.proposals_client.get_or_create_collection(
                    name="proposals",
                    metadata={"description": "Historical proposals for retrofitting analysis"}
                )
            
            print(f"✓ Successfully recovered {db_type} database")
        except Exception as e:
            print(f"Failed to recover {db_type} database: {e}")
    
    def add_researcher_profile(self, profile_id: str, profile: Dict[str, Any], embedding: List[float]):
        """Add researcher profile with isolated error handling"""
        def _add():
            if not self.researchers:
                raise Exception("Researchers collection not initialized")
                
            # Check if researcher already exists
            try:
                existing = self.researchers.get(ids=[profile_id])
                if existing and isinstance(existing, dict) and existing.get('ids') and len(existing['ids']) > 0:
                    print(f"  ℹ️  Researcher profile already exists for {profile.get('name', 'Unknown')}, updating...")
            except Exception:
                pass
            
            # Prepare metadata
            metadata = {
                "researcher_name": str(profile.get("name", "Unknown")),
                "total_documents": str(len(profile.get("extracted_pdfs", {}))),
                "research_interests": json.dumps(profile.get("research_interests", []))[:500],
                "summary": str(profile.get("summary", ""))[:500],
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in ChromaDB
            self.researchers.upsert(
                ids=[profile_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[json.dumps(profile)]
            )
            
            return True
        
        return self._safe_operation("add_researcher_profile", _add)
    
    def add_funding_opportunity(self, opp_id: str, opportunity: Dict[str, Any], embedding: List[float]):
        """Add funding opportunity with isolated error handling"""
        def _add():
            if not self.opportunities:
                raise Exception("Opportunities collection not initialized")
                
            # Prepare metadata
            metadata = {
                "title": opportunity.get("title", "")[:100],
                "agency": opportunity.get("agency", ""),
                "deadline": opportunity.get("close_date", ""),
                "url": opportunity.get("url", ""),
                "program": opportunity.get("program", ""),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in ChromaDB
            self.opportunities.upsert(
                ids=[opp_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[json.dumps(opportunity)]
            )
            
            return True
        
        return self._safe_operation("add_funding_opportunity", _add)
    
    def batch_add_opportunities(self, opportunities: List[Tuple[str, Dict[str, Any], List[float]]]):
        """Batch add opportunities with isolated error handling"""
        def _batch_add():
            if not self.opportunities:
                raise Exception("Opportunities collection not initialized")
                
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
                    "url": opportunity.get("url", ""),
                    "program": opportunity.get("program", ""),
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
            
            return True
        
        return self._safe_operation("batch_add_opportunities", _batch_add)
    
    def search_opportunities_for_profile(self, 
                                       profile_embedding: List[float], 
                                       n_results: int = 20,
                                       filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search opportunities with isolated error handling"""
        def _search():
            if not self.opportunities:
                raise Exception("Opportunities collection not initialized")
                
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
                opportunity['similarity_score'] = 1 - results['distances'][0][i]
                opportunity['match_id'] = results['ids'][0][i]
                opportunities.append(opportunity)
                
            return opportunities
        
        result = self._safe_operation("search_opportunities_for_profile", _search)
        return result if result is not None else []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics with error isolation"""
        stats = {
            "researchers": 0,
            "opportunities": 0,
            "proposals": 0,
            "status": {
                "users_db": "unknown",
                "opportunities_db": "unknown",
                "proposals_db": "unknown"
            }
        }
        
        # Check researchers
        try:
            if self.researchers:
                count = self.researchers.count()
                stats["researchers"] = count
                stats["status"]["users_db"] = "healthy"
        except Exception as e:
            stats["status"]["users_db"] = f"error: {str(e)[:50]}"
        
        # Check opportunities
        try:
            if self.opportunities:
                count = self.opportunities.count()
                stats["opportunities"] = count
                stats["status"]["opportunities_db"] = "healthy"
        except Exception as e:
            stats["status"]["opportunities_db"] = f"error: {str(e)[:50]}"
        
        # Check proposals
        try:
            if self.proposals:
                count = self.proposals.count()
                stats["proposals"] = count
                stats["status"]["proposals_db"] = "healthy"
        except Exception as e:
            stats["status"]["proposals_db"] = f"error: {str(e)[:50]}"
        
        return stats
    
    def get_all_opportunities(self) -> List[Dict[str, Any]]:
        """Get all opportunities with error isolation"""
        def _get_all():
            if not self.opportunities:
                return []
                
            try:
                results = self.opportunities.get()
                
                opportunities = []
                if results and isinstance(results, dict) and 'ids' in results and results['ids']:
                    for i, id in enumerate(results['ids']):
                        metadata = results['metadatas'][i] if 'metadatas' in results else {}
                        # Parse the full document
                        if 'documents' in results and i < len(results['documents']):
                            try:
                                doc = json.loads(results['documents'][i])
                                opportunities.append({
                                    'id': id,
                                    'title': doc.get('title', metadata.get('title', 'Unknown')),
                                    'agency': doc.get('agency', metadata.get('agency', 'Unknown')),
                                    'url': doc.get('url', doc.get('solicitation_url', '')),
                                    'description': (doc.get('description', '')[:200] + '...') if doc.get('description') else '',
                                    'deadline': doc.get('close_date', metadata.get('deadline', '')),
                                    'topic_number': doc.get('topic_number', '')
                                })
                            except:
                                opportunities.append({
                                    'id': id,
                                    'title': metadata.get('title', 'Unknown'),
                                    'agency': metadata.get('agency', 'Unknown'),
                                    'url': metadata.get('url', ''),
                                    'description': '',
                                    'deadline': metadata.get('deadline', '')
                                })
                
                return opportunities
            except Exception as e:
                print(f"Error getting opportunities: {e}")
                return []
        
        result = self._safe_operation("get_all_opportunities", _get_all)
        return result if result is not None else []
    
    def get_all_researchers(self) -> List[Dict[str, Any]]:
        """Get all researchers with error isolation"""
        def _get_all():
            if not self.researchers:
                return []
                
            try:
                results = self.researchers.get()
                
                researchers = []
                if results and results.get('ids'):
                    for i, id in enumerate(results['ids']):
                        metadata = results['metadatas'][i] if results.get('metadatas') else {}
                        researchers.append({
                            'id': id,
                            'name': metadata.get('researcher_name', 'Unknown'),
                            'research_interests': metadata.get('research_interests', []),
                            'summary': metadata.get('summary', '')
                        })
                
                return researchers
            except Exception as e:
                if "empty" in str(e).lower():
                    return []
                print(f"Error getting researchers: {e}")
                return []
        
        result = self._safe_operation("get_all_researchers", _get_all)
        return result if result is not None else []
    
    def clear_collection(self, collection_name: str):
        """Clear a specific collection with error isolation"""
        def _clear():
            if collection_name == "researchers":
                self.users_client.delete_collection("researcher_profiles")
                self.researchers = self.users_client.get_or_create_collection(
                    name="researcher_profiles",
                    metadata={"description": "Researcher semantic profiles with embeddings"}
                )
            elif collection_name == "opportunities":
                self.opportunities_client.delete_collection("funding_opportunities")
                self.opportunities = self.opportunities_client.get_or_create_collection(
                    name="funding_opportunities",
                    metadata={"description": "Funding opportunities with embeddings"}
                )
            elif collection_name == "proposals":
                self.proposals_client.delete_collection("proposals")
                self.proposals = self.proposals_client.get_or_create_collection(
                    name="proposals",
                    metadata={"description": "Historical proposals for retrofitting analysis"}
                )
            return True
        
        return self._safe_operation(f"clear_{collection_name}", _clear)
    
    def remove_researcher(self, researcher_id: str):
        """Remove researcher with error isolation"""
        def _remove():
            if not self.researchers:
                return False
            self.researchers.delete(ids=[researcher_id])
            return True
        
        return self._safe_operation("remove_researcher", _remove)
    
    def validate_databases(self) -> Dict[str, Any]:
        """Validate all databases and report status"""
        validation = {
            "users_db": self._validate_db("users"),
            "opportunities_db": self._validate_db("opportunities"), 
            "proposals_db": self._validate_db("proposals"),
            "overall_status": "healthy"
        }
        
        # Check overall status
        for db_status in validation.values():
            if isinstance(db_status, dict) and db_status.get("status") != "healthy":
                validation["overall_status"] = "degraded"
                break
        
        return validation
    
    def _validate_db(self, db_type: str) -> Dict[str, Any]:
        """Validate a specific database"""
        result = {
            "status": "unknown",
            "message": "",
            "item_count": 0
        }
        
        try:
            if db_type == "users":
                if self.researchers:
                    count = self.researchers.count()
                    result["status"] = "healthy"
                    result["message"] = f"Database operational with {count} items"
                    result["item_count"] = count
                else:
                    result["status"] = "error"
                    result["message"] = "Collection not initialized"
            elif db_type == "opportunities":
                if self.opportunities:
                    count = self.opportunities.count()
                    result["status"] = "healthy"
                    result["message"] = f"Database operational with {count} items"
                    result["item_count"] = count
                else:
                    result["status"] = "error"
                    result["message"] = "Collection not initialized"
            elif db_type == "proposals":
                if self.proposals:
                    count = self.proposals.count()
                    result["status"] = "healthy"
                    result["message"] = f"Database operational with {count} items"
                    result["item_count"] = count
                else:
                    result["status"] = "error"
                    result["message"] = "Collection not initialized"
        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)[:100]
        
        return result


# Create a singleton instance that can be imported
isolated_vector_db = None

def get_isolated_vector_db():
    """Get or create the singleton isolated vector database instance"""
    global isolated_vector_db
    if isolated_vector_db is None:
        isolated_vector_db = IsolatedVectorDatabaseManager()
    return isolated_vector_db


if __name__ == "__main__":
    # Test the isolated vector database
    db = IsolatedVectorDatabaseManager()
    
    # Validate databases
    validation = db.validate_databases()
    print(f"Database validation: {json.dumps(validation, indent=2)}")
    
    # Get stats
    stats = db.get_collection_stats()
    print(f"Collection stats: {json.dumps(stats, indent=2)}")