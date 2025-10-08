from config import COLLECTION_NAME
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics

class SimpleAnalytics:
    def __init__(self, qdrant_client):
        self.queries = []
        self.sessions = defaultdict(list)
        self.models_used = Counter()
        self.search_types = Counter()
        self.errors = []
        self.qdrant = qdrant_client
    
    def log_query(self, question, results_count, response_time, model="unknown", search_type="semantic", session_id=None):
        query_data = {
            "question": question,
            "results_count": results_count,
            "response_time": response_time,
            "model": model,
            "search_type": search_type,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
        self.queries.append(query_data)
        self.models_used[model] += 1
        self.search_types[search_type] += 1
        
        if session_id:
            self.sessions[session_id].append(query_data)
    
    def log_error(self, error_type, error_message, context=None):
        self.errors.append({
            "type": error_type,
            "message": error_message,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_usage_metrics(self):
        if not self.queries:
            return {"total_queries": 0, "avg_response_time": 0, "active_sessions": 0}
        
        response_times = [q["response_time"] for q in self.queries]
        recent_queries = [q for q in self.queries if 
                         datetime.fromisoformat(q["timestamp"]) > datetime.now() - timedelta(hours=24)]
        
        return {
            "total_queries": len(self.queries),
            "queries_24h": len(recent_queries),
            "avg_response_time": round(statistics.mean(response_times), 2),
            "median_response_time": round(statistics.median(response_times), 2),
            "active_sessions": len(self.sessions),
            "total_errors": len(self.errors),
            "models_usage": dict(self.models_used.most_common()),
            "search_types_usage": dict(self.search_types.most_common())
        }
    
    def get_document_stats(self):
        try:
            info = self.qdrant.get_collection(COLLECTION_NAME)
            
            # Get source type distribution
            scroll_result = self.qdrant.scroll(
                collection_name=COLLECTION_NAME,
                limit=1000,
                with_payload=["source_type", "created_at"]
            )
            
            source_types = Counter()
            recent_docs = 0
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for point in scroll_result[0]:
                source_type = point.payload.get("source_type", "unknown")
                source_types[source_type] += 1
                
                created_at = point.payload.get("created_at")
                if created_at and datetime.fromisoformat(created_at) > cutoff_date:
                    recent_docs += 1
            
            return {
                "total_documents": info.points_count,
                "documents_7d": recent_docs,
                "source_distribution": dict(source_types),
                "collection_size_mb": round(info.points_count * 0.001, 2)
            }
        except Exception as e:
            return {
                "total_documents": 0,
                "error": str(e),
                "source_distribution": {},
                "collection_size_mb": 0
            }
    
    def get_popular_queries(self, limit=10):
        if not self.queries:
            return []
        
        question_counts = Counter(q["question"].lower() for q in self.queries)
        
        popular = []
        for question, count in question_counts.most_common(limit):
            matching_queries = [q for q in self.queries if q["question"].lower() == question]
            avg_time = statistics.mean(q["response_time"] for q in matching_queries)
            avg_results = statistics.mean(q["results_count"] for q in matching_queries)
            
            popular.append({
                "question": question,
                "frequency": count,
                "avg_response_time": round(avg_time, 2),
                "avg_results_count": round(avg_results, 1)
            })
        
        return popular
    
    def get_performance_insights(self):
        if not self.queries:
            return {"insights": [], "recommendations": [], "health_score": 100}
        
        insights = []
        recommendations = []
        
        response_times = [q["response_time"] for q in self.queries]
        avg_time = statistics.mean(response_times)
        
        if avg_time > 5.0:
            insights.append("High average response time detected")
            recommendations.append("Consider optimizing search parameters")
        
        zero_results = len([q for q in self.queries if q["results_count"] == 0])
        zero_results_pct = (zero_results / len(self.queries)) * 100
        
        if zero_results_pct > 30:
            insights.append(f"{zero_results_pct:.1f}% of queries return no results")
            recommendations.append("Consider syncing more documentation")
        
        if len(self.models_used) > 1:
            most_used = self.models_used.most_common(1)[0]
            insights.append(f"Most popular model: {most_used[0]} ({most_used[1]} uses)")
        
        if self.errors:
            recent_errors = [e for e in self.errors if 
                           datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(hours=1)]
            if recent_errors:
                insights.append(f"{len(recent_errors)} errors in the last hour")
                recommendations.append("Check system health")
        
        return {
            "insights": insights,
            "recommendations": recommendations,
            "health_score": self._calculate_health_score()
        }
    
    def _calculate_health_score(self):
        if not self.queries:
            return 100
        
        score = 100
        avg_time = statistics.mean(q["response_time"] for q in self.queries)
        if avg_time > 3.0:
            score -= min(30, (avg_time - 3.0) * 10)
        
        zero_results_pct = (len([q for q in self.queries if q["results_count"] == 0]) / len(self.queries)) * 100
        if zero_results_pct > 20:
            score -= min(25, zero_results_pct - 20)
        
        recent_errors = len([e for e in self.errors if 
                           datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(hours=1)])
        score -= min(20, recent_errors * 5)
        
        return max(0, int(score))