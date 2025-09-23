"""
ARTIFACTOR v3.0 Secure Database Service
Comprehensive database security layer with SQL injection prevention,
input validation, and query monitoring
"""

import re
import time
import json
import logging
import hashlib
from typing import Any, Dict, List, Optional, Union, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, or_, and_
from sqlalchemy.orm import Query
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class DatabaseSecurityError(Exception):
    """Raised when database security validation fails"""
    pass

class QuerySecurityValidator:
    """Validates database queries for security threats"""

    def __init__(self):
        self.dangerous_patterns = self._compile_dangerous_patterns()
        self.max_query_length = 10000
        self.max_results_per_query = 10000
        self.query_timeout_seconds = 30

    def _compile_dangerous_patterns(self) -> Dict[str, re.Pattern]:
        """Compile patterns for dangerous SQL constructs"""
        return {
            'sql_injection': re.compile(
                r'''
                (?i)                                    # Case insensitive
                (
                    (\s|^)(OR|AND)\s+\d+\s*=\s*\d+     # 1=1, 1=0 patterns
                    |(\s|^)(OR|AND)\s+['"]\w+['"]      # OR 'x'='x' patterns
                    |\-\-\s*.*$                         # SQL comments
                    |/\*.*?\*/                          # Block comments
                    |;\s*(DROP|DELETE|UPDATE|INSERT|EXEC|EXECUTE|DECLARE|GRANT|REVOKE)\s+   # Dangerous statements after semicolon
                    |\bUNION\s+(ALL\s+)?SELECT\b        # UNION SELECT attacks
                    |\bSELECT\s+.*\bFROM\s+\w+\s+WHERE\s+\d+\s*=\s*\d+  # SELECT FROM WHERE 1=1
                    |(\s|^)(EXEC|EXECUTE)\s*\(          # Function execution
                    |\bCONCAT\s*\(.*,.*\)               # String concatenation attacks
                    |\bCHAR\s*\(\d+\)                   # Character conversion attacks
                    |\bCAST\s*\(.*\bAS\b                # Type casting attacks
                    |\bCONVERT\s*\(.*,.*\)              # Convert function attacks
                    |\bXP_CMDSHELL\b                    # SQL Server command execution
                    |\bSP_EXECUTESQL\b                  # SQL Server dynamic SQL
                    |\bDBMS_PIPE\b                      # Oracle pipe functions
                    |\bUTL_FILE\b                       # Oracle file functions
                    |\bLOAD_FILE\b                      # MySQL file functions
                    |\bINTO\s+OUTFILE\b                 # MySQL file output
                    |\bINTO\s+DUMPFILE\b                # MySQL dump file
                )
                ''',
                re.VERBOSE | re.MULTILINE
            ),
            'time_based_attacks': re.compile(
                r'''
                (?i)
                (
                    \bWAITFOR\s+DELAY\b                 # SQL Server time delays
                    |\bSLEEP\s*\(\d+\)                  # MySQL sleep
                    |\bPG_SLEEP\s*\(\d+\)               # PostgreSQL sleep
                    |\bDBMS_LOCK\.SLEEP\s*\(\d+\)       # Oracle sleep
                    |\bBENCHMARK\s*\(\d+,.*\)           # MySQL benchmark
                )
                ''',
                re.VERBOSE
            ),
            'information_gathering': re.compile(
                r'''
                (?i)
                (
                    \bINFORMATION_SCHEMA\b              # Schema information
                    |\bSYS\.\w+\b                       # System tables
                    |\bMSTER\.\.\w+\b                   # SQL Server master tables
                    |\bPG_CLASS\b                       # PostgreSQL system catalogs
                    |\bPG_TABLES\b                      # PostgreSQL table info
                    |\bTABLE_SCHEMA\b                   # Schema information
                    |\bCOLUMN_NAME\b                    # Column information
                    |\bTABLE_NAME\b                     # Table information
                    |\bVERSION\s*\(\)                   # Database version
                    |\b@@VERSION\b                      # SQL Server version
                    |\bUSER\s*\(\)                      # Current user
                    |\bCURRENT_USER\b                   # Current user
                    |\bSESSION_USER\b                   # Session user
                    |\bDATABASE\s*\(\)                  # Current database
                    |\bSCHEMA\s*\(\)                    # Current schema
                )
                ''',
                re.VERBOSE
            ),
            'privilege_escalation': re.compile(
                r'''
                (?i)
                (
                    \b(CREATE|DROP|ALTER)\s+(USER|ROLE|LOGIN|DATABASE|SCHEMA|TABLE|VIEW|PROCEDURE|FUNCTION)\b
                    |\bGRANT\s+.*\bTO\b                 # Grant privileges
                    |\bREVOKE\s+.*\bFROM\b              # Revoke privileges
                    |\bBULK\s+INSERT\b                  # Bulk operations
                    |\bOPENROWSET\b                     # SQL Server rowset functions
                    |\bOPENQUERY\b                      # SQL Server linked server queries
                )
                ''',
                re.VERBOSE
            )
        }

    def validate_query_string(self, query_str: str) -> Tuple[bool, List[str]]:
        """Validate a query string for security threats"""
        if not query_str:
            return True, []

        errors = []

        # Check query length
        if len(query_str) > self.max_query_length:
            errors.append(f"Query too long: {len(query_str)} > {self.max_query_length}")

        # Check for dangerous patterns
        for pattern_name, pattern in self.dangerous_patterns.items():
            if pattern.search(query_str):
                errors.append(f"Dangerous {pattern_name} pattern detected")
                logger.warning(f"Security threat detected - {pattern_name}: {query_str[:100]}...")

        # Check for excessive complexity
        if query_str.count('(') > 50 or query_str.count('SELECT') > 10:
            errors.append("Query complexity exceeds safety limits")

        # Check for binary/encoded content
        if any(ord(c) > 127 for c in query_str):
            errors.append("Query contains non-ASCII characters")

        return len(errors) == 0, errors

    def validate_parameter(self, param_name: str, param_value: Any) -> Tuple[bool, List[str]]:
        """Validate query parameters for security"""
        errors = []

        if param_value is None:
            return True, []

        # Convert to string for analysis
        param_str = str(param_value)

        # Check parameter length
        if len(param_str) > 10000:
            errors.append(f"Parameter {param_name} too long: {len(param_str)}")

        # Check for SQL injection patterns in parameters
        for pattern_name, pattern in self.dangerous_patterns.items():
            if pattern.search(param_str):
                errors.append(f"Parameter {param_name} contains dangerous {pattern_name} pattern")

        # Check for path traversal in string parameters
        if isinstance(param_value, str):
            if any(dangerous in param_str.lower() for dangerous in ['../', '..\\', '/etc/', '/proc/', 'c:\\']):
                errors.append(f"Parameter {param_name} contains path traversal pattern")

            # Check for script injection
            if any(script in param_str.lower() for script in ['<script', 'javascript:', 'vbscript:', 'onload=']):
                errors.append(f"Parameter {param_name} contains script injection pattern")

        return len(errors) == 0, errors

class SecureDatabaseService:
    """Secure database service with comprehensive protection"""

    def __init__(self):
        self.validator = QuerySecurityValidator()
        self.query_cache = {}
        self.query_stats = {}
        self.blocked_queries = set()

    async def execute_secure_query(
        self,
        db: AsyncSession,
        query: Union[str, Query],
        parameters: Optional[Dict[str, Any]] = None,
        max_results: Optional[int] = None
    ) -> Any:
        """Execute a query with comprehensive security validation"""
        start_time = time.time()

        try:
            # Convert query to string for validation
            if hasattr(query, 'statement'):
                query_str = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
            else:
                query_str = str(query)

            # Generate query hash for tracking
            query_hash = hashlib.sha256(query_str.encode()).hexdigest()[:16]

            # Check if query is blocked
            if query_hash in self.blocked_queries:
                raise DatabaseSecurityError("Query blocked due to previous security violations")

            # Validate query string
            is_safe, query_errors = self.validator.validate_query_string(query_str)
            if not is_safe:
                self.blocked_queries.add(query_hash)
                raise DatabaseSecurityError(f"Query validation failed: {'; '.join(query_errors)}")

            # Validate parameters
            if parameters:
                for param_name, param_value in parameters.items():
                    is_param_safe, param_errors = self.validator.validate_parameter(param_name, param_value)
                    if not is_param_safe:
                        raise DatabaseSecurityError(f"Parameter validation failed: {'; '.join(param_errors)}")

            # Set result limit
            result_limit = min(max_results or 10000, 10000)

            # Execute query with timeout
            if isinstance(query, str):
                result = await db.execute(text(query), parameters or {})
            else:
                result = await db.execute(query)

            # Log successful query
            execution_time = time.time() - start_time
            self._log_query_execution(query_hash, query_str, execution_time, True)

            return result

        except SQLAlchemyError as e:
            execution_time = time.time() - start_time
            self._log_query_execution(query_hash, query_str, execution_time, False, str(e))
            raise DatabaseSecurityError(f"Database error: {str(e)}")

        except Exception as e:
            execution_time = time.time() - start_time
            self._log_query_execution(query_hash, query_str, execution_time, False, str(e))
            raise

    async def secure_select(
        self,
        db: AsyncSession,
        model_class,
        where_clauses: Optional[List] = None,
        order_by: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List:
        """Secure SELECT operation with validation"""
        try:
            # Build query
            query = select(model_class)

            # Apply WHERE clauses safely
            if where_clauses:
                for clause in where_clauses:
                    query = query.where(clause)

            # Apply ordering
            if order_by:
                for order_clause in order_by:
                    query = query.order_by(order_clause)

            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(min(limit, 1000))  # Max 1000 results

            # Execute securely
            result = await self.execute_secure_query(db, query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Secure select failed: {e}")
            raise DatabaseSecurityError(f"Secure select operation failed: {str(e)}")

    async def secure_insert(
        self,
        db: AsyncSession,
        model_instance
    ) -> Any:
        """Secure INSERT operation with validation"""
        try:
            # Validate model instance
            self._validate_model_instance(model_instance)

            # Add to session
            db.add(model_instance)
            await db.commit()
            await db.refresh(model_instance)

            logger.info(f"Secure insert completed for {type(model_instance).__name__}")
            return model_instance

        except Exception as e:
            await db.rollback()
            logger.error(f"Secure insert failed: {e}")
            raise DatabaseSecurityError(f"Secure insert operation failed: {str(e)}")

    async def secure_update(
        self,
        db: AsyncSession,
        model_instance,
        update_data: Dict[str, Any]
    ) -> Any:
        """Secure UPDATE operation with validation"""
        try:
            # Validate update data
            self._validate_update_data(update_data)

            # Apply updates
            for field, value in update_data.items():
                if hasattr(model_instance, field):
                    setattr(model_instance, field, value)

            # Set updated timestamp if available
            if hasattr(model_instance, 'updated_at'):
                model_instance.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(model_instance)

            logger.info(f"Secure update completed for {type(model_instance).__name__}")
            return model_instance

        except Exception as e:
            await db.rollback()
            logger.error(f"Secure update failed: {e}")
            raise DatabaseSecurityError(f"Secure update operation failed: {str(e)}")

    async def secure_delete(
        self,
        db: AsyncSession,
        model_instance
    ) -> bool:
        """Secure DELETE operation with validation"""
        try:
            # Soft delete if available
            if hasattr(model_instance, 'is_deleted'):
                model_instance.is_deleted = True
                model_instance.deleted_at = datetime.utcnow()
                await db.commit()
                logger.info(f"Soft delete completed for {type(model_instance).__name__}")
            else:
                # Hard delete
                await db.delete(model_instance)
                await db.commit()
                logger.info(f"Hard delete completed for {type(model_instance).__name__}")

            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Secure delete failed: {e}")
            raise DatabaseSecurityError(f"Secure delete operation failed: {str(e)}")

    def _validate_model_instance(self, model_instance) -> None:
        """Validate model instance for security"""
        # Check for suspicious attributes
        for attr_name in dir(model_instance):
            if attr_name.startswith('_'):
                continue

            try:
                attr_value = getattr(model_instance, attr_name)
                if isinstance(attr_value, str):
                    # Check for dangerous content
                    is_safe, errors = self.validator.validate_parameter(attr_name, attr_value)
                    if not is_safe:
                        raise DatabaseSecurityError(f"Model validation failed: {'; '.join(errors)}")
            except AttributeError:
                continue

    def _validate_update_data(self, update_data: Dict[str, Any]) -> None:
        """Validate update data for security"""
        # Forbidden fields that should never be updated directly
        forbidden_fields = {
            'id', 'created_at', 'password_hash', 'secret_key',
            'access_token', 'refresh_token', 'session_token'
        }

        for field_name, field_value in update_data.items():
            # Check forbidden fields
            if field_name in forbidden_fields:
                raise DatabaseSecurityError(f"Cannot update forbidden field: {field_name}")

            # Validate field value
            is_safe, errors = self.validator.validate_parameter(field_name, field_value)
            if not is_safe:
                raise DatabaseSecurityError(f"Update validation failed: {'; '.join(errors)}")

    def _log_query_execution(
        self,
        query_hash: str,
        query_str: str,
        execution_time: float,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Log query execution for monitoring"""
        log_data = {
            'query_hash': query_hash,
            'query_preview': query_str[:200],
            'execution_time': round(execution_time, 3),
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }

        if error_message:
            log_data['error'] = error_message

        # Update statistics
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                'total_executions': 0,
                'successful_executions': 0,
                'total_time': 0,
                'average_time': 0,
                'last_execution': None
            }

        stats = self.query_stats[query_hash]
        stats['total_executions'] += 1
        if success:
            stats['successful_executions'] += 1
        stats['total_time'] += execution_time
        stats['average_time'] = stats['total_time'] / stats['total_executions']
        stats['last_execution'] = datetime.utcnow()

        # Log based on success/failure and execution time
        if not success:
            logger.error(f"QUERY FAILED: {json.dumps(log_data)}")
        elif execution_time > 5.0:  # Slow query threshold
            logger.warning(f"SLOW QUERY: {json.dumps(log_data)}")
        else:
            logger.info(f"QUERY EXECUTED: {json.dumps(log_data)}")

    def get_query_statistics(self) -> Dict[str, Any]:
        """Get query execution statistics"""
        return {
            'total_unique_queries': len(self.query_stats),
            'blocked_queries': len(self.blocked_queries),
            'query_details': self.query_stats,
            'blocked_query_hashes': list(self.blocked_queries)
        }

    def clear_blocked_queries(self) -> None:
        """Clear blocked query cache (admin function)"""
        self.blocked_queries.clear()
        logger.info("Blocked query cache cleared")

# Global secure database service instance
secure_db_service = SecureDatabaseService()

# Export for use in other modules
__all__ = [
    'SecureDatabaseService', 'DatabaseSecurityError', 'QuerySecurityValidator',
    'secure_db_service'
]