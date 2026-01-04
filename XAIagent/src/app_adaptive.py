"""
Adaptive XAI Agent with Dynamic Anthropomorphism Optimization

This app integrates AnthroKit's adaptive framework to dynamically optimize
anthropomorphism thresholds during the user study. Instead of fixed HighA/LowA,
it uses multi-armed bandit to find optimal levels.

Run with:
    streamlit run app_adaptive.py
    
Environment variables:
    ADAPTIVE_MODE=enabled  # Enable adaptive optimization
    ADAPTIVE_TOKENS=warmth,empathy  # Tokens to optimize
    ADAPTIVE_LEVELS=5  # Number of levels per token
"""

import streamlit as st
import env_loader  # Load environment variables
import sys
import os
from pathlib import Path

# Add parent directory to path for anthrokit import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import AnthroKit adaptive framework
try:
    from anthrokit.adaptive import ThresholdOptimizer
    from anthrokit import load_preset
    ADAPTIVE_AVAILABLE = True
except ImportError:
    ADAPTIVE_AVAILABLE = False
    st.warning("⚠️ AnthroKit adaptive module not available. Install with: pip install -e .")

from ab_config import AppConfig
from loan_assistant import LoanAssistant, ConversationState
from data_logger import DataLogger

# Configure page
st.set_page_config(
    page_title="AI Loan Assistant - Adaptive Study",
    layout="wide"
)


# ========== ADAPTIVE OPTIMIZER SETUP ==========

@st.cache_resource
def get_optimizer():
    """Initialize or load the threshold optimizer."""
    if not ADAPTIVE_AVAILABLE:
        return None
    
    adaptive_mode = os.getenv("ADAPTIVE_MODE", "disabled")
    if adaptive_mode != "enabled":
        return None
    
    optimizer_path = Path(__file__).parent.parent / "data" / "optimizer_state.json"
    
    # Load existing optimizer or create new one
    if optimizer_path.exists():
        try:
            optimizer = ThresholdOptimizer.load(optimizer_path)
            st.sidebar.success(f"✅ Loaded optimizer ({optimizer.get_statistics()['n_trials']} trials)")
            return optimizer
        except Exception as e:
            st.sidebar.warning(f"⚠️ Could not load optimizer: {e}")
    
    # Create new optimizer
    tokens = os.getenv("ADAPTIVE_TOKENS", "warmth,empathy").split(",")
    n_levels = int(os.getenv("ADAPTIVE_LEVELS", "5"))
    
    optimizer = ThresholdOptimizer(
        tokens=tokens,
        n_levels=n_levels,
        base_preset="LowA",
        exploration_rate=0.2  # 20% exploration
    )
    
    st.sidebar.info(f"🆕 Created new optimizer (tokens: {', '.join(tokens)})")
    return optimizer


def save_optimizer(optimizer):
    """Save optimizer state to disk."""
    if optimizer is None:
        return
    
    optimizer_path = Path(__file__).parent.parent / "data" / "optimizer_state.json"
    optimizer_path.parent.mkdir(parents=True, exist_ok=True)
    optimizer.save(optimizer_path)


def get_adaptive_preset(optimizer, user_id=None):
    """Get next preset from optimizer or fall back to standard config."""
    if optimizer is None:
        # Fall back to standard A/B testing
        config = AppConfig()
        return load_preset(config.anthro_preset)
    
    # Get adaptive preset
    preset = optimizer.get_next_condition()
    
    # Display condition info
    st.sidebar.markdown("### 🎯 Adaptive Condition")
    st.sidebar.json({
        "warmth": round(preset.get("warmth", 0), 2),
        "empathy": round(preset.get("empathy", 0), 2),
        "formality": round(preset.get("formality", 0), 2),
    })
    
    return preset


def record_adaptive_outcome(optimizer, preset, outcomes, user_id=None):
    """Record outcome for the optimizer."""
    if optimizer is None:
        return
    
    optimizer.record_outcome(
        preset=preset,
        outcomes=outcomes,
        user_id=user_id,
        domain="loan_assessment"
    )
    
    # Save after each outcome
    save_optimizer(optimizer)
    
    # Display statistics
    stats = optimizer.get_statistics()
    st.sidebar.markdown("### 📊 Optimization Stats")
    st.sidebar.metric("Total Trials", stats['n_trials'])
    st.sidebar.metric("Best Score", f"{stats['best_score']:.2f}")
    st.sidebar.metric("Coverage", f"{stats['coverage']:.1%}")


# ========== MAIN APP ==========

def main():
    """Main application with adaptive optimization."""
    
    # Initialize optimizer
    optimizer = get_optimizer()
    
    # Session state initialization
    if 'user_id' not in st.session_state:
        import uuid
        st.session_state.user_id = str(uuid.uuid4())
    
    if 'preset' not in st.session_state:
        # Get adaptive preset for this user
        st.session_state.preset = get_adaptive_preset(optimizer, st.session_state.user_id)
    
    if 'assistant' not in st.session_state:
        # Create assistant with adaptive preset
        config = AppConfig()
        
        # Override config with adaptive preset values
        for key, value in st.session_state.preset.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        st.session_state.assistant = LoanAssistant(config)
    
    if 'data_logger' not in st.session_state:
        st.session_state.data_logger = DataLogger()
    
    # Header
    st.title("🏦 AI Loan Assistant")
    
    if optimizer:
        st.info("🔬 **Adaptive Study Mode**: This session uses dynamically optimized anthropomorphism levels.")
    
    # Sidebar info
    st.sidebar.title("Study Information")
    st.sidebar.markdown(f"**Session ID**: `{st.session_state.user_id[:8]}...`")
    
    # Main conversation interface
    assistant = st.session_state.assistant
    
    # Display conversation history
    for message in assistant.conversation_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # User input
    if assistant.state != ConversationState.COMPLETE:
        if prompt := st.chat_input("Type your message..."):
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get assistant response
            response = assistant.process_input(prompt)
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.markdown(response)
    
    # If conversation complete, show feedback form
    if assistant.state == ConversationState.COMPLETE and 'feedback_submitted' not in st.session_state:
        st.markdown("---")
        st.subheader("📋 Study Feedback")
        
        with st.form("feedback_form"):
            trust = st.slider(
                "How much do you trust this AI assistant?",
                min_value=1, max_value=5, value=3,
                help="1 = Not at all, 5 = Completely"
            )
            
            satisfaction = st.slider(
                "How satisfied are you with the interaction?",
                min_value=1, max_value=5, value=3,
                help="1 = Very dissatisfied, 5 = Very satisfied"
            )
            
            acceptance = st.slider(
                "Would you use this assistant in real life?",
                min_value=1, max_value=5, value=3,
                help="1 = Definitely not, 5 = Definitely yes"
            )
            
            perceived_anthro = st.slider(
                "How human-like did the assistant feel?",
                min_value=1, max_value=5, value=3,
                help="1 = Very robotic, 5 = Very human-like"
            )
            
            comments = st.text_area(
                "Additional comments (optional)",
                placeholder="Any thoughts about your experience?"
            )
            
            submitted = st.form_submit_button("Submit Feedback")
            
            if submitted:
                # Record outcome for optimizer
                outcomes = {
                    "trust": trust,
                    "satisfaction": satisfaction,
                    "acceptance": acceptance,
                    "perceived_anthropomorphism": perceived_anthro
                }
                
                record_adaptive_outcome(
                    optimizer,
                    st.session_state.preset,
                    outcomes,
                    st.session_state.user_id
                )
                
                # Log to data logger
                st.session_state.data_logger.log_feedback({
                    "user_id": st.session_state.user_id,
                    "preset": st.session_state.preset,
                    "outcomes": outcomes,
                    "comments": comments
                })
                
                st.session_state.feedback_submitted = True
                st.success("✅ Thank you for your feedback!")
                st.balloons()
                
                # Show what happens next
                if optimizer:
                    st.info("🔄 Your feedback helps optimize future interactions!")
    
    # Admin panel (hidden in production)
    if os.getenv("SHOW_ADMIN", "false") == "true":
        with st.expander("🔧 Admin Panel"):
            if optimizer:
                st.subheader("Optimization Statistics")
                stats = optimizer.get_statistics()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Trials", stats['n_trials'])
                with col2:
                    st.metric("Unique Configs", stats['n_unique_presets'])
                with col3:
                    st.metric("Coverage", f"{stats['coverage']:.1%}")
                
                st.subheader("Best Configuration Found")
                best = optimizer.get_best_preset()
                st.json(best)
                
                if st.button("Export Optimizer State"):
                    import json
                    export_data = {
                        "statistics": stats,
                        "best_preset": best,
                        "all_outcomes": [o.to_dict() for o in optimizer.outcomes]
                    }
                    st.download_button(
                        "Download JSON",
                        data=json.dumps(export_data, indent=2),
                        file_name="optimizer_results.json",
                        mime="application/json"
                    )


if __name__ == "__main__":
    main()
