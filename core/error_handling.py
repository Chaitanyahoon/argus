"""
Enhanced error handling utilities for robust voice streaming.
Includes retry logic, graceful degradation, and detailed error tracking.
"""

import logging
import asyncio
import functools
from typing import Callable, TypeVar, Any, Optional, Awaitable
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── Error Classifications ──────────────────────────────────────────────────

class ErrorSeverity(Enum):
    """Error severity levels for categorization and handling."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for recovery strategy selection."""
    NETWORK = "network"  # Connection, timeout issues
    API = "api"  # API rate limits, auth failures
    AUDIO = "audio"  # Audio encoding, corruption
    STATE = "state"  # Invalid state transitions
    UNKNOWN = "unknown"  # Unknown errors


class VoiceError(Exception):
    """Base exception for voice-related errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        recoverable: bool = False,
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.recoverable = recoverable
        self.timestamp = datetime.now()
        super().__init__(message)


# ── Error Recovery Registry ──────────────────────────────────────────────────

class ErrorRecoveryRegistry:
    """Track errors and apply recovery strategies."""
    
    def __init__(self, max_retries: int = 3, backoff_base: float = 1.0):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.error_counts = {}  # {category: count}
        self.last_error_time = {}  # {category: datetime}
    
    def should_retry(self, category: ErrorCategory) -> bool:
        """Determine if we should retry based on error history."""
        count = self.error_counts.get(category, 0)
        return count < self.max_retries
    
    def record_error(self, category: ErrorCategory) -> None:
        """Record an error occurrence."""
        if category not in self.error_counts:
            self.error_counts[category] = 0
        self.error_counts[category] += 1
        self.last_error_time[category] = datetime.now()
        
        logger.warning(
            f"⚠️ {category.value} error recorded ({self.error_counts[category]}/{self.max_retries})"
        )
    
    def reset_errors(self, category: ErrorCategory) -> None:
        """Reset error count for category."""
        self.error_counts[category] = 0
    
    def get_backoff_delay(self, category: ErrorCategory) -> float:
        """Calculate exponential backoff delay."""
        count = self.error_counts.get(category, 0)
        return self.backoff_base ** count  # 1s, 2s, 4s, 8s...
    
    def is_circuit_open(self, category: ErrorCategory) -> bool:
        """Check if circuit breaker is triggered for category."""
        count = self.error_counts.get(category, 0)
        return count >= self.max_retries


# ── Retry Decorator ───────────────────────────────────────────────────

F = TypeVar('F', bound=Callable[..., Awaitable[Any]])

def async_retry(
    max_retries: int = 3,
    backoff_base: float = 1.0,
    error_category: ErrorCategory = ErrorCategory.UNKNOWN,
) -> Callable[[F], F]:
    """
    Decorator for async functions with exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_base: Base for exponential backoff (delay = base ^ attempt)
        error_category: Category of error for logging
    
    Usage:
        @async_retry(max_retries=3, error_category=ErrorCategory.NETWORK)
        async def send_audio(pcm_bytes):
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise VoiceError(
                            f"Failed: {str(e)}",
                            category=error_category,
                            recoverable=False,
                        )
                    
                    delay = backoff_base ** attempt
                    logger.warning(
                        f"⚠️ {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
        
        return wrapper  # type: ignore
    return decorator


# ── Context Manager for graceful error handling ──────────────────────────────

class SafeVoiceContext:
    """Context manager for voice operations with automatic cleanup."""
    
    def __init__(self, operation_name: str, timeout_seconds: float = 30.0):
        self.operation_name = operation_name
        self.timeout_seconds = timeout_seconds
        self.start_time = None
        self.error = None
    
    async def __aenter__(self):
        self.start_time = datetime.now()
        logger.debug(f"▶️ Starting operation: {self.operation_name}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type:
            logger.error(
                f"❌ Operation '{self.operation_name}' failed after {elapsed:.2f}s: "
                f"{exc_type.__name__}: {exc_val}"
            )
            self.error = exc_val
            return False  # Propagate exception
        
        if elapsed > self.timeout_seconds:
            logger.warning(
                f"⚠️ Operation '{self.operation_name}' took {elapsed:.2f}s "
                f"(timeout: {self.timeout_seconds}s)"
            )
        
        logger.debug(f"✅ Completed operation: {self.operation_name} ({elapsed:.2f}s)")
        return False


# ── Error Summary & Metrics ──────────────────────────────────────────

class ErrorMetrics:
    """Track error metrics for monitoring and debugging."""
    
    def __init__(self):
        self.total_errors = 0
        self.errors_by_category = {}
        self.errors_by_severity = {}
        self.error_history = []  # Recent errors with timestamps
        self.last_error = None
    
    def record(self, error: VoiceError) -> None:
        """Record error metrics."""
        self.total_errors += 1
        self.last_error = error
        
        # Category stats
        cat = error.category.value
        self.errors_by_category[cat] = self.errors_by_category.get(cat, 0) + 1
        
        # Severity stats
        sev = error.severity.value
        self.errors_by_severity[sev] = self.errors_by_severity.get(sev, 0) + 1
        
        # History (keep last 50)
        self.error_history.append({
            'timestamp': error.timestamp.isoformat(),
            'category': cat,
            'severity': sev,
            'message': error.message,
        })
        if len(self.error_history) > 50:
            self.error_history.pop(0)
    
    def get_summary(self) -> dict:
        """Get error summary for logging/monitoring."""
        return {
            'total_errors': self.total_errors,
            'by_category': self.errors_by_category,
            'by_severity': self.errors_by_severity,
            'last_error': {
                'timestamp': self.last_error.timestamp.isoformat() if self.last_error else None,
                'message': self.last_error.message if self.last_error else None,
            } if self.last_error else None,
        }


# Singleton error metrics instance
_error_metrics = ErrorMetrics()

def get_error_metrics() -> ErrorMetrics:
    """Get global error metrics."""
    return _error_metrics
