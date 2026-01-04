"""
A/B Testing Configuration for AnthroKit
This module configures experimental conditions for the live study.

Experiment factors (3 × 2):
- Explanation type: none | counterfactual | feature_importance
- Anthropomorphism: low | high

Backwards compatibility:
- ANTHROKIT_VERSION = v0 | v1 still works
  v0 -> explanation=none, anthropomorphism=low
  v1 -> explanation=feature_importance, anthropomorphism=high

Environment variables (preferred) or CLI flags:
- ANTHROKIT_EXPLANATION = none | counterfactual | feature_importance
- ANTHROKIT_ANTHRO      = low | high
- ANTHROKIT_VERSION     = v0 | v1  (legacy)
CLI flags:
  --explanation=none|counterfactual|feature_importance
  --anthro=low|high
  --ANTHROKIT_VERSION=v0|v1 or --v0 / --v1 or --ab=v0|v1
"""

import os
import sys
import uuid
import time
import streamlit as st

_VALID_EXPLANATIONS = {"none", "counterfactual", "feature_importance"}
_VALID_ANTHRO       = {"low", "high"}


class AppConfig:
    """Configuration class for A/B testing versions and factor levels with AnthroKit preset support."""

    def __init__(self):
        # read factor levels (env and CLI), then derive UI toggles
        self.explanation = self._get_explanation_level()           # none | counterfactual | feature_importance
        self.anthro      = self._get_anthropomorphism_level()      # low | high
        self.version     = self._legacy_version_label()            # v0 | v1 (for sidebar display only)
        self.session_id  = self._generate_session_id()             # unique session tracking

        # Adaptive optimization settings (read from env)
        self.adaptive_mode = os.getenv("ADAPTIVE_MODE", "disabled") == "enabled"
        self.adaptive_range_min = float(os.getenv("ADAPTIVE_RANGE_MIN", "0.25"))
        self.adaptive_range_max = float(os.getenv("ADAPTIVE_RANGE_MAX", "0.75"))
        self.adaptive_tokens = os.getenv("ADAPTIVE_TOKENS", "warmth,empathy").split(",")

        # derived feature flags for UI rendering, explanations, and logging
        self.show_anthropomorphic   = (self.anthro == "high")
        self.show_profile_pic       = self.show_anthropomorphic
        self.show_shap_visualizations = (self.explanation == "feature_importance" and self.anthro == "high")
        self.show_counterfactual    = (self.explanation == "counterfactual")
        self.show_any_explanation   = (self.explanation != "none")

        # AnthroKit preset loader (using anthrokit package)
        self.anthro_preset = "HighA" if self.show_anthropomorphic else "LowA"
        self._load_anthrokit_preset()

        # assistant identity and copy are derived from anthropomorphism
        self.assistant_name = getattr(self, 'persona_name', "Luna" if self.show_anthropomorphic else "AI Assistant")
        if self.show_anthropomorphic:
            self.assistant_intro = "Hi, I'm Luna—an AI assistant for credit pre-assessment. I'll guide you through a short check and explain the result if you'd like."
        else:
            self.assistant_intro = "Welcome. This is the AI Loan Assistant for credit pre-assessment. Please provide the requested information to proceed with your evaluation."

        # data collection options
        self.collect_feedback = True
        self.show_debug_info  = False  # keep False in production
        
        # Legacy compatibility
        self.use_full_features = self.show_any_explanation

    def _load_anthrokit_preset(self):
        """Load AnthroKit configuration using anthrokit package.
        If ADAPTIVE_MODE is enabled, uses ThresholdOptimizer for ranged exploration.
        Supports personality-based personalization."""
        try:
            from anthrokit import load_preset
            from anthrokit.config import AnthroKitConfig
            from anthrokit.personality import (
                get_personality_from_session,
                apply_personality_to_preset
            )
            
            # Load base preset
            preset = load_preset(self.anthro_preset)
            
            # Check for personality-based personalization
            personality = get_personality_from_session()
            if personality:
                preset = apply_personality_to_preset(preset, personality)
                print(f"🧠 Applied personality-based adjustments to {self.anthro_preset} preset")
            
            # Load base preset values
            self.emoji_style = preset.get("emoji", "none")
            self.temperature = preset.get("temperature", 0.6 if self.show_anthropomorphic else 0.3)
            self.persona_name = preset.get("persona_name", "Luna" if self.show_anthropomorphic else "")
            self.warmth = preset.get("warmth", 0.7 if self.show_anthropomorphic else 0.25)
            self.formality = preset.get("formality", 0.55 if self.show_anthropomorphic else 0.7)
            self.empathy = preset.get("empathy", 0.55 if self.show_anthropomorphic else 0.15)
            self.self_reference = preset.get("self_reference", "I" if self.show_anthropomorphic else "none")
            
            # Check if adaptive mode is enabled - override adaptive tokens
            if self.adaptive_mode:
                from anthrokit.adaptive import ThresholdOptimizer
                
                # Use base preset matching the condition (CRITICAL for range exploration)
                # This ensures optimizer generates values within the appropriate range
                optimizer_base = self.anthro_preset  # Use same preset as condition
                
                try:
                    optimizer = ThresholdOptimizer(
                        tokens=self.adaptive_tokens,
                        target_metric="social_presence",
                        threshold_range=(self.adaptive_range_min, self.adaptive_range_max),
                        base_preset=optimizer_base,
                        n_levels=5
                    )
                    
                    # Get next condition from optimizer (explores within range)
                    next_condition = optimizer.get_next_condition()
                    
                    # Override adaptive tokens with optimizer-suggested values
                    if 'warmth' in self.adaptive_tokens:
                        self.warmth = next_condition.get('warmth', self.warmth)
                    if 'empathy' in self.adaptive_tokens:
                        self.empathy = next_condition.get('empathy', self.empathy)
                    if 'formality' in self.adaptive_tokens:
                        self.formality = next_condition.get('formality', self.formality)
                    
                    # Store optimizer for later outcome recording
                    self.optimizer = optimizer
                    self.current_condition = next_condition
                    
                    print(f"🔧 Adaptive mode: exploring {self.adaptive_tokens} in range [{self.adaptive_range_min:.2f}, {self.adaptive_range_max:.2f}]")
                    print(f"   Base preset: {optimizer_base}, Current values: warmth={self.warmth:.2f}, empathy={self.empathy:.2f}")
                
                except Exception as e:
                    print(f"⚠️ Adaptive optimizer failed to initialize: {e}")
                    print(f"   Falling back to fixed preset values")
                    self.optimizer = None
                    self.current_condition = None
            else:
                # Standard preset loading (fixed values)
                self.optimizer = None
                self.current_condition = None
            
            # Load full config for policy flags
            try:
                config = AnthroKitConfig()
                policy = config._policy
                self.no_deception = policy.get("no_deception", True)
                self.no_human_experience_claims = policy.get("no_human_experience_claims", True)
                self.no_sensitive_inference = policy.get("no_sensitive_inference", True)
                self.no_emojis_in_numbered_explanations = policy.get("no_emojis_in_numbered_explanations", True)
            except:
                # Fallback policy defaults
                self.no_deception = True
                self.no_human_experience_claims = True
                self.no_sensitive_inference = True
                self.no_emojis_in_numbered_explanations = True
                
        except ImportError:
            # If anthrokit package not installed, use fallback
            self._set_fallback_anthrokit_values()
        except Exception:
            # If any error, use fallback
            self._set_fallback_anthrokit_values()
    
    def _set_fallback_anthrokit_values(self):
        """Set fallback AnthroKit values if yaml loading fails."""
        self.emoji_style = "subtle" if self.show_anthropomorphic else "none"
        self.temperature = 0.6 if self.show_anthropomorphic else 0.3
        self.persona_name = "Luna" if self.show_anthropomorphic else ""
        self.warmth = 0.7 if self.show_anthropomorphic else 0.25
        self.formality = 0.55 if self.show_anthropomorphic else 0.7
        self.empathy = 0.55 if self.show_anthropomorphic else 0.15
        self.self_reference = "I" if self.show_anthropomorphic else "none"
        self.optimizer = None
        self.current_condition = None
        
        # Policy defaults
        self.no_deception = True
        self.no_human_experience_claims = True
        self.no_sensitive_inference = True
        self.no_emojis_in_numbered_explanations = True

    # ------------- parsing helpers -------------

    def _get_explanation_level(self):
        """Resolve explanation factor from env or CLI, with legacy fallback."""
        # env first
        env_val = os.getenv("ANTHROKIT_EXPLANATION", "").strip().lower()
        if env_val in _VALID_EXPLANATIONS:
            return env_val

        # CLI flags
        for arg in sys.argv[1:]:
            if arg.startswith("--explanation="):
                cand = arg.split("=", 1)[1].strip().lower()
                if cand in _VALID_EXPLANATIONS:
                    return cand

        # legacy version mapping
        legacy = os.getenv("ANTHROKIT_VERSION", "").strip().lower()
        cli_ver = self._cli_version_flag()
        legacy = cli_ver or legacy
        if legacy == "v1":
            return "feature_importance"
        if legacy == "v0":
            return "none"

        # default
        return "none"

    def _get_anthropomorphism_level(self):
        """Resolve anthropomorphism factor from env or CLI, with legacy fallback."""
        # env first
        env_val = os.getenv("ANTHROKIT_ANTHRO", "").strip().lower()
        if env_val in _VALID_ANTHRO:
            return env_val

        # CLI flags
        for arg in sys.argv[1:]:
            if arg.startswith("--anthro="):
                cand = arg.split("=", 1)[1].strip().lower()
                if cand in _VALID_ANTHRO:
                    return cand

        # legacy version mapping
        legacy = os.getenv("ANTHROKIT_VERSION", "").strip().lower()
        cli_ver = self._cli_version_flag()
        legacy = cli_ver or legacy
        if legacy == "v1":
            return "high"
        if legacy == "v0":
            return "low"

        # default
        return "low"

    def _cli_version_flag(self):
        """Read legacy version flags from CLI to support existing scripts."""
        for arg in sys.argv[1:]:
            if arg in ("--v0", "--v1"):
                return arg[2:]
            if arg.startswith("--ANTHROKIT_VERSION="):
                cand = arg.split("=", 1)[1].strip().lower()
                if cand in {"v0", "v1"}:
                    return cand
            if arg.startswith("--ab="):
                cand = arg.split("=", 1)[1].strip().lower()
                if cand in {"v0", "v1"}:
                    return cand
        return ""

    def _legacy_version_label(self):
        """Provide a simple label for the sidebar, does not affect factor levels."""
        # map current factors to a human friendly tag
        if self.explanation == "feature_importance" and self.anthro == "high":
            return "v1"
        if self.explanation == "none" and self.anthro == "low":
            return "v0"
        return "custom"

    def _generate_session_id(self):
        """Generate unique session ID for concurrent user tracking."""
        return f"{self.condition_code()}_{int(time.time())}_{str(uuid.uuid4())[:8]}"

    # ------------- public helpers for UI and logging -------------

    def condition_code(self):
        """
        Compact code for logging and analysis.
        Examples: E_none_A_low, E_cf_A_high, E_shap_A_high
        """
        e = {"none": "none", "counterfactual": "cf", "feature_importance": "shap"}[self.explanation]
        a = {"low": "low", "high": "high"}[self.anthro]
        return f"E_{e}_A_{a}"

    def get_assistant_avatar(self):
        """Return avatar path for high anthropomorphism, else None."""
        if not self.show_profile_pic:
            return None
        possible_paths = [
            "assets/luna_avatar.png",
            "images/assistant_avatar.png",
            "data_questions/Luna_is_a_Dutch_customer_service_assistant_working_at_a_restaurant_she_is_27_years_old_Please_genera.png",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None  # UI can fall back to initials

    def get_welcome_message(self):
        """Version specific welcome message for the chat header."""
        if self.show_anthropomorphic:
            return f"Hi, I am {self.assistant_name}. I will review your information and explain what factors influenced this loan decision."
        return "Welcome, this AI credit assistant can review your information and show which factors influenced the decision."

    def should_show_visual_explanations(self):
        """Whether to render SHAP bars or equivalent visuals."""
        return self.show_shap_visualizations

    def should_show_counterfactuals(self):
        """Whether to render counterfactual suggestions."""
        return self.show_counterfactual

    def explanation_style(self):
        """Control tone for natural language explanations."""
        return "conversational" if self.show_anthropomorphic else "technical"

    def explanation_label(self):
        """Human readable label for the assigned explanation type."""
        if self.explanation == "none":
            return "No explanation"
        if self.explanation == "counterfactual":
            return "Counterfactual explanation"
        return "Feature importance explanation"
    
    # Legacy compatibility methods
    def get_explanation_style(self):
        """Get explanation style based on version (alias for explanation_style)"""
        return self.explanation_style()


# Global config instance
config = AppConfig()


# ------------- sidebar debug -------------

def show_debug_sidebar():
    """Display condition and toggles for quick inspection."""
    st.sidebar.write("### AnthroKit Experiment Condition")
    st.sidebar.write(f"Version tag: **{config.version}**")
    st.sidebar.write(f"Condition: **{config.condition_code()}**")
    st.sidebar.write(f"Assistant: **{config.assistant_name}**")
    st.sidebar.write(f"Anthropomorphism: **{config.anthro}**")
    st.sidebar.write(f"Explanation: **{config.explanation}**")
    st.sidebar.write(f"Visual SHAP: {'✅' if config.show_shap_visualizations else '❌'}")
    st.sidebar.write(f"Counterfactual: {'✅' if config.show_counterfactual else '❌'}")
    st.sidebar.caption(f"Session ID: {config.session_id}")