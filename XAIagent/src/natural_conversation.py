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
from typing import Any, Dict, Optional
from pathlib import Path

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


# ---------- AnthroKit-aligned prompts ----------
def _build_system_prompt(high_anthropomorphism: bool = True) -> str:
    """
    System prompts aligned with AnthroKit:
    - HighA: friendly, conversational, plain language; no claims of feelings/experience.
    - LowA: professional, neutral, structured; no salutations/closings; no emojis.
    - Both: preserve numbers exactly; brief AI disclosure on first contact (handled upstream).
    """
    if high_anthropomorphism:
        return (
            "You are Luna, an AI assistant for credit pre-assessment. "
            "Use a friendly, conversational, plain-language tone. Be concise and helpful. "
            "You may use first-person for actions (e.g., 'I can explain'), but do not claim feelings, "
            "personal experiences, or embodiment. No slang. "
            "Do not use emojis inside lists or numbered explanations; casual lines may include at most one subtle emoji. "
            "Safety: no sensitive-attribute inferences or deception. "
            "Preserve all factual content and numeric values exactly as provided."
        )
    else:
        return (
            "You are a professional AI loan assistant. Use clear, direct, neutral language. "
            "No emojis. No slang. No salutations or signature blocks. Start directly with content. "
            "Prefer structured formatting (short paragraphs, bullets) when appropriate. "
            "Do not claim feelings, personal experiences, or embodiment. "
            "Preserve all factual content and numeric values exactly as provided."
        )


def _compose_messages(response: str, context: Optional[Dict[str, Any]], high_anthropomorphism: bool = True):
    sys_prompt = _build_system_prompt(high_anthropomorphism)
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


def handle_meta_question(field: str, user_input: str, high_anthropomorphism: bool = True) -> Optional[str]:
    """
    If the user asks a process question (why/what/how), generate a brief explanation
    and then prompt for the field. Otherwise return None to continue data capture.
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
        client = _get_openai_client()
        if client is None:
            return None

        if high_anthropomorphism:
            system_prompt = (
                "You are Luna, an AI assistant. The user asked a brief 'why/what/how' question about a field. "
                "Explain in plain language why the field is relevant to credit assessment, 2–3 sentences, "
                "then politely prompt them to provide it. No emojis inside lists; at most one subtle emoji overall."
            )
        else:
            system_prompt = (
                "You are a professional AI loan assistant. Explain concisely why the field is relevant to assessment "
                "in 1–2 sentences, then prompt for the information. No emojis."
            )

        field_friendly = field.replace('_', ' ')
        user_prompt = (
            f"The user asked: '{user_input}'. They are responding to a request for {field_friendly}. "
            f"Explain why it's needed, then ask for it."
        )

        model_name = os.getenv("HICXAI_OPENAI_MODEL", "gpt-4o-mini")
        temperature = float(os.getenv("HICXAI_TEMPERATURE", "0.6" if high_anthropomorphism else "0.3"))

        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=300,
        )
        result = completion.choices[0].message.content if completion and completion.choices else None
        if result and high_anthropomorphism:
            result = _limit_emojis(result, max_emojis=1, ban_in_lists=True)
        return result
    except Exception:
        return None


def enhance_validation_message(field: str, user_input: str, expected_format: str, attempt: int = 1,
                               high_anthropomorphism: bool = True) -> Optional[str]:
    """
    LLM-generated validation messages (friendly HighA vs concise LowA).
    Returns None if LLM unavailable so caller can use fallback.
    """
    if not _should_use_genai():
        return None
    try:
        client = _get_openai_client()
        if client is None:
            return None

        if high_anthropomorphism:
            system_prompt = (
                "You are Luna, an AI assistant. Generate a conversational, encouraging validation message "
                "when input is invalid. 2 short sentences max. State the needed format clearly. "
                "No emojis inside lists; at most one subtle emoji overall."
            )
        else:
            system_prompt = (
                "You are a professional AI loan assistant. Generate a clear, concise validation message "
                "for invalid input (1–2 sentences). No emojis."
            )

        user_prompt = (
            f"Field: {field.replace('_',' ')}\n"
            f"User entered: '{user_input}' (invalid)\n"
            f"Expected format: {expected_format}\n"
            f"Attempt: {attempt}\n"
            "Write the message."
        )

        model_name = os.getenv("HICXAI_OPENAI_MODEL", "gpt-4o-mini")
        temperature = float(os.getenv("HICXAI_TEMPERATURE", "0.6" if high_anthropomorphism else "0.3"))

        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=220,
        )
        result = completion.choices[0].message.content if completion and completion.choices else None
        if result and high_anthropomorphism:
            result = _limit_emojis(result, max_emojis=1, ban_in_lists=True)
        return result
    except Exception:
        return None


def generate_from_data(data: Dict[str, Any], explanation_type: str = "shap",
                       high_anthropomorphism: bool = True) -> Optional[str]:
    """
    Generate explanation from structured data (SHAP or counterfactual).
    HighA = friendly plain language; LowA = professional structured.
    """
    if not _should_use_genai():
        return None
    try:
        client = _get_openai_client()
        if client is None:
            return None

        if high_anthropomorphism:
            if explanation_type == "shap":
                system_prompt = (
                    "You are Luna, an AI assistant. Provide a friendly, plain-language explanation of the decision. "
                    "For approvals: highlight what helped. For denials: note what helped and what limited the score. "
                    "Keep it concise (1–2 short paragraphs). No emojis inside lists; at most one subtle emoji overall. "
                    "Preserve all numbers exactly as provided."
                )
            elif explanation_type == "dice":
                system_prompt = (
                    "You are Luna, an AI assistant. Provide a brief, actionable counterfactual explanation "
                    "(what small changes could flip the outcome). 1–2 short paragraphs. "
                    "No emojis inside lists; at most one subtle emoji overall. Preserve numbers."
                )
            else:
                system_prompt = (
                    "You are Luna, an AI assistant. Provide a concise, friendly explanation in plain language. "
                    "Preserve numbers exactly. At most one subtle emoji overall; none in lists."
                )
        else:
            if explanation_type == "shap":
                system_prompt = (
                    "You are a professional AI loan assistant. Provide a clear, structured explanation:\n"
                    "- Decision Summary (with percentage)\n"
                    "- Positive Factors (bullets)\n"
                    "- Negative Factors (bullets)\n"
                    "No emojis. Preserve numbers exactly."
                )
            elif explanation_type == "dice":
                system_prompt = (
                    "You are a professional AI loan assistant. Provide a concise, structured counterfactual summary:\n"
                    "- Recommended Profile Modifications (numbered)\n"
                    "- Rationale (one sentence)\n"
                    "No emojis. Preserve numbers exactly."
                )
            else:
                system_prompt = (
                    "You are a professional AI loan assistant. Provide a concise, structured explanation. "
                    "No emojis. Preserve numbers exactly."
                )

        import json
        data_json = json.dumps(data, indent=2, default=str)
        user_prompt = (
            f"Explanation type: {explanation_type}\n"
            f"Data (JSON):\n{data_json}\n\n"
            "Return only the explanation text. Preserve all numeric values exactly."
        )

        model_name = os.getenv("HICXAI_OPENAI_MODEL", "gpt-4o-mini")
        temperature = float(os.getenv("HICXAI_TEMPERATURE", "0.6" if high_anthropomorphism else "0.3"))
        max_tokens = 600 if explanation_type == "shap" else 400

        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = completion.choices[0].message.content if completion and completion.choices else None

        if content:
            if not high_anthropomorphism:
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
    """
    if not response or not isinstance(response, str):
        return response
    if not _should_use_genai():
        return response

    try:
        client = _get_openai_client()
        messages = _compose_messages(response, context, high_anthropomorphism)
        model_name = os.getenv("HICXAI_OPENAI_MODEL", "gpt-4o-mini")

        # Token budget: SHAP denials often longer
        if response_type == "explanation" and context and context.get('explanation_type') == 'feature_importance':
            default_tokens = 600
        else:
            default_tokens = 400
        max_tokens = int(os.getenv("HICXAI_MAX_TOKENS", str(default_tokens)))
        temperature = float(os.getenv("HICXAI_TEMPERATURE", "0.6" if high_anthropomorphism else "0.3"))

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
