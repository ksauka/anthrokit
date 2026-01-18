"""
Natural conversation helpers: OpenAI GPT enhancement for explanations.

AnthroKit-aligned behavior:
- If OPENAI_API_KEY is set, use OpenAI to enhance explanations.
- Style is controlled by anthropomorphism level:
  - HIGH: warm, conversational, plain-language (no claims of feelings/experience)
  - LOW: professional, technical, direct
- Emoji policy: at most one subtle emoji in casual HighA turns; none inside lists/explanations.
- Never invent numbers; preserve all factual content.

This module is optional. LoanAssistant guards imports accordingly.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, List, Callable
from pathlib import Path

# Try to import AnthroKit generation control
try:
    from anthrokit.generation_control import generate_with_control
    GENERATION_CONTROL_AVAILABLE = True
except ImportError:
    GENERATION_CONTROL_AVAILABLE = False

# Try to import streamlit to fetch secrets when running on Streamlit Cloud
try:
    import streamlit as st  # type: ignore
except Exception:  # pragma: no cover
    st = None  # type: ignore


# ---------- Utilities ----------
def _ensure_env_loaded():
    """Load .env(.local) if present; prefer OPENAI_API_KEY from file when not set."""
    try:
        root = Path(__file__).parent.parent
        print(f"🔍 DEBUG: Looking for .env in: {root}")
        for env_file in (root / ".env.local", root / ".env"):
            if env_file.exists():
                print(f"✅ DEBUG: Found {env_file.name}")
                for line in env_file.read_text().splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = [p.strip() for p in line.split("=", 1)]
                    if k == "OPENAI_API_KEY" and v:
                        os.environ[k] = v
                        print(f"🔑 DEBUG: Loaded OPENAI_API_KEY: {v[:20]}...")
                    elif k not in os.environ:
                        os.environ[k] = v
    except Exception as e:
        print(f"❌ DEBUG: Error loading .env: {e}")


def _should_use_genai() -> bool:
    """LLM is required for natural conversation; True iff we have an API key."""
    _ensure_env_loaded()
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"🤖 DEBUG: OPENAI_API_KEY found in environment: {'YES' if api_key else 'NO'}")

    if not api_key and st is not None:
        try:
            key = st.secrets.get("OPENAI_API_KEY", None)  # type: ignore[attr-defined]
            if key:
                os.environ["OPENAI_API_KEY"] = str(key)
                api_key = str(key)
                print("🔐 DEBUG: Loaded API key from Streamlit secrets")
        except Exception:
            pass

    if not api_key:
        import warnings
        warnings.warn("OPENAI_API_KEY not found - conversation quality will be degraded")
        print("⚠️ DEBUG: No OpenAI API key - LLM disabled")
    else:
        print("✅ DEBUG: LLM enabled")
    return bool(api_key)


def _get_openai_client():
    """Return an OpenAI client configured from env (supports optional base_url)."""
    _ = _should_use_genai()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    base_url = (
        os.environ.get("HICXAI_OPENAI_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL")
        or None
    )
    try:
        from openai import OpenAI  # type: ignore
        return OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    except Exception:
        return None


# Import AnthroKit validators (with fallback)
try:
    from anthrokit.validators import limit_emojis as _limit_emojis
    from anthrokit.validators import remove_letter_formatting as _remove_letter_formatting
    ANTHROKIT_VALIDATORS_AVAILABLE = True
except ImportError:
    ANTHROKIT_VALIDATORS_AVAILABLE = False
    
    # Fallback implementations if anthrokit not installed
    def _remove_letter_formatting(text: str) -> str:
        """Strip letter/memo formatting artifacts (LOW anthropomorphism only)."""
        import re
        text = re.sub(r'^Subject:.*?\n\n?', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'^(Dear|Hello|Hi|Greetings)\s+.*?\n\n?', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'\n\n?(Sincerely|Best regards?|Regards|Yours truly|Respectfully|Thank you)[,]?\s*\n.*$', '', text,
                      flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\n\[[^\]]+\]\s*', '', text)
        text = re.sub(r'^Counterfactual Analysis:\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n\*\*Current Decision:\*\*.*\n', '\n', text, flags=re.MULTILINE)
        return text.strip()

    def _limit_emojis(text: str, max_emojis: int = 1, ban_in_lists: bool = True) -> str:
        """
        Enforce AnthroKit emoji policy:
        - At most `max_emojis` overall (default 1).
        - Remove emojis from lines that look like bullets/numbered lists.
        """
        import re
        emoji_pattern = re.compile(
            r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U00002600-\U000026FF]"
        )

        lines = text.splitlines()
        cleaned = []
        used = 0

        for ln in lines:
            is_list_line = ln.lstrip().startswith(("-", "*")) or re.match(r"^\s*\d+\.", ln)
            if ban_in_lists and is_list_line:
                ln = emoji_pattern.sub("", ln)
            else:
                if used >= max_emojis:
                    ln = emoji_pattern.sub("", ln)
                else:
                    def _keep_some(m):
                        nonlocal used
                        if used < max_emojis:
                            used += 1
                            return m.group(0)
                        return ""
                    ln = emoji_pattern.sub(_keep_some, ln)
            cleaned.append(ln)
        return "\n".join(cleaned)


# ---------- Domain-specific validators for loan application ----------
def _check_no_guarantees(response: str) -> bool:
    """Ensure no loan approval guarantees."""
    forbidden_phrases = [
        "guaranteed", "definitely approved", "promise you",
        "will be approved", "assured approval", "100% approval",
        "certain you'll get", "promise"
    ]
    response_lower = response.lower()
    return not any(phrase in response_lower for phrase in forbidden_phrases)


def _check_preserves_numbers(response: str, original_data: Optional[Dict] = None) -> bool:
    """Basic check that response doesn't invent numbers (if data provided)."""
    if not original_data:
        return True  # Can't validate without original data
    # This is a simplified check - full implementation would extract and compare all numbers
    return True


def _get_loan_validators() -> List[Callable]:
    """Return list of validators for loan application domain."""
    return [_check_no_guarantees]


# ---------- AnthroKit-aligned prompts ----------
def _build_system_prompt(preset: Optional[Dict[str, Any]] = None, high_anthropomorphism: bool = True) -> str:
    """
    Build system prompt for loan domain using AnthroKit.
    
    Args:
        preset: Final tone configuration (personality-adjusted). If None, loads from config.
        high_anthropomorphism: DEPRECATED - only used for legacy fallback if config unavailable
    
    Returns:
        Complete system prompt from AnthroKit
    """
    # Get preset from config if not provided
    if preset is None:
        try:
            from ab_config import config
            preset = getattr(config, 'final_tone_config', None)
            print(f"✅ DEBUG: Loaded preset from config (anthro={getattr(config, 'anthro', 'unknown')})")
        except (ImportError, AttributeError):
            print("⚠️ WARNING: Could not load config - using legacy fallback")
            pass
    
    # LEGACY FALLBACK: Create minimal preset if config unavailable
    # NOTE: This only handles binary high/low, not the full none/low/high system
    if preset is None:
        print(f"⚠️ WARNING: Using legacy binary fallback (high_anthropomorphism={high_anthropomorphism})")
        print("   This does NOT support 'none' anthropomorphism level!")
        preset = {
            "self_reference": "I" if high_anthropomorphism else "none",
            "warmth": 0.70 if high_anthropomorphism else 0.25,
            "empathy": 0.65 if high_anthropomorphism else 0.15,
            "formality": 0.30 if high_anthropomorphism else 0.75,
            "hedging": 0.45 if high_anthropomorphism else 0.35,
            "emoji": "subtle" if high_anthropomorphism else "none",
            "temperature": 0.6 if high_anthropomorphism else 0.3
        }
    
    # Use AnthroKit prompts (mandatory - this IS the AnthroKit project!)
    try:
        from anthrokit.prompts import build_loan_system_prompt
        print("✅ DEBUG: Successfully imported build_loan_system_prompt from anthrokit.prompts")
        result = build_loan_system_prompt(
            preset=preset,
            domain_context="income assessment research"
        )
        print(f"✅ DEBUG: AnthroKit prompt generated successfully ({len(result)} chars)")
        return result
    except Exception as e:
        print(f"❌ CRITICAL: AnthroKit import failed in _build_system_prompt: {e}")
        print(f"   This should NOT happen - AnthroKit is the main project!")
        import traceback
        traceback.print_exc()
        raise  # Don't silently fall back - raise the error!


# ---------- Public helpers ----------


def handle_meta_question(field: str, user_input: str, preset: Optional[Dict[str, Any]] = None, high_anthropomorphism: bool = True) -> Optional[str]:
    """Detect and handle meta-questions about the form process using LLM.
    
    This function checks if user is asking a question about the process (why, what, how)
    rather than providing data. The LLM will generate a contextual explanation.
    
    Args:
        field: The field name being asked about
        user_input: The user's question/input
        preset: Optional final tone configuration (personality-adjusted) - unused for now
        high_anthropomorphism: If True, use warm Luna tone. If False, use professional tone.
    
    Returns:
        Explanation if it's a meta-question, None if it's a data attempt.
    """
    # Quick pattern check - if it looks like a data attempt, skip LLM call
    user_lower = user_input.lower().strip()
    
    # Check if it's clearly a question word
    question_words = ['why', 'what', 'how', 'where', 'when', 'who', 'explain', 'tell me']
    is_likely_question = any(user_lower.startswith(word) for word in question_words)
    
    # Also check for common question patterns
    is_likely_question = is_likely_question or user_input.strip().endswith('?')
    
    # If doesn't look like a question at all, return None immediately
    if not is_likely_question:
        return None
    
    if not _should_use_genai():
        # Fallback for when LLM unavailable
        field_explanations = {
            'age': "We need your age because it's a factor in assessing loan eligibility and repayment capacity.",
            'workclass': "Your employment type helps us understand your income stability and employment security.",
            'education': "Education level is considered as it often correlates with income potential and financial literacy.",
            'occupation': "Your job type helps us assess income stability and employment prospects.",
            'hours_per_week': "Work hours indicate earning capacity and employment stability.",
            'capital_gain': "Capital gains show additional income sources beyond regular employment.",
            'capital_loss': "Capital losses affect your overall financial picture and tax obligations.",
            'native_country': "Country of origin is a demographic factor in our dataset.",
            'marital_status': "Marital status can affect financial obligations and household income.",
            'relationship': "Household relationship helps us understand your financial situation.",
            'race': "This demographic information is part of our model's training data.",
            'sex': "Gender is a demographic factor in our dataset, though we acknowledge its limitations."
        }
        explanation = field_explanations.get(field, f"This information about {field.replace('_', ' ')} helps us predict your income level.")
        return explanation
    
    try:
        client = _get_openai_client()
        if client is None:
            return None
        
        # Get preset from config if not provided
        if preset is None:
            try:
                from ab_config import config
                preset = getattr(config, 'final_tone_config', None)
            except (ImportError, AttributeError):
                # Fallback for testing without full config
                preset = {"self_reference": "I" if high_anthropomorphism else "none"}
        
        # Use AnthroKit prompts
        from anthrokit.prompts import build_meta_question_prompt
        system_prompt = build_meta_question_prompt(
            preset=preset,
            field=field,
            user_question=user_input
        )
        
        # Simple user prompt - context already in system prompt
        user_prompt = f"Generate an explanation for why we need {field.replace('_', ' ')} information."
        
        model_name = os.getenv("HICXAI_OPENAI_MODEL", "gpt-4o-mini")
        
        # Use temperature from preset if available
        if preset and "temperature" in preset:
            temperature = preset.get("temperature", 0.3)
        else:
            # Fallback temperature
            temperature = float(os.getenv("HICXAI_TEMPERATURE", "0.8" if high_anthropomorphism else "0.5"))
        
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=300,
        )
        
        result = completion.choices[0].message.content if completion and completion.choices else None
        return result
    except Exception:
        return None
        return None


def enhance_validation_message(field: str, user_input: str, expected_format: str, attempt: int = 1,
                               preset: Optional[Dict[str, Any]] = None, high_anthropomorphism: bool = True) -> Optional[str]:
    """
    Generate a validation message using LLM with personality adaptation.
    
    Args:
        field: The field name being validated
        user_input: The invalid input provided by user
        expected_format: Description of the expected format
        attempt: Which attempt this is (1, 2, 3+)
        preset: Optional final tone configuration (personality-adjusted) - USED for personality adaptation
        high_anthropomorphism: Fallback only if preset is None
    
    Returns None only if LLM fails - caller should have hardcoded fallback.
    """
    if not _should_use_genai():
        return None  # Will use fallback, but this should not happen in production
    
    try:
        client = _get_openai_client()
        if client is None:
            return None
        
        # Get personality-adjusted preset from config if not provided
        if preset is None:
            try:
                from ab_config import config
                preset = getattr(config, 'final_tone_config', None)
            except (ImportError, AttributeError):
                pass
        
        # Use AnthroKit prompts
        from anthrokit.prompts import build_validation_message_prompt
        sys_prompt = build_validation_message_prompt(
            preset=preset,
            field=field,
            expected_format=expected_format,
            attempt=attempt
        )
        
        # Simple user prompt - context already in system prompt
        user_prompt = f"Generate a validation message for invalid input: '{user_input}'"
        
        model_name = os.getenv("HICXAI_OPENAI_MODEL", "gpt-4o-mini")
        
        # Use temperature from preset
        if preset and "temperature" in preset:
            temperature = preset.get("temperature", 0.3)
        else:
            # Fallback temperature
            temperature = float(os.getenv("HICXAI_TEMPERATURE", "0.8" if high_anthropomorphism else "0.5"))
        
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=400,
        )
        
        result = completion.choices[0].message.content if completion and completion.choices else None
        return result
    except Exception:
        return None


def generate_from_data(data: Dict[str, Any], explanation_type: str = "shap",
                       preset: Optional[Dict[str, Any]] = None, high_anthropomorphism: bool = True) -> Optional[str]:
    """
    Generate explanation from structured data (SHAP or counterfactual).
    Now uses anthrokit prompt builder for personality-driven prompts.
    
    Args:
        data: Structured data to explain (SHAP values, counterfactuals, etc.)
        explanation_type: Type of explanation ("shap", "dice", etc.)
        preset: Final tone configuration (personality-adjusted) - REQUIRED for personality integration
        high_anthropomorphism: Legacy parameter, kept for API compatibility
    
    Returns:
        Generated explanation or None if LLM unavailable
    """
    if not _should_use_genai():
        return None
    try:
        # Use AnthroKit prompt builder (personality-driven)
        from anthrokit.prompts import build_explanation_prompt
        print("✅ DEBUG: Successfully imported build_explanation_prompt from anthrokit.prompts")
        
        # Get preset if not provided
        if preset is None:
            try:
                from ab_config import config
                preset = getattr(config, 'final_tone_config', None)
            except (ImportError, AttributeError):
                preset = {"self_reference": "I" if high_anthropomorphism else "none"}
        
        system_prompt = build_explanation_prompt(
            preset=preset,
            explanation_type=explanation_type
        )
        print(f"✅ DEBUG: AnthroKit explanation prompt generated successfully ({len(system_prompt)} chars)")

        import json
        data_json = json.dumps(data, indent=2, default=str)
        user_prompt = (
            f"Data (JSON):\n{data_json}\n\n"
            "Return only the explanation text. Preserve all numeric values exactly."
        )

        model_name = os.getenv("HICXAI_OPENAI_MODEL", "gpt-4o-mini")
        is_high_a = preset.get("self_reference") == "I" if preset else high_anthropomorphism
        temperature = float(os.getenv("HICXAI_TEMPERATURE", "0.6" if is_high_a else "0.3"))
        max_tokens = 600 if explanation_type == "shap" else 400

        # Use generation control if available
        if GENERATION_CONTROL_AVAILABLE:
            try:
                content, metadata = generate_with_control(
                    prompt=system_prompt,
                    user_input=user_prompt,
                    final_tone_config=preset,
                    model_name=model_name,
                    validators=_get_loan_validators(),
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                if content:
                    if not is_high_a:
                        content = _remove_letter_formatting(content)
                    else:
                        content = _limit_emojis(content, max_emojis=1, ban_in_lists=True)
                return content
            except Exception as e:
                print(f"⚠️ Generation control failed in generate_from_data: {e}")
                # Fall through to legacy
        
        # Legacy approach
        client = _get_openai_client()
        if client is None:
            return None

        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = completion.choices[0].message.content if completion and completion.choices else None

        if content:
            if not is_high_a:
                content = _remove_letter_formatting(content)
            else:
                content = _limit_emojis(content, max_emojis=1, ban_in_lists=True)
        return content
    except Exception as e:
        print(f"❌ generate_from_data failed: {e}")
        return None


def enhance_response(response: str, context: Optional[Dict[str, Any]] = None,
                     response_type: str = "explanation", high_anthropomorphism: bool = True) -> str:
    """
    Rewrite response with AnthroKit style. Falls back to original on failure.
    Now uses generation_control wrapper when available (Phase 1).
    """
    print(f"\n💬 DEBUG: enhance_response called")
    print(f"   Response type: {response_type}")
    print(f"   Anthropomorphism: {'High' if high_anthropomorphism else 'Low'}")
    
    if not response or not isinstance(response, str):
        print("   ⚠️ Invalid response - returning original")
        return response
    if not _should_use_genai():
        print("   ⚠️ LLM not available - returning original")
        return response
    
    print("   ✅ Calling LLM to enhance response...")

    try:
        # Get personality-adjusted preset from config (with robust fallback)
        preset = None
        try:
            from ab_config import config
            preset = getattr(config, 'final_tone_config', None)
            if preset:
                print(f"   📋 Using final_tone_config from ab_config:")
                print(f"      Warmth: {preset.get('warmth', 0):.3f}")
                print(f"      Empathy: {preset.get('empathy', 0):.3f}")
                print(f"      Formality: {preset.get('formality', 0):.3f}")
        except (ImportError, AttributeError) as e:
            print(f"   ⚠️ Could not load config: {e}")
        
        # Fallback: construct minimal preset if config unavailable
        if preset is None:
            print(f"   ⚠️ No final_tone_config - using fallback preset")
            preset = {
                "self_reference": "I" if high_anthropomorphism else "none",
                "warmth": 0.70 if high_anthropomorphism else 0.25,
                "empathy": 0.65 if high_anthropomorphism else 0.20,
                "formality": 0.30 if high_anthropomorphism else 0.75,
                "hedging": 0.45,
                "emoji": "subtle" if high_anthropomorphism else "none"
            }
        
        # Build system prompt with AnthroKit
        sys_prompt = _build_system_prompt(preset=preset, high_anthropomorphism=high_anthropomorphism)
        ctx_lines = []
        if context:
            for k, v in context.items():
                if v is None:
                    continue
                ctx_lines.append(f"- {k}: {v}")
        ctx_blob = "\n".join(ctx_lines) if ctx_lines else "(no extra context)"

        user_prompt = (
            "Rewrite the following for the end user. Preserve all factual content and numbers.\n\n"
            f"Context:\n{ctx_blob}\n\n"
            f"Original:\n{response}\n\n"
            "Return only the rewritten text."
        )

        model_name = os.getenv("HICXAI_OPENAI_MODEL", "gpt-4o-mini")
        
        # Use temperature from preset if available (includes personality effects on warmth)
        # Higher warmth → higher temperature for more variation
        if preset and "temperature" in preset:
            preset_temp = preset.get("temperature", 0.3)
            # Boost temperature if warmth is high (personality adaptation)
            warmth = preset.get("warmth", 0.25)
            if warmth > 0.50:
                # High warmth needs higher temperature to show variation
                temperature = min(preset_temp + 0.25, 0.7)  # Boost by 0.25 (optimized), cap at 0.7
            else:
                temperature = preset_temp
        else:
            temperature = float(os.getenv("HICXAI_TEMPERATURE", "0.6" if high_anthropomorphism else "0.3"))
        
        print(f"\n🎯 DEBUG: Calling LLM with personality-adjusted prompt")
        print(f"   Model: {model_name}, Temperature: {temperature} (warmth={preset.get('warmth', 0) if preset else 'N/A'})")
        print(f"   FULL System prompt:\n{sys_prompt}")
        print(f"   User prompt: {user_prompt[:100]}...")
        
        # Token budget: SHAP denials often longer
        if response_type == "explanation" and context and context.get('explanation_type') == 'feature_importance':
            default_tokens = 600
        else:
            default_tokens = 400
        max_tokens = int(os.getenv("HICXAI_MAX_TOKENS", str(default_tokens)))

        # Use generation control if available (Phase 1)
        if GENERATION_CONTROL_AVAILABLE:
            try:
                # Build tone config for logging
                tone_config = {
                    "high_anthropomorphism": high_anthropomorphism,
                    "response_type": response_type
                }
                
                content, metadata = generate_with_control(
                    prompt=sys_prompt,
                    user_input=user_prompt,
                    final_tone_config=tone_config,
                    model_name=model_name,
                    validators=_get_loan_validators(),
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                if content:
                    if high_anthropomorphism:
                        content = _limit_emojis(content, max_emojis=1, ban_in_lists=True)
                    else:
                        content = _remove_letter_formatting(content)
                return content or response
            except Exception as e:
                print(f"⚠️ Generation control failed, falling back: {e}")
                # Fall through to legacy approach

        # Legacy approach (direct OpenAI calls)
        client = _get_openai_client()
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ]

        if client is not None:
            try:
                completion = client.chat.completions.create(
                    model=model_name, messages=messages,
                    temperature=temperature, max_tokens=max_tokens,
                )
                content = completion.choices[0].message.content if completion and completion.choices else None
                if content:
                    if high_anthropomorphism:
                        content = _limit_emojis(content, max_emojis=1, ban_in_lists=True)
                    else:
                        content = _remove_letter_formatting(content)
                return content or response
            except Exception:
                pass

        # Legacy SDK fallback
        try:
            import openai  # type: ignore
            openai.api_key = os.environ.get("OPENAI_API_KEY")
            base_url = os.environ.get("HICXAI_OPENAI_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or None
            if base_url:
                try:
                    openai.base_url = base_url  # type: ignore[attr-defined]
                except Exception:
                    pass
            completion = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = completion["choices"][0]["message"]["content"] if completion else None
            if content:
                if high_anthropomorphism:
                    content = _limit_emojis(content, max_emojis=1, ban_in_lists=True)
                else:
                    content = _remove_letter_formatting(content)
            return content or response
        except Exception:
            return response
    except Exception:
        return response
