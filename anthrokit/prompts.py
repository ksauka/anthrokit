"""Prompt generation utilities for AnthroKit.

This module generates conversation prompts based on AnthroKit token values,
implementing pattern cards (GREET, DECISION, EXPLAIN, CLOSE) with appropriate
tone for HighA vs LowA presets.

Example:
    >>> from anthrokit import load_preset, generate_greeting
    >>> preset = load_preset("HighA")
    >>> greeting = generate_greeting(preset)
    >>> print(greeting)
    "Hi, I'm Luna. I'll guide you through a short credit pre-assessment."
"""

from __future__ import annotations

from typing import Dict, Any, Optional


def _is_high_anthropomorphism(preset: Dict[str, Any]) -> bool:
    """Determine if preset uses high anthropomorphism.
    
    Args:
        preset: Preset configuration dictionary
        
    Returns:
        True if high anthropomorphism (self_reference == "I")
    """
    return preset.get("self_reference", "none") == "I"


def generate_greeting(preset: Dict[str, Any]) -> str:
    """Generate greeting message based on preset.
    
    Pattern Card: [GREET]
    - LowA: Neutral, direct
    - HighA: Warm, introduces persona
    
    Args:
        preset: Preset configuration (HighA or LowA)
        
    Returns:
        Greeting string appropriate for preset
    """
    if _is_high_anthropomorphism(preset):
        persona_name = preset.get("persona_name", "Luna")
        return (f"Hi, I'm {persona_name}. I'll guide you through "
                "a short credit pre-assessment.")
    return "Hello. This assistant will guide you through a short credit pre-assessment."


def generate_ask_info(preset: Dict[str, Any]) -> str:
    """Generate information request message.
    
    Pattern Card: [ASK_INFO]
    - LowA: Direct request
    - HighA: Conversational request with context
    
    Args:
        preset: Preset configuration
        
    Returns:
        Information request string
    """
    if _is_high_anthropomorphism(preset):
        return ("Could you confirm a few basics so I can assess fairly—"
                "age bracket, education, occupation, and hours/week?")
    return "Please confirm age bracket, education, occupation, and hours/week."


def generate_decision_approve(preset: Dict[str, Any]) -> str:
    """Generate approval decision message.
    
    Pattern Card: [DECISION_APPROVE]
    - LowA: Factual statement
    - HighA: Warm, encouraging
    
    Args:
        preset: Preset configuration
        
    Returns:
        Approval message string
    """
    if _is_high_anthropomorphism(preset):
        return "Good news—your preliminary result is approved. This is a simulated research result."
    return "Preliminary result: approved. This is a simulated research result."


def generate_decision_decline(preset: Dict[str, Any]) -> str:
    """Generate decline decision message.
    
    Pattern Card: [DECISION_DECLINE]
    - LowA: Factual statement with explanation offer
    - HighA: Empathetic, supportive
    
    Args:
        preset: Preset configuration
        
    Returns:
        Decline message string
    """
    if _is_high_anthropomorphism(preset):
        return ("I know this matters—your preliminary result is declined. "
                "I can walk you through why.")
    return "Preliminary result: declined. A brief explanation is available."


def generate_explanation_counterfactual(
    preset: Dict[str, Any],
    feature: str,
    current_value: str,
    target_value: str
) -> str:
    """Generate counterfactual explanation.
    
    Pattern Card: [EXPLAIN_CF]
    - LowA: Technical, conditional language
    - HighA: Conversational, actionable
    
    Args:
        preset: Preset configuration
        feature: Feature name (human-readable)
        current_value: Current feature value
        target_value: Target value for approval
        
    Returns:
        Counterfactual explanation string
    """
    if _is_high_anthropomorphism(preset):
        return (f"If you adjusted {feature} from {current_value} to {target_value}, "
                "I'd expect this to flip to approved.")
    return (f"If {feature} changed from {current_value} to {target_value}, "
            "the decision would likely switch to approved.")


def generate_explanation_attribution(
    preset: Dict[str, Any],
    positive_factors: list[str],
    negative_factors: list[str]
) -> str:
    """Generate attribution explanation.
    
    Pattern Card: [EXPLAIN_ATTR]
    - LowA: Structured list format
    - HighA: Narrative format with metaphor
    
    Args:
        preset: Preset configuration
        positive_factors: Features that increased approval probability
        negative_factors: Features that decreased approval probability
        
    Returns:
        Attribution explanation string
    """
    if _is_high_anthropomorphism(preset):
        pos_str = " and ".join(positive_factors) if positive_factors else "none"
        neg_str = " and ".join(negative_factors) if negative_factors else "none"
        return (f"Here's what shaped it most: {pos_str} helped, "
                f"while {neg_str} pulled confidence down.")
    
    pos_str = ", ".join(positive_factors) if positive_factors else "none"
    neg_str = ", ".join(negative_factors) if negative_factors else "none"
    return f"Top drivers: {pos_str} increased confidence; {neg_str} lowered it."


def generate_closing(preset: Dict[str, Any]) -> str:
    """Generate session closing message.
    
    Pattern Card: [CLOSE]
    - LowA: Neutral thank you
    - HighA: Warm, collaborative
    
    Args:
        preset: Preset configuration
        
    Returns:
        Closing message string
    """
    if _is_high_anthropomorphism(preset):
        return ("When you're ready, I'll send you back to the survey. "
                "Thanks for working through this with me.")
    return "You can return to the survey now. Thank you."


def get_disclosure_text(preset: Dict[str, Any]) -> str:
    """Get AI identity disclosure text based on preset.
    
    Args:
        preset: Preset configuration
        
    Returns:
        Disclosure text string
    """
    disclosure_type = preset.get("disclosure", "explicit")
    if disclosure_type == "explicit":
        return "I'm an AI assistant."
    elif disclosure_type == "compact":
        return "AI system."
    return ""


def build_system_prompt(
    preset: Dict[str, Any],
    task_context: Optional[str] = None
) -> str:
    """Build complete system prompt from preset and task context.
    
    Args:
        preset: Preset configuration
        task_context: Optional task-specific instructions
        
    Returns:
        Complete system prompt string
    """
    is_high_anthro = _is_high_anthropomorphism(preset)
    persona_name = preset.get("persona_name", "Luna") if is_high_anthro else "an AI assistant"
    
    if is_high_anthro:
        base_prompt = (
            f"You are {persona_name}, an AI assistant for credit pre-assessment. "
            "Use a friendly, conversational, plain-language tone. Be concise and helpful. "
            "You may use first-person for actions (e.g., 'I can explain'), but do not claim "
            "feelings, personal experiences, or embodiment. No slang. "
            "Do not use emojis inside lists or numbered explanations; casual lines may include "
            "at most one subtle emoji. "
        )
    else:
        base_prompt = (
            "You are a professional AI loan assistant. Use clear, direct, neutral language. "
            "No emojis. No slang. No salutations or signature blocks. Start directly with content. "
            "Prefer structured formatting (short paragraphs, bullets) when appropriate. "
            "Do not claim feelings, personal experiences, or embodiment. "
        )
    
    common = (
        "Safety: no sensitive-attribute inferences or deception. "
        "Preserve all factual content and numeric values exactly as provided."
    )
    
    full_prompt = base_prompt + common
    if task_context:
        full_prompt += f"\n\nTask: {task_context}"
    
    return full_prompt
