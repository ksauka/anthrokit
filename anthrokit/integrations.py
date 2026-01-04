"""
Integration utilities for AnthroKit adaptive framework with XAIagent apps.

This module provides helper functions to integrate adaptive anthropomorphism
optimization into existing Streamlit apps without major refactoring.

Example usage in existing apps:
    from adaptive_integration import (
        init_adaptive_session,
        get_current_preset,
        record_session_outcome
    )
    
    # In your app initialization
    preset = init_adaptive_session()
    
    # Use preset to configure assistant
    config.warmth = preset['warmth']
    config.empathy = preset['empathy']
    
    # After user completes session
    record_session_outcome({
        "trust": 4.2,
        "satisfaction": 3.8
    })
"""

import os
import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Try to import AnthroKit adaptive
try:
    from .adaptive import ThresholdOptimizer
    from .config import load_preset
    ADAPTIVE_AVAILABLE = True
except ImportError:
    ADAPTIVE_AVAILABLE = False

# Import session tracking
try:
    from .tracking import (
        track_session_start,
        track_session_end,
        track_interaction,
        get_or_create_user_id,
        get_app_name
    )
    TRACKING_AVAILABLE = True
except ImportError:
    TRACKING_AVAILABLE = False


# Global optimizer instance (cached)
_OPTIMIZER = None
_OPTIMIZER_PATH = Path(__file__).parent.parent / "data" / "optimizer_state.json"


def is_adaptive_mode() -> bool:
    """Check if adaptive mode is enabled via environment variable."""
    return os.getenv("ADAPTIVE_MODE", "disabled").lower() == "enabled"


def get_or_create_optimizer(
    tokens: Optional[list] = None,
    n_levels: int = 5,
    exploration_rate: float = 0.2
) -> Optional['ThresholdOptimizer']:
    """Get or create the global optimizer instance.
    
    Args:
        tokens: List of tokens to optimize (default: warmth, empathy)
        n_levels: Number of levels per token
        exploration_rate: Exploration probability
        
    Returns:
        ThresholdOptimizer instance or None if adaptive mode disabled
    """
    global _OPTIMIZER
    
    if not ADAPTIVE_AVAILABLE or not is_adaptive_mode():
        return None
    
    if _OPTIMIZER is not None:
        return _OPTIMIZER
    
    # Try to load existing optimizer
    if _OPTIMIZER_PATH.exists():
        try:
            _OPTIMIZER = ThresholdOptimizer.load(_OPTIMIZER_PATH)
            return _OPTIMIZER
        except Exception as e:
            st.sidebar.warning(f"Could not load optimizer: {e}")
    
    # Create new optimizer
    if tokens is None:
        tokens = os.getenv("ADAPTIVE_TOKENS", "warmth,empathy").split(",")
    
    _OPTIMIZER = ThresholdOptimizer(
        tokens=tokens,
        n_levels=n_levels,
        base_preset="LowA",
        exploration_rate=exploration_rate
    )
    
    return _OPTIMIZER


def save_optimizer():
    """Save optimizer state to disk."""
    if _OPTIMIZER is None:
        return
    
    _OPTIMIZER_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OPTIMIZER.save(_OPTIMIZER_PATH)


def init_adaptive_session(
    user_id: Optional[str] = None,
    fallback_preset: str = "LowA",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Initialize adaptive session and get preset for current user.
    
    This function should be called once at the start of each user session.
    It will either:
    1. Return an adaptively selected preset (if adaptive mode enabled)
    2. Return a standard preset based on AppConfig (if adaptive mode disabled)
    
    Automatically tracks session start with app name, preset, and user ID.
    
    Args:
        user_id: Optional user identifier (auto-generated if None)
        fallback_preset: Preset to use if adaptive mode disabled
        metadata: Optional metadata (domain, experiment_id, etc.)
        
    Returns:
        Preset dictionary with token values
        
    Example:
        preset = init_adaptive_session(
            metadata={"domain": "loan_approval", "experiment_id": "exp_001"}
        )
        config.warmth = preset['warmth']
        config.empathy = preset['empathy']
    """
    # Initialize session state if needed
    if 'adaptive_preset' not in st.session_state:
        # Get or create user ID
        if user_id is None and TRACKING_AVAILABLE:
            user_id = get_or_create_user_id()
        
        optimizer = get_or_create_optimizer()
        preset_name = None
        
        if optimizer is None:
            # Fall back to standard preset
            preset = load_preset(fallback_preset)
            preset_name = fallback_preset
        else:
            # Get adaptive preset
            preset = optimizer.get_next_condition()
            preset_name = "adaptive"
            
            # Show info in sidebar
            st.sidebar.markdown("### 🎯 Adaptive Condition")
            st.sidebar.json({
                k: round(v, 2) if isinstance(v, float) else v
                for k, v in preset.items()
                if k in optimizer.tokens
            })
        
        st.session_state.adaptive_preset = preset
        st.session_state.adaptive_user_id = user_id
        st.session_state.adaptive_preset_name = preset_name
        
        # Track session start
        if TRACKING_AVAILABLE:
            track_session_start(
                preset_name=preset_name,
                preset_config=preset,
                user_id=user_id,
                metadata=metadata
            )
    
    return st.session_state.adaptive_preset


def get_current_preset() -> Dict[str, Any]:
    """Get the preset for the current session.
    
    Returns:
        Preset dictionary, or None if not initialized
    """
    return st.session_state.get('adaptive_preset')


def record_session_outcome(
    outcomes: Dict[str, float],
    user_id: Optional[str] = None,
    domain: Optional[str] = None,
    feedback: Optional[Dict[str, Any]] = None,
    personality: Optional[Dict[str, float]] = None
):
    """Record outcome for current session.
    
    This should be called after the user completes the interaction and
    provides feedback. Automatically tracks session end with app name,
    preset, outcomes, and anthropomorphism level.
    
    Args:
        outcomes: Dictionary of outcome metrics (MUST include 'social_presence')
        user_id: Optional user identifier
        domain: Optional domain label
        feedback: Optional additional feedback (comments, etc.)
        personality: Optional Big 5 personality traits
                    {'openness': 3.5, 'conscientiousness': 4.2, ...}
        
    Example:
        from anthrokit import collect_personality_traits
        
        personality = collect_personality_traits()
        record_session_outcome(
            outcomes={
                "social_presence": 4.1,  # PRIMARY METRIC
                "trust": trust_score,
                "satisfaction": satisfaction_score,
            },
            personality=personality,
            feedback={"comments": "Very helpful"}
        )
    """
    preset = st.session_state.get('adaptive_preset')
    if preset is None:
        return
    
    # Use session user_id if not provided
    if user_id is None:
        user_id = st.session_state.get('adaptive_user_id')
    
    # Track session end
    if TRACKING_AVAILABLE:
        track_session_end(outcomes=outcomes, feedback=feedback, personality=personality)
    
    # Record to optimizer if available
    optimizer = get_or_create_optimizer()
    if optimizer is not None:
        optimizer.record_outcome(
            preset=preset,
            outcomes=outcomes,
            user_id=user_id,
            domain=domain,
            personality=personality
        )
        
        # Save to disk
        save_optimizer()
        
        # Update sidebar with stats
        stats = optimizer.get_statistics()
        st.sidebar.markdown("### 📊 Optimization Progress")
        st.sidebar.metric("Total Trials", stats['n_trials'])
        st.sidebar.metric("Best Score", f"{stats['best_score']:.2f}")


def get_optimization_stats() -> Optional[Dict[str, Any]]:
    """Get current optimization statistics.
    
    Returns:
        Statistics dictionary or None if adaptive mode disabled
    """
    optimizer = get_or_create_optimizer()
    if optimizer is None:
        return None
    
    return optimizer.get_statistics()


def get_best_preset() -> Optional[Dict[str, Any]]:
    """Get the best performing preset found so far.
    
    Returns:
        Best preset dictionary or None if no data yet
    """
    optimizer = get_or_create_optimizer()
    if optimizer is None:
        return None
    
    return optimizer.get_best_preset()


def export_optimization_results(filepath: Optional[Path] = None) -> Dict[str, Any]:
    """Export optimization results for analysis.
    
    Args:
        filepath: Optional path to save JSON file
        
    Returns:
        Dictionary with all optimization data
    """
    optimizer = get_or_create_optimizer()
    if optimizer is None:
        return {"error": "Adaptive mode not enabled"}
    
    stats = optimizer.get_statistics()
    best = optimizer.get_best_preset()
    
    results = {
        "statistics": stats,
        "best_preset": best,
        "all_outcomes": [o.to_dict() for o in optimizer.outcomes],
        "preset_pool": optimizer.preset_pool,
        "configuration": {
            "tokens": optimizer.tokens,
            "n_levels": optimizer.n_levels,
            "exploration_rate": optimizer.exploration_rate
        }
    }
    
    if filepath:
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
    
    return results


def display_admin_panel():
    """Display admin panel with optimization statistics (for debugging).
    
    Add this to your app with:
        if os.getenv("SHOW_ADMIN", "false") == "true":
            display_admin_panel()
    """
    if not is_adaptive_mode():
        st.info("Adaptive mode is disabled. Set ADAPTIVE_MODE=enabled to use.")
        return
    
    optimizer = get_or_create_optimizer()
    if optimizer is None:
        return
    
    st.subheader("🔧 Adaptive Optimization Admin Panel")
    
    # Statistics
    stats = get_optimization_stats()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trials", stats['n_trials'])
    with col2:
        st.metric("Unique Configs", stats['n_unique_presets'])
    with col3:
        st.metric("Best Score", f"{stats['best_score']:.2f}")
    with col4:
        st.metric("Coverage", f"{stats['coverage']:.1%}")
    
    # Best configuration
    st.subheader("Best Configuration Found")
    best = get_best_preset()
    st.json(best)
    
    # Export button
    if st.button("Export Results"):
        results = export_optimization_results()
        st.download_button(
            "Download JSON",
            data=json.dumps(results, indent=2),
            file_name="optimization_results.json",
            mime="application/json"
        )
    
    # Outcome distribution
    if optimizer.outcomes:
        st.subheader("Outcome Distribution")
        import pandas as pd
        
        # Convert outcomes to DataFrame
        data = []
        for record in optimizer.outcomes:
            row = {
                **record.preset_config,
                **record.outcomes,
                "user_id": record.user_id
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        st.dataframe(df)


# ========== INTEGRATION EXAMPLES ==========

def integrate_with_existing_app_example():
    """
    Example of how to integrate adaptive optimization into existing app.
    
    Replace your existing configuration logic with:
    """
    # OLD CODE:
    # from ab_config import AppConfig
    # config = AppConfig()
    
    # NEW CODE:
    from adaptive_integration import init_adaptive_session, record_session_outcome
    from ab_config import AppConfig
    
    # Initialize config
    config = AppConfig()
    
    # Get adaptive preset (or fall back to standard A/B)
    preset = init_adaptive_session()
    
    # Override config with adaptive values
    config.warmth = preset.get('warmth', config.warmth)
    config.empathy = preset.get('empathy', config.empathy)
    config.formality = preset.get('formality', config.formality)
    
    # ... rest of your app ...
    
    # After user completes session and provides feedback:
    record_session_outcome({
        "trust": trust_score,
        "satisfaction": satisfaction_score
    })


__all__ = [
    "is_adaptive_mode",
    "init_adaptive_session",
    "get_current_preset",
    "record_session_outcome",
    "get_optimization_stats",
    "get_best_preset",
    "export_optimization_results",
    "display_admin_panel",
]
