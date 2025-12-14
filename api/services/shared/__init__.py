"""
Shared Domain

This domain handles cross-cutting concerns and shared utilities including:
- Authentication and authorization
- Common utilities and helpers
- Response formatting
- Base service classes
- Demo data generation
"""

# Import all shared services
from .base_service import BaseService
from .common_utilities import CommonUtilities
from .response_formatter import ResponseFormatter
from .auth import auth_service as AuthService
from .oauth import oauth_service as OAuthService
from .demo_data_generator import DemoDataGenerator

__all__ = [
    'BaseService',
    'CommonUtilities',
    'ResponseFormatter',
    'AuthService',
    'OAuthService',
    'DemoDataGenerator'
]