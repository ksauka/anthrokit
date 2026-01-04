"""Configuration loader and validator for AnthroKit presets.

This module handles loading and validation of anthrokit.yaml configuration files,
providing access to token definitions, presets, and policy guardrails.

Example:
    >>> from anthrokit.config import load_preset
    >>> preset = load_preset("HighA")
    >>> print(preset["warmth"])
    0.7
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class AnthroKitConfig:
    """AnthroKit configuration manager.
    
    Loads and validates anthrokit.yaml configuration files, providing
    structured access to tokens, presets, and policies.
    
    Attributes:
        config_path: Path to anthrokit.yaml configuration file
        _config: Loaded configuration dictionary
        _presets: Available preset configurations (HighA, LowA)
        _tokens: Token definitions
        _policy: Safety policy guardrails
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration loader.
        
        Args:
            config_path: Path to anthrokit.yaml file. If None, searches
                in standard locations (package dir, project root).
        """
        self.config_path = config_path or self._find_config()
        self._config: Dict[str, Any] = {}
        self._presets: Dict[str, Dict[str, Any]] = {}
        self._tokens: Dict[str, Any] = {}
        self._policy: Dict[str, Any] = {}
        
        if self.config_path and self.config_path.exists():
            self._load()
    
    def _find_config(self) -> Optional[Path]:
        """Search for anthrokit.yaml in standard locations.
        
        Returns:
            Path to config file if found, None otherwise.
        """
        search_paths = [
            Path(__file__).parent / "anthrokit.yaml",  # Package directory
            Path.cwd() / "anthrokit.yaml",  # Current working directory
            Path.cwd().parent / "anthrokit.yaml",  # Parent directory
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        return None
    
    def _load(self) -> None:
        """Load and parse anthrokit.yaml configuration."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            self._config = data.get("anthrokit", {})
            self._presets = self._config.get("presets", {})
            self._tokens = self._config.get("tokens", {})
            self._policy = self._config.get("policy", {})
            
        except Exception as e:
            raise ValueError(f"Failed to load anthrokit.yaml: {e}")
    
    def get_preset(self, preset_name: str) -> Dict[str, Any]:
        """Get preset configuration by name.
        
        Args:
            preset_name: Name of preset ("HighA" or "LowA")
            
        Returns:
            Dictionary of preset token values
            
        Raises:
            KeyError: If preset not found
        """
        if preset_name not in self._presets:
            raise KeyError(f"Preset '{preset_name}' not found. "
                         f"Available: {list(self._presets.keys())}")
        return self._presets[preset_name].copy()
    
    def get_token_definition(self, token_name: str) -> Dict[str, Any]:
        """Get token definition including type, range, examples, guardrails.
        
        Args:
            token_name: Name of token (e.g., "warmth", "emoji")
            
        Returns:
            Dictionary of token metadata
            
        Raises:
            KeyError: If token not found
        """
        if token_name not in self._tokens:
            raise KeyError(f"Token '{token_name}' not found. "
                         f"Available: {list(self._tokens.keys())}")
        return self._tokens[token_name].copy()
    
    def get_policy(self) -> Dict[str, Any]:
        """Get safety policy guardrails.
        
        Returns:
            Dictionary of policy flags and guardrail text
        """
        return self._policy.copy()
    
    @property
    def version(self) -> str:
        """Get AnthroKit configuration version."""
        return self._config.get("version", "unknown")


# Global configuration instance
_config_instance: Optional[AnthroKitConfig] = None


def load_config(config_path: Optional[Path] = None) -> AnthroKitConfig:
    """Load AnthroKit configuration (singleton pattern).
    
    Args:
        config_path: Optional path to anthrokit.yaml
        
    Returns:
        AnthroKitConfig instance
    """
    global _config_instance
    if _config_instance is None or config_path is not None:
        _config_instance = AnthroKitConfig(config_path)
    return _config_instance


def load_preset(preset_name: str, config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load a preset configuration (HighA or LowA).
    
    Args:
        preset_name: Name of preset to load
        config_path: Optional path to anthrokit.yaml
        
    Returns:
        Dictionary of preset token values
        
    Example:
        >>> preset = load_preset("HighA")
        >>> print(preset["warmth"])
        0.7
    """
    config = load_config(config_path)
    return config.get_preset(preset_name)


def get_preset(anthropomorphism_level: str = "low",
               config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Get preset based on anthropomorphism level from environment or parameter.
    
    Args:
        anthropomorphism_level: "high" or "low" (default: from ANTHROKIT_ANTHRO env var)
        config_path: Optional path to anthrokit.yaml
        
    Returns:
        Dictionary of preset token values
    """
    level = os.getenv("ANTHROKIT_ANTHRO", 
                     os.getenv("HICXAI_ANTHRO", anthropomorphism_level)).lower()
    preset_name = "HighA" if level == "high" else "LowA"
    return load_preset(preset_name, config_path)
