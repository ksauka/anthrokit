"""
A/B Testing Configuration for AnthroKit
This module configures experimental conditions for the live study.
It reads factor levels from environment variables or command-line arguments,
and sets up the AnthroKit preset accordingly.



"""

import os
import sys
import uuid
import time
import streamlit as st

_VALID_EXPLANATIONS = {"none", "counterfactual", "feature_importance"}
_VALID_ANTHRO       = {"none", "low", "high"}


class AppConfig:
    """Configuration class for A/B testing versions and factor levels with AnthroKit preset support."""

    def __init__(self):
        # read factor levels (env and CLI), then derive UI toggles
        self.explanation = self._get_explanation_level()           # none | counterfactual | feature_importance
        self.anthro      = self._get_anthropomorphism_level()      # low | high
        self.version     = self._legacy_version_label()            # v0 | v1 (for sidebar display only)
        self.session_id  = self._generate_session_id()             # unique session tracking

        # derived feature flags for UI rendering, explanations, and logging
        self.show_anthropomorphic   = (self.anthro == "high")
        self.show_profile_pic       = self.show_anthropomorphic
        self.show_shap_visualizations = (self.explanation == "feature_importance" and self.anthro == "high")
        self.show_counterfactual    = (self.explanation == "counterfactual")
        self.show_any_explanation   = (self.explanation != "none")

        # AnthroKit preset loader (using anthrokit package)
        if self.anthro == "none":
            self.anthro_preset = "NoA"
        elif self.anthro == "high":
            self.anthro_preset = "HighA"
        else:
            self.anthro_preset = "LowA"
        self._load_anthrokit_preset()

        # assistant identity and copy are derived from anthropomorphism
        persona_name = getattr(self, 'persona_name', "")
        if persona_name:
            self.assistant_name = persona_name
        elif self.anthro == "high":
            self.assistant_name = "Luna"
        else:
            self.assistant_name = "Loan Assistant"
        
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
                apply_personality_to_preset,
                map_traits_to_token_adjustments
            )
            
            # Load base preset
            base_preset = load_preset(self.anthro_preset)
            
            # Store base preset for logging (BEFORE adjustments)
            self.base_preset = base_preset.copy()
            
            # Check for personality-based personalization
            personality = get_personality_from_session()
            print(f"\n🧬 DEBUG: Personality Detection")
            if personality:
                print(f"   ✅ Personality found in session:")
                print(f"      Extraversion: {personality.get('extraversion', 0):.2f}")
                print(f"      Agreeableness: {personality.get('agreeableness', 0):.2f}")
                print(f"      Conscientiousness: {personality.get('conscientiousness', 0):.2f}")
                print(f"      Neuroticism: {personality.get('neuroticism', 0):.2f}")
                print(f"      Openness: {personality.get('openness', 0):.2f}")
                
                # Calculate adjustments
                self.personality_adjustments = map_traits_to_token_adjustments(personality)
                print(f"\n🎚️ DEBUG: Personality Adjustments Calculated:")
                print(f"      Warmth: {self.personality_adjustments.get('warmth', 0):+.3f}")
                print(f"      Empathy: {self.personality_adjustments.get('empathy', 0):+.3f}")
                print(f"      Formality: {self.personality_adjustments.get('formality', 0):+.3f}")
                print(f"      Hedging: {self.personality_adjustments.get('hedging', 0):+.3f}")
                
                # Apply adjustments
                preset = apply_personality_to_preset(base_preset, personality)
                print(f"\n🔧 DEBUG: Applied personality adjustments to {self.anthro_preset} preset")
                print(f"   Base warmth: {base_preset.get('warmth', 0):.3f}")
                print(f"   Final warmth: {preset.get('warmth', 0):.3f}")
            else:
                print(f"   ⚠️ No personality data found in session")
                print(f"   Using base {self.anthro_preset} preset without adjustments")
                # No personality adjustments
                self.personality_adjustments = {
                    "warmth": 0.0,
                    "empathy": 0.0,
                    "formality": 0.0,
                    "hedging": 0.0
                }
                preset = base_preset.copy()
            
            # Store final config for logging (AFTER adjustments)
            self.final_tone_config = preset.copy()
            
            # Load final preset values into config (fallbacks match _set_fallback_anthrokit_values)
            self.emoji_style = preset.get("emoji", "subtle" if self.anthro == "high" else "none")
            self.temperature = preset.get("temperature", 0.6 if self.anthro == "high" else (0.1 if self.anthro == "none" else 0.3))
            self.persona_name = preset.get("persona_name", "Luna" if self.anthro == "high" else "")
            self.warmth = preset.get("warmth", 0.7 if self.anthro == "high" else (0.0 if self.anthro == "none" else 0.25))
            self.formality = preset.get("formality", 0.55 if self.anthro == "high" else (0.85 if self.anthro == "none" else 0.7))
            self.empathy = preset.get("empathy", 0.55 if self.anthro == "high" else (0.0 if self.anthro == "none" else 0.15))
            self.hedging = preset.get("hedging", 0.45 if self.anthro == "high" else (0.20 if self.anthro == "none" else 0.35))
            self.self_reference = preset.get("self_reference", "I" if self.anthro == "high" else "none")
            
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
        if self.anthro == "high":
            # HighA fallback
            self.emoji_style = "subtle"
            self.temperature = 0.6
            self.persona_name = "Luna"
            self.warmth = 0.7
            self.formality = 0.55
            self.empathy = 0.55
            self.self_reference = "I"
            self.hedging = 0.45
        elif self.anthro == "none":
            # NoA fallback (zero anthropomorphism)
            self.emoji_style = "none"
            self.temperature = 0.1
            self.persona_name = ""
            self.warmth = 0.0
            self.formality = 0.85
            self.empathy = 0.0
            self.self_reference = "none"
            self.hedging = 0.20
        else:
            # LowA fallback (low anthropomorphism)
            self.emoji_style = "none"
            self.temperature = 0.3
            self.persona_name = ""
            self.warmth = 0.25
            self.formality = 0.7
            self.empathy = 0.15
            self.self_reference = "none"
            self.hedging = 0.35
        
        # CRITICAL: Set final_tone_config for natural_conversation.py
        self.final_tone_config = {
            "emoji": self.emoji_style,
            "temperature": self.temperature,
            "persona_name": self.persona_name,
            "warmth": self.warmth,
            "formality": self.formality,
            "empathy": self.empathy,
            "self_reference": self.self_reference,
            "hedging": self.hedging  # Use the hedging value set above, not hardcoded
        }
        
        # Set empty personality tracking
        self.base_preset = self.final_tone_config.copy()
        self.personality_adjustments = {}
        self.self_reference = "I" if self.show_anthropomorphic else "none"
        
        # Policy defaults
        self.no_deception = True
        self.no_human_experience_claims = True
        self.no_sensitive_inference = True
        self.no_emojis_in_numbered_explanations = True
    
    def refresh_personality_adjustments(self):
        """Refresh personality adjustments after questionnaire completion.
        Call this after save_personality_to_session() to update final_tone_config."""
        try:
            from anthrokit import load_preset
            from anthrokit.personality import (
                get_personality_from_session,
                apply_personality_to_preset,
                map_traits_to_token_adjustments
            )
            
            print(f"\n🔄 DEBUG: Refreshing personality adjustments...")
            
            # Reload base preset
            base_preset = load_preset(self.anthro_preset)
            
            # Check for personality data
            personality = get_personality_from_session()
            if personality:
                print(f"   ✅ Found personality in session")
                print(f"      Extraversion: {personality.get('extraversion', 0):.2f}")
                print(f"      Agreeableness: {personality.get('agreeableness', 0):.2f}")
                
                # Calculate and apply adjustments
                self.personality_adjustments = map_traits_to_token_adjustments(personality)
                preset = apply_personality_to_preset(base_preset, personality)
                
                print(f"\n   🎚️ Adjustments applied:")
                print(f"      Warmth: {base_preset.get('warmth', 0):.3f} → {preset.get('warmth', 0):.3f}")
                print(f"      Empathy: {base_preset.get('empathy', 0):.3f} → {preset.get('empathy', 0):.3f}")
                print(f"      Formality: {base_preset.get('formality', 0):.3f} → {preset.get('formality', 0):.3f}")
                print(f"      Hedging: {base_preset.get('hedging', 0):.3f} → {preset.get('hedging', 0):.3f}")
                
                # Update final_tone_config and instance variables
                self.final_tone_config = preset.copy()
                self.warmth = preset.get("warmth", self.warmth)
                self.empathy = preset.get("empathy", self.empathy)
                self.formality = preset.get("formality", self.formality)
                print(f"   ✅ final_tone_config updated!")
            else:
                print(f"   ⚠️ No personality found - keeping base preset")
                
        except Exception as e:
            print(f"   ❌ ERROR refreshing personality: {e}")
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
        Examples: E_none_A_none, E_none_A_low, E_cf_A_high, E_shap_A_high
        """
        e = {"none": "none", "counterfactual": "cf", "feature_importance": "shap"}[self.explanation]
        a = {"none": "none", "low": "low", "high": "high"}[self.anthro]
        return f"E_{e}_A_{a}"

    def get_assistant_avatar(self):
        """Return avatar path for high anthropomorphism, else None."""
        if not self.show_profile_pic:
            return None
        
        from pathlib import Path
        base_dir = Path(__file__).parent.parent  # XAIagent directory
        
        possible_paths = [
            base_dir / "assets" / "luna_avatar.png",
            base_dir / "images" / "assistant_avatar.png",
            base_dir / "data_questions" / "Luna_is_a_Dutch_customer_service_assistant_working_at_a_restaurant_she_is_27_years_old_Please_genera.png",
        ]
        for path in possible_paths:
            if path.exists():
                return str(path)
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