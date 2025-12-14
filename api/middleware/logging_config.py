"""
Comprehensive Logging Configuration

Provides structured logging setup with multiple handlers, formatters,
and integration with monitoring systems for production-ready logging.
"""

import logging
import logging.config
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs for better parsing
    by log aggregation systems like ELK stack, Fluentd, or CloudWatch.
    """
    
    def __init__(self, service_name: str = "enterprise-rag-api", version: str = "2.0.0"):
        super().__init__()
        self.service_name = service_name
        self.version = version
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "version": self.version,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "pathname": record.pathname
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info', 'message'
            ]:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry["extra"] = extra_fields
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Colored console formatter for development environments.
    Provides readable, colored output for better development experience.
    """
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors for console output."""
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        colored_level = f"{level_color}{record.levelname}{self.COLORS['RESET']}"
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build log message
        message = record.getMessage()
        
        # Add extra fields if present
        extra_info = ""
        if hasattr(record, 'correlation_id'):
            extra_info += f" [ID: {record.correlation_id}]"
        if hasattr(record, 'method') and hasattr(record, 'path'):
            extra_info += f" [{record.method} {record.path}]"
        if hasattr(record, 'processing_time_seconds'):
            extra_info += f" [{record.processing_time_seconds:.3f}s]"
        
        # Format final message
        formatted_message = f"{timestamp} | {colored_level:8} | {record.name:20} | {message}{extra_info}"
        
        # Add exception information if present
        if record.exc_info:
            formatted_message += f"\n{self.formatException(record.exc_info)}"
        
        return formatted_message


def setup_logging(
    log_level: str = "INFO",
    environment: str = "development",
    log_file: Optional[str] = None,
    service_name: str = "enterprise-rag-api",
    version: str = "2.0.0",
    enable_file_logging: bool = True,
    enable_json_logging: bool = False,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Set up comprehensive logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Environment name (development, staging, production)
        log_file: Path to log file (optional)
        service_name: Name of the service for structured logging
        version: Version of the service
        enable_file_logging: Whether to enable file logging
        enable_json_logging: Whether to use JSON format for logs
        max_file_size: Maximum size of log files before rotation
        backup_count: Number of backup log files to keep
    """
    
    # Determine log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    if enable_file_logging:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        if not log_file:
            log_file = log_dir / f"{service_name}.log"
    
    # Configure logging
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
                "service_name": service_name,
                "version": version
            },
            "console": {
                "()": ColoredConsoleFormatter
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level.upper(),
                "formatter": "console" if environment == "development" else "structured",
                "stream": sys.stdout
            }
        },
        "loggers": {
            # Root logger
            "": {
                "level": log_level.upper(),
                "handlers": ["console"],
                "propagate": False
            },
            # FastAPI loggers
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "WARNING",  # Reduce noise from access logs
                "handlers": ["console"],
                "propagate": False
            },
            # Application loggers
            "api": {
                "level": log_level.upper(),
                "handlers": ["console"],
                "propagate": False
            },
            "services": {
                "level": log_level.upper(),
                "handlers": ["console"],
                "propagate": False
            },
            "middleware": {
                "level": log_level.upper(),
                "handlers": ["console"],
                "propagate": False
            },
            # Third-party loggers (reduce noise)
            "asyncpg": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "aiohttp": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "urllib3": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # Add file handler if enabled
    if enable_file_logging and log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level.upper(),
            "formatter": "structured" if enable_json_logging else "simple",
            "filename": str(log_file),
            "maxBytes": max_file_size,
            "backupCount": backup_count,
            "encoding": "utf-8"
        }
        
        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            if "file" not in logger_config["handlers"]:
                logger_config["handlers"].append("file")
    
    # Add error file handler for production
    if environment == "production" and enable_file_logging:
        error_log_file = Path(log_file).parent / f"{service_name}-errors.log"
        config["handlers"]["error_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "structured",
            "filename": str(error_log_file),
            "maxBytes": max_file_size,
            "backupCount": backup_count,
            "encoding": "utf-8"
        }
        
        # Add error file handler to all loggers
        for logger_config in config["loggers"].values():
            if "error_file" not in logger_config["handlers"]:
                logger_config["handlers"].append("error_file")
    
    # Apply logging configuration
    logging.config.dictConfig(config)
    
    # Log configuration success
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured successfully",
        extra={
            "environment": environment,
            "log_level": log_level,
            "service_name": service_name,
            "version": version,
            "file_logging": enable_file_logging,
            "json_logging": enable_json_logging,
            "log_file": str(log_file) if log_file else None
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration: float,
    **kwargs
) -> None:
    """
    Log performance metrics in a structured way.
    
    Args:
        logger: Logger instance
        operation: Name of the operation
        duration: Duration in seconds
        **kwargs: Additional context data
    """
    log_data = {
        "operation": operation,
        "duration_seconds": round(duration, 3),
        "performance_category": _categorize_performance(duration),
        **kwargs
    }
    
    if duration > 5.0:
        logger.warning(f"Slow operation: {operation}", extra=log_data)
    elif duration > 2.0:
        logger.info(f"Moderate operation: {operation}", extra=log_data)
    else:
        logger.debug(f"Fast operation: {operation}", extra=log_data)


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    severity: str,
    details: Dict[str, Any],
    **kwargs
) -> None:
    """
    Log security-related events in a structured way.
    
    Args:
        logger: Logger instance
        event_type: Type of security event
        severity: Severity level (low, medium, high, critical)
        details: Event details
        **kwargs: Additional context data
    """
    log_data = {
        "security_event": True,
        "event_type": event_type,
        "severity": severity,
        "details": details,
        **kwargs
    }
    
    if severity in ["critical", "high"]:
        logger.error(f"Security event: {event_type}", extra=log_data)
    elif severity == "medium":
        logger.warning(f"Security event: {event_type}", extra=log_data)
    else:
        logger.info(f"Security event: {event_type}", extra=log_data)


def _categorize_performance(duration: float) -> str:
    """Categorize performance based on duration."""
    if duration > 10.0:
        return "very_slow"
    elif duration > 5.0:
        return "slow"
    elif duration > 2.0:
        return "moderate"
    elif duration > 1.0:
        return "acceptable"
    else:
        return "fast"


# Environment-specific logging configurations
LOGGING_CONFIGS = {
    "development": {
        "log_level": "DEBUG",
        "enable_json_logging": False,
        "enable_file_logging": True
    },
    "testing": {
        "log_level": "WARNING",
        "enable_json_logging": False,
        "enable_file_logging": False
    },
    "staging": {
        "log_level": "INFO",
        "enable_json_logging": True,
        "enable_file_logging": True
    },
    "production": {
        "log_level": "INFO",
        "enable_json_logging": True,
        "enable_file_logging": True
    }
}


def setup_environment_logging(environment: str = None) -> None:
    """
    Set up logging based on environment configuration.
    
    Args:
        environment: Environment name (auto-detected if not provided)
    """
    if not environment:
        environment = os.getenv("ENVIRONMENT", "development").lower()
    
    config = LOGGING_CONFIGS.get(environment, LOGGING_CONFIGS["development"])
    
    setup_logging(
        environment=environment,
        **config
    )