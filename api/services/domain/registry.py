"""
Domain Service Registry

Manages service boundaries and dependencies between domains.
Provides a centralized way to access services while maintaining domain separation.
"""

from typing import Dict, Any, Optional, Type
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class IDomainService(ABC):
    """Base interface for all domain services."""
    
    @property
    @abstractmethod
    def domain_name(self) -> str:
        """Return the domain name this service belongs to."""
        pass


class DomainRegistry:
    """
    Registry for managing domain services and their boundaries.
    
    Ensures proper separation of concerns and manages cross-domain dependencies.
    """
    
    def __init__(self):
        self._services: Dict[str, Dict[str, Any]] = {
            'ai': {},
            'analytics': {},
            'search': {},
            'sync': {},
            'infrastructure': {},
            'shared': {}
        }
        self._dependencies: Dict[str, list] = {}
    
    def register_service(
        self,
        domain: str,
        service_name: str,
        service_instance: Any,
        interface_type: Optional[Type] = None
    ):
        """Register a service within a domain."""
        if domain not in self._services:
            raise ValueError(f"Unknown domain: {domain}")
        
        self._services[domain][service_name] = {
            'instance': service_instance,
            'interface': interface_type
        }
        
        logger.info(f"Registered service '{service_name}' in domain '{domain}'")
    
    def get_service(self, domain: str, service_name: str) -> Any:
        """Get a service from a specific domain."""
        if domain not in self._services:
            raise ValueError(f"Unknown domain: {domain}")
        
        if service_name not in self._services[domain]:
            raise ValueError(f"Service '{service_name}' not found in domain '{domain}'")
        
        return self._services[domain][service_name]['instance']
    
    def register_dependency(self, from_domain: str, to_domain: str):
        """Register a dependency between domains."""
        if from_domain not in self._dependencies:
            self._dependencies[from_domain] = []
        
        if to_domain not in self._dependencies[from_domain]:
            self._dependencies[from_domain].append(to_domain)
            logger.info(f"Registered dependency: {from_domain} -> {to_domain}")
    
    def validate_dependencies(self) -> bool:
        """Validate that domain dependencies don't create cycles."""
        def has_cycle(domain: str, visited: set, rec_stack: set) -> bool:
            visited.add(domain)
            rec_stack.add(domain)
            
            for dep in self._dependencies.get(domain, []):
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(domain)
            return False
        
        visited = set()
        for domain in self._services.keys():
            if domain not in visited:
                if has_cycle(domain, visited, set()):
                    logger.error(f"Circular dependency detected involving domain: {domain}")
                    return False
        
        return True
    
    def get_domain_services(self, domain: str) -> Dict[str, Any]:
        """Get all services in a domain."""
        if domain not in self._services:
            raise ValueError(f"Unknown domain: {domain}")
        
        return {
            name: info['instance'] 
            for name, info in self._services[domain].items()
        }
    
    def list_domains(self) -> list:
        """List all registered domains."""
        return list(self._services.keys())
    
    def get_dependency_graph(self) -> Dict[str, list]:
        """Get the complete dependency graph."""
        return self._dependencies.copy()


# Global domain registry instance
domain_registry = DomainRegistry()


# Domain-specific service getters for convenience
class AIServices:
    """Convenience class for accessing AI domain services."""
    
    @staticmethod
    def get_ai_service():
        return domain_registry.get_service('ai', 'ai_service')
    
    @staticmethod
    def get_intent_analyzer():
        return domain_registry.get_service('ai', 'intent_analyzer')
    
    @staticmethod
    def get_auto_tagging_service():
        return domain_registry.get_service('ai', 'auto_tagging_service')


class AnalyticsServices:
    """Convenience class for accessing analytics domain services."""
    
    @staticmethod
    def get_predictive_analytics():
        return domain_registry.get_service('analytics', 'predictive_analytics')
    
    @staticmethod
    def get_gap_detector():
        return domain_registry.get_service('analytics', 'gap_detector')
    
    @staticmethod
    def get_impact_analyzer():
        return domain_registry.get_service('analytics', 'impact_analyzer')
    
    @staticmethod
    def get_relationship_service():
        return domain_registry.get_service('analytics', 'relationship_service')


class SearchServices:
    """Convenience class for accessing search domain services."""
    
    @staticmethod
    def get_search_service():
        return domain_registry.get_service('search', 'search_service')
    
    @staticmethod
    def get_qdrant_indexer():
        return domain_registry.get_service('search', 'qdrant_indexer')


class SyncServices:
    """Convenience class for accessing sync domain services."""
    
    @staticmethod
    def get_jira_service():
        return domain_registry.get_service('sync', 'jira_service')
    
    @staticmethod
    def get_repo_service():
        return domain_registry.get_service('sync', 'repo_service')
    
    @staticmethod
    def get_document_service():
        return domain_registry.get_service('sync', 'document_service')


class InfrastructureServices:
    """Convenience class for accessing infrastructure services."""
    
    @staticmethod
    def get_database_service():
        return domain_registry.get_service('infrastructure', 'database_service')
    
    @staticmethod
    def get_cache_service():
        return domain_registry.get_service('infrastructure', 'cache_service')
    
    @staticmethod
    def get_redis_service():
        return domain_registry.get_service('infrastructure', 'redis_service')


class SharedServices:
    """Convenience class for accessing shared services."""
    
    @staticmethod
    def get_auth_service():
        return domain_registry.get_service('shared', 'auth_service')
    
    @staticmethod
    def get_demo_data_generator():
        return domain_registry.get_service('shared', 'demo_data_generator')