"""
Predictive Analytics Repository

Example of using the BaseRepository pattern to eliminate duplicate
database connection code in the predictive analytics service.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from services.infrastructure.database.base_repository import OrganizationScopedRepository


class PredictiveAnalyticsRepository(OrganizationScopedRepository):
    """
    Repository for predictive analytics data operations.
    
    Demonstrates how the BaseRepository pattern eliminates the need for
    repetitive `async with self.db.pool.acquire() as conn:` patterns.
    """
    
    async def get_ticket_details(self, ticket_key: str, org_id: str) -> Optional[Dict]:
        """Get ticket details for prediction analysis."""
        query = """
            SELECT ticket_key, summary, issue_type, priority, status,
                   created_date, updated_date
            FROM jira_tickets 
            WHERE organization_id = $1 AND ticket_key = $2
        """
        return await self.execute_query(query, org_id, ticket_key, fetch_mode="one")
    
    async def get_similar_tickets_for_velocity(
        self, 
        issue_type: str, 
        priority: str, 
        org_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get similar completed tickets for velocity analysis."""
        query = """
            SELECT 
                created_date,
                updated_date,
                EXTRACT(EPOCH FROM (updated_date - created_date)) / 86400 as days_to_complete
            FROM jira_tickets 
            WHERE organization_id = $1 
                AND issue_type = $2 
                AND priority = $3 
                AND status IN ('Done', 'Closed')
                AND updated_date > created_date
            ORDER BY updated_date DESC 
            LIMIT $4
        """
        return await self.execute_query(query, org_id, issue_type, priority, limit, fetch_mode="all")
    
    async def get_file_change_frequency(
        self, 
        org_id: str, 
        lookback_days: int = 90
    ) -> List[Dict]:
        """Get file change frequency for hotspot detection."""
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        query = """
            SELECT 
                unnest(files_changed) as file_path,
                COUNT(*) as change_count,
                COUNT(DISTINCT author_email) as contributor_count,
                MAX(commit_date) as last_changed
            FROM commits 
            WHERE organization_id = $1 
                AND commit_date >= $2
                AND files_changed IS NOT NULL
            GROUP BY file_path
            HAVING COUNT(*) > 1
            ORDER BY change_count DESC
        """
        return await self.execute_query(query, org_id, cutoff_date, fetch_mode="all")
    
    async def get_developer_workload(self, org_id: str) -> List[Dict]:
        """Get current developer workload for bottleneck analysis."""
        query = """
            SELECT 
                assignee,
                COUNT(*) as open_tickets,
                AVG(story_points) as avg_story_points,
                STRING_AGG(DISTINCT priority, ', ') as priorities
            FROM jira_tickets 
            WHERE organization_id = $1 
                AND status IN ('To Do', 'In Progress')
                AND assignee IS NOT NULL
            GROUP BY assignee
            ORDER BY open_tickets DESC
        """
        return await self.execute_query(query, org_id, fetch_mode="all")
    
    async def get_developer_completion_rates(self, org_id: str) -> List[Dict]:
        """Get historical completion rates for developers."""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        query = """
            SELECT 
                assignee,
                COUNT(*) as completed_tickets,
                AVG(EXTRACT(EPOCH FROM (updated_date - created_date)) / 86400) as avg_completion_days
            FROM jira_tickets 
            WHERE organization_id = $1 
                AND status IN ('Done', 'Closed')
                AND updated_date >= $2
                AND assignee IS NOT NULL
            GROUP BY assignee
            HAVING COUNT(*) >= 3
        """
        return await self.execute_query(query, org_id, thirty_days_ago, fetch_mode="all")
    
    async def get_ticket_risk_factors(self, ticket_key: str, org_id: str) -> Dict:
        """Get risk factors for a specific ticket."""
        query = """
            SELECT ticket_key, summary, description, issue_type, priority,
                   assignee, components, labels
            FROM jira_tickets 
            WHERE organization_id = $1 AND ticket_key = $2
        """
        return await self.execute_query(query, org_id, ticket_key, fetch_mode="one")
    
    async def get_assignee_experience(self, assignee: str, org_id: str) -> int:
        """Get assignee experience (number of completed tickets)."""
        query = """
            SELECT COUNT(*)
            FROM jira_tickets 
            WHERE organization_id = $1 
                AND assignee = $2 
                AND status IN ('Done', 'Closed')
        """
        result = await self.execute_query(query, org_id, assignee, fetch_mode="val")
        return result or 0
    
    async def get_component_complexity_score(self, components: List[str], org_id: str) -> float:
        """Get complexity score for ticket components."""
        if not components:
            return 0.0
        
        # Create placeholders for the IN clause
        placeholders = ','.join(f'${i+2}' for i in range(len(components)))
        
        query = f"""
            SELECT AVG(story_points) as avg_complexity
            FROM jira_tickets 
            WHERE organization_id = $1 
                AND components && ARRAY[{placeholders}]
                AND story_points IS NOT NULL
        """
        
        result = await self.execute_query(query, org_id, *components, fetch_mode="val")
        return float(result or 0.0)
    
    async def bulk_update_predictions(
        self, 
        predictions: List[Dict[str, Any]], 
        org_id: str
    ) -> None:
        """
        Bulk update predictions using transaction.
        
        Demonstrates the transaction support in BaseRepository.
        """
        operations = []
        
        for prediction in predictions:
            operations.append({
                'query': """
                    INSERT INTO ticket_predictions 
                    (organization_id, ticket_key, predicted_completion_date, 
                     confidence_score, factors, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (organization_id, ticket_key) 
                    DO UPDATE SET 
                        predicted_completion_date = EXCLUDED.predicted_completion_date,
                        confidence_score = EXCLUDED.confidence_score,
                        factors = EXCLUDED.factors,
                        updated_at = EXCLUDED.created_at
                """,
                'args': (
                    org_id,
                    prediction['ticket_key'],
                    prediction['predicted_completion_date'],
                    prediction['confidence_score'],
                    prediction['factors'],
                    datetime.now()
                ),
                'fetch_mode': 'none'
            })
        
        await self.execute_transaction(operations)
    
    async def get_prediction_accuracy_metrics(self, org_id: str) -> Dict:
        """Get accuracy metrics for past predictions."""
        query = """
            WITH prediction_accuracy AS (
                SELECT 
                    tp.ticket_key,
                    tp.predicted_completion_date,
                    jt.updated_date as actual_completion_date,
                    ABS(EXTRACT(EPOCH FROM (tp.predicted_completion_date - jt.updated_date)) / 86400) as error_days
                FROM ticket_predictions tp
                JOIN jira_tickets jt ON tp.ticket_key = jt.ticket_key 
                    AND tp.organization_id = jt.organization_id
                WHERE tp.organization_id = $1 
                    AND jt.status IN ('Done', 'Closed')
                    AND tp.created_at < jt.updated_date
            )
            SELECT 
                COUNT(*) as total_predictions,
                AVG(error_days) as mean_absolute_error,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY error_days) as median_error,
                COUNT(CASE WHEN error_days <= 2 THEN 1 END) as within_2_days,
                COUNT(CASE WHEN error_days <= 7 THEN 1 END) as within_1_week
            FROM prediction_accuracy
        """
        return await self.execute_query(query, org_id, fetch_mode="one")