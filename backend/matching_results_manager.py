"""
Matching Results Manager - Stores and retrieves user-specific funding matches
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class MatchingResultsManager:
    """Manages storage and retrieval of user funding matches"""
    
    def __init__(self, db_path: str = "./matching_results.db"):
        """
        Initialize the matching results database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funding_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                opportunity_id TEXT NOT NULL,
                title TEXT NOT NULL,
                agency TEXT NOT NULL,
                deadline TEXT NOT NULL,
                url TEXT,
                description TEXT,
                keywords TEXT,
                confidence_score REAL NOT NULL,
                similarity_score REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, opportunity_id)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_matches 
            ON funding_matches(user_id, confidence_score DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def save_matches(self, user_id: str, matches: List[Dict[str, Any]]) -> bool:
        """
        Save matching results for a user
        
        Args:
            user_id: User identifier
            matches: List of matching opportunities
            
        Returns:
            Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear existing matches for user
            cursor.execute("DELETE FROM funding_matches WHERE user_id = ?", (user_id,))
            
            # Insert new matches
            for match in matches:
                # Extract opportunity ID from match
                opp_id = match.get('match_id', '') or match.get('id', '') or match.get('title', '').replace(' ', '_')[:50]
                
                cursor.execute("""
                    INSERT OR REPLACE INTO funding_matches 
                    (user_id, opportunity_id, title, agency, deadline, url, 
                     description, keywords, confidence_score, similarity_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    opp_id,
                    match.get('title', 'Unknown'),
                    match.get('agency', 'Unknown'),
                    match.get('deadline', match.get('close_date', 'Not specified')),
                    match.get('url', ''),
                    match.get('description', ''),
                    json.dumps(match.get('keywords', [])),
                    match.get('confidence_score', 0),
                    match.get('similarity_score', 0)
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error saving matches: {e}")
            return False
    
    def get_matches(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve matching results for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of results to return
            
        Returns:
            List of matching opportunities sorted by confidence score
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM funding_matches 
                WHERE user_id = ? 
                ORDER BY confidence_score DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
            matches = []
            for row in rows:
                match = dict(row)
                # Parse keywords from JSON
                try:
                    match['keywords'] = json.loads(match['keywords'])
                except:
                    match['keywords'] = []
                matches.append(match)
            
            conn.close()
            return matches
            
        except Exception as e:
            print(f"Error retrieving matches: {e}")
            return []
    
    def get_match_count(self, user_id: str) -> int:
        """Get total number of matches for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) FROM funding_matches WHERE user_id = ?", 
                (user_id,)
            )
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            print(f"Error getting match count: {e}")
            return 0
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent search activities across all users"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, COUNT(*) as match_count, 
                       MAX(created_at) as last_search
                FROM funding_matches 
                GROUP BY user_id 
                ORDER BY last_search DESC 
                LIMIT ?
            """, (limit,))
            
            searches = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return searches
            
        except Exception as e:
            print(f"Error getting recent searches: {e}")
            return []


if __name__ == "__main__":
    # Test the matching results manager
    manager = MatchingResultsManager()
    
    # Test save
    test_matches = [
        {
            'title': 'Test Opportunity 1',
            'agency': 'NSF',
            'deadline': '2025-12-31',
            'confidence_score': 85.5,
            'similarity_score': 0.855
        },
        {
            'title': 'Test Opportunity 2',
            'agency': 'NIH',
            'deadline': '2025-11-30',
            'confidence_score': 72.3,
            'similarity_score': 0.723
        }
    ]
    
    manager.save_matches('test_user', test_matches)
    
    # Test retrieve
    results = manager.get_matches('test_user')
    print(f"Retrieved {len(results)} matches")
    
    # Test count
    count = manager.get_match_count('test_user')
    print(f"Total matches: {count}")