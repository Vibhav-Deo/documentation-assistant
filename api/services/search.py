import re
from typing import List
from config import COLLECTION_NAME
from .encryption import encryption_service

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text for hybrid search"""
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]
    return list(set(keywords))[:20]

class SearchService:
    def __init__(self, qdrant_client, embedder):
        self.qdrant = qdrant_client
        self.embedder = embedder
    
    def get_collection_name(self, organization_id: str) -> str:
        """Get organization-specific collection name"""
        return f"{COLLECTION_NAME}_{organization_id}"
    
    def decrypt_results(self, results, organization_id: str):
        """Decrypt search results for organization"""
        for result in results:
            if "text" in result.payload:
                result.payload["text"] = encryption_service.decrypt_data(
                    result.payload["text"], organization_id
                )
            if "title" in result.payload:
                result.payload["title"] = encryption_service.decrypt_data(
                    result.payload["title"], organization_id
                )
        return results
    
    def semantic_search(self, query: str, limit: int, organization_id: str):
        """Pure semantic vector search with organization isolation"""
        collection_name = self.get_collection_name(organization_id)
        q_emb = self.embedder.encode(query).tolist()
        
        results = self.qdrant.search(
            collection_name=collection_name,
            query_vector=q_emb,
            limit=limit
        )
        
        return self.decrypt_results(results, organization_id)
    
    def keyword_search(self, query: str, limit: int, organization_id: str):
        """Keyword-based search with organization isolation"""
        collection_name = self.get_collection_name(organization_id)
        query_keywords = extract_keywords(query)
        if not query_keywords:
            return []
        
        results = self.qdrant.scroll(
            collection_name=collection_name,
            scroll_filter={
                "should": [
                    {"key": "keywords", "match": {"any": query_keywords}}
                ]
            },
            limit=limit
        )[0]
        
        return self.decrypt_results(results, organization_id)
    
    def hybrid_search(self, query: str, limit: int, organization_id: str):
        """Combine semantic and keyword search with scoring"""
        semantic_results = self.semantic_search(query, limit * 2, organization_id)
        keyword_results = self.keyword_search(query, limit * 2, organization_id)
        
        combined_results = {}
        
        # Add semantic results
        for result in semantic_results:
            point_id = result.id
            combined_results[point_id] = {
                'point': result,
                'semantic_score': result.score,
                'keyword_score': 0.0
            }
        
        # Add keyword results
        query_keywords = set(extract_keywords(query))
        for result in keyword_results:
            point_id = result.id
            doc_keywords = set(result.payload.get('keywords', []))
            keyword_score = len(query_keywords.intersection(doc_keywords)) / max(len(query_keywords), 1)
            
            if point_id in combined_results:
                combined_results[point_id]['keyword_score'] = keyword_score
            else:
                combined_results[point_id] = {
                    'point': result,
                    'semantic_score': 0.0,
                    'keyword_score': keyword_score
                }
        
        # Calculate hybrid score
        for item in combined_results.values():
            item['hybrid_score'] = (0.7 * item['semantic_score']) + (0.3 * item['keyword_score'])
        
        sorted_results = sorted(combined_results.values(), key=lambda x: x['hybrid_score'], reverse=True)
        return [item['point'] for item in sorted_results[:limit]]
    
    def enhanced_search(self, query: str, search_type: str, limit: int, organization_id: str):
        """Enhanced search with organization isolation"""
        collection_name = self.get_collection_name(organization_id)
        try:
            collection_info = self.qdrant.get_collection(collection_name)
            if collection_info.points_count == 0:
                return []
        except Exception:
            return []
        
        if search_type == "semantic":
            return self.semantic_search(query, limit, organization_id)
        elif search_type == "keyword":
            return self.keyword_search(query, limit, organization_id)
        elif search_type == "hybrid":
            return self.hybrid_search(query, limit, organization_id)
        else:
            return self.semantic_search(query, limit, organization_id)