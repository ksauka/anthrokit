"""
AnthroKit: Token-based Anthropomorphism Design System for Conversational AI

A research-grade reusable package for implementing measurable, responsible 
anthropomorphic tone in conversational interfaces to promote social presence.

Design Philosophy:
    - Separation of content (scaffolds) from tone (stylizer)
    - Token-based control of anthropomorphic dimensions
    - LLM-based + pattern-based fallback stylization
    - Comprehensive guardrails for ethical AI
    - Adaptive optimization for finding optimal thresholds

Example:
    >>> from anthrokit import load_preset, stylize_text
    >>> from anthrokit.scaffolds import decision_decline
    >>> preset = load_preset("HighA")
    >>> base = decision_decline()
    >>> styled = stylize_text(base, preset)
    >>> print(styled)
    "I know this isn't ideal — your preliminary result is declined."

Adaptive Research:
    >>> from anthrokit.adaptive import ThresholdOptimizer
    >>> optimizer = ThresholdOptimizer(tokens=["warmth", "empathy"])
    >>> preset = optimizer.get_next_condition()
    >>> # Run experiment...
    >>> optimizer.record_outcome(preset, {"trust": 4.2})
    >>> best = optimizer.get_best_preset()

Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "AnthroKit Contributors"

# Configuration
from .config import load_config, load_preset, get_preset

# Content scaffolds (base, neutral content)
from .scaffolds import (
    greet,
    ask_info,
    inform,
    acknowledge,
    decide,
    explain_counterfactual,
    explain_factors,
    explain_impact,
    error_message,
    close_conversation,
    disclosure_statement,
    get_scaffold,
)

# Stylization (tone application)
from .stylizer import stylize_text, stylize_with_preset

# Pattern-based prompt generation (legacy interface)
from .prompts import (
    generate_greeting,
    generate_decision_approve,
    generate_decision_decline,
    generate_closing,
    get_disclosure_text,
)

# Validation and post-processing
from .validators import (
    validate_emoji_policy,
    validate_guardrails,
    limit_emojis,
    post_process_response,
)

# Adaptive optimization (research utilities)
from .adaptive import (
    ThresholdExplorer,
    ThresholdOptimizer,
    OutcomeRecord,
)
from .personality import (
    collect_personality_traits,
    collect_personality_once,
    display_personality_profile,
    map_traits_to_token_adjustments,
    apply_personality_to_preset,
    BIG_5_ITEMS,
)
from .tracking import (
    track_session_start,
    track_session_end,
    track_interaction,
    get_session_summary,
    load_all_sessions,
    get_sessions_by_app,
    get_sessions_by_preset,
    get_anthropomorphism_distribution,
    get_app_usage_stats,
    export_analytics,
)
from .integrations import (
    init_adaptive_session,
    get_current_preset,
    record_session_outcome,
    get_optimization_stats,
    get_best_preset,
    display_admin_panel,
)

__all__ = [
    # Config
    "load_config",
    "load_preset",
    "get_preset",
    # Prompts
    "generate_greeting",
    "generate_decision_approve",
    "generate_decision_decline",
    "generate_closing",
    "get_disclosure_text",
    # Validators
    "validate_emoji_policy",
    "validate_guardrails",
    "limit_emojis",
    # Adaptive
    "ThresholdExplorer",
    "ThresholdOptimizer",
    "OutcomeRecord",
    # Personality
    "collect_personality_traits",
    "collect_personality_once",
    "display_personality_profile",
    "predict_preferred_anthropomorphism",
    "BIG_5_ITEMS",
    # Tracking
    "track_session_start",
    "track_session_end",
    "track_interaction",
    "get_session_summary",
    "load_all_sessions",
    "get_sessions_by_app",
    "get_sessions_by_preset",
    "get_anthropomorphism_distribution",
    "get_app_usage_stats",
    "export_analytics",
    # Integrations (Streamlit helpers)
    "init_adaptive_session",
    "get_current_preset",
    "record_session_outcome",
    "get_optimization_stats",
    "get_best_preset",
    "display_admin_panel",
]
