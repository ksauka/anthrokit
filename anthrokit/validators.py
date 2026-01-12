"""Validation and post-processing utilities for AnthroKit.

This module implements emoji policy enforcement, guardrail validation,
and content post-processing to ensure responsible anthropomorphism.

Example:
    >>> from anthrokit.validators import limit_emojis
    >>> text = "Great! 😊 Here are your results: 1. Score ✅ 2. Status 🎉"
    >>> cleaned = limit_emojis(text, max_emojis=1, ban_in_lists=True)
    >>> print(cleaned)
    "Great! 😊 Here are your results: 1. Score 2. Status"
"""

from __future__ import annotations

import re
from typing import Dict, Any, List


# Emoji regex pattern (covers most common emoji ranges)
EMOJI_PATTERN = re.compile(
    r"[\U0001F300-\U0001FAFF"  # Misc symbols and pictographs
    r"\U00002700-\U000027BF"   # Dingbats
    r"\U00002600-\U000026FF]"  # Misc symbols
)

# Forbidden phrases indicating feelings/embodiment claims
FORBIDDEN_PHRASES = [
    r"\bI feel\b",
    r"\bI\s+felt\b",
    r"\bI'm\s+(worried|excited|happy|sad|frustrated|angry)\b",
    r"\bI\s+hope\b",
    r"\bI\s+wish\b",
    r"\bmy\s+experience\b",
    r"\bfrom\s+my\s+perspective\b",
    r"\bas\s+someone\s+who\b",
]

# Allowed subtle emojis for HighA (professional/formal only)
ALLOWED_EMOJIS = {
    # Check marks and status
    "✅", "✓", "☑️", "✔️", 
    # Neutral faces
    "🙂", "😊",
    # Arrows and navigation
    "→", "←", "↑", "↓", "➡️", "⬅️", "⬆️", "⬇️", "↔️",
    # Bullets and separators
    "•", "·", "◦", "▪️", "▫️",
    # Numbers and indicators
    "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
    # Information symbols
    "ℹ️", "❗", "❓", "⚠️", "📌", "📍",
    # Professional icons
    "📄", "📁", "📊", "📈", "📉", "💼", "🏦", "💳", "📝", "🔍",
    # Basic symbols
    "⭐", "★", "◆", "◇", "■", "□", "●", "○",
}

# Banned emojis (excessive warmth/informality)
BANNED_EMOJIS = {"😂", "😘", "🔥", "💖", "🎉", "✨", "😍", "🤣"}


def limit_emojis(
    text: str,
    max_emojis: int = 1,
    ban_in_lists: bool = True
) -> str:
    """Enforce emoji policy: max count and no emojis in lists.
    
    Args:
        text: Input text to process
        max_emojis: Maximum number of emojis allowed (default: 1)
        ban_in_lists: If True, remove all emojis from bullet/numbered lists
        
    Returns:
        Text with emoji policy enforced
        
    Example:
        >>> text = "Hi! 😊 Here's your score: 1. Result ✅ 2. Status 🎉"
        >>> limit_emojis(text, max_emojis=1, ban_in_lists=True)
        "Hi! 😊 Here's your score: 1. Result 2. Status"
    """
    lines = text.splitlines()
    cleaned_lines = []
    emoji_count = 0
    
    for line in lines:
        # Check if line is part of a list
        is_list_line = (
            line.lstrip().startswith(("-", "*", "•")) or
            re.match(r"^\s*\d+\.", line)
        )
        
        if ban_in_lists and is_list_line:
            # Remove all emojis from list lines
            line = EMOJI_PATTERN.sub("", line)
        else:
            # Keep emojis up to quota
            def replace_emoji(match):
                nonlocal emoji_count
                emoji = match.group(0)
                
                # Always remove banned emojis
                if emoji in BANNED_EMOJIS:
                    return ""
                
                # Keep allowed emojis within quota
                if emoji_count < max_emojis and emoji in ALLOWED_EMOJIS:
                    emoji_count += 1
                    return emoji
                
                # Keep other emojis within quota
                if emoji_count < max_emojis:
                    emoji_count += 1
                    return emoji
                
                return ""
            
            line = EMOJI_PATTERN.sub(replace_emoji, line)
        
        cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)


def validate_guardrails(text: str) -> List[str]:
    """Check text for forbidden phrases (feeling/embodiment claims).
    
    Args:
        text: Input text to validate
        
    Returns:
        List of violated guardrails (empty if valid)
        
    Example:
        >>> text = "I feel this is a good result."
        >>> violations = validate_guardrails(text)
        >>> print(violations)
        ["Contains forbidden phrase: 'I feel'"]
    """
    violations = []
    text_lower = text.lower()
    
    for pattern in FORBIDDEN_PHRASES:
        if re.search(pattern, text_lower):
            phrase = pattern.replace(r"\b", "").replace(r"\s+", " ")
            violations.append(f"Contains forbidden phrase: '{phrase}'")
    
    return violations


def validate_emoji_policy(text: str, preset: Dict[str, Any]) -> bool:
    """Validate that text follows emoji policy for given preset.
    
    Args:
        text: Input text to validate
        preset: Preset configuration (HighA or LowA)
        
    Returns:
        True if valid, False if policy violated
    """
    emoji_policy = preset.get("emoji", "none")
    
    if emoji_policy == "none":
        # No emojis allowed
        return not EMOJI_PATTERN.search(text)
    
    elif emoji_policy == "subtle":
        # Count emojis and check for banned ones
        emojis = EMOJI_PATTERN.findall(text)
        
        # Check for banned emojis
        if any(emoji in BANNED_EMOJIS for emoji in emojis):
            return False
        
        # Check count (max 1 overall, none in lists)
        lines = text.splitlines()
        for line in lines:
            is_list_line = (
                line.lstrip().startswith(("-", "*", "•")) or
                re.match(r"^\s*\d+\.", line)
            )
            if is_list_line and EMOJI_PATTERN.search(line):
                return False
        
        return len(emojis) <= 1
    
    return True


def remove_letter_formatting(text: str) -> str:
    """Remove letter/memo formatting artifacts (for LowA explanations).
    
    Args:
        text: Input text to clean
        
    Returns:
        Text with letter formatting removed
    """
    # Remove subject lines
    text = re.sub(
        r'^Subject:.*?\n\n?', '', text,
        flags=re.IGNORECASE | re.MULTILINE
    )
    
    # Remove salutations
    text = re.sub(
        r'^(Dear|Hello|Hi|Greetings)\s+.*?\n\n?', '', text,
        flags=re.IGNORECASE | re.MULTILINE
    )
    
    # Remove signature blocks
    text = re.sub(
        r'\n\n?(Sincerely|Best regards?|Regards|Yours truly|'
        r'Respectfully|Thank you)[,]?\s*\n.*$', '', text,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Remove placeholder blocks
    text = re.sub(r'\n\[[^\]]+\]\s*', '', text)
    
    # Remove document-style headers
    text = re.sub(
        r'^(Counterfactual Analysis|Feature Impact Analysis):\s*', '', text,
        flags=re.MULTILINE
    )
    
    return text.strip()


def post_process_response(
    text: str,
    preset: Dict[str, Any],
    apply_emoji_limit: bool = True,
    apply_guardrails: bool = True
) -> str:
    """Apply all post-processing steps to response.
    
    Args:
        text: Input text to process
        preset: Preset configuration
        apply_emoji_limit: If True, enforce emoji policy
        apply_guardrails: If True, check for forbidden phrases (raises warning)
        
    Returns:
        Post-processed text
        
    Raises:
        Warning: If guardrails violated (doesn't block output)
    """
    is_high_anthro = preset.get("self_reference", "none") == "I"
    
    # Apply emoji policy
    if apply_emoji_limit and is_high_anthro:
        text = limit_emojis(text, max_emojis=1, ban_in_lists=True)
    elif apply_emoji_limit and not is_high_anthro:
        text = EMOJI_PATTERN.sub("", text)  # Remove all emojis in LowA
    
    # Remove letter formatting for LowA
    if not is_high_anthro:
        text = remove_letter_formatting(text)
    
    # Check guardrails (warn but don't block)
    if apply_guardrails:
        violations = validate_guardrails(text)
        if violations:
            import warnings
            warnings.warn(
                f"Guardrail violations detected: {'; '.join(violations)}\n"
                f"Text: {text[:100]}..."
            )
    
    return text
