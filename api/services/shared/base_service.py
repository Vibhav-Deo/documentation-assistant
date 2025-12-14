"""
Base Service Pattern

Provides common functionality for all business logic services,
including error handling, logging, and repository management.
"""

import logging
from typing import Any, Dict, Optional, Type
from fastapi import HTTPException
from services.infrastructure.database.base_repository import BaseRepository, OrganizationScopedRepository

logger = logging.getLogger(__name__)


class BaseService:
    """
    Base service class providing common functionality for all services.
    
    Features:
    - Centralized error handling
    - Logging integration
    - Repository management
    - Common validation patterns
    """
    
    def __init__(self, repository: BaseRepository):
        """Initialize service with repository."""
        self.repository = repository
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def handle_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """
        Handle service operations with consistent error handling and logging.
        
        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to execute
            *args, **kwargs: Arguments for the operation function
            
        Returns:
            Result of the operation
            
        Raises:
            HTTPException: On operation failure
        """
        try:
            self.logger.info(f"Starting operation: {operation_name}")
            result = await operation_func(*args, **kwargs)
            self.logger.info(f"Operation completed successfully: {operation_name}")
            return result
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            self.logger.error(f"Operation failed: {operation_name}. Error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error in {operation_name}: {str(e)}"
            )
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: list) -> None:
        """
        Validate that required fields are present in data.
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Raises:
            HTTPException: If required fields are missing
        """
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
    
    def validate_field_types(self, data: Dict[str, Any], field_types: Dict[str, Type]) -> None:
        """
        Validate field types in data.
        
        Args:
            data: Data dictionary to validate
            field_types: Dictionary mapping field names to expected types
            
        Raises:
            HTTPException: If field types are invalid
        """
        type_errors = []
        
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    type_errors.append(f"{field} must be of type {expected_type.__name__}")
        
        if type_errors:
            raise HTTPException(
                status_code=400,
                detail=f"Type validation errors: {'; '.join(type_errors)}"
            )
    
    def validate_string_length(
        self, 
        data: Dict[str, Any], 
        field_limits: Dict[str, Dict[str, int]]
    ) -> None:
        """
        Validate string field lengths.
        
        Args:
            data: Data dictionary to validate
            field_limits: Dict mapping field names to {"min": int, "max": int}
            
        Raises:
            HTTPException: If string lengths are invalid
        """
        length_errors = []
        
        for field, limits in field_limits.items():
            if field in data and isinstance(data[field], str):
                value_length = len(data[field])
                min_length = limits.get("min", 0)
                max_length = limits.get("max", float('inf'))
                
                if value_length < min_length:
                    length_errors.append(f"{field} must be at least {min_length} characters")
                elif value_length > max_length:
                    length_errors.append(f"{field} must be at most {max_length} characters")
        
        if length_errors:
            raise HTTPException(
                status_code=400,
                detail=f"Length validation errors: {'; '.join(length_errors)}"
            )
    
    async def check_exists(self, table: str, where_clause: str, *args) -> bool:
        """
        Check if a record exists.
        
        Args:
            table: Table name
            where_clause: WHERE clause
            *args: Query parameters
            
        Returns:
            True if record exists, False otherwise
        """
        return await self.repository.exists(table, where_clause, *args)
    
    async def get_by_id(self, table: str, record_id: str, id_column: str = "id") -> Optional[Dict]:
        """
        Get a record by ID.
        
        Args:
            table: Table name
            record_id: Record ID
            id_column: Name of ID column (default: "id")
            
        Returns:
            Record dictionary or None if not found
        """
        records = await self.repository.select(
            table=table,
            where_clause=f"{id_column} = $1",
            *[record_id]
        )
        return records[0] if records else None
    
    async def create_record(
        self, 
        table: str, 
        data: Dict[str, Any], 
        required_fields: Optional[list] = None,
        field_types: Optional[Dict[str, Type]] = None,
        field_limits: Optional[Dict[str, Dict[str, int]]] = None
    ) -> str:
        """
        Create a new record with validation.
        
        Args:
            table: Table name
            data: Record data
            required_fields: List of required fields
            field_types: Field type validation
            field_limits: String length validation
            
        Returns:
            ID of created record
        """
        # Validate input
        if required_fields:
            self.validate_required_fields(data, required_fields)
        
        if field_types:
            self.validate_field_types(data, field_types)
        
        if field_limits:
            self.validate_string_length(data, field_limits)
        
        # Create record
        record_id = await self.repository.insert(table, data, returning="id")
        
        if not record_id:
            raise HTTPException(status_code=500, detail="Failed to create record")
        
        return str(record_id)
    
    async def update_record(
        self, 
        table: str, 
        record_id: str, 
        data: Dict[str, Any],
        id_column: str = "id",
        field_types: Optional[Dict[str, Type]] = None,
        field_limits: Optional[Dict[str, Dict[str, int]]] = None
    ) -> bool:
        """
        Update a record with validation.
        
        Args:
            table: Table name
            record_id: Record ID
            data: Updated data
            id_column: Name of ID column
            field_types: Field type validation
            field_limits: String length validation
            
        Returns:
            True if record was updated, False if not found
        """
        # Check if record exists
        if not await self.check_exists(table, f"{id_column} = $1", record_id):
            return False
        
        # Validate input
        if field_types:
            self.validate_field_types(data, field_types)
        
        if field_limits:
            self.validate_string_length(data, field_limits)
        
        # Update record
        await self.repository.update(
            table=table,
            data=data,
            where_clause=f"{id_column} = $1",
            *[record_id]
        )
        
        return True
    
    async def delete_record(self, table: str, record_id: str, id_column: str = "id") -> bool:
        """
        Delete a record by ID.
        
        Args:
            table: Table name
            record_id: Record ID
            id_column: Name of ID column
            
        Returns:
            True if record was deleted, False if not found
        """
        # Check if record exists
        if not await self.check_exists(table, f"{id_column} = $1", record_id):
            return False
        
        # Delete record
        await self.repository.delete(table, f"{id_column} = $1", record_id)
        return True


class OrganizationScopedService(BaseService):
    """
    Base service class for organization-scoped operations.
    
    Automatically handles organization filtering and validation.
    """
    
    def __init__(self, repository: OrganizationScopedRepository):
        super().__init__(repository)
        self.org_repository = repository
    
    async def validate_organization_access(self, org_id: str, user_org_id: str) -> None:
        """
        Validate that user has access to the organization.
        
        Args:
            org_id: Requested organization ID
            user_org_id: User's organization ID
            
        Raises:
            HTTPException: If access is denied
        """
        if org_id != user_org_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: You can only access data from your organization"
            )
    
    async def get_by_org(
        self, 
        table: str, 
        org_id: str, 
        user_org_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "created_at DESC"
    ) -> list:
        """
        Get records for an organization with access validation.
        
        Args:
            table: Table name
            org_id: Organization ID
            user_org_id: User's organization ID
            limit: Maximum number of records
            offset: Number of records to skip
            order_by: Sort order
            
        Returns:
            List of records
        """
        await self.validate_organization_access(org_id, user_org_id)
        
        return await self.org_repository.select_by_org(
            table=table,
            org_id=org_id,
            limit=limit,
            offset=offset,
            order_by=order_by
        )
    
    async def create_for_org(
        self, 
        table: str, 
        data: Dict[str, Any], 
        org_id: str,
        user_org_id: str,
        required_fields: Optional[list] = None,
        field_types: Optional[Dict[str, Type]] = None,
        field_limits: Optional[Dict[str, Dict[str, int]]] = None
    ) -> str:
        """
        Create a record for an organization with access validation.
        
        Args:
            table: Table name
            data: Record data
            org_id: Organization ID
            user_org_id: User's organization ID
            required_fields: List of required fields
            field_types: Field type validation
            field_limits: String length validation
            
        Returns:
            ID of created record
        """
        await self.validate_organization_access(org_id, user_org_id)
        
        # Validate input
        if required_fields:
            self.validate_required_fields(data, required_fields)
        
        if field_types:
            self.validate_field_types(data, field_types)
        
        if field_limits:
            self.validate_string_length(data, field_limits)
        
        # Create record with organization ID
        record_id = await self.org_repository.insert_with_org(table, data, org_id, returning="id")
        
        if not record_id:
            raise HTTPException(status_code=500, detail="Failed to create record")
        
        return str(record_id)
    
    async def count_by_org(self, table: str, org_id: str, user_org_id: str) -> int:
        """
        Count records for an organization with access validation.
        
        Args:
            table: Table name
            org_id: Organization ID
            user_org_id: User's organization ID
            
        Returns:
            Number of records
        """
        await self.validate_organization_access(org_id, user_org_id)
        return await self.org_repository.count_by_org(table, org_id)