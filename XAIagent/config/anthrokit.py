# AnthroKit Python Glue Module
# Minimal helper for loading presets and generating tone-appropriate responses

import yaml
import os
from pathlib import Path

# Load AnthroKit configuration
_config_path = Path(__file__).parent / "anthrokit.yaml"
TOKENS = yaml.safe_load(_config_path.read_text()) if _config_path.exists() else {}

# Determine active preset from environment
_anthro_level = os.getenv("ANTHROKIT_ANTHRO", os.getenv("HICXAI_ANTHRO", "low"))
PRESET = TOKENS.get("presets", {}).get("HighA" if _anthro_level == "high" else "LowA", {})


def pick(low, high):
    """Pick response based on anthropomorphism level."""
    return high if PRESET.get("self_reference") == "I" else low


def disclosure():
    """Return AI disclosure text based on preset."""
    disclosure_type = PRESET.get("disclosure", "explicit")
    if disclosure_type == "explicit":
        return TOKENS.get("tokens", {}).get("disclosure", {}).get("explicit_text", "I'm an AI assistant.")
    return "AI system."


def greet():
    """Generate greeting based on anthropomorphism level."""
    return pick(
        "Hello. This assistant will guide you through a short credit pre-assessment.",
        f"Hi, I'm {PRESET.get('persona_name', 'Luna')}. I'll guide you through a short credit pre-assessment."
    )


def decision_approve():
    """Generate approval message."""
    return pick(
        "Preliminary result: approved. This is a simulated research result.",
        "Good news—your preliminary result is approved. This is a simulated research result."
    )


def decision_decline():
    """Generate decline message."""
    return pick(
        "Preliminary result: declined. A brief explanation is available.",
        "I know this matters—your preliminary result is declined. I can walk you through why."
    )


def close():
    """Generate closing message."""
    return pick(
        "You can return to the survey now. Thank you.",
        "When you're ready, I'll send you back to the survey. Thanks for working through this with me."
    )


def get_preset():
    """Return the active preset configuration."""
    return PRESET


def get_temperature():
    """Return temperature setting for current preset."""
    return PRESET.get("temperature", 0.6 if _anthro_level == "high" else 0.3)
