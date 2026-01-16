"""Text stylizer for applying anthropomorphic tone to base content.

This module applies anthropomorphic tone modulation to base scaffolds using
either LLM-based stylization (when available) or pattern-based fallback rules.

The stylizer respects token values (warmth, formality, empathy, etc.) and
enforces guardrails for responsible anthropomorphism.


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
    print(f"\n🎨 DEBUG: _build_stylization_prompt CALLED!")
    print(f"   Preset keys: {list(preset.keys())}")
    
    warmth = preset.get("warmth", 0.5)
    formality = preset.get("formality", 0.5)
    empathy = preset.get("empathy", 0.5)
    self_ref = preset.get("self_reference", "none")
    hedging = preset.get("hedging", 0.3)
    emoji = preset.get("emoji", "none")
    persona = preset.get("persona_name", "")
    
    print(f"   Extracted values: warmth={warmth:.3f}, empathy={empathy:.3f}, formality={formality:.3f}")
    
    # Build tone instructions
    tone_instructions = []
    
    # PERSONALITY-SENSITIVE THRESHOLDS with EXPLICIT examples
    # LowA base=0.25: With high extraversion (+0.30) → 0.55 → "warm"
    # LowA base=0.25: With low extraversion (-0.30) → 0.00 → "very neutral"
    # HighA base=0.70: With high extraversion (+0.30) → 1.00 → "very warm"
    
    # DEBUG: Test each warmth threshold
    print(f"   🔍 Warmth threshold tests:")
    print(f"      warmth > 0.80? {warmth > 0.80} (warmth={warmth})")
    print(f"      warmth > 0.50? {warmth > 0.50} (warmth={warmth})")
    print(f"      warmth > 0.35? {warmth > 0.35} (warmth={warmth})")
    print(f"      warmth < 0.15? {warmth < 0.15} (warmth={warmth})")
    
    if warmth > 0.80:
        instr = "Use a VERY warm, enthusiastic, friendly tone with engaging language"
        print(f"      ✅ Adding: {instr}")
        tone_instructions.append(instr)
    elif warmth > 0.50:
        instr = "Use a warm, friendly, encouraging tone - be welcoming and positive"
        print(f"      ✅ Adding: {instr}")
        tone_instructions.append(instr)
    elif warmth > 0.50:
        instr = "Use a warm, friendly, encouraging tone - be welcoming and positive"
        print(f"      ✅ Adding: {instr}")
        tone_instructions.append(instr)
    elif warmth > 0.35:
        instr = "Use a moderately warm, approachable tone"
        print(f"      ✅ Adding: {instr}")
        tone_instructions.append(instr)
    elif warmth < 0.15:
        instr = "Use a strictly neutral, detached, impersonal tone - minimize warmth completely"
        print(f"      ✅ Adding: {instr}")
        tone_instructions.append(instr)
    else:
        instr = "Use a neutral, professional tone without extra warmth"
        print(f"      ✅ Adding: {instr}")
        tone_instructions.append(instr)
    
    if formality >= 0.95:
        tone_instructions.append("Use MAXIMALLY formal, robotic, machine-like language - be extremely mechanical, impersonal, and bureaucratic. Write like an automated system, not a human. Use passive voice, technical terminology, and avoid ALL conversational elements including greetings (no 'Greetings', 'Welcome', 'Hello'). Start directly with system information.")
    elif formality > 0.80:
        tone_instructions.append("Maintain VERY formal, academic language - be extremely precise and structured")
    elif formality > 0.60:
        tone_instructions.append("Maintain formal, professional language")
    elif formality < 0.40:
        tone_instructions.append("Use conversational, accessible language - write like you're talking to someone")
    elif formality < 0.20:
        tone_instructions.append("Use casual, everyday language - be relaxed and informal")
    
    if empathy > 0.70:
        tone_instructions.append("Show strong empathy and understanding - acknowledge feelings and validate concerns warmly")
    elif empathy > 0.45:
        tone_instructions.append("Show empathy and understanding - be supportive")
    elif empathy < 0.25:
        tone_instructions.append("Remain strictly objective and task-focused - no emotional language or validation")
    elif empathy < 0.10:
        tone_instructions.append("Be completely impersonal - pure information delivery only")
    
    if self_ref == "I":
        tone_instructions.append(f"Use first-person (I/my) when appropriate")
        if persona:
            tone_instructions.append(f"Your name is {persona}")
    else:
        tone_instructions.append("Use neutral third-person or passive voice")
    
    if hedging > 0.65:
        tone_instructions.append("Use frequent hedging language (might, could, possibly, perhaps)")
    elif hedging > 0.45:
        tone_instructions.append("Use hedging language (might, could, possibly)")
    elif hedging < 0.30:
        tone_instructions.append("Use confident, direct language without hedging")
    
    # Emoji policy
    emoji_instruction = {
        "none": "Do not use any emojis",
        "subtle": "You may use at most one subtle emoji (🙂, ✅) outside of lists",
        "moderate": "You may use emojis sparingly where appropriate"
    }.get(emoji, "Do not use any emojis")
    
    tone_instructions.append(emoji_instruction)
    
    # DEBUG: Print which tone instructions are being used
    print(f"\n🎨 DEBUG: Tone Instructions Generated:")
    print(f"   Warmth={warmth:.3f}, Empathy={empathy:.3f}, Formality={formality:.3f}, Hedging={hedging:.3f}")
    for i, instr in enumerate(tone_instructions, 1):
        print(f"   {i}. {instr}")
    
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

CRITICAL: You MUST noticeably apply the tone instructions above. The rephrased text should sound meaningfully different from the original based on the warmth, empathy, and formality levels specified. Don't just make minimal changes - fully embody the requested tone.

TASK: Rephrase the following text maintaining its factual content while STRONGLY applying the tone guidelines above.

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
