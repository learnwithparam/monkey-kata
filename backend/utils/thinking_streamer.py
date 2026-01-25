"""
Thinking Streamer
==================

Utility for streaming LLM thinking/reasoning to the frontend in real-time.

This module provides a unified way to stream intermediate processing steps,
agent reasoning, tool usage, and analysis results to the frontend.

Usage:
    streamer = ThinkingStreamer()
    
    # Emit different types of thinking blocks
    await streamer.emit_thinking("reasoning", "Analyzing the input data...")
    await streamer.emit_tool_use("search_web", {"query": "competitor info"}, "Found 5 results")
    await streamer.emit_step("Step 1", "Processing document", progress=25)
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, AsyncGenerator, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Session-based registry for managing multiple ThinkingStreamer instances
_session_registry: Dict[str, "ThinkingStreamer"] = {}


class ThinkingCategory(str, Enum):
    """Categories of thinking/reasoning events"""
    REASONING = "reasoning"      # LLM's internal reasoning
    TOOL_USE = "tool_use"        # Using a tool (search, scrape, etc.)
    OBSERVATION = "observation"  # Observing tool output
    PLANNING = "planning"        # Planning next steps
    ANALYSIS = "analysis"        # Analyzing data
    PROCESSING = "processing"    # Generic processing step
    AGENT = "agent"              # Agent-level action
    ERROR = "error"              # Error occurred
    COMPLETE = "complete"        # Task completed


@dataclass
class ThinkingEvent:
    """A single thinking/reasoning event"""
    category: str
    content: str
    timestamp: str
    agent: Optional[str] = None
    tool: Optional[str] = None
    target: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    progress: Optional[int] = None  # 0-100 progress indicator
    duration_ms: Optional[int] = None  # How long this step took
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                result[key] = value
        return result
    
    def to_sse(self) -> str:
        """Convert to SSE format"""
        return f"data: {json.dumps({'thinking': self.to_dict()}, ensure_ascii=False)}\n\n"


class ThinkingStreamer:
    """
    Streams thinking/reasoning events to SSE or WebSocket connections.
    
    This class provides a unified interface for emitting thinking events
    that can be consumed by the frontend to show real-time processing.
    """
    
    def __init__(self, agent_name: Optional[str] = None):
        """
        Initialize the streamer.
        
        Args:
            agent_name: Default agent name for events
        """
        self.agent_name = agent_name
        self._queue: asyncio.Queue[Optional[ThinkingEvent]] = asyncio.Queue(maxsize=100)
        self._start_time = datetime.now()
        self._step_start_time: Optional[datetime] = None
        self._is_closed = False
        self._callbacks: List[Callable[[ThinkingEvent], None]] = []
    
    def add_callback(self, callback: Callable[[ThinkingEvent], None]):
        """Add a callback to be called on each thinking event"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[ThinkingEvent], None]):
        """Remove a callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def emit_thinking(
        self,
        category: str,
        content: str,
        agent: Optional[str] = None,
        tool: Optional[str] = None,
        target: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        progress: Optional[int] = None
    ) -> ThinkingEvent:
        """
        Emit a thinking event.
        
        Args:
            category: Type of thinking (reasoning, tool_use, etc.)
            content: The actual thought/reasoning content
            agent: Agent name (uses default if not provided)
            tool: Tool being used (if applicable)
            target: Target of the action (URL, query, etc.)
            metadata: Additional metadata
            progress: Progress percentage (0-100)
            
        Returns:
            The created ThinkingEvent
        """
        # Calculate duration if we have a step start time
        duration_ms = None
        if self._step_start_time:
            duration_ms = int((datetime.now() - self._step_start_time).total_seconds() * 1000)
        
        event = ThinkingEvent(
            category=category,
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent=agent or self.agent_name,
            tool=tool,
            target=target,
            metadata=metadata,
            progress=progress,
            duration_ms=duration_ms
        )
        
        # Reset step start time
        self._step_start_time = datetime.now()
        
        # Put in queue for streaming
        if not self._is_closed:
            try:
                self._queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Thinking queue is full, dropping event")
        
        # Call callbacks
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"Error in thinking callback: {e}")
        
        return event
    
    async def emit_reasoning(self, content: str, step: Optional[int] = None, **kwargs) -> ThinkingEvent:
        """Emit a reasoning event"""
        metadata = kwargs.pop("metadata", None) or {}
        if step is not None:
            metadata["step"] = step
        return await self.emit_thinking(
            ThinkingCategory.REASONING,
            content,
            metadata=metadata if metadata else None,
            **kwargs
        )
    
    async def emit_tool_use(
        self,
        tool: str,
        input_data: Optional[Dict[str, Any]] = None,
        output: Optional[str] = None,
        **kwargs
    ) -> ThinkingEvent:
        """Emit a tool usage event"""
        content = f"Using {tool}"
        if input_data:
            # Truncate long input data
            input_str = str(input_data)
            if len(input_str) > 100:
                input_str = input_str[:100] + "..."
            content += f": {input_str}"
        
        metadata = {"input": input_data}
        if output:
            # Truncate long output
            if len(output) > 200:
                output = output[:200] + "..."
            metadata["output"] = output
        
        return await self.emit_thinking(
            ThinkingCategory.TOOL_USE,
            content,
            tool=tool,
            metadata=metadata,
            **kwargs
        )
    
    async def emit_observation(self, content: str, tool: Optional[str] = None, **kwargs) -> ThinkingEvent:
        """Emit an observation event (result of tool use)"""
        return await self.emit_thinking(
            ThinkingCategory.OBSERVATION,
            content,
            tool=tool,
            **kwargs
        )
    
    async def emit_planning(self, plan: str, **kwargs) -> ThinkingEvent:
        """Emit a planning event"""
        return await self.emit_thinking(
            ThinkingCategory.PLANNING,
            plan,
            **kwargs
        )
    
    async def emit_analysis(self, topic: str, analysis: str, **kwargs) -> ThinkingEvent:
        """Emit an analysis event"""
        content = f"{topic}: {analysis}"
        return await self.emit_thinking(
            ThinkingCategory.ANALYSIS,
            content,
            **kwargs
        )
    
    async def emit_agent_action(
        self,
        agent: str,
        action: str,
        is_complete: bool = False,
        **kwargs
    ) -> ThinkingEvent:
        """Emit an agent action event"""
        category = ThinkingCategory.COMPLETE if is_complete else ThinkingCategory.AGENT
        return await self.emit_thinking(
            category,
            action,
            agent=agent,
            **kwargs
        )
    
    async def emit_step(
        self,
        title: str,
        description: str,
        progress: Optional[int] = None,
        **kwargs
    ) -> ThinkingEvent:
        """Emit a processing step event"""
        content = f"{title}: {description}" if description else title
        return await self.emit_thinking(
            ThinkingCategory.PROCESSING,
            content,
            progress=progress,
            **kwargs
        )
    
    async def emit_error(self, error: str, **kwargs) -> ThinkingEvent:
        """Emit an error event"""
        return await self.emit_thinking(
            ThinkingCategory.ERROR,
            error,
            **kwargs
        )
    
    async def emit_complete(self, message: str = "Processing complete", **kwargs) -> ThinkingEvent:
        """Emit a completion event"""
        return await self.emit_thinking(
            ThinkingCategory.COMPLETE,
            message,
            progress=100,
            **kwargs
        )
    
    def close(self):
        """Close the streamer"""
        self._is_closed = True
        try:
            self._queue.put_nowait(None)  # Signal end
        except asyncio.QueueFull:
            pass
    
    async def stream_events(self) -> AsyncGenerator[str, None]:
        """
        Stream thinking events as SSE format.
        
        Yields:
            SSE formatted strings
        """
        while True:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=60.0)
                if event is None:
                    break
                yield event.to_sse()
            except asyncio.TimeoutError:
                # Send keepalive
                yield f": keepalive\n\n"
            except Exception as e:
                logger.error(f"Error streaming thinking events: {e}")
                break
    
    def get_events_sync(self) -> List[ThinkingEvent]:
        """
        Get all queued events synchronously (for testing/debugging).
        
        Returns:
            List of queued events
        """
        events = []
        while not self._queue.empty():
            try:
                event = self._queue.get_nowait()
                if event is not None:
                    events.append(event)
            except asyncio.QueueEmpty:
                break
        return events
    
    # -------------------------------------------------------------------------
    # Static/Class methods for session-based access
    # -------------------------------------------------------------------------
    
    @staticmethod
    def get_streamer(session_id: str) -> "ThinkingStreamer":
        """
        Get or create a ThinkingStreamer for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            ThinkingStreamer instance for this session
        """
        if session_id not in _session_registry:
            _session_registry[session_id] = ThinkingStreamer(agent_name=f"session_{session_id}")
        return _session_registry[session_id]
    
    @staticmethod
    def add_event(session_id: str, category: str, content: str, **kwargs) -> None:
        """
        Add a thinking event to a session's streamer (non-async convenience method).
        
        Args:
            session_id: Unique session identifier
            category: Type of thinking event (reasoning, tool_use, etc.)
            content: The thought/reasoning content
            **kwargs: Additional arguments passed to emit_thinking
        """
        streamer = ThinkingStreamer.get_streamer(session_id)
        
        # Create event synchronously and add to queue
        event = ThinkingEvent(
            category=category,
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent=kwargs.get("agent") or streamer.agent_name,
            tool=kwargs.get("tool"),
            target=kwargs.get("target"),
            metadata=kwargs.get("metadata"),
            progress=kwargs.get("progress"),
            duration_ms=None
        )
        
        try:
            streamer._queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(f"Thinking queue full for session {session_id}, dropping event")
    
    @staticmethod
    async def stream_events(session_id: str) -> AsyncGenerator[ThinkingEvent, None]:
        """
        Stream thinking events for a session.
        
        Args:
            session_id: Unique session identifier
            
        Yields:
            ThinkingEvent instances
        """
        streamer = ThinkingStreamer.get_streamer(session_id)
        
        while True:
            try:
                event = await asyncio.wait_for(streamer._queue.get(), timeout=60.0)
                if event is None:
                    break
                yield event
            except asyncio.TimeoutError:
                # Timeout without events, stop streaming
                break
            except Exception as e:
                logger.error(f"Error streaming thinking events for session {session_id}: {e}")
                break
    
    @staticmethod
    def cleanup_session(session_id: str) -> None:
        """
        Clean up a session's streamer.
        
        Args:
            session_id: Unique session identifier
        """
        if session_id in _session_registry:
            streamer = _session_registry[session_id]
            streamer.close()
            del _session_registry[session_id]


def create_thinking_callback(streamer: ThinkingStreamer) -> Callable[[Any], None]:
    """
    Create a callback function compatible with existing progress callback systems.
    
    This bridges the old progress callback pattern with the new ThinkingStreamer.
    
    Args:
        streamer: The ThinkingStreamer to emit events to
        
    Returns:
        Callback function that can be used with set_progress_callback()
    """
    def callback(step_data):
        """Handle progress updates and convert to thinking events"""
        try:
            # Handle both string and dict formats
            if isinstance(step_data, str):
                message = step_data
                agent = None
                tool = None
                target = None
            else:
                message = step_data.get("message", "")
                agent = step_data.get("agent")
                tool = step_data.get("tool")
                target = step_data.get("target")
            
            # Determine category based on tool type
            if tool in ["search_web", "scrape_website"]:
                category = ThinkingCategory.TOOL_USE
            elif tool == "agent_invoke":
                category = ThinkingCategory.AGENT
            elif tool == "agent_complete":
                category = ThinkingCategory.COMPLETE
            else:
                category = ThinkingCategory.PROCESSING
            
            # Create event synchronously (will be picked up by stream)
            event = ThinkingEvent(
                category=category,
                content=message,
                timestamp=datetime.now().isoformat(),
                agent=agent,
                tool=tool,
                target=target
            )
            
            # Put in queue without blocking
            try:
                streamer._queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Thinking queue full, dropping callback event")
            
            # Call streamer callbacks
            for cb in streamer._callbacks:
                try:
                    cb(event)
                except Exception as e:
                    logger.warning(f"Error in thinking callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error in thinking callback wrapper: {e}")
    
    return callback
