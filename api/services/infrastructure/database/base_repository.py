"""
Base Repository Pattern

Provides a centralized abstraction for database operations, eliminating
the duplicate `async with self.db.pool.acquire() as conn:` patterns
found across 15+ service files.

This base class handles:
- Connection management
- Transaction handling
- Error handling
- Query execution
- Result formatting
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class BaseRepository:
    """
    Base repository class providing common database operations.
    
    Eliminates duplicate connection patterns and provides consistent
    error handling across all database operations.
    """
    
    def __init__(self, db_service):
        """Initialize repository with database service."""
        self.db = db_service
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Context manager for database connections.
        
        Replaces the repetitive pattern:
        async with self.db.pool.acquire() as conn:
        """
        async with self.db.pool.acquire() as conn:
            try:
                yield conn
            except Exception as e:
                logger.error(f"Database operation failed: {e}")
                raise
    
    @asynccontextmanager
    async def get_transaction(self):
        """
        Context manager for database transactions.
        
        Provides automatic rollback on errors.
        """
        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                try:
                    yield conn
                except Exception as e:
                    logger.error(f"Transaction failed, rolling back: {e}")
                    raise
    
    async def execute_query(
        self, 
        query: str, 
        *args, 
        fetch_mode: str = "all"
    ) -> Union[List[Dict], Dict, Any, None]:
        """
        Execute a query with automatic connection management.
        
        Args:
            query: SQL query string
            *args: Query parameters
            fetch_mode: "all", "one", "val", or "none"
            
        Returns:
            Query results based on fetch_mode
        """
        async with self.get_connection() as conn:
            try:
                if fetch_mode == "all":
                    result = await conn.fetch(query, *args)
                    return [dict(row) for row in result]
                elif fetch_mode == "one":
                    result = await conn.fetchrow(query, *args)
                    return dict(result) if result else None
                elif fetch_mode == "val":
                    return await conn.fetchval(query, *args)
                elif fetch_mode == "none":
                    await conn.execute(query, *args)
                    return None
                else:
                    raise ValueError(f"Invalid fetch_mode: {fetch_mode}")
            except Exception as e:
                logger.error(f"Query execution failed: {query[:100]}... Error: {e}")
                raise
    
    async def execute_many(self, query: str, args_list: List[tuple]) -> None:
        """
        Execute a query multiple times with different parameters.
        
        Useful for bulk operations.
        """
        async with self.get_connection() as conn:
            try:
                await conn.executemany(query, args_list)
            except Exception as e:
                logger.error(f"Bulk query execution failed: {e}")
                raise
    
    async def execute_transaction(self, operations: List[Dict]) -> List[Any]:
        """
        Execute multiple operations in a single transaction.
        
        Args:
            operations: List of dicts with 'query', 'args', and 'fetch_mode'
            
        Returns:
            List of results from each operation
        """
        results = []
        
        async with self.get_transaction() as conn:
            for op in operations:
                query = op['query']
                args = op.get('args', ())
                fetch_mode = op.get('fetch_mode', 'none')
                
                try:
                    if fetch_mode == "all":
                        result = await conn.fetch(query, *args)
                        results.append([dict(row) for row in result])
                    elif fetch_mode == "one":
                        result = await conn.fetchrow(query, *args)
                        results.append(dict(result) if result else None)
                    elif fetch_mode == "val":
                        result = await conn.fetchval(query, *args)
                        results.append(result)
                    elif fetch_mode == "none":
                        await conn.execute(query, *args)
                        results.append(None)
                except Exception as e:
                    logger.error(f"Transaction operation failed: {query[:100]}... Error: {e}")
                    raise
        
        return results
    
    async def count(self, table: str, where_clause: str = "", *args) -> int:
        """
        Get count of records in a table.
        
        Args:
            table: Table name
            where_clause: Optional WHERE clause (without WHERE keyword)
            *args: Parameters for WHERE clause
            
        Returns:
            Number of records
        """
        query = f"SELECT COUNT(*) FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        return await self.execute_query(query, *args, fetch_mode="val")
    
    async def exists(self, table: str, where_clause: str, *args) -> bool:
        """
        Check if a record exists.
        
        Args:
            table: Table name
            where_clause: WHERE clause (without WHERE keyword)
            *args: Parameters for WHERE clause
            
        Returns:
            True if record exists, False otherwise
        """
        query = f"SELECT EXISTS(SELECT 1 FROM {table} WHERE {where_clause})"
        return await self.execute_query(query, *args, fetch_mode="val")
    
    async def insert(
        self, 
        table: str, 
        data: Dict[str, Any], 
        returning: Optional[str] = None,
        on_conflict: Optional[str] = None
    ) -> Optional[Any]:
        """
        Insert a record into a table.
        
        Args:
            table: Table name
            data: Dictionary of column names and values
            returning: Column to return (e.g., "id")
            on_conflict: ON CONFLICT clause
            
        Returns:
            Value of returning column if specified
        """
        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        values = list(data.values())
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        if on_conflict:
            query += f" {on_conflict}"
        
        if returning:
            query += f" RETURNING {returning}"
            return await self.execute_query(query, *values, fetch_mode="val")
        else:
            await self.execute_query(query, *values, fetch_mode="none")
            return None
    
    async def update(
        self, 
        table: str, 
        data: Dict[str, Any], 
        where_clause: str, 
        *where_args,
        returning: Optional[str] = None
    ) -> Optional[Any]:
        """
        Update records in a table.
        
        Args:
            table: Table name
            data: Dictionary of column names and new values
            where_clause: WHERE clause (without WHERE keyword)
            *where_args: Parameters for WHERE clause
            returning: Column to return
            
        Returns:
            Value of returning column if specified
        """
        set_clauses = [f"{col} = ${i+1}" for i, col in enumerate(data.keys())]
        values = list(data.values()) + list(where_args)
        
        # Adjust parameter numbers for WHERE clause
        where_params = []
        for i, arg in enumerate(where_args):
            param_num = len(data) + i + 1
            where_params.append(f"${param_num}")
        
        # Replace parameter placeholders in WHERE clause
        formatted_where = where_clause
        for i, param in enumerate(where_params):
            formatted_where = formatted_where.replace(f"${i+1}", param, 1)
        
        query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {formatted_where}"
        
        if returning:
            query += f" RETURNING {returning}"
            return await self.execute_query(query, *values, fetch_mode="val")
        else:
            await self.execute_query(query, *values, fetch_mode="none")
            return None
    
    async def delete(
        self, 
        table: str, 
        where_clause: str, 
        *args,
        returning: Optional[str] = None
    ) -> Optional[Any]:
        """
        Delete records from a table.
        
        Args:
            table: Table name
            where_clause: WHERE clause (without WHERE keyword)
            *args: Parameters for WHERE clause
            returning: Column to return
            
        Returns:
            Value of returning column if specified
        """
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        if returning:
            query += f" RETURNING {returning}"
            return await self.execute_query(query, *args, fetch_mode="val")
        else:
            await self.execute_query(query, *args, fetch_mode="none")
            return None
    
    async def select(
        self,
        table: str,
        columns: str = "*",
        where_clause: str = "",
        order_by: str = "",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        *args
    ) -> List[Dict]:
        """
        Select records from a table.
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            where_clause: WHERE clause (without WHERE keyword)
            order_by: ORDER BY clause (without ORDER BY keyword)
            limit: LIMIT value
            offset: OFFSET value
            *args: Parameters for WHERE clause
            
        Returns:
            List of records as dictionaries
        """
        query = f"SELECT {columns} FROM {table}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        if offset:
            query += f" OFFSET {offset}"
        
        return await self.execute_query(query, *args, fetch_mode="all")


class OrganizationScopedRepository(BaseRepository):
    """
    Repository base class for organization-scoped operations.
    
    Automatically adds organization_id filtering to queries.
    """
    
    def __init__(self, db_service):
        super().__init__(db_service)
    
    async def select_by_org(
        self,
        table: str,
        org_id: str,
        columns: str = "*",
        where_clause: str = "",
        order_by: str = "",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        *args
    ) -> List[Dict]:
        """
        Select records filtered by organization ID.
        
        Automatically adds organization_id = $1 to WHERE clause.
        """
        org_where = "organization_id = $1"
        
        if where_clause:
            full_where = f"{org_where} AND ({where_clause})"
            all_args = (org_id,) + args
        else:
            full_where = org_where
            all_args = (org_id,)
        
        return await self.select(
            table=table,
            columns=columns,
            where_clause=full_where,
            order_by=order_by,
            limit=limit,
            offset=offset,
            *all_args
        )
    
    async def count_by_org(self, table: str, org_id: str, where_clause: str = "", *args) -> int:
        """Count records filtered by organization ID."""
        org_where = "organization_id = $1"
        
        if where_clause:
            full_where = f"{org_where} AND ({where_clause})"
            all_args = (org_id,) + args
        else:
            full_where = org_where
            all_args = (org_id,)
        
        return await self.count(table, full_where, *all_args)
    
    async def insert_with_org(
        self, 
        table: str, 
        data: Dict[str, Any], 
        org_id: str,
        returning: Optional[str] = None,
        on_conflict: Optional[str] = None
    ) -> Optional[Any]:
        """Insert record with organization ID automatically added."""
        data_with_org = {**data, "organization_id": org_id}
        return await self.insert(table, data_with_org, returning, on_conflict)