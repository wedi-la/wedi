"""
Custom database types that work across different databases.

This module provides type adapters that allow PostgreSQL-specific types
to work with SQLite during testing.
"""
import json
from typing import Any, Optional

from sqlalchemy import String, TypeDecorator
from sqlalchemy.dialects import postgresql


class ArrayType(TypeDecorator):
    """
    Custom array type that uses PostgreSQL ARRAY in production
    and JSON serialization in SQLite for testing.
    """
    impl = String
    cache_ok = True
    
    def __init__(self, item_type: Any):
        super().__init__()
        self.item_type = item_type
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            # Use native PostgreSQL ARRAY
            return dialect.type_descriptor(postgresql.ARRAY(self.item_type))
        else:
            # Use JSON string for SQLite
            return dialect.type_descriptor(String())
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        # Convert list to JSON string for SQLite
        return json.dumps(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        # Convert JSON string back to list for SQLite
        return json.loads(value) if isinstance(value, str) else value


class JSONType(TypeDecorator):
    """
    Custom JSON type that works across databases.
    """
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import JSON
            return dialect.type_descriptor(JSON)
        else:
            return dialect.type_descriptor(String())
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        return json.dumps(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        return json.loads(value) if isinstance(value, str) else value 