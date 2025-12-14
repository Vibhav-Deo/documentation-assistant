"""
Analytics Domain Models

Data models specific to the analytics domain including:
- Predictive analytics results
- Gap detection findings
- Impact analysis results
- Relationship mappings
"""

from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GapType(str, Enum):
    """Types of gaps that can be detected."""
    ORPHANED_TICKET = "orphaned_ticket"
    UNDOCUMENTED_COMMIT = "undocumented_commit"
    MISSING_DECISION = "missing_decision"
    STALE_TICKET = "stale_ticket"


class BottleneckSeverity(str, Enum):
    """Severity levels for resource bottlenecks."""
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class TicketPrediction(BaseModel):
    """Prediction for ticket completion."""
    ticket_key: str
    predicted_completion_date: datetime
    confidence_interval_low: datetime
    confidence_interval_high: datetime
    confidence_score: float
    factors: List[str]
    historical_velocity: float
    reasoning: str


class CodeHotspot(BaseModel):
    """Code file predicted to change frequently."""
    file_path: str
    change_frequency: int
    predicted_changes_next_30_days: int
    risk_level: RiskLevel
    contributors: List[str]
    last_changed: datetime
    change_patterns: List[str]


class ResourceBottleneck(BaseModel):
    """Developer predicted to be overloaded."""
    developer: str
    current_workload: int
    predicted_workload: int
    bottleneck_severity: BottleneckSeverity
    suggested_actions: List[str]
    workload_breakdown: Dict[str, int]


class RiskAssessment(BaseModel):
    """Risk assessment for tickets or changes."""
    risk_score: float
    risk_level: RiskLevel
    risk_factors: List[str]
    mitigation_suggestions: List[str]
    confidence: float
    assessment_date: datetime


class GapDetectionResult(BaseModel):
    """Result from gap detection analysis."""
    gap_type: GapType
    item_id: str
    title: str
    description: str
    severity: str
    detected_at: datetime
    age_days: int
    metadata: Dict[str, Any]


class ImpactAnalysis(BaseModel):
    """Impact analysis for code changes."""
    change_id: str
    files_affected: List[str]
    tickets_impacted: List[str]
    developers_involved: List[str]
    risk_score: float
    blast_radius: Dict[str, Any]
    recommendations: List[str]
    analysis_date: datetime


class RelationshipMapping(BaseModel):
    """Mapping of relationships between entities."""
    entity_id: str
    entity_type: str
    relationships: List[Dict[str, Any]]
    relationship_strength: Dict[str, float]
    last_updated: datetime


class DeveloperContribution(BaseModel):
    """Developer contribution analysis."""
    developer_email: str
    commits_count: int
    tickets_worked: List[str]
    files_modified: List[str]
    activity_timeline: List[Dict[str, Any]]
    expertise_areas: List[str]
    collaboration_score: float


class FileHistory(BaseModel):
    """Change history for a specific file."""
    file_path: str
    total_changes: int
    contributors: List[str]
    change_timeline: List[Dict[str, Any]]
    related_tickets: List[str]
    complexity_trend: List[Dict[str, Any]]


class RepositoryStats(BaseModel):
    """Comprehensive statistics for a repository."""
    repository_id: str
    total_commits: int
    active_contributors: int
    files_count: int
    languages: Dict[str, int]
    activity_metrics: Dict[str, Any]
    health_score: float


class FeatureTimeline(BaseModel):
    """Timeline for a feature/ticket development."""
    ticket_key: str
    timeline_events: List[Dict[str, Any]]
    development_phases: List[str]
    duration_days: int
    completion_status: str
    milestone_dates: Dict[str, datetime]


class AnalyticsMetrics(BaseModel):
    """General analytics metrics."""
    metric_name: str
    metric_value: float
    metric_type: str
    organization_id: str
    calculated_at: datetime
    metadata: Dict[str, Any] = {}