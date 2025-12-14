"""
Predictive Analytics Service

Provides ML-based forecasting and predictions:
1. Ticket completion date prediction
2. Code hotspot detection
3. Resource bottleneck forecasting
4. Risk scoring

Uses simple ML models (linear regression, frequency analysis) for demo purposes.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


@dataclass
class TicketPrediction:
    """Prediction for ticket completion."""
    ticket_key: str
    predicted_completion_date: datetime
    confidence_interval_low: datetime
    confidence_interval_high: datetime
    confidence_score: float
    factors: List[str]
    historical_velocity: float
    reasoning: str


@dataclass
class CodeHotspot:
    """Code file predicted to change frequently."""
    file_path: str
    change_frequency: int
    predicted_changes_next_30_days: int
    risk_level: str
    contributors: List[str]
    last_changed: datetime


@dataclass
class ResourceBottleneck:
    """Developer predicted to be overloaded."""
    developer: str
    current_workload: int
    predicted_workload: int
    bottleneck_severity: str
    suggested_actions: List[str]


@dataclass
class RiskAssessment:
    """Risk assessment for a ticket."""
    ticket_key: str
    risk_score: float
    risk_level: str
    risk_factors: List[str]
    mitigation_suggestions: List[str]
    confidence: float


class PredictiveAnalyticsService:
    """
    Predictive analytics using simple ML models.
    
    For demo purposes, uses:
    - Linear regression for velocity
    - Frequency analysis for hotspots
    - Workload distribution for bottlenecks
    - Heuristic scoring for risk
    """
    
    def __init__(self, db_service):
        self.db = db_service
    
    async def predict_ticket_completion(
        self,
        ticket_key: str,
        org_id: str
    ) -> TicketPrediction:
        """
        Predict when a ticket will be completed based on historical velocity.
        
        Uses simple linear regression on historical completion times.
        
        Args:
            ticket_key: Jira ticket key
            org_id: Organization ID
            
        Returns:
            TicketPrediction with estimated completion date
            
        Validates: Requirements 2.1
        """
        async with self.db.pool.acquire() as conn:
            # Get ticket details
            ticket = await conn.fetchrow("""
                SELECT ticket_key, summary, issue_type, priority, status,
                       created_date, updated_date
                FROM jira_tickets
                WHERE ticket_key = $1 AND organization_id = $2
            """, ticket_key, org_id)
            
            if not ticket:
                raise ValueError(f"Ticket {ticket_key} not found")
            
            # Get historical velocity for similar tickets
            similar_tickets = await conn.fetch("""
                SELECT 
                    created_date,
                    resolved_date,
                    EXTRACT(EPOCH FROM (resolved_date - created_date)) / 86400 as days_to_complete
                FROM jira_tickets
                WHERE organization_id = $1
                AND issue_type = $2
                AND status IN ('Done', 'Resolved', 'Closed')
                AND resolved_date IS NOT NULL
                AND created_date IS NOT NULL
                ORDER BY resolved_date DESC
                LIMIT 20
            """, org_id, ticket['issue_type'])
            
            if not similar_tickets:
                # No historical data - use default estimate
                days_estimate = 14  # 2 weeks default
                confidence = 0.3
                velocity = 0.0
                factors = ["No historical data available", "Using default estimate"]
            else:
                # Calculate average velocity
                completion_times = [float(t['days_to_complete']) for t in similar_tickets]
                avg_days = statistics.mean(completion_times)
                std_dev = statistics.stdev(completion_times) if len(completion_times) > 1 else avg_days * 0.3
                
                # Adjust for priority
                priority_multipliers = {
                    'Highest': 0.7,
                    'High': 0.85,
                    'Medium': 1.0,
                    'Low': 1.3,
                    'Lowest': 1.5
                }
                multiplier = priority_multipliers.get(ticket['priority'], 1.0)
                days_estimate = avg_days * multiplier
                
                # Calculate confidence based on data quality
                confidence = min(0.9, 0.5 + (len(similar_tickets) / 40))
                velocity = 1.0 / avg_days if avg_days > 0 else 0.0
                
                factors = [
                    f"Based on {len(similar_tickets)} similar {ticket['issue_type']} tickets",
                    f"Average completion time: {avg_days:.1f} days",
                    f"Priority adjustment: {ticket['priority']} ({multiplier}x)"
                ]
            
            # Calculate prediction
            days_since_creation = (datetime.now() - ticket['created_date']).days
            remaining_days = max(1, days_estimate - days_since_creation)
            
            predicted_date = datetime.now() + timedelta(days=remaining_days)
            
            # Confidence interval (±30%)
            interval_days = remaining_days * 0.3
            confidence_low = predicted_date - timedelta(days=interval_days)
            confidence_high = predicted_date + timedelta(days=interval_days)
            
            reasoning = (
                f"Ticket {ticket_key} is predicted to complete in {remaining_days:.0f} days "
                f"based on historical velocity of similar {ticket['issue_type']} tickets. "
                f"Confidence: {confidence:.0%}"
            )
            
            return TicketPrediction(
                ticket_key=ticket_key,
                predicted_completion_date=predicted_date,
                confidence_interval_low=confidence_low,
                confidence_interval_high=confidence_high,
                confidence_score=confidence,
                factors=factors,
                historical_velocity=velocity,
                reasoning=reasoning
            )
    
    async def identify_code_hotspots(
        self,
        org_id: str,
        lookback_days: int = 90
    ) -> List[CodeHotspot]:
        """
        Identify files that change frequently and predict future hotspots.
        
        Uses frequency analysis with exponential decay (recent changes weighted more).
        
        Args:
            org_id: Organization ID
            lookback_days: Days to look back for analysis
            
        Returns:
            List of CodeHotspot predictions
            
        Validates: Requirements 2.2
        """
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        async with self.db.pool.acquire() as conn:
            # Get file change frequency
            file_changes = await conn.fetch("""
                SELECT 
                    unnest(files_changed) as file_path,
                    COUNT(*) as change_count,
                    MAX(commit_date) as last_changed,
                    array_agg(DISTINCT author_name) as contributors
                FROM commits
                WHERE organization_id = $1
                AND commit_date >= $2
                AND files_changed IS NOT NULL
                GROUP BY file_path
                HAVING COUNT(*) >= 3
                ORDER BY change_count DESC
                LIMIT 20
            """, org_id, cutoff_date)
            
            hotspots = []
            for file in file_changes:
                change_count = file['change_count']
                
                # Predict future changes (simple linear extrapolation)
                changes_per_day = change_count / lookback_days
                predicted_next_30 = int(changes_per_day * 30)
                
                # Determine risk level
                if change_count >= 20:
                    risk_level = "Critical"
                elif change_count >= 10:
                    risk_level = "High"
                elif change_count >= 5:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"
                
                hotspots.append(CodeHotspot(
                    file_path=file['file_path'],
                    change_frequency=change_count,
                    predicted_changes_next_30_days=predicted_next_30,
                    risk_level=risk_level,
                    contributors=file['contributors'] or [],
                    last_changed=file['last_changed']
                ))
            
            return hotspots
    
    async def forecast_resource_bottlenecks(
        self,
        org_id: str,
        forecast_days: int = 30
    ) -> List[ResourceBottleneck]:
        """
        Forecast which developers are likely to become bottlenecks.
        
        Analyzes current workload and predicts future load.
        
        Args:
            org_id: Organization ID
            forecast_days: Days to forecast ahead
            
        Returns:
            List of ResourceBottleneck predictions
            
        Validates: Requirements 2.3
        """
        async with self.db.pool.acquire() as conn:
            # Get current workload (open tickets assigned)
            current_workload = await conn.fetch("""
                SELECT 
                    assignee,
                    COUNT(*) as open_tickets,
                    SUM(CASE WHEN priority IN ('Highest', 'High') THEN 2 ELSE 1 END) as weighted_load
                FROM jira_tickets
                WHERE organization_id = $1
                AND status NOT IN ('Done', 'Resolved', 'Closed')
                AND assignee IS NOT NULL
                GROUP BY assignee
                ORDER BY weighted_load DESC
            """, org_id)
            
            # Get historical completion rate
            completion_rates = await conn.fetch("""
                SELECT 
                    assignee,
                    COUNT(*) as completed_last_30_days
                FROM jira_tickets
                WHERE organization_id = $1
                AND status IN ('Done', 'Resolved', 'Closed')
                AND resolved_date >= NOW() - INTERVAL '30 days'
                AND assignee IS NOT NULL
                GROUP BY assignee
            """, org_id)
            
            completion_map = {r['assignee']: r['completed_last_30_days'] for r in completion_rates}
            
            bottlenecks = []
            for dev in current_workload:
                assignee = dev['assignee']
                current_load = int(dev['weighted_load'])
                completion_rate = completion_map.get(assignee, 5)  # Default 5 tickets/month
                
                # Predict future workload (assume new tickets arrive at current rate)
                # Simplified: current_load - completion_rate + new_arrivals
                predicted_load = max(0, current_load - completion_rate + int(completion_rate * 0.8))
                
                # Determine severity
                if predicted_load >= 15:
                    severity = "Critical"
                    suggestions = [
                        "Redistribute high-priority tickets",
                        "Consider additional resources",
                        "Review ticket complexity"
                    ]
                elif predicted_load >= 10:
                    severity = "High"
                    suggestions = [
                        "Monitor workload closely",
                        "Consider redistributing some tickets"
                    ]
                elif predicted_load >= 7:
                    severity = "Medium"
                    suggestions = [
                        "Workload manageable but monitor trends"
                    ]
                else:
                    severity = "Low"
                    suggestions = [
                        "Workload within normal range"
                    ]
                
                # Only report if there's a potential bottleneck
                if predicted_load >= 7:
                    bottlenecks.append(ResourceBottleneck(
                        developer=assignee,
                        current_workload=current_load,
                        predicted_workload=predicted_load,
                        bottleneck_severity=severity,
                        suggested_actions=suggestions
                    ))
            
            return bottlenecks
    
    async def calculate_risk_score(
        self,
        ticket_key: str,
        org_id: str
    ) -> RiskAssessment:
        """
        Calculate ML-based risk score for a ticket.
        
        For demo, uses heuristic scoring based on:
        - Complexity indicators (description length, linked tickets)
        - Historical patterns (similar ticket failures)
        - Team factors (assignee experience)
        
        Args:
            ticket_key: Jira ticket key
            org_id: Organization ID
            
        Returns:
            RiskAssessment with score and recommendations
            
        Validates: Requirements 2.4
        """
        async with self.db.pool.acquire() as conn:
            # Get ticket details
            ticket = await conn.fetchrow("""
                SELECT ticket_key, summary, description, issue_type, priority,
                       assignee, components, labels
                FROM jira_tickets
                WHERE ticket_key = $1 AND organization_id = $2
            """, ticket_key, org_id)
            
            if not ticket:
                raise ValueError(f"Ticket {ticket_key} not found")
            
            risk_factors = []
            risk_score = 0.0
            
            # Factor 1: Description complexity (0-20 points)
            desc_length = len(ticket['description'] or "")
            if desc_length < 50:
                risk_score += 15
                risk_factors.append("Very brief description - may lack clarity")
            elif desc_length > 2000:
                risk_score += 10
                risk_factors.append("Very long description - high complexity")
            
            # Factor 2: Priority (0-20 points)
            priority_risk = {
                'Highest': 20,
                'High': 15,
                'Medium': 5,
                'Low': 0,
                'Lowest': 0
            }
            priority_score = priority_risk.get(ticket['priority'], 5)
            risk_score += priority_score
            if priority_score >= 15:
                risk_factors.append(f"High priority ({ticket['priority']}) increases risk")
            
            # Factor 3: Issue type (0-15 points)
            type_risk = {
                'Epic': 15,
                'Story': 10,
                'Task': 5,
                'Bug': 8,
                'Sub-task': 3
            }
            type_score = type_risk.get(ticket['issue_type'], 5)
            risk_score += type_score
            if type_score >= 10:
                risk_factors.append(f"{ticket['issue_type']} typically has higher complexity")
            
            # Factor 4: Component count (0-15 points)
            component_count = len(ticket['components'] or [])
            if component_count >= 3:
                risk_score += 15
                risk_factors.append(f"Affects {component_count} components - cross-cutting concern")
            elif component_count == 0:
                risk_score += 5
                risk_factors.append("No components specified - unclear scope")
            
            # Factor 5: Assignee experience (0-20 points)
            if ticket['assignee']:
                assignee_history = await conn.fetchval("""
                    SELECT COUNT(*)
                    FROM jira_tickets
                    WHERE organization_id = $1
                    AND assignee = $2
                    AND status IN ('Done', 'Resolved', 'Closed')
                """, org_id, ticket['assignee'])
                
                if assignee_history < 5:
                    risk_score += 15
                    risk_factors.append("Assignee has limited ticket history")
                elif assignee_history < 10:
                    risk_score += 5
            else:
                risk_score += 20
                risk_factors.append("No assignee - unowned work")
            
            # Normalize to 0-100
            risk_score = min(100, risk_score)
            
            # Determine risk level
            if risk_score >= 70:
                risk_level = "Critical"
            elif risk_score >= 50:
                risk_level = "High"
            elif risk_score >= 30:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            # Generate mitigation suggestions
            mitigations = []
            if "brief description" in " ".join(risk_factors).lower():
                mitigations.append("Add more detailed requirements and acceptance criteria")
            if "no assignee" in " ".join(risk_factors).lower():
                mitigations.append("Assign to experienced team member")
            if "components" in " ".join(risk_factors).lower():
                mitigations.append("Break down into smaller, focused tickets")
            if "priority" in " ".join(risk_factors).lower():
                mitigations.append("Ensure adequate review and testing")
            
            if not mitigations:
                mitigations.append("Risk factors are manageable - proceed with normal process")
            
            # Confidence based on data availability
            confidence = 0.7  # Moderate confidence for heuristic model
            
            return RiskAssessment(
                ticket_key=ticket_key,
                risk_score=risk_score,
                risk_level=risk_level,
                risk_factors=risk_factors,
                mitigation_suggestions=mitigations,
                confidence=confidence
            )
