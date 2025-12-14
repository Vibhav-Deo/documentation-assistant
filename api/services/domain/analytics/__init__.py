"""
Analytics Domain

This domain handles all analytics and prediction functionality including:
- Predictive analytics and forecasting
- Gap detection and analysis
- Impact analysis and risk assessment
- Relationship mapping and analysis
- Performance metrics and reporting
"""

# Import interfaces first
from .interfaces import (
    IPredictiveAnalyticsService,
    IGapDetector,
    IImpactAnalyzer,
    IRelationshipService,
    TicketPrediction as ITicketPrediction,
    CodeHotspot as ICodeHotspot,
    ResourceBottleneck as IResourceBottleneck,
    RiskAssessment as IRiskAssessment
)

# Import domain models
from .models import (
    RiskLevel,
    GapType,
    BottleneckSeverity,
    TicketPrediction,
    CodeHotspot,
    ResourceBottleneck,
    RiskAssessment,
    GapDetectionResult,
    ImpactAnalysis,
    RelationshipMapping,
    DeveloperContribution,
    FileHistory,
    RepositoryStats,
    FeatureTimeline,
    AnalyticsMetrics
)

# Import all analytics domain services
from .predictive_analytics import PredictiveAnalyticsService
from .analytics import SimpleAnalytics
from .gap_detector import GapDetector
from .impact_analyzer import ImpactAnalyzer
from .relationship_service import RelationshipService
from .predictive_repository import PredictiveAnalyticsRepository as PredictiveRepository

__all__ = [
    # Interfaces
    'IPredictiveAnalyticsService',
    'IGapDetector',
    'IImpactAnalyzer', 
    'IRelationshipService',
    'ITicketPrediction',
    'ICodeHotspot',
    'IResourceBottleneck',
    'IRiskAssessment',
    # Models
    'RiskLevel',
    'GapType',
    'BottleneckSeverity',
    'TicketPrediction',
    'CodeHotspot', 
    'ResourceBottleneck',
    'RiskAssessment',
    'GapDetectionResult',
    'ImpactAnalysis',
    'RelationshipMapping',
    'DeveloperContribution',
    'FileHistory',
    'RepositoryStats',
    'FeatureTimeline',
    'AnalyticsMetrics',
    # Services
    'PredictiveAnalyticsService',
    'SimpleAnalytics',
    'GapDetector',
    'ImpactAnalyzer',
    'RelationshipService',
    'PredictiveRepository'
]