"""
LangChain Thinking Callback Handler
====================================

Callback handler for LangChain agents that captures and streams
reasoning, tool usage, and agent actions to the frontend.

Usage:
    from utils.thinking_callback import ThinkingCallbackHandler
    from utils.thinking_streamer import ThinkingStreamer
    
    streamer = ThinkingStreamer(agent_name="Research Agent")
    handler = ThinkingCallbackHandler(streamer)
    
    # Use with LangChain agents
    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, callbacks=[handler])
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.outputs import LLMResult

from .thinking_streamer import ThinkingStreamer, ThinkingCategory

logger = logging.getLogger(__name__)


class ThinkingCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler that streams agent thinking to frontend.
    
    This handler captures:
    - LLM start/end events
    - Tool start/end events
    - Agent action events
    - Chain start/end events
    
    And converts them to ThinkingEvents for real-time streaming.
    """
    
    def __init__(
        self,
        streamer: ThinkingStreamer,
        agent_name: Optional[str] = None,
        verbose: bool = True
    ):
        """
        Initialize the callback handler.
        
        Args:
            streamer: ThinkingStreamer to emit events to
            agent_name: Default agent name for events
            verbose: If True, emit detailed events
        """
        super().__init__()
        self.streamer = streamer
        self.agent_name = agent_name
        self.verbose = verbose
        self._current_tool: Optional[str] = None
        self._tool_start_time: Optional[datetime] = None
    
    # ==================== LLM Events ====================
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """Called when LLM starts processing"""
        if self.verbose:
            # Emit a reasoning event
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.streamer.emit_reasoning(
                        "Analyzing input and formulating response...",
                        agent=self.agent_name
                    ))
                else:
                    loop.run_until_complete(self.streamer.emit_reasoning(
                        "Analyzing input and formulating response...",
                        agent=self.agent_name
                    ))
            except RuntimeError:
                # No event loop, just log
                logger.debug("LLM start: Analyzing input")
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM finishes processing"""
        pass  # We handle this in agent_action for more context
    
    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        """Called when LLM encounters an error"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.streamer.emit_error(
                    f"LLM error: {str(error)}",
                    agent=self.agent_name
                ))
            else:
                loop.run_until_complete(self.streamer.emit_error(
                    f"LLM error: {str(error)}",
                    agent=self.agent_name
                ))
        except RuntimeError:
            logger.error(f"LLM error: {error}")
    
    # ==================== Tool Events ====================
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """Called when a tool starts executing"""
        tool_name = serialized.get("name", "unknown_tool")
        self._current_tool = tool_name
        self._tool_start_time = datetime.now()
        
        # Truncate long inputs
        display_input = input_str
        if len(display_input) > 100:
            display_input = display_input[:100] + "..."
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.streamer.emit_tool_use(
                    tool_name,
                    {"input": display_input},
                    agent=self.agent_name,
                    target=display_input
                ))
            else:
                loop.run_until_complete(self.streamer.emit_tool_use(
                    tool_name,
                    {"input": display_input},
                    agent=self.agent_name,
                    target=display_input
                ))
        except RuntimeError:
            logger.debug(f"Tool start: {tool_name}")
    
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool finishes executing"""
        tool_name = self._current_tool or "tool"
        
        # Truncate long outputs
        display_output = str(output)
        if len(display_output) > 200:
            display_output = display_output[:200] + "..."
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.streamer.emit_observation(
                    f"Result from {tool_name}: {display_output}",
                    tool=tool_name,
                    agent=self.agent_name
                ))
            else:
                loop.run_until_complete(self.streamer.emit_observation(
                    f"Result from {tool_name}: {display_output}",
                    tool=tool_name,
                    agent=self.agent_name
                ))
        except RuntimeError:
            logger.debug(f"Tool end: {tool_name}")
        
        self._current_tool = None
    
    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        """Called when a tool encounters an error"""
        tool_name = self._current_tool or "tool"
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.streamer.emit_error(
                    f"Tool error ({tool_name}): {str(error)}",
                    agent=self.agent_name,
                    tool=tool_name
                ))
            else:
                loop.run_until_complete(self.streamer.emit_error(
                    f"Tool error ({tool_name}): {str(error)}",
                    agent=self.agent_name,
                    tool=tool_name
                ))
        except RuntimeError:
            logger.error(f"Tool error: {error}")
    
    # ==================== Agent Events ====================
    
    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> None:
        """Called when agent takes an action"""
        # The action.log contains the agent's reasoning
        reasoning = action.log if hasattr(action, 'log') and action.log else ""
        
        # Clean up the reasoning text
        if reasoning:
            # Remove tool call syntax if present
            reasoning = reasoning.strip()
            if len(reasoning) > 300:
                reasoning = reasoning[:300] + "..."
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.streamer.emit_planning(
                    f"Decided to use {action.tool}: {reasoning}" if reasoning else f"Using {action.tool}",
                    agent=self.agent_name,
                    tool=action.tool
                ))
            else:
                loop.run_until_complete(self.streamer.emit_planning(
                    f"Decided to use {action.tool}: {reasoning}" if reasoning else f"Using {action.tool}",
                    agent=self.agent_name,
                    tool=action.tool
                ))
        except RuntimeError:
            logger.debug(f"Agent action: {action.tool}")
    
    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Called when agent finishes"""
        # Get the final output
        output = finish.return_values.get("output", "") if finish.return_values else ""
        display_output = str(output)
        if len(display_output) > 200:
            display_output = display_output[:200] + "..."
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.streamer.emit_agent_action(
                    self.agent_name or "Agent",
                    f"Completed task: {display_output}",
                    is_complete=True
                ))
            else:
                loop.run_until_complete(self.streamer.emit_agent_action(
                    self.agent_name or "Agent",
                    f"Completed task: {display_output}",
                    is_complete=True
                ))
        except RuntimeError:
            logger.debug(f"Agent finish")
    
    # ==================== Chain Events ====================
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when a chain starts"""
        chain_name = serialized.get("name", serialized.get("id", ["unknown"])[-1])
        
        if self.verbose and chain_name != "AgentExecutor":
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.streamer.emit_step(
                        "Starting",
                        chain_name,
                        agent=self.agent_name
                    ))
                else:
                    loop.run_until_complete(self.streamer.emit_step(
                        "Starting",
                        chain_name,
                        agent=self.agent_name
                    ))
            except RuntimeError:
                logger.debug(f"Chain start: {chain_name}")
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when a chain ends"""
        pass  # Handled by agent_finish
    
    def on_chain_error(self, error: BaseException, **kwargs: Any) -> None:
        """Called when a chain encounters an error"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.streamer.emit_error(
                    f"Chain error: {str(error)}",
                    agent=self.agent_name
                ))
            else:
                loop.run_until_complete(self.streamer.emit_error(
                    f"Chain error: {str(error)}",
                    agent=self.agent_name
                ))
        except RuntimeError:
            logger.error(f"Chain error: {error}")


class AsyncThinkingCallbackHandler(ThinkingCallbackHandler):
    """
    Async version of ThinkingCallbackHandler for async agent execution.
    
    Use this when running agents with ainvoke() instead of invoke().
    """
    
    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """Called when LLM starts processing"""
        if self.verbose:
            await self.streamer.emit_reasoning(
                "Analyzing input and formulating response...",
                agent=self.agent_name
            )
    
    async def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        """Called when LLM encounters an error"""
        await self.streamer.emit_error(
            f"LLM error: {str(error)}",
            agent=self.agent_name
        )
    
    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """Called when a tool starts executing"""
        tool_name = serialized.get("name", "unknown_tool")
        self._current_tool = tool_name
        self._tool_start_time = datetime.now()
        
        display_input = input_str
        if len(display_input) > 100:
            display_input = display_input[:100] + "..."
        
        await self.streamer.emit_tool_use(
            tool_name,
            {"input": display_input},
            agent=self.agent_name,
            target=display_input
        )
    
    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool finishes executing"""
        tool_name = self._current_tool or "tool"
        
        display_output = str(output)
        if len(display_output) > 200:
            display_output = display_output[:200] + "..."
        
        await self.streamer.emit_observation(
            f"Result from {tool_name}: {display_output}",
            tool=tool_name,
            agent=self.agent_name
        )
        
        self._current_tool = None
    
    async def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        """Called when a tool encounters an error"""
        tool_name = self._current_tool or "tool"
        await self.streamer.emit_error(
            f"Tool error ({tool_name}): {str(error)}",
            agent=self.agent_name,
            tool=tool_name
        )
    
    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> None:
        """Called when agent takes an action"""
        reasoning = action.log if hasattr(action, 'log') and action.log else ""
        
        if reasoning:
            reasoning = reasoning.strip()
            if len(reasoning) > 300:
                reasoning = reasoning[:300] + "..."
        
        await self.streamer.emit_planning(
            f"Decided to use {action.tool}: {reasoning}" if reasoning else f"Using {action.tool}",
            agent=self.agent_name,
            tool=action.tool
        )
    
    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Called when agent finishes"""
        output = finish.return_values.get("output", "") if finish.return_values else ""
        display_output = str(output)
        if len(display_output) > 200:
            display_output = display_output[:200] + "..."
        
        await self.streamer.emit_agent_action(
            self.agent_name or "Agent",
            f"Completed task: {display_output}",
            is_complete=True
        )
    
    async def on_chain_error(self, error: BaseException, **kwargs: Any) -> None:
        """Called when a chain encounters an error"""
        await self.streamer.emit_error(
            f"Chain error: {str(error)}",
            agent=self.agent_name
        )
