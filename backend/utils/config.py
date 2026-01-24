"""
Demo Configuration Utility
===========================

Provides utilities for loading demo-specific environment variables.
Each demo can have its own .env file (e.g., demos/image_to_drawing/.env)
to override global settings like models or API keys.

Usage:
    from utils.config import load_demo_env, get_demo_config
    
    # Load demo-specific environment (call early in demo initialization)
    load_demo_env("image_to_drawing")
    
    # Or get config dict without modifying environment
    config = get_demo_config("image_to_drawing")
"""

import os
from pathlib import Path
from typing import Dict, Optional
from dotenv import dotenv_values
import logging

logger = logging.getLogger(__name__)

# Cache for loaded demo configs
_demo_configs: Dict[str, Dict[str, str]] = {}


def get_demos_dir() -> Path:
    """Get the absolute path to the demos directory."""
    # This file is at backend/utils/config.py
    # demos is at backend/demos/
    return Path(__file__).parent.parent / "demos"


def get_demo_env_path(demo_name: str) -> Path:
    """Get the path to a demo's .env file."""
    return get_demos_dir() / demo_name / ".env"


def load_demo_env(demo_name: str, override: bool = True) -> Dict[str, str]:
    """
    Load environment variables from a demo-specific .env file.
    
    Args:
        demo_name: Name of the demo (e.g., "image_to_drawing")
        override: If True, override existing environment variables
        
    Returns:
        Dict of loaded environment variables
    """
    env_path = get_demo_env_path(demo_name)
    
    if not env_path.exists():
        logger.debug(f"No .env file found for demo '{demo_name}' at {env_path}")
        return {}
    
    # Load values from demo .env file
    demo_env = dotenv_values(env_path)
    
    # Apply to environment
    for key, value in demo_env.items():
        if value is not None:
            if override or key not in os.environ:
                os.environ[key] = value
                logger.debug(f"Set {key} from {demo_name}/.env")
    
    # Cache the config
    _demo_configs[demo_name] = {k: v for k, v in demo_env.items() if v is not None}
    
    logger.info(f"Loaded {len(demo_env)} environment variables from {demo_name}/.env")
    return _demo_configs[demo_name]


def get_demo_config(demo_name: str) -> Dict[str, str]:
    """
    Get demo-specific configuration without modifying the environment.
    
    Args:
        demo_name: Name of the demo
        
    Returns:
        Dict of demo-specific environment variables (empty if no .env file)
    """
    if demo_name in _demo_configs:
        return _demo_configs[demo_name]
    
    env_path = get_demo_env_path(demo_name)
    
    if not env_path.exists():
        return {}
    
    demo_env = dotenv_values(env_path)
    _demo_configs[demo_name] = {k: v for k, v in demo_env.items() if v is not None}
    return _demo_configs[demo_name]


def get_demo_setting(demo_name: str, key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a specific setting for a demo.
    
    Priority:
    1. Demo-specific .env file
    2. Global environment variable
    3. Default value
    
    Args:
        demo_name: Name of the demo
        key: Environment variable key
        default: Default value if not found
        
    Returns:
        The setting value or default
    """
    # Check demo-specific config first
    demo_config = get_demo_config(demo_name)
    if key in demo_config:
        return demo_config[key]
    
    # Fall back to global environment
    return os.getenv(key, default)
