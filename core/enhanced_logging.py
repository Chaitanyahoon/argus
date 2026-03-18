"""
Enhanced logging utilities with structured logging, performance metrics, and debugging.
Extends the basic logger with additional capabilities.
"""

import logging
import time
import functools
from typing import Callable, TypeVar, Any, Optional, Awaitable
from datetime import datetime
from pathlib import Path

# ── Performance Tracking ─────────────────────────────────────────────────────

class PerformanceTracker:
    """Track performance metrics for functions and operations."""
    
    def __init__(self):
        self.metrics = {}  # {operation_name: [times]}
    
    def record(self, operation_name: str, duration_seconds: float) -> None:
        """Record operation duration."""
        if operation_name not in self.metrics:
            self.metrics[operation_name] = []
        self.metrics[operation_name].append(duration_seconds)
        
        # Keep only last 100 measurements per operation
        if len(self.metrics[operation_name]) > 100:
            self.metrics[operation_name].pop(0)
    
    def get_stats(self, operation_name: str) -> dict:
        """Get statistics for operation."""
        if operation_name not in self.metrics or not self.metrics[operation_name]:
            return {}
        
        times = self.metrics[operation_name]
        return {
            'count': len(times),
            'min': min(times),
            'max': max(times),
            'avg': sum(times) / len(times),
            'total': sum(times),
        }
    
    def print_all_stats(self) -> None:
        """Print all operation statistics."""
        print("\n📊 Performance Metrics:")
        print("-" * 80)
        for op_name, times in self.metrics.items():
            stats = self.get_stats(op_name)
            print(f"  {op_name:30s}: count={stats['count']:3d}, "
                  f"avg={stats['avg']:7.3f}s, min={stats['min']:7.3f}s, max={stats['max']:7.3f}s")
        print("-" * 80)


_performance_tracker = PerformanceTracker()

def get_performance_tracker() -> PerformanceTracker:
    """Get global performance tracker."""
    return _performance_tracker


# ── Timing Decorator ────────────────────────────────────────────────────────

_AnyCallable = Callable[..., Awaitable[Any]]

def measure_performance(operation_name: Optional[str] = None) -> Callable[[_AnyCallable], _AnyCallable]:
    """
    Decorator to measure and log function execution time.

    Usage:
        @measure_performance("send_audio")
        async def send_audio(self, pcm):
            ...
    """
    def decorator(func: _AnyCallable) -> _AnyCallable:
        op_name = operation_name or getattr(func, "__name__", repr(func))

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            _logger = logging.getLogger(getattr(func, "__module__", __name__))
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start
                _performance_tracker.record(op_name, duration)
                if duration > 1.0:
                    _logger.warning("⚠️ %s took %.3fs (slow operation)", op_name, duration)
                else:
                    _logger.debug("⏱️ %s took %.3fs", op_name, duration)

        return wrapper  # type: ignore[return-value]
    return decorator


# ── Structured Logging Adaptor ───────────────────────────────────────────────

class StructuredLogger:
    """Wrapper around logging.Logger for structured logging."""
    
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
    
    def debug(self, message: str, **context) -> None:
        """Log debug message with context."""
        self._log("DEBUG", message, context)
    
    def info(self, message: str, **context) -> None:
        """Log info message with context."""
        self._log("INFO", message, context)
    
    def warning(self, message: str, **context) -> None:
        """Log warning message with context."""
        self._log("WARNING", message, context)
    
    def error(self, message: str, **context) -> None:
        """Log error message with context."""
        self._log("ERROR", message, context)
    
    def _log(self, level: str, message: str, context: dict) -> None:
        """Internal logging method."""
        log_method = getattr(self._logger, level.lower())
        
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            log_method(f"{message} [{context_str}]")
        else:
            log_method(message)


# ── JSON Structured Logging (Optional) ───────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging (useful for log aggregation)."""
    
    def format(self, record: logging.LogRecord) -> str:
        import json
        
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if record.exc_info and record.exc_info[0] is not None:
            log_data['exception'] = self.formatException(record.exc_info)  # type: ignore[arg-type]
        
        return json.dumps(log_data)


# ── Audit Logger for Security Events ──────────────────────────────────────────

class AuditLogger:
    """Logger specifically for security/audit events."""
    
    def __init__(self, log_file: str = "logs/audit.log"):
        self._logger = logging.getLogger("audit")
        self._log_file = Path(log_file)
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Add file handler
        fh = logging.FileHandler(self._log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self._logger.addHandler(fh)
    
    def log_voice_command(self, user_id: int, guild_id: int, command: str, result: str) -> None:
        """Log a voice command execution."""
        self._logger.info(
            f"VOICE_COMMAND | user={user_id} | guild={guild_id} | "
            f"command={command} | result={result}"
        )
    
    def log_tool_execution(self, user_id: int, tool_name: str, args: dict, result: str) -> None:
        """Log tool execution."""
        self._logger.info(
            f"TOOL_EXEC | user={user_id} | tool={tool_name} | "
            f"args={args} | result={result}"
        )
    
    def log_api_error(self, api_name: str, error: str, recoverable: bool) -> None:
        """Log API errors."""
        status = "RECOVERABLE" if recoverable else "CRITICAL"
        self._logger.warning(
            f"API_ERROR | api={api_name} | status={status} | error={error}"
        )


# Create audit logger instance
audit_logger = AuditLogger()


# ── Helper Functions ────────────────────────────────────────────────────────

def get_logger(name: str, structured: bool = False) -> logging.Logger | StructuredLogger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        structured: Use structured logging wrapper
    
    Returns:
        Logger instance
    """
    if structured:
        return StructuredLogger(name)
    return logging.getLogger(name)


def log_network_event(logger: logging.Logger, event: str, duration_ms: float, 
                      bytes_transferred: int = 0) -> None:
    """Log network-related event with metrics."""
    msg = f"🌐 {event} ({duration_ms:.1f}ms)"
    if bytes_transferred:
        msg += f" | {bytes_transferred} bytes"
    logger.debug(msg)


def log_audio_event(logger: logging.Logger, event: str, audio_size: int, 
                    sample_rate: int = 16000) -> None:
    """Log audio processing event."""
    duration_ms = (audio_size / 2 / sample_rate) * 1000  # Assuming 16-bit mono
    logger.debug(f"🔊 {event} | {audio_size} bytes | {duration_ms:.1f}ms")
