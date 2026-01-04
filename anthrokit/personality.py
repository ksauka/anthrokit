"""
Big 5 Personality Trait Collection for AnthroKit Research.

Measures individual differences that moderate anthropomorphism effects.
Uses validated short-form Big 5 inventory (10-item TIPI scale).

Research Question:
    Do personality traits moderate the Anthropomorphism → Social Presence relationship?
    
Hypotheses:
    - High extraversion → Prefers high warmth/anthropomorphism
    - High openness → Receptive to AI anthropomorphism
    - High neuroticism → Prefers formal/low anthropomorphism (need for control)
    - High agreeableness → Responds positively to empathy tokens
    - Conscientiousness → Prefers accuracy over warmth
"""

import streamlit as st
from typing import Dict, Optional, Any


# Ten-Item Personality Inventory (TIPI)
# Gosling, S. D., Rentfrow, P. J., & Swann, W. B., Jr. (2003).
BIG_5_ITEMS = {
    "extraversion": [
        ("Extraverted, enthusiastic", 1),
        ("Reserved, quiet", -1)
    ],
    "agreeableness": [
        ("Sympathetic, warm", 1),
        ("Critical, quarrelsome", -1)
    ],
    "conscientiousness": [
        ("Dependable, self-disciplined", 1),
        ("Disorganized, careless", -1)
    ],
    "neuroticism": [
        ("Anxious, easily upset", 1),
        ("Calm, emotionally stable", -1)
    ],
    "openness": [
        ("Open to new experiences, complex", 1),
        ("Conventional, uncreative", -1)
    ]
}


def collect_personality_traits(
    show_instructions: bool = True,
    key_prefix: str = "personality"
) -> Optional[Dict[str, float]]:
    """Collect Big 5 personality traits using TIPI scale.
    
    Args:
        show_instructions: Whether to show instructions
        key_prefix: Prefix for session state keys
        
    Returns:
        Dictionary with Big 5 scores (1-7 scale), or None if incomplete
        
    Example:
        personality = collect_personality_traits()
        if personality:
            print(personality)
            # {'openness': 5.5, 'conscientiousness': 4.0, ...}
    """
    if show_instructions:
        st.markdown("""
        ### 📋 Brief Personality Survey
        
        Please rate yourself on these personality traits (1-7 scale):
        
        - **1** = Disagree strongly
        - **4** = Neither agree nor disagree  
        - **7** = Agree strongly
        
        There are no right or wrong answers. This helps us personalize your experience.
        """)
    
    responses = {}
    
    # Collect responses for all items
    all_items = []
    for trait, items in BIG_5_ITEMS.items():
        for item_text, direction in items:
            all_items.append((trait, item_text, direction))
    
    # Display items
    for i, (trait, item_text, direction) in enumerate(all_items):
        key = f"{key_prefix}_{trait}_{i}"
        
        response = st.slider(
            f"I see myself as: **{item_text}**",
            min_value=1,
            max_value=7,
            value=4,
            key=key
        )
        
        responses[key] = (trait, response, direction)
    
    # Calculate Big 5 scores
    if not responses:
        return None
    
    trait_scores = {trait: [] for trait in BIG_5_ITEMS.keys()}
    
    for key, (trait, response, direction) in responses.items():
        # Reverse-code negative items
        if direction == -1:
            score = 8 - response  # Reverse 1-7 scale
        else:
            score = response
        
        trait_scores[trait].append(score)
    
    # Average across items for each trait
    big5 = {
        trait: sum(scores) / len(scores)
        for trait, scores in trait_scores.items()
    }
    
    return big5


def display_personality_profile(personality: Dict[str, float]):
    """Display visual profile of Big 5 traits.
    
    Args:
        personality: Dictionary of Big 5 scores
    """
    st.markdown("### Your Personality Profile")
    
    for trait, score in personality.items():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.progress(score / 7.0)
        
        with col2:
            st.metric(trait.title(), f"{score:.1f}/7")
    
    st.caption("Scores above 5.5 indicate high levels; below 3.5 indicate low levels")


def get_personality_from_session() -> Optional[Dict[str, float]]:
    """Get cached personality traits from session state.
    
    Returns:
        Cached personality dictionary or None if not collected yet
    """
    return st.session_state.get('big5_personality')


def save_personality_to_session(personality: Dict[str, float]):
    """Save personality traits to session state.
    
    Args:
        personality: Dictionary of Big 5 scores
    """
    st.session_state.big5_personality = personality


def collect_personality_once(
    show_instructions: bool = True,
    show_profile: bool = False
) -> Dict[str, float]:
    """Collect personality traits once per session.
    
    Args:
        show_instructions: Whether to show instructions
        show_profile: Whether to show visual profile after collection
        
    Returns:
        Dictionary of Big 5 scores (from cache or new collection)
    """
    # Check if already collected
    cached = get_personality_from_session()
    if cached is not None:
        return cached
    
    # Collect new
    with st.form("personality_form"):
        personality = collect_personality_traits(
            show_instructions=show_instructions,
            key_prefix="form_personality"
        )
        
        submitted = st.form_submit_button("Submit Personality Survey")
        
        if submitted and personality:
            save_personality_to_session(personality)
            
            if show_profile:
                display_personality_profile(personality)
            
            return personality
    
    # Return empty if not submitted yet
    return {}


def map_traits_to_token_adjustments(
    personality: Dict[str, float]
) -> Dict[str, float]:
    """
    Map Big 5 traits to AnthroKit token adjustments using weighted model.
    
    Trait-to-token mappings follow PERSONAGE (Mairesse & Walker, 2007), which 
    grounded trait-to-linguistic-feature relationships in psycholinguistic literature.
    Where PERSONAGE used binary rules, we implement continuous weighted functions.
    
    Personalization mechanism:
    - Trait-to-token mappings are research-grounded (e.g., extraversion → warmth)
    - Equal weights (0.5/0.5) serve as theoretically neutral initial coefficients
    - Individual differences in TIPI scores create personalized adjustments
    - Validation study (N=20-30) will derive optimized weights via regression
    
    Mapping rationale:
    - Extraversion → warmth (verbosity, expressiveness)
    - Agreeableness → empathy (acknowledgments, supportiveness), warmth
    - Conscientiousness → formality (structured, precise communication)
    - Neuroticism → empathy (reassurance), hedging (uncertainty markers)
    - Openness → formality (creative vs. conventional style), emoji
    
    Args:
        personality: Big 5 scores (1-7 scale)
        
    Returns:
        Token adjustment deltas (-0.3 to +0.3 for numeric tokens)
        
    Example:
        >>> personality = {'extraversion': 6.5, 'agreeableness': 5.5, ...}
        >>> adjustments = map_traits_to_token_adjustments(personality)
        >>> # {'warmth': +0.24, 'empathy': +0.15, 'formality': -0.12, ...}
    """
    # Center around midpoint (4 on 1-7 scale)
    centered = {
        k: (v - 4.0) / 3.0 
        for k, v in personality.items()
    }
    
    # Trait-to-token influence weights
    # Following PERSONAGE (Mairesse & Walker, 2007) conceptual mappings
    # Equal weights (0.5/0.5) serve as theoretically neutral initial coefficients
    # Personalization emerges from individual differences in TIPI scores
    # Validation study will optimize these via regression on preference data
    weights = {
        "warmth": {"extraversion": 0.5, "agreeableness": 0.5},
        "empathy": {"agreeableness": 0.5, "neuroticism": 0.5},
        "formality": {"conscientiousness": 0.5, "openness": -0.5},
        "hedging": {"neuroticism": 0.5, "agreeableness": 0.5},
    }
    
    # Compute adjustments
    adjustments = {}
    for token, influences in weights.items():
        delta = sum(
            centered.get(trait, 0) * weight 
            for trait, weight in influences.items()
        )
        # Clamp to reasonable range (-0.3 to +0.3)
        adjustments[token] = max(min(delta, 0.3), -0.3)
    
    # Discrete style tokens based on extraversion
    extraversion_centered = centered.get("extraversion", 0)
    openness_centered = centered.get("openness", 0)
    
    if extraversion_centered > 0:
        adjustments["self_reference"] = "I"
    else:
        adjustments["self_reference"] = "none"
    
    # Emoji preference: extraversion + openness
    emoji_score = (extraversion_centered * 0.5) + (openness_centered * 0.4)
    if emoji_score > 0:
        adjustments["emoji"] = "subtle"
    else:
        adjustments["emoji"] = "none"
    
    return adjustments


def apply_personality_to_preset(
    base_preset: Dict[str, Any],
    personality: Dict[str, float]
) -> Dict[str, Any]:
    """
    Apply personality-based adjustments to a base preset.
    
    This enables personalized anthropomorphism:
    - Base preset (HighA/LowA) sets the general level
    - Personality adjustments fine-tune within that level
    
    Args:
        base_preset: Base AnthroKit preset dictionary (from load_preset)
        personality: Big 5 personality scores (1-7 scale)
        
    Returns:
        Personalized preset with trait-based adjustments applied
        
    Example:
        >>> from anthrokit.config import load_preset
        >>> base = load_preset("HighA")
        >>> personality = {'extraversion': 6.5, 'agreeableness': 5.8, ...}
        >>> personalized = apply_personality_to_preset(base, personality)
        >>> # base warmth=0.7 + adjustment=+0.24 = 0.94 (clamped to 0.85)
    """
    adjustments = map_traits_to_token_adjustments(personality)
    
    personalized = base_preset.copy()
    
    # Apply numeric adjustments
    for token in ["warmth", "empathy", "formality", "hedging"]:
        if token in adjustments and token in personalized:
            personalized[token] += adjustments[token]
            # Clamp to valid ranges [0.0, 1.0]
            personalized[token] = max(0.0, min(1.0, personalized[token]))
    
    # Apply categorical adjustments
    for token in ["self_reference", "emoji"]:
        if token in adjustments:
            personalized[token] = adjustments[token]
    
    return personalized


# REMOVED: predict_preferred_anthropomorphism()
# This function used a different formula and is not part of the validated framework.
# Use apply_personality_to_preset() with map_traits_to_token_adjustments() instead.
# 
# Framework Paper uses:
#   centered = (score - 4.0) / 3.0
#   warmth_delta = 0.6×extraversion + 0.4×agreeableness
#   adjusted = base_preset + deltas (clamped to [0.0, 1.0])


# ========== INTEGRATION WITH ADAPTIVE FRAMEWORK ==========

def adaptive_with_personality(
    personality: Dict[str, float],
    optimizer: 'ThresholdOptimizer',
    outcomes: Dict[str, float]
):
    """Record outcome with personality data for moderation analysis.
    
    Args:
        personality: Big 5 personality traits
        optimizer: ThresholdOptimizer instance
        outcomes: Outcome metrics including social_presence
        
    Example:
        personality = collect_personality_traits()
        preset = optimizer.get_next_condition()
        # ... run experiment ...
        adaptive_with_personality(personality, optimizer, outcomes)
    """
    preset = optimizer.preset_pool[-1]  # Current preset
    
    optimizer.record_outcome(
        preset=preset,
        outcomes=outcomes,
        personality=personality
    )


__all__ = [
    "collect_personality_traits",
    "display_personality_profile",
    "get_personality_from_session",
    "save_personality_to_session",
    "collect_personality_once",
    "map_traits_to_token_adjustments",
    "apply_personality_to_preset",
    "adaptive_with_personality",
    "BIG_5_ITEMS",
]
