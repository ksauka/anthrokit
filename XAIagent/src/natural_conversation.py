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
        for env_file in (root / ".env.local", root / ".env"):
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = [p.strip() for p in line.split("=", 1)]
                    if k == "OPENAI_API_KEY" and v:
                        os.environ[k] = v
                    elif k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass


def _should_use_genai() -> bool:
    """LLM is required for natural conversation; True iff we have an API key."""
    _ensure_env_loaded()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key and st is not None:
        try:
            key = st.secrets.get("OPENAI_API_KEY", None)  # type: ignore[attr-defined]
            if key:
                os.environ["OPENAI_API_KEY"] = str(key)
                api_key = str(key)
        except Exception:
            pass

    if not api_key:
        import warnings
        warnings.warn("OPENAI_API_KEY not found - conversation quality will be degraded")
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
    Build system prompt for loan domain using AnthroKit integration.
    
    REQUIRES: preset parameter (personality-adjusted tone configuration)
    USES: anthrokit.prompts.build_loan_system_prompt() for ALL prompts
    
    Args:
        preset: Final tone configuration with personality adjustments
                (from config.final_tone_config) - REQUIRED
        high_anthropomorphism: Deprecated, kept for API compatibility
    
    Returns:
        Complete system prompt with personality-driven tone
    """
    if preset is None:
        raise ValueError(
            "_build_system_prompt now requires 'preset' parameter. "
            "Pass config.final_tone_config from ab_config."
        )
    
    from anthrokit.prompts import build_loan_system_prompt
    return build_loan_system_prompt(
        preset=preset,
        domain_context="credit pre-assessment"
    )


def _compose_messages(response: str, context: Optional[Dict[str, Any]], preset: Optional[Dict[str, Any]] = None, high_anthropomorphism: bool = True):
    """Compose OpenAI messages with personality-driven system prompt.
    
    Args:
        response: System response to enhance
        context: Additional context information
        preset: Final tone configuration (personality-adjusted)
        high_anthropomorphism: Legacy parameter (used if preset=None)
    """
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
    return [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
    ]


# ---------- Public helpers ----------


def handle_meta_question(field: str, user_input: str, preset: Optional[Dict[str, Any]] = None, high_anthropomorphism: bool = True) -> Optional[str]:
    """
    If the user asks a process question (why/what/how), generate a brief explanation
    and then prompt for the field. Otherwise return None to continue data capture.
    
    Args:
        field: Field name being asked about
        user_input: User's question
        preset: Final tone configuration (personality-adjusted) - REQUIRED for personality integration
        high_anthropomorphism: Legacy parameter, kept for API compatibility
    
    Returns:
        Explanation + prompt, or None if not a question
    """
    user_lower = user_input.lower().strip()
    question_words = ['why', 'what', 'how', 'where', 'when', 'who', 'explain', 'tell me']
    is_likely_question = any(user_lower.startswith(w) for w in question_words) or user_input.strip().endswith("?")
    if not is_likely_question:
        return None

    if not _should_use_genai():
        # Fallback
        basics = {
            'age': "Age helps assess eligibility and repayment capacity.",
            'workclass': "Employment type is a signal of income stability.",
            'education': "Education often correlates with income potential.",
            'occupation': "Job type informs stability and prospects.",
            'hours_per_week': "Weekly hours indicate earning capacity.",
            'capital_gain': "Capital gains reflect additional income sources.",
            'capital_loss': "Capital losses affect the financial picture.",
            'native_country': "Country is a demographic feature in this dataset.",
            'marital_status': "Marital status can affect obligations and income.",
            'relationship': "Household role contextualizes finances.",
            'race': "This is present in the dataset; we handle it cautiously.",
            'sex': "This is present in the dataset; we handle it cautiously.",
        }
        return basics.get(field, f"This information about {field.replace('_', ' ')} supports assessment.")

    try:
        # Use AnthroKit prompt builder (personality-driven)
        from anthrokit.prompts import build_meta_question_prompt
        
        # Get preset if not provided
        if preset is None:
            try:
                from ab_config import config
                preset = getattr(config, 'final_tone_config', None)
            except (ImportError, AttributeError):
                # Fallback: construct minimal preset from high_anthropomorphism flag
                preset = {"self_reference": "I" if high_anthropomorphism else "none"}
        
        system_prompt = build_meta_question_prompt(
            preset=preset,
            field=field,
            user_question=user_input
        )

        
        user_prompt = "Explain why this field is needed and request the information."

        model_name = os.getenv("HICXAI_OPENAI_MODEL", "gpt-4o-mini")
        is_high_a = preset.get("self_reference") == "I" if preset else high_anthropomorphism
        temperature = float(os.getenv("HICXAI_TEMPERATURE", "0.6" if is_high_a else "0.3"))

        # Use generation control if available
        if GENERATION_CONTROL_AVAILABLE:
            try:
                result, metadata = generate_with_control(
                    prompt=system_prompt,
                    user_input=user_prompt,
                    final_tone_config=preset,
                    model_name=model_name,
                    validators=_get_loan_validators(),
                    temperature=temperature,
                    max_tokens=300
                )
                if result and is_high_a:
                    result = _limit_emojis(result, max_emojis=1, ban_in_lists=True)
                return result
            except Exception:
                pass  # Fall through to legacy
        
        # Legacy approach
        client = _get_openai_client()
        if client is None:
            return None

        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=300,
        )
        result = completion.choices[0].message.content if completion and completion.choices else None
        if result and is_high_a:
            result = _limit_emojis(result, max_emojis=1, ban_in_lists=True)
        return result
    except Exception:
        return None


def enhance_validation_message(field: str, user_input: str, expected_format: str, attempt: int = 1,
                               preset: Optional[Dict[str, Any]] = None, high_anthropomorphism: bool = True) -> Optional[str]:
    """
    LLM-generated validation messages (friendly HighA vs concise LowA).
    Returns None if LLM unavailable so caller can use fallback.
    Now uses generation control and anthrokit prompt builder.
    
    Args:
        field: Field name with validation error
        user_input: Invalid input provided by user
        expected_format: Description of expected format
        attempt: Validation attempt number
        preset: Final tone configuration (personality-adjusted) - REQUIRED for personality integration
        high_anthropomorphism: Legacy parameter, kept for API compatibility
    
    Returns:
        Validation message or None if LLM unavailable
    """
    if not _should_use_genai():
        return None
    try:
        # Use AnthroKit prompt builder (personality-driven)
        from anthrokit.prompts import build_validation_message_prompt
        
        # Get preset if not provided
        if preset is None:
            try:
                from ab_config import config
                preset = getattr(config, 'final_tone_config', None)
            except (ImportError, AttributeError):
                preset = {"self_reference": "I" if high_anthropomorphism else "none"}
        
        system_prompt = build_validation_message_prompt(
            preset=preset,
            field=field,
            expected_format=expected_format,
            attempt=attempt
        )

        user_prompt = (
            f"User entered: '{user_input}' (invalid)\n"
            "Generate the validation message."
        )

        model_name = os.getenv("HICXAI_OPENAI_MODEL", "gpt-4o-mini")
        is_high_a = preset.get("self_reference") == "I" if preset else high_anthropomorphism
        temperature = float(os.getenv("HICXAI_TEMPERATURE", "0.6" if is_high_a else "0.3"))

        # Use generation control if available
        if GENERATION_CONTROL_AVAILABLE:
            try:
                result, metadata = generate_with_control(
                    prompt=system_prompt,
                    user_input=user_prompt,
                    final_tone_config=preset,
                    model_name=model_name,
                    validators=_get_loan_validators(),
                    temperature=temperature,
                    max_tokens=220
                )
                if result and is_high_a:
                    result = _limit_emojis(result, max_emojis=1, ban_in_lists=True)
                return result
            except Exception:
                pass  # Fall through to legacy
        
        # Legacy approach
        client = _get_openai_client()
        if client is None:
            return None

        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=220,
        )
        result = completion.choices[0].message.content if completion and completion.choices else None
        if result and is_high_a:
            result = _limit_emojis(result, max_emojis=1, ban_in_lists=True)
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
    if not response or not isinstance(response, str):
        return response
    if not _should_use_genai():
        return response

    try:
        # Get personality-adjusted preset from config (with robust fallback)
        preset = None
        try:
            from ab_config import config
            preset = getattr(config, 'final_tone_config', None)
        except (ImportError, AttributeError):
            pass
        
        # Fallback: construct minimal preset if config unavailable
        if preset is None:
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
        temperature = float(os.getenv("HICXAI_TEMPERATURE", "0.6" if high_anthropomorphism else "0.3"))
        
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
