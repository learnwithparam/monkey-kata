"""
Progress Reporting for Legal Case Intake
========================================

This module provides progress reporting functionality for the legal case intake workflow.
It allows tracking agent activities in real-time for educational purposes.
"""

import logging
import sys
import io
from typing import Optional, Callable, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Global callback for progress updates
_progress_callback: Optional[Callable[[Any], None]] = None
_log_capture_callback: Optional[Callable[[str], None]] = None

def set_progress_callback(callback: Optional[Callable[[Any], None]]):
    """Set a callback function to report progress updates"""
    global _progress_callback
    _progress_callback = callback

def set_log_capture_callback(callback: Optional[Callable[[str], None]]):
    """Set a callback function to capture and stream logs"""
    global _log_capture_callback
    _log_capture_callback = callback

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

def capture_log_line(line: str):
    """Capture a log line and send it to the callback"""
    if _log_capture_callback:
        try:
            # Capture all non-empty lines from CrewAI verbose output
            # Filter out only very noisy/unhelpful lines
            line_stripped = line.strip()
            if not line_stripped:
                return
            
            # Skip very verbose/unhelpful lines
            line_lower = line_stripped.lower()
            skip_patterns = [
                'wrapper: completed call',
                'litellm completion()',
                'utils.py:',
                'calling success_handler',
                'trace batch finalization',
                'view here:',
                'access code:',
            ]
            
            # Only skip if it matches skip patterns
            if any(pattern in line_lower for pattern in skip_patterns):
                return
            
            # Capture everything else (CrewAI verbose output, agent activities, etc.)
            _log_capture_callback(line_stripped)
        except Exception as e:
            logger.warning(f"Error in log capture callback: {e}")

class CrewAILogHandler(logging.Handler):
    """Custom logging handler to capture CrewAI verbose output"""
    def emit(self, record):
        try:
            msg = self.format(record)
            capture_log_line(msg)
        except Exception:
            self.handleError(record)

@contextmanager
def capture_crewai_logs():
    """Context manager to capture CrewAI's stdout/stderr output"""
    import sys
    import threading
    
    # Store original streams
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    
    # Create a custom stream that captures output
    class LoggingStream:
        def __init__(self, original_stream, name='stdout'):
            self.original_stream = original_stream
            self.name = name
            self._lock = threading.Lock()
        
        def write(self, text):
            # Capture the log line
            if text.strip():  # Only capture non-empty lines
                # Split by newlines to handle multi-line output
                for line in text.split('\n'):
                    if line.strip():
                        # Clean the line to avoid JSON issues
                        cleaned_line = line.strip().replace('\x00', '').replace('\r', '')
                        if cleaned_line:
                            capture_log_line(cleaned_line)
            
            # Also write to original stream to maintain normal logging
            if self.original_stream:
                self.original_stream.write(text)
        
        def flush(self):
            if self.original_stream:
                self.original_stream.flush()
        
        def __getattr__(self, name):
            # Delegate other attributes to original stream
            return getattr(self.original_stream, name)
    
    # Replace stdout and stderr temporarily
    sys.stdout = LoggingStream(old_stdout, 'stdout')
    sys.stderr = LoggingStream(old_stderr, 'stderr')
    
    try:
        yield
    finally:
        # Restore original streams
        sys.stdout = old_stdout
        sys.stderr = old_stderr

