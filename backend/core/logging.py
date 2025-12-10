"""Logging configuration."""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict
from backend.core.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add standard fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration"):
            log_data["duration"] = record.duration
        
        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """Wrapper for structured logging."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def _log(self, level: int, message: str, **kwargs):
        """Log with extra structured fields."""
        extra = {"extra_fields": kwargs}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured fields."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured fields."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured fields."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured fields."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured fields."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with structured fields."""
        kwargs["exception"] = True
        self._log(logging.ERROR, message, exc_info=True, **kwargs)


# Determine log format based on environment
# Use JSON logging if explicitly enabled via JSON_LOGGING env var
# ConfigMap에서 "true"/"false" 문자열로 설정됨
json_logging_str = getattr(settings, "JSON_LOGGING", "false")
USE_JSON_LOGGING = str(json_logging_str).lower() == "true"

# Configure logging
if USE_JSON_LOGGING:
    formatter = JSONFormatter()
else:
    # Human-readable format for development
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

# Configure root logger
root_logger = logging.getLogger()
# Safely set log level with fallback to INFO
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
root_logger.setLevel(log_level)
root_logger.handlers = [handler]

# Get logger for this module
logger = logging.getLogger(__name__)

# Create structured logger wrapper
structured_logger = StructuredLogger(logger)



