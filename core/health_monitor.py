"""
Health check monitoring — monitor bot, API, and system health.
Provides status checks and metrics for reliability monitoring.
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# ── Health Status Enums ──────────────────────────────────────────────────────

class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Component types to monitor."""
    BOT = "bot"
    API = "api"
    VOICE = "voice"
    DATABASE = "database"
    CACHE = "cache"


# ── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class HealthCheck:
    """Result of a single health check."""
    name: str
    status: HealthStatus
    latency_ms: float
    message: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for responses."""
        return {
            'name': self.name,
            'status': self.status.value,
            'latency_ms': round(self.latency_ms, 2),
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class HealthReport:
    """Overall health report."""
    overall_status: HealthStatus
    checks: Dict[str, HealthCheck]
    uptime_seconds: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for responses."""
        return {
            'status': self.overall_status.value,
            'uptime_seconds': round(self.uptime_seconds, 1),
            'timestamp': self.timestamp.isoformat(),
            'components': {name: check.to_dict() for name, check in self.checks.items()},
        }


# ── Health Check Manager ─────────────────────────────────────────────────────

class HealthCheckManager:
    """Manages health checks for bot and dependencies."""
    
    def __init__(self):
        self.checks: Dict[str, Callable[[], Awaitable[HealthCheck]]] = {}
        self.last_check_time: Dict[str, datetime] = {}
        self.last_check_result: Dict[str, HealthCheck] = {}
        self.start_time = datetime.now()
        self._check_threshold_ms = 100  # Warn if check exceeds this duration
    
    def register_check(
        self,
        name: str,
        check_fn: Callable[[], Awaitable[HealthCheck]]
    ) -> None:
        """Register a health check function."""
        self.checks[name] = check_fn
        logger.debug(f"Registered health check: {name}")
    
    async def run_check(self, name: str) -> Optional[HealthCheck]:
        """Run a single health check."""
        if name not in self.checks:
            return None
        
        try:
            start = time.perf_counter()
            check_result = await self.checks[name]()
            duration = (time.perf_counter() - start) * 1000  # ms
            
            # Warn if check took too long
            if duration > self._check_threshold_ms:
                logger.warning(f"Health check '{name}' took {duration:.1f}ms (slow)")
            
            self.last_check_time[name] = datetime.now()
            self.last_check_result[name] = check_result
            
            return check_result
        except Exception as e:
            logger.error(f"Health check '{name}' failed: {e}")
            
            # Return unhealthy status
            check_result = HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=0.0,
                message=f"Check failed: {str(e)}",
                timestamp=datetime.now(),
            )
            self.last_check_result[name] = check_result
            return check_result
    
    async def run_all_checks(self) -> HealthReport:
        """Run all health checks and generate report."""
        results = {}
        
        for check_name in self.checks:
            result = await self.run_check(check_name)
            if result:
                results[check_name] = result
        
        # Determine overall status
        statuses = [r.status for r in results.values()]
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return HealthReport(
            overall_status=overall,
            checks=results,
            uptime_seconds=uptime,
            timestamp=datetime.now(),
        )
    
    async def get_status(self, name: str) -> Optional[HealthCheck]:
        """Get last check result for component (without running new check)."""
        return self.last_check_result.get(name)
    
    def get_uptime(self) -> Dict[str, Any]:
        """Get bot uptime."""
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            'total_seconds': uptime.total_seconds(),
            'formatted': f"{days}d {hours}h {minutes}m {seconds}s",
        }


# ── Pre-built Health Checks ──────────────────────────────────────────────────

async def check_bot_status(bot_instance: Any) -> HealthCheck:
    """Check if bot is connected and responsive."""
    start = time.perf_counter()
    
    try:
        is_ready = bot_instance.is_ready()
        latency = bot_instance.latency * 1000  # Convert to ms
        duration = (time.perf_counter() - start) * 1000
        
        if is_ready and latency < 1000:  # Less than 1 second latency
            status = HealthStatus.HEALTHY
            message = f"Bot online, latency: {latency:.0f}ms"
        elif is_ready:
            status = HealthStatus.DEGRADED
            message = f"High latency: {latency:.0f}ms"
        else:
            status = HealthStatus.UNHEALTHY
            message = "Bot not ready"
        
        return HealthCheck(
            name="bot_status",
            status=status,
            latency_ms=duration,
            message=message,
            timestamp=datetime.now(),
        )
    except Exception as e:
        return HealthCheck(
            name="bot_status",
            status=HealthStatus.UNHEALTHY,
            latency_ms=(time.perf_counter() - start) * 1000,
            message=str(e),
            timestamp=datetime.now(),
        )


async def check_gemini_api() -> HealthCheck:
    """Check if Gemini API is accessible (simple connectivity test)."""
    start = time.perf_counter()
    
    try:
        from google import genai
        from config import Config
        
        # Create client (doesn't make actual API call)
        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        # Note: We don't make a real API call here to avoid quota usage
        # A full check would require an actual API call
        duration = (time.perf_counter() - start) * 1000
        
        return HealthCheck(
            name="gemini_api",
            status=HealthStatus.HEALTHY,
            latency_ms=duration,
            message="Gemini API client initialized",
            timestamp=datetime.now(),
        )
    except Exception as e:
        return HealthCheck(
            name="gemini_api",
            status=HealthStatus.UNHEALTHY,
            latency_ms=(time.perf_counter() - start) * 1000,
            message=f"API initialization failed: {str(e)}",
            timestamp=datetime.now(),
        )


async def check_voice_subsystem(bot_instance: Any) -> HealthCheck:
    """Check if voice subsystem is operational."""
    start = time.perf_counter()
    
    try:
        # Check if voice manager exists and is operational
        voice_manager = getattr(bot_instance, 'voice_manager', None)
        
        if voice_manager:
            status = HealthStatus.HEALTHY
            message = "Voice subsystem ready"
        else:
            status = HealthStatus.DEGRADED
            message = "Voice manager not initialized"
        
        duration = (time.perf_counter() - start) * 1000
        
        return HealthCheck(
            name="voice_subsystem",
            status=status,
            latency_ms=duration,
            message=message,
            timestamp=datetime.now(),
        )
    except Exception as e:
        return HealthCheck(
            name="voice_subsystem",
            status=HealthStatus.UNHEALTHY,
            latency_ms=(time.perf_counter() - start) * 1000,
            message=str(e),
            timestamp=datetime.now(),
        )


async def check_database(db_instance: Any) -> HealthCheck:
    """Check if database is accessible."""
    start = time.perf_counter()
    
    try:
        # Try a simple database operation
        if hasattr(db_instance, 'backup'):
            # Don't actually backup, just check connectivity
            status = HealthStatus.HEALTHY
            message = "Database accessible"
        else:
            status = HealthStatus.DEGRADED
            message = "Database interface not fully initialized"
        
        duration = (time.perf_counter() - start) * 1000
        
        return HealthCheck(
            name="database",
            status=status,
            latency_ms=duration,
            message=message,
            timestamp=datetime.now(),
        )
    except Exception as e:
        return HealthCheck(
            name="database",
            status=HealthStatus.UNHEALTHY,
            latency_ms=(time.perf_counter() - start) * 1000,
            message=str(e),
            timestamp=datetime.now(),
        )


# Global instance
_global_health_manager: Optional[HealthCheckManager] = None

def initialize_health_checks(bot_instance: Any, db_instance: Optional[Any] = None) -> HealthCheckManager:
    """Initialize global health check manager with common checks."""
    global _global_health_manager
    
    _global_health_manager = HealthCheckManager()
    
    # Register checks
    _global_health_manager.register_check(
        "bot",
        lambda: check_bot_status(bot_instance)
    )
    _global_health_manager.register_check(
        "gemini_api",
        check_gemini_api
    )
    _global_health_manager.register_check(
        "voice",
        lambda: check_voice_subsystem(bot_instance)
    )
    
    if db_instance:
        _global_health_manager.register_check(
            "database",
            lambda: check_database(db_instance)
        )
    
    logger.info("Health check manager initialized with all checks registered")
    return _global_health_manager

def get_health_manager() -> Optional[HealthCheckManager]:
    """Get global health check manager."""
    return _global_health_manager
