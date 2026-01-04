"""Text stylizer for applying anthropomorphic tone to base content.

This module applies anthropomorphic tone modulation to base scaffolds using
either LLM-based stylization (when available) or pattern-based fallback rules.

The stylizer respects token values (warmth, formality, empathy, etc.) and
enforces guardrails for responsible anthropomorphism.

Example:
    >>> from anthrokit.stylizer import stylize_text
    >>> from anthrokit import load_preset
    >>> preset = load_preset("HighA")
    >>> base = "Preliminary result: declined."
    >>> styled = stylize_text(base, preset)
    >>> print(styled)
    "I know this isn't ideal — your preliminary result is declined."
"""

from __future__ import annotations

import os
from typing import Dict, Any, Optional

from .config import load_preset
from .validators import post_process_response


def _get_llm_client():
    """Get OpenAI client if available.
    
    Returns:
        OpenAI client or None if unavailable
    """
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        return OpenAI(api_key=api_key)
    except ImportError:
        return None


def _call_llm(
    model: str,
    messages: list,
    temperature: float = 0.5,
    max_tokens: int = 300
) -> Optional[str]:
    """Call OpenAI LLM with messages.
    
    Args:
        model: Model name (e.g., "gpt-4o-mini")
        messages: List of message dictionaries
        temperature: Sampling temperature
        max_tokens: Maximum response tokens
        
    Returns:
        LLM response text or None if unavailable
    """
    client = _get_llm_client()
    if not client:
        return None
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception:
        return None


def _build_stylization_prompt(
    preset: Dict[str, Any],
    text: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Build system prompt for LLM stylization.
    
    Args:
        preset: AnthroKit preset configuration
        text: Base text to stylize
        context: Optional context information
        
    Returns:
        System prompt string
    """
    warmth = preset.get("warmth", 0.5)
    formality = preset.get("formality", 0.5)
    empathy = preset.get("empathy", 0.5)
    self_ref = preset.get("self_reference", "none")
    hedging = preset.get("hedging", 0.3)
    emoji = preset.get("emoji", "none")
    persona = preset.get("persona_name", "")
    
    # Build tone instructions
    tone_instructions = []
    
    if warmth > 0.6:
        tone_instructions.append("Use a warm, friendly tone")
    elif warmth < 0.4:
        tone_instructions.append("Use a neutral, professional tone")
    
    if formality > 0.6:
        tone_instructions.append("Maintain formal language")
    elif formality < 0.4:
        tone_instructions.append("Use conversational, accessible language")
    
    if empathy > 0.6:
        tone_instructions.append("Show empathy and understanding")
    
    if self_ref == "I":
        tone_instructions.append(f"Use first-person (I/my) when appropriate")
        if persona:
            tone_instructions.append(f"Your name is {persona}")
    else:
        tone_instructions.append("Use neutral third-person or passive voice")
    
    if hedging > 0.5:
        tone_instructions.append("Use hedging language (might, could, possibly)")
    
    # Emoji policy
    emoji_instruction = {
        "none": "Do not use any emojis",
        "subtle": "You may use at most one subtle emoji (🙂, ✅) outside of lists",
        "moderate": "You may use emojis sparingly where appropriate"
    }.get(emoji, "Do not use any emojis")
    
    tone_instructions.append(emoji_instruction)
    
    # Guardrails
    guardrails = [
        "NEVER claim human feelings, emotions, or experiences",
        "NEVER claim embodiment or physical presence",
        "NEVER make inferences about sensitive attributes (race, gender, etc.)",
        "DO NOT add or fabricate factual information",
        "Preserve all numbers and technical details exactly",
    ]
    
    prompt = f"""You are a tone stylizer for conversational AI. Your task is to rephrase the following text according to these guidelines:

TONE INSTRUCTIONS:
{chr(10).join(f"• {instr}" for instr in tone_instructions)}

SAFETY GUARDRAILS:
{chr(10).join(f"• {rule}" for rule in guardrails)}

TASK: Rephrase the following text maintaining its factual content while applying the tone guidelines above.

Original text: {text}

Rephrased version (start directly with the content, no preamble):"""
    
    return prompt


def _apply_pattern_based_stylization(
    text: str,
    preset: Dict[str, Any]
) -> str:
    """Apply pattern-based stylization rules as fallback.
    
    Args:
        text: Base text to stylize
        preset: AnthroKit preset configuration
        
    Returns:
        Stylized text using simple rules
    """
    is_high_anthro = preset.get("self_reference") == "I"
    warmth = preset.get("warmth", 0.5)
    empathy = preset.get("empathy", 0.5)
    persona = preset.get("persona_name", "")
    
    # Apply simple transformation rules
    styled = text
    
    if is_high_anthro:
        # Add first-person markers
        if "declined" in text.lower() and empathy > 0.5:
            styled = f"I know this isn't ideal — {text.lower()}"
        elif "approved" in text.lower() and warmth > 0.6:
            styled = f"Good news — {text.lower()}"
        
        # Add persona in greetings
        if persona and ("assistant" in text.lower() or "guide" in text.lower()):
            styled = styled.replace("assistant", persona)
            if "This " in styled:
                styled = styled.replace("This", "I'm", 1)
        
        # First-person for explanations
        if "available" in text:
            styled = styled.replace("is available", "I can provide that")
    
    return styled


def stylize_text(
    text: str,
    preset: Optional[Dict[str, Any]] = None,
    preset_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    use_llm: bool = True,
    model: str = "gpt-4o-mini"
) -> str:
    """Apply anthropomorphic tone stylization to base text.
    
    This is the main stylization function. It attempts LLM-based stylization
    when available and API key is set, otherwise falls back to pattern-based
    rules.
    
    Args:
        text: Base text to stylize
        preset: AnthroKit preset dictionary (HighA or LowA)
        preset_name: Preset name if preset dict not provided
        context: Optional context for stylization
        use_llm: Whether to attempt LLM stylization (default: True)
        model: LLM model name (default: "gpt-4o-mini")
        
    Returns:
        Stylized text with appropriate tone
        
    Example:
        >>> from anthrokit.stylizer import stylize_text
        >>> text = "Preliminary result: declined."
        >>> styled = stylize_text(text, preset_name="HighA")
        >>> print(styled)
        "I know this isn't ideal — your preliminary result is declined."
    """
    # Load preset if not provided
    if preset is None:
        if preset_name is None:
            preset_name = "LowA"
        preset = load_preset(preset_name)
    
    # Attempt LLM stylization if enabled
    if use_llm:
        system_prompt = _build_stylization_prompt(preset, text, context)
        temperature = 0.7 if preset.get("self_reference") == "I" else 0.3
        
        messages = [
            {"role": "system", "content": "You are a helpful tone stylizer."},
            {"role": "user", "content": system_prompt}
        ]
        
        llm_output = _call_llm(model, messages, temperature=temperature)
        
        if llm_output:
            # Post-process LLM output
            return post_process_response(llm_output, preset)
    
    # Fallback to pattern-based stylization
    styled = _apply_pattern_based_stylization(text, preset)
    return post_process_response(styled, preset)


def stylize_with_preset(
    text: str,
    preset_name: str = "LowA",
    **kwargs
) -> str:
    """Convenience function for stylization with preset name.
    
    Args:
        text: Base text to stylize
        preset_name: Preset name ("HighA" or "LowA")
        **kwargs: Additional arguments for stylize_text
        
    Returns:
        Stylized text
    """
    return stylize_text(text, preset_name=preset_name, **kwargs)


__all__ = [
    "stylize_text",
    "stylize_with_preset",
]
