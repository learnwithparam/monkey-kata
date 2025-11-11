"""
Progress Reporting for Legal Case Intake
========================================

This module provides progress reporting functionality for the legal case intake workflow.
It allows tracking agent activities in real-time for educational purposes.
"""

import logging
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)

# Global callback for progress updates
_progress_callback: Optional[Callable[[Any], None]] = None

def set_progress_callback(callback: Optional[Callable[[Any], None]]):
    """Set a callback function to report progress updates"""
    global _progress_callback
    _progress_callback = callback

def report_progress(message: str, agent: str = None, tool: str = None, target: str = None):
    """Report progress if callback is set"""
    if _progress_callback:
        try:
            step_data = {
                "message": message,
                "agent": agent,
                "tool": tool,
                "target": target
            }
            _progress_callback(step_data)
        except Exception as e:
            logger.warning(f"Error in progress callback: {e}")

