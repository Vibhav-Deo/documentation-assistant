"""
Dependency Injection Container

Provides centralized service management and dependency injection
for the FastAPI application.
"""

from typing import Dict, Any, Optional, Type, TypeVar
import logging
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceContainer:
    """
    Simple dependency injection container for managing services.
    
    Features:
    - Service registration and resolution
    - Singleton pattern support
    - Lazy initialization
    - Dependency graph management
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._initialized = False
    
    def register_singleton(self, name: str, factory: callable) -> None:
        """
        Register a singleton service factory.
        
        Args:
            name: Service name
            factory: Factory function that creates the service
        """
        self._factories[name] = factory
        logger.debug(f"Registered singleton service: {name}")
    
    def register_instance(self, name: str, instance: Any) -> None:
        """
        Register a service instance directly.
        
        Args:
            name: Service name
            instance: Service instance
        """
        self._services[name] = instance
        logger.debug(f"Registered service instance: {name}")
    
    async def get_service(self, name: str) -> Any:
        """
        Get a service by name.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service is not registered
        """
        # Check if we have a direct instance
        if name in self._services:
            return self._services[name]
        
        # Check if we have a singleton
        if name in self._singletons:
            return self._singletons[name]
        
        # Check if we have a factory
        if name in self._factories:
            factory = self._factories[name]
            
            # Create and cache singleton
            try:
                if asyncio.iscoroutinefunction(factory):
                    instance = await factory()
                else:
                    instance = factory()
                
                self._singletons[name] = instance
                logger.debug(f"Created singleton service: {name}")
                return instance
            except Exception as e:
                logger.error(f"Failed to create service {name}: {e}")
                raise
        
        raise KeyError(f"Service not registered: {name}")
    
    def has_service(self, name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            name: Service name
            
        Returns:
            True if service is registered
        """
        return (name in self._services or 
                name in self._singletons or 
                name in self._factories)
    
    async def initialize_all(self) -> None:
        """Initialize all registered services."""
        if self._initialized:
            return
        
        logger.info("Initializing all services...")
        
        # Initialize all factory-based services
        for name in self._factories:
            try:
                await self.get_service(name)
            except Exception as e:
                logger.error(f"Failed to initialize service {name}: {e}")
                raise
        
        self._initialized = True
        logger.info("All services initialized successfully")
    
    def clear(self) -> None:
        """Clear all services (useful for testing)."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._initialized = False
        logger.debug("Service container cleared")


# Global service container instance
container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get the global service container."""
    return container


async def setup_services():
    """
    Set up all application services in the container.
    
    This function registers all services and their dependencies.
    """
    import asyncio
    from services.infrastructure.database import db_service
    from services.infrastructure.redis_service import redis_service
    from services.infrastructure.monitoring import monitoring_service
    from services.shared.oauth import oauth_service
    from services.infrastructure.cache import SimpleCache
    from services.domain.ai.conversation import SimpleConversation
    from services.domain.analytics.analytics import SimpleAnalytics
    from services.domain.ai import UnifiedAIService
    
    # Register core infrastructure services
    container.register_instance("db_service", db_service)
    container.register_instance("redis_service", redis_service)
    container.register_instance("monitoring_service", monitoring_service)
    container.register_instance("oauth_service", oauth_service)
    
    # Register simple services
    container.register_instance("cache_service", SimpleCache())
    container.register_instance("conversation_service", SimpleConversation())
    # AI service will be created as unified service
    
    # Register analytics service (requires qdrant client)
    def create_analytics_service():
        from config import QDRANT_HOST, QDRANT_PORT
        from qdrant_client import QdrantClient
        qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        return SimpleAnalytics(qdrant)
    
    container.register_singleton("analytics_service", create_analytics_service)
    
    # Register search service
    def create_search_service():
        from config import QDRANT_HOST, QDRANT_PORT
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer
        from services.domain.search import SearchService
        
        qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
        return SearchService(qdrant, embedder)
    
    container.register_singleton("search_service", create_search_service)
    
    # Register document service
    def create_document_service():
        from config import QDRANT_HOST, QDRANT_PORT
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer
        from services.domain.sync import DocumentService
        
        qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
        return DocumentService(qdrant, embedder)
    
    container.register_singleton("document_service", create_document_service)
    
    # Register relationship service
    async def create_relationship_service():
        from services.domain.analytics import RelationshipService
        return RelationshipService(db_service)
    
    container.register_singleton("relationship_service", create_relationship_service)
    
    # Register Qdrant services
    def create_qdrant_setup():
        from config import QDRANT_HOST, QDRANT_PORT
        from qdrant_client import QdrantClient
        from services.domain.search import init_qdrant_setup
        
        qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        return init_qdrant_setup(qdrant)
    
    container.register_singleton("qdrant_setup", create_qdrant_setup)
    
    def create_qdrant_indexer():
        from config import QDRANT_HOST, QDRANT_PORT
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer
        from services.domain.search import init_qdrant_indexer
        
        qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
        return init_qdrant_indexer(qdrant, embedder)
    
    container.register_singleton("qdrant_indexer", create_qdrant_indexer)
    
    # Register unified services (Phase 3 consolidation)
    async def create_unified_ai_service():
        from services.domain.ai import UnifiedAIService, create_ai_service
        from services.infrastructure.database.base_repository import BaseRepository
        repository = BaseRepository(db_service)
        return create_ai_service(repository, enhanced=True)
    
    container.register_singleton("unified_ai_service", create_unified_ai_service)
    
    async def create_unified_intent_analyzer():
        from services.domain.ai import UnifiedIntentAnalyzer, create_intent_analyzer
        from services.infrastructure.database.base_repository import OrganizationScopedRepository
        repository = OrganizationScopedRepository(db_service)
        ai_service = await container.get_service("unified_ai_service")
        return create_intent_analyzer(repository, ai_service, enhanced=True)
    
    container.register_singleton("unified_intent_analyzer", create_unified_intent_analyzer)
    
    # Legacy AI service for backward compatibility
    async def create_legacy_ai_service():
        return await container.get_service("unified_ai_service")
    
    container.register_singleton("ai_service", create_legacy_ai_service)
    
    # Keep legacy services for backward compatibility during migration
    async def create_intent_analyzer():
        return await container.get_service("unified_intent_analyzer")
    
    container.register_singleton("intent_analyzer", create_intent_analyzer)
    
    async def create_gap_detector():
        from services.domain.analytics import GapDetector
        return GapDetector(db_service)
    
    container.register_singleton("gap_detector", create_gap_detector)
    
    async def create_impact_analyzer():
        from services.domain.analytics import ImpactAnalyzer
        return ImpactAnalyzer(db_service)
    
    container.register_singleton("impact_analyzer", create_impact_analyzer)
    
    # Register enhanced services
    async def create_predictive_analytics():
        from services.domain.analytics import PredictiveAnalyticsService
        return PredictiveAnalyticsService(db_service)
    
    container.register_singleton("predictive_analytics", create_predictive_analytics)
    
    async def create_auto_tagging():
        from services.domain.ai import AutoTaggingService
        return AutoTaggingService(db_service)
    
    container.register_singleton("auto_tagging", create_auto_tagging)
    

    
    async def create_demo_data_generator():
        from services.shared import DemoDataGenerator
        return DemoDataGenerator(db_service)
    
    container.register_singleton("demo_data_generator", create_demo_data_generator)
    
    logger.info("All services registered in container")


# Dependency injection helpers for FastAPI
async def get_db_service():
    """FastAPI dependency for database service."""
    return await container.get_service("db_service")


async def get_cache_service():
    """FastAPI dependency for cache service."""
    return await container.get_service("cache_service")


async def get_ai_service():
    """FastAPI dependency for AI service."""
    return await container.get_service("ai_service")


async def get_search_service():
    """FastAPI dependency for search service."""
    return await container.get_service("search_service")


async def get_analytics_service():
    """FastAPI dependency for analytics service."""
    return await container.get_service("analytics_service")


async def get_relationship_service():
    """FastAPI dependency for relationship service."""
    return await container.get_service("relationship_service")


async def get_intent_analyzer():
    """FastAPI dependency for intent analyzer."""
    return await container.get_service("intent_analyzer")


async def get_unified_ai_service():
    """FastAPI dependency for unified AI service."""
    return await container.get_service("unified_ai_service")


async def get_unified_intent_analyzer():
    """FastAPI dependency for unified intent analyzer."""
    return await container.get_service("unified_intent_analyzer")


async def get_gap_detector():
    """FastAPI dependency for gap detector."""
    return await container.get_service("gap_detector")


async def get_impact_analyzer():
    """FastAPI dependency for impact analyzer."""
    return await container.get_service("impact_analyzer")


async def get_predictive_analytics():
    """FastAPI dependency for predictive analytics."""
    return await container.get_service("predictive_analytics")


async def get_auto_tagging():
    """FastAPI dependency for auto tagging."""
    return await container.get_service("auto_tagging")


async def get_demo_data_generator():
    """FastAPI dependency for demo data generator."""
    return await container.get_service("demo_data_generator")


async def get_qdrant_indexer():
    """FastAPI dependency for qdrant indexer."""
    try:
        return await container.get_service("qdrant_indexer")
    except Exception as e:
        logger.warning(f"Qdrant indexer not available: {e}")
        return None


@asynccontextmanager
async def service_lifespan():
    """
    Context manager for service lifecycle management.
    
    Use this to ensure proper initialization and cleanup of services.
    """
    import os
    from services.infrastructure.database import db_service
    
    try:
        # Initialize database pool first
        await db_service.init_pool()
        
        # Set up all services
        await setup_services()
        
        # Initialize all services
        await container.initialize_all()
        
        # Seed comprehensive data in development environment
        environment = os.getenv("ENVIRONMENT", "development").lower()
        if environment == "development":
            try:
                from services.shared.comprehensive_data_seeder import seed_development_data
                seed_result = await seed_development_data(db_service)
                if seed_result:
                    logger.info(f"✅ Development data seeded: {seed_result['tickets_added']} tickets, "
                              f"{seed_result['commits_added']} commits, {seed_result['decisions_added']} decisions")
                else:
                    logger.info("Development data seeding skipped (data already exists)")
            except Exception as e:
                logger.warning(f"Development data seeding failed (non-critical): {e}")
        
        logger.info("Service container fully initialized")
        yield container
        
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise
    finally:
        # Cleanup if needed
        logger.info("Service container shutting down")
        container.clear()