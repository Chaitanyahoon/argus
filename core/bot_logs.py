"""
Bot Logs Manager — reads bot logs, displays them in Discord, and manages logging channels.
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple
import json

logger = logging.getLogger(__name__)

LOG_DIR = Path("logs")


class BotLogsManager:
    """Manages bot logging and log retrieval for Discord display."""

    def __init__(self):
        self.log_dir = LOG_DIR
        self.max_lines = 50  # Max lines to display in Discord

    def get_latest_logs(self, lines: int = 30, level: Optional[str] = None) -> str:
        """
        Read the latest bot logs.
        
        Args:
            lines: Number of lines to return
            level: Filter by level (ERROR, WARNING, INFO, DEBUG)
        
        Returns:
            Formatted log string
        """
        if not self.log_dir.exists():
            return "📭 No logs found. Log directory doesn't exist."

        # Find the latest log file
        log_files = sorted(self.log_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
        if not log_files:
            return "📭 No log files found yet."

        latest_log = log_files[0]

        try:
            with open(latest_log, "r", encoding="utf-8") as f:
                all_lines = f.readlines()

            # Filter by level if specified
            if level:
                all_lines = [ln for ln in all_lines if f" {level.upper()} " in ln.upper()]

            # Get last N lines
            selected = all_lines[-lines:]
            if not selected:
                return f"📭 No logs found at level {level}."

            log_text = "".join(selected)

            # Truncate to Discord message limit
            if len(log_text) > 1900:
                log_text = "...\n" + log_text[-1900:]

            return f"```\n{log_text}\n```"
        except Exception as e:
            logger.error("Error reading logs: %s", e)
            return f"❌ Error reading logs: {str(e)}"

    def get_errors_and_warnings(self, hours: int = 24) -> Tuple[int, int, str]:
        """
        Count errors and warnings in the last N hours.
        
        Returns:
            (error_count, warning_count, summary)
        """
        if not self.log_dir.exists():
            return 0, 0, "📭 No logs found."

        log_files = sorted(self.log_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
        if not log_files:
            return 0, 0, "📭 No log files found."

        cutoff_time = datetime.now() - timedelta(hours=hours)
        error_count = 0
        warning_count = 0
        recent_errors = []

        try:
            for log_file in log_files:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                if file_mtime < cutoff_time:
                    break

                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if " ERROR " in line:
                            error_count += 1
                            if len(recent_errors) < 5:
                                # Extract just the message part
                                msg = line.split(" | ")[-1].strip() if " | " in line else line.strip()
                                recent_errors.append(msg[:100])
                        elif " WARNING " in line:
                            warning_count += 1

            summary = f"🚨 **{error_count}** errors · ⚠️ **{warning_count}** warnings (last {hours}h)\n"
            if recent_errors:
                summary += "\n**Recent errors:**\n"
                for err in recent_errors[:3]:
                    summary += f"• {err}\n"

            return error_count, warning_count, summary
        except Exception as e:
            logger.error("Error analyzing logs: %s", e)
            return 0, 0, f"❌ Error: {str(e)}"

    def get_system_health(self) -> str:
        """Get bot system health summary."""
        error_count, warning_count, _ = self.get_errors_and_warnings(hours=1)

        if error_count > 10:
            status = "🔴 Critical"
        elif error_count > 5 or warning_count > 20:
            status = "🟡 Warning"
        else:
            status = "🟢 Healthy"

        health = f"**System Status**: {status}\n"
        health += f"🚨 Errors (1h): {error_count}\n"
        health += f"⚠️ Warnings (1h): {warning_count}\n"

        return health

    def get_log_timestamps(self) -> str:
        """Get info about available log files."""
        if not self.log_dir.exists():
            return "📭 No logs available."

        log_files = sorted(self.log_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
        if not log_files:
            return "📭 No log files found."

        info = "**Available Logs:**\n"
        for i, log_file in enumerate(log_files[:5]):
            mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
            size_kb = os.path.getsize(log_file) / 1024
            info += f"`{i+1}.` {log_file.name} ({size_kb:.1f}KB) — {mtime.strftime('%Y-%m-%d %H:%M')}\n"

        return info


# Global instance
_logs_manager: Optional[BotLogsManager] = None


def get_logs_manager() -> BotLogsManager:
    """Get or create the global logs manager."""
    global _logs_manager
    if _logs_manager is None:
        _logs_manager = BotLogsManager()
    return _logs_manager
