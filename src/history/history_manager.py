"""
SQLite-based query history manager
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class QueryHistoryEntry:
    """Query history entry structure"""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    database_name: str = ""
    question: str = ""
    generated_query: str = ""
    execution_time: float = 0.0
    row_count: int = 0
    success: bool = True
    error_message: Optional[str] = None
    is_favorite: bool = False
    tags: List[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.tags is None:
            self.tags = []


class HistoryManager:
    """SQLite-based query history manager"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path or self._get_default_db_path()
        self._init_database()
    
    def _get_default_db_path(self) -> str:
        """Get default database path"""
        import os
        if os.name == 'nt':  # Windows
            data_dir = Path.home() / "AppData" / "Local" / "InsightPilot"
        else:  # Unix-like
            data_dir = Path.home() / ".local" / "share" / "insightpilot"
        
        data_dir.mkdir(parents=True, exist_ok=True)
        return str(data_dir / "history.db")
    
    def _init_database(self) -> None:
        """Initialize SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create query history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS query_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        database_name TEXT NOT NULL,
                        question TEXT NOT NULL,
                        generated_query TEXT NOT NULL,
                        execution_time REAL DEFAULT 0.0,
                        row_count INTEGER DEFAULT 0,
                        success BOOLEAN DEFAULT 1,
                        error_message TEXT,
                        is_favorite BOOLEAN DEFAULT 0,
                        tags TEXT DEFAULT '[]'
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON query_history(timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_database_name 
                    ON query_history(database_name)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_favorites 
                    ON query_history(is_favorite)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_success 
                    ON query_history(success)
                ''')
                
                # Create saved queries table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS saved_queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        database_name TEXT NOT NULL,
                        query TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        tags TEXT DEFAULT '[]'
                    )
                ''')
                
                conn.commit()
                self.logger.info(f"History database initialized: {self.db_path}")
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to initialize history database: {e}")
            raise
    
    def add_query(self, entry: QueryHistoryEntry) -> int:
        """Add a query to history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO query_history 
                    (database_name, question, generated_query, execution_time, 
                     row_count, success, error_message, is_favorite, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.database_name,
                    entry.question,
                    entry.generated_query,
                    entry.execution_time,
                    entry.row_count,
                    entry.success,
                    entry.error_message,
                    entry.is_favorite,
                    json.dumps(entry.tags)
                ))
                
                query_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Added query to history: {query_id}")
                return query_id
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to add query to history: {e}")
            raise
    
    def get_recent_queries(self, limit: int = 50) -> List[QueryHistoryEntry]:
        """Get recent queries from history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM query_history 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                return [self._row_to_entry(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get recent queries: {e}")
            return []
    
    def get_queries_by_database(self, database_name: str, limit: int = 50) -> List[QueryHistoryEntry]:
        """Get queries for a specific database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM query_history 
                    WHERE database_name = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (database_name, limit))
                
                return [self._row_to_entry(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get queries by database: {e}")
            return []
    
    def get_favorite_queries(self) -> List[QueryHistoryEntry]:
        """Get favorite queries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM query_history 
                    WHERE is_favorite = 1 
                    ORDER BY timestamp DESC
                ''')
                
                return [self._row_to_entry(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get favorite queries: {e}")
            return []
    
    def toggle_favorite(self, query_id: int) -> bool:
        """Toggle favorite status of a query"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE query_history 
                    SET is_favorite = NOT is_favorite 
                    WHERE id = ?
                ''', (query_id,))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Toggled favorite status for query: {query_id}")
                    return True
                else:
                    self.logger.warning(f"Query not found: {query_id}")
                    return False
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to toggle favorite: {e}")
            return False
    
    def delete_query(self, query_id: int) -> bool:
        """Delete a query from history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM query_history WHERE id = ?', (query_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Deleted query: {query_id}")
                    return True
                else:
                    self.logger.warning(f"Query not found: {query_id}")
                    return False
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete query: {e}")
            return False
    
    def search_queries(self, search_term: str, limit: int = 50) -> List[QueryHistoryEntry]:
        """Search queries by question or query text"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM query_history 
                    WHERE question LIKE ? OR generated_query LIKE ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (f'%{search_term}%', f'%{search_term}%', limit))
                
                return [self._row_to_entry(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to search queries: {e}")
            return []
    
    def cleanup_old_queries(self, days_to_keep: int = 30) -> int:
        """Clean up old queries beyond specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM query_history 
                    WHERE timestamp < ? AND is_favorite = 0
                ''', (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old queries")
                return deleted_count
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to cleanup old queries: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get history statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total queries
                cursor.execute('SELECT COUNT(*) FROM query_history')
                total_queries = cursor.fetchone()[0]
                
                # Successful queries
                cursor.execute('SELECT COUNT(*) FROM query_history WHERE success = 1')
                successful_queries = cursor.fetchone()[0]
                
                # Favorite queries
                cursor.execute('SELECT COUNT(*) FROM query_history WHERE is_favorite = 1')
                favorite_queries = cursor.fetchone()[0]
                
                # Most used databases
                cursor.execute('''
                    SELECT database_name, COUNT(*) as count 
                    FROM query_history 
                    GROUP BY database_name 
                    ORDER BY count DESC 
                    LIMIT 5
                ''')
                top_databases = cursor.fetchall()
                
                # Recent activity (last 7 days)
                week_ago = datetime.now() - timedelta(days=7)
                cursor.execute('''
                    SELECT COUNT(*) FROM query_history 
                    WHERE timestamp >= ?
                ''', (week_ago,))
                recent_activity = cursor.fetchone()[0]
                
                return {
                    "total_queries": total_queries,
                    "successful_queries": successful_queries,
                    "favorite_queries": favorite_queries,
                    "success_rate": successful_queries / total_queries if total_queries > 0 else 0,
                    "top_databases": top_databases,
                    "recent_activity": recent_activity
                }
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def _row_to_entry(self, row) -> QueryHistoryEntry:
        """Convert database row to QueryHistoryEntry"""
        return QueryHistoryEntry(
            id=row[0],
            timestamp=datetime.fromisoformat(row[1]) if row[1] else None,
            database_name=row[2],
            question=row[3],
            generated_query=row[4],
            execution_time=row[5],
            row_count=row[6],
            success=bool(row[7]),
            error_message=row[8],
            is_favorite=bool(row[9]),
            tags=json.loads(row[10]) if row[10] else []
        )
    
    def export_history(self, filepath: str, format: str = "json") -> bool:
        """Export query history to file"""
        try:
            queries = self.get_recent_queries(limit=1000)
            
            if format.lower() == "json":
                with open(filepath, 'w') as f:
                    json.dump([asdict(q) for q in queries], f, indent=2, default=str)
            elif format.lower() == "csv":
                import csv
                with open(filepath, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=asdict(queries[0]).keys())
                    writer.writeheader()
                    for query in queries:
                        row = asdict(query)
                        row['timestamp'] = str(row['timestamp'])
                        row['tags'] = json.dumps(row['tags'])
                        writer.writerow(row)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Exported {len(queries)} queries to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export history: {e}")
            return False
