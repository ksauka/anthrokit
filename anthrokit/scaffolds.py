"""Base content scaffolds for AnthroKit prompts.

This module provides minimal, neutral base content for each conversation pattern.
These scaffolds are domain-agnostic and can be used for any conversational AI
application (customer service, healthcare, education, e-commerce, etc.).

Pattern Cards:
    - GREET: Initial welcome
    - ASK_INFO: Request user information
    - INFORM: Deliver information
    - ACKNOWLEDGE: Confirm understanding
    - EXPLAIN: Provide explanations
    - DECIDE: Communicate decisions/outcomes
    - ERROR: Handle errors
    - CLOSE: End conversation

Design Principle:
    Scaffolds contain only factual content. Tone modulation (warmth, formality,
    empathy) is applied separately via stylizer or pattern-based functions.

Example:
    >>> from anthrokit.scaffolds import greet
    >>> base = greet(context="support request")
    >>> print(base)
    "This assistant can help with your support request."
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List


def greet(context: Optional[str] = None) -> str:
    """Base greeting scaffold.
    
    Args:
        context: Optional context description (e.g., "support request", "order inquiry")
    
    Returns:
        Minimal neutral greeting without tone markers
    """
    if context:
        return f"This assistant can help with your {context}."
    return "This assistant is ready to help."


def ask_info(fields: Optional[List[str]] = None, purpose: Optional[str] = None) -> str:
    """Base information request scaffold.
    
    Args:
        fields: List of fields to request
        purpose: Optional purpose description (e.g., "to process your request")
        
    Returns:
        Neutral request for information
    """
    if not fields:
        return "Please provide the requested information."
    
    field_list = ", ".join(fields)
    base = f"Please provide: {field_list}."
    
    if purpose:
        base += f" This information is needed {purpose}."
    
    return base


def inform(content: str, category: Optional[str] = None) -> str:
    """Base information delivery scaffold.
    
    Args:
        content: Information to communicate
        category: Optional category label (e.g., "status", "result", "update")
        
    Returns:
        Factual information statement
    """
    if category:
        return f"{category.capitalize()}: {content}"
    return content


def acknowledge(content: Optional[str] = None) -> str:
    """Base acknowledgment scaffold.
    
    Args:
        content: Optional specific thing being acknowledged
        
    Returns:
        Neutral acknowledgment
    """
    if content:
        return f"Confirmed: {content}"
    return "Confirmed."


def decide(outcome: str, explanation_available: bool = False) -> str:
    """Base decision/outcome scaffold.
    
    Args:
        outcome: The decision or outcome to communicate
        explanation_available: Whether explanation can be provided
        
    Returns:
        Factual decision statement
    """
    base = f"Result: {outcome}."
    if explanation_available:
        base += " An explanation is available."
    return base


def explain_counterfactual(
    factor: str,
    current_value: Any,
    target_value: Any,
    outcome: str
) -> str:
    """Base counterfactual explanation scaffold.
    
    Args:
        factor: Factor name (e.g., "delivery_method", "payment_type")
        current_value: Current value
        target_value: Required value for different outcome
        outcome: Target outcome
        
    Returns:
        Factual counterfactual statement
    """
    return (
        f"If {factor} changed from {current_value} to {target_value}, "
        f"the outcome would likely change to {outcome}."
    )


def explain_factors(
    supporting_factors: Optional[List[str]] = None,
    opposing_factors: Optional[List[str]] = None
) -> str:
    """Base factor attribution explanation scaffold.
    
    Args:
        supporting_factors: Factors supporting the outcome
        opposing_factors: Factors opposing the outcome
        
    Returns:
        Factual attribution statement
    """
    parts = []
    
    if supporting_factors:
        factors_str = ", ".join(supporting_factors)
        parts.append(f"Supporting factors: {factors_str}")
    
    if opposing_factors:
        factors_str = ", ".join(opposing_factors)
        parts.append(f"Opposing factors: {factors_str}")
    
    if not parts:
        return "No specific factors identified."
    
    return "; ".join(parts) + "."


def explain_impact(
    factor_impacts: Dict[str, float],
    top_n: int = 3,
    outcome_label: str = "outcome likelihood"
) -> str:
    """Base impact explanation scaffold (e.g., for SHAP values).
    
    Args:
        factor_impacts: Dictionary of factor names to impact values
        top_n: Number of top factors to include
        outcome_label: Label for what the impact affects (default: "outcome likelihood")
        
    Returns:
        Factual impact-based explanation
    """
    if not factor_impacts:
        return "No impact factors available."
    
    sorted_factors = sorted(
        factor_impacts.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )[:top_n]
    
    explanations = []
    for factor, impact in sorted_factors:
        direction = "increased" if impact > 0 else "decreased"
        explanations.append(f"{factor} {direction} {outcome_label}")
    
    return "Key factors: " + "; ".join(explanations) + "."


def error_message(error_type: Optional[str] = None) -> str:
    """Base error handling scaffold.
    
    Args:
        error_type: Optional error type description
        
    Returns:
        Neutral error message
    """
    if error_type:
        return f"Error: {error_type}. Please try again."
    return "An error occurred. Please try again."


def close_conversation(summary: Optional[str] = None) -> str:
    """Base closing scaffold.
    
    Args:
        summary: Optional summary of interaction
        
    Returns:
        Neutral conversation closure
    """
    if summary:
        return f"{summary} Thank you."
    return "Interaction complete. Thank you."


def disclosure_statement(specificity: str = "basic") -> str:
    """Base AI disclosure scaffold.
    
    Args:
        specificity: Level of detail ("basic", "detailed")
        
    Returns:
        Factual AI identity disclosure
    """
    if specificity == "detailed":
        return "This is an AI assistant. It does not have feelings or personal experiences."
    return "This is an AI assistant."


def get_scaffold(
    pattern: str,
    **kwargs
) -> str:
    """Get base scaffold for a given pattern card.
    
    Args:
        pattern: Pattern card name (greet, ask_info, inform, acknowledge, etc.)
        **kwargs: Pattern-specific arguments
        
    Returns:
        Base content scaffold
        
    Raises:
        ValueError: If pattern is not recognized
        
    Example:
        >>> get_scaffold("greet", context="order inquiry")
        "This assistant can help with your order inquiry."
        >>> get_scaffold("explain_counterfactual", 
        ...              factor="shipping_method",
        ...              current_value="standard", 
        ...              target_value="express",
        ...              outcome="next-day delivery")
        "If shipping_method changed from standard to express, the outcome would..."
    """
    scaffolds = {
        "greet": greet,
        "ask_info": ask_info,
        "inform": inform,
        "acknowledge": acknowledge,
        "decide": decide,
        "explain_counterfactual": explain_counterfactual,
        "explain_factors": explain_factors,
        "explain_impact": explain_impact,
        "error": error_message,
        "close": close_conversation,
        "disclosure": disclosure_statement,
    }
    
    if pattern not in scaffolds:
        raise ValueError(
            f"Unknown pattern: {pattern}. "
            f"Available: {', '.join(sorted(scaffolds.keys()))}"
        )
    
    return scaffolds[pattern](**kwargs)


__all__ = [
    "greet",
    "ask_info",
    "inform",
    "acknowledge",
    "decide",
    "explain_counterfactual",
    "explain_factors",
    "explain_impact",
    "error_message",
    "close_conversation",
    "disclosure_statement",
    "get_scaffold",
]
