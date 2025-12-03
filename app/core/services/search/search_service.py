"""
Search Service - General purpose search functionality
Supports both database and in-memory storage with fuzzy matching
"""
import re
from typing import List, Dict, Any, Optional, Callable
from difflib import SequenceMatcher


class SearchService:
    """
    General purpose search service that can work with:
    - Database collections (MongoDB)
    - In-memory data structures (lists, dicts)
    - Custom data sources via adapters
    """
    
    def __init__(self, db_service=None):
        """
        Initialize search service
        
        Args:
            db_service: Optional database service for DB searches
        """
        self.db_service = db_service
    
    def search_memory(
        self,
        data: List[Dict[str, Any]],
        query: str,
        fields: List[str],
        limit: int = 10,
        fuzzy: bool = True,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Search in-memory data structures
        
        Args:
            data: List of dictionaries to search
            query: Search query string
            fields: List of field names to search in
            limit: Maximum number of results
            fuzzy: Enable fuzzy matching
            min_score: Minimum similarity score (0-1) for fuzzy matching
            
        Returns:
            List of matching items with relevance scores
        """
        if not query or not data:
            return data[:limit]
        
        query_lower = query.lower()
        results = []
        
        for item in data:
            score = 0.0
            matches = []
            
            for field in fields:
                field_value = self._get_nested_value(item, field)
                if field_value is None:
                    continue
                
                field_str = str(field_value).lower()
                
                # Exact match (highest score)
                if query_lower == field_str:
                    score += 1.0
                    matches.append(field)
                # Contains match
                elif query_lower in field_str:
                    score += 0.7
                    matches.append(field)
                # Fuzzy match
                elif fuzzy:
                    similarity = self._fuzzy_match(query_lower, field_str)
                    if similarity >= min_score:
                        score += similarity * 0.5
                        matches.append(field)
            
            if score > 0:
                results.append({
                    **item,
                    "_search_score": score,
                    "_search_matches": matches
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x["_search_score"], reverse=True)
        
        return results[:limit]
    
    async def search_database(
        self,
        collection: str,
        query: str,
        fields: List[str],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search database collections using MongoDB text search or regex
        
        Args:
            collection: Collection name
            query: Search query string
            fields: List of field names to search in
            limit: Maximum number of results
            filters: Additional filters to apply
            
        Returns:
            List of matching documents
        """
        if not self.db_service:
            raise ValueError("Database service not configured")
        
        if not query:
            # Return all with filters
            return await self.db_service.find(
                collection,
                filters or {},
                limit=limit
            )
        
        # Build regex search query for multiple fields
        search_conditions = []
        for field in fields:
            search_conditions.append({
                field: {"$regex": query, "$options": "i"}
            })
        
        # Combine with filters
        query_filter = {"$or": search_conditions}
        if filters:
            query_filter = {"$and": [query_filter, filters]}
        
        results = await self.db_service.find(
            collection,
            query_filter,
            limit=limit
        )
        
        return results
    
    def search_with_filters(
        self,
        data: List[Dict[str, Any]],
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        search_fields: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search with additional filters (category, price range, etc.)
        
        Args:
            data: List of dictionaries to search
            query: Optional search query
            filters: Dictionary of field:value filters
            search_fields: Fields to search in (if query provided)
            limit: Maximum results
            
        Returns:
            Filtered and searched results
        """
        # Apply filters first
        filtered_data = data
        if filters:
            filtered_data = [
                item for item in data
                if self._matches_filters(item, filters)
            ]
        
        # Then search if query provided
        if query and search_fields:
            return self.search_memory(
                filtered_data,
                query,
                search_fields,
                limit=limit
            )
        
        return filtered_data[:limit]
    
    def create_search_index(
        self,
        data: List[Dict[str, Any]],
        fields: List[str]
    ) -> Dict[str, List[int]]:
        """
        Create an inverted index for faster searching
        
        Args:
            data: List of dictionaries
            fields: Fields to index
            
        Returns:
            Inverted index mapping terms to item indices
        """
        index = {}
        
        for idx, item in enumerate(data):
            for field in fields:
                value = self._get_nested_value(item, field)
                if value is None:
                    continue
                
                # Tokenize and index
                tokens = self._tokenize(str(value))
                for token in tokens:
                    if token not in index:
                        index[token] = []
                    index[token].append(idx)
        
        return index
    
    def search_with_index(
        self,
        data: List[Dict[str, Any]],
        index: Dict[str, List[int]],
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fast search using pre-built index
        
        Args:
            data: Original data list
            index: Pre-built inverted index
            query: Search query
            limit: Maximum results
            
        Returns:
            Matching items
        """
        tokens = self._tokenize(query.lower())
        matching_indices = set()
        
        for token in tokens:
            if token in index:
                matching_indices.update(index[token])
        
        results = [data[idx] for idx in matching_indices if idx < len(data)]
        return results[:limit]
    
    # Helper methods
    
    def _get_nested_value(self, obj: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = path.split('.')
        value = obj
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
    
    def _fuzzy_match(self, query: str, text: str) -> float:
        """Calculate fuzzy match score using SequenceMatcher"""
        return SequenceMatcher(None, query, text).ratio()
    
    def _matches_filters(self, item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if item matches all filters"""
        for key, value in filters.items():
            item_value = self._get_nested_value(item, key)
            
            # Handle range filters (e.g., {"price": {"$gte": 10, "$lte": 100}})
            if isinstance(value, dict):
                if "$gte" in value and item_value < value["$gte"]:
                    return False
                if "$lte" in value and item_value > value["$lte"]:
                    return False
                if "$gt" in value and item_value <= value["$gt"]:
                    return False
                if "$lt" in value and item_value >= value["$lt"]:
                    return False
                if "$in" in value and item_value not in value["$in"]:
                    return False
            # Exact match
            elif item_value != value:
                return False
        
        return True
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into searchable terms"""
        # Remove special characters and split
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = text.split()
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        return [t for t in tokens if t not in stop_words and len(t) > 1]
    
    def highlight_matches(
        self,
        text: str,
        query: str,
        tag: str = "mark"
    ) -> str:
        """
        Highlight search matches in text
        
        Args:
            text: Original text
            query: Search query
            tag: HTML tag to wrap matches (default: mark)
            
        Returns:
            Text with highlighted matches
        """
        if not query:
            return text
        
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(f'<{tag}>\\g<0></{tag}>', text)
