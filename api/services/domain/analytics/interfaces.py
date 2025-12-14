"""
Analytics Domain Interfaces

Defines the contracts and interfaces for analytics domain services.
This establishes clear boundaries between the analytics domain and other domains.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


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
    """Risk assessment for tickets or changes."""
    risk_score: float
    risk_level: str
    risk_factors: List[str]
    mitigation_suggestions: List[str]
    confidence: float


class IPredictiveAnalyticsService(ABC):
    """Interface for predictive analytics and forecasting."""
    
    @abstractmethod
    async def predict_ticket_completion(
        self,
        ticket_key: str,
        org_id: str
    ) -> TicketPrediction:
        """Predict completion date for a ticket."""
        pass
    
    @abstractmethod
    async def identify_code_hotspots(
        self,
        org_id: str,
        lookback_days: int = 90
    ) -> List[CodeHotspot]:
        """Identify files likely to change frequently."""
        pass
    
    @abstractmethod
    async def forecast_resource_bottlenecks(
        self,
        org_id: str,
        forecast_days: int = 30
    ) -> List[ResourceBottleneck]:
        """Forecast team member workload bottlenecks."""
        pass
    
    @abstractmethod
    async def calculate_risk_score(
        self,
        ticket_key: str,
        org_id: str
    ) -> RiskAssessment:
        """Calculate ML-based risk score for tickets."""
        pass


class IGapDetector(ABC):
    """Interface for gap detection and analysis."""
    
    @abstractmethod
    async def find_orphaned_tickets(
        self,
        org_id: str,
        days_threshold: int = 30
    ) -> List[Dict]:
        """Find tickets without related commits."""
        pass
    
    @abstractmethod
    async def find_undocumented_commits(
        self,
        org_id: str,
        days_threshold: int = 30
    ) -> List[Dict]:
        """Find commits without related tickets."""
        pass
    
    @abstractmethod
    async def find_missing_decisions(
        self,
        org_id: str
    ) -> List[Dict]:
        """Find tickets lacking decision documentation."""
        pass
    
    @abstractmethod
    async def find_stale_tickets(
        self,
        org_id: str,
        days_threshold: int = 14
    ) -> List[Dict]:
        """Find tickets that haven't been updated recently."""
        pass


class IImpactAnalyzer(ABC):
    """Interface for impact analysis and risk assessment."""
    
    @abstractmethod
    async def analyze_change_impact(
        self,
        files: List[str],
        org_id: str
    ) -> Dict[str, Any]:
        """Analyze potential impact of file changes."""
        pass
    
    @abstractmethod
    async def get_related_tickets(
        self,
        files: List[str],
        org_id: str
    ) -> List[Dict]:
        """Get tickets related to specific files."""
        pass
    
    @abstractmethod
    async def calculate_blast_radius(
        self,
        change_description: str,
        files: List[str],
        org_id: str
    ) -> Dict[str, Any]:
        """Calculate potential blast radius of changes."""
        pass


class IRelationshipService(ABC):
    """Interface for relationship mapping and analysis."""
    
    @abstractmethod
    async def get_ticket_relationships(
        self,
        ticket_key: str,
        org_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive relationship data for a ticket."""
        pass
    
    @abstractmethod
    async def get_developer_contributions(
        self,
        developer_email: str,
        org_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive contribution data for a developer."""
        pass
    
    @abstractmethod
    async def get_file_history(
        self,
        file_path: str,
        org_id: str
    ) -> Dict[str, Any]:
        """Get change history for a specific file."""
        pass
    
    @abstractmethod
    async def search_relationships(
        self,
        query: str,
        org_id: str,
        relationship_type: str = "all",
        limit: int = 20
    ) -> List[Dict]:
        """Search across all relationship data."""
        pass