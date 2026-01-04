# XAIagent: AnthroKit Framework Validation Study

**Implementation of loan pre-assessment chatbot for validating the AnthroKit personality-adaptive anthropomorphism framework.**

## Overview

This directory contains the validation study implementation for the AnthroKit framework paper. The study uses a loan application scenario to test whether personality-adaptive anthropomorphism improves user experience.

## Study Design

**2×2 Within-subjects (N=20-30):**

**Independent Variables:**
- **Anthropomorphism**: Low (warmth=0.25) vs High (warmth=0.70)
- **Personality Adaptation**: Fixed vs Personality-Adapted (TIPI-based adjustments ±0.30)

**4 Conditions:**
1. Low Anthropomorphism + Fixed preset
2. Low Anthropomorphism + Personality-Adapted
3. High Anthropomorphism + Fixed preset
4. High Anthropomorphism + Personality-Adapted

**Dependent Measures:**
- Social Presence Scale (Gefen & Straub, 2004)
- Trust in AI system
- Satisfaction ratings

## Project Structure

```
XAIagent/
├── src/
│   ├── app_v1.py              # High anthropomorphism app
│   ├── app_condition_5.py     # Low anthropomorphism app
│   ├── loan_assistant.py      # Loan assessment logic
│   └── natural_conversation.py # LLM integration
├── config/
│   ├── system_prompt_high.txt # HighA system prompt
│   └── system_prompt_low.txt  # LowA system prompt
├── data/
│   └── adult.data             # Census income dataset
├── models/                     # Trained classifiers
└── assets/                     # UI resources
```

## Setup

**1. Install AnthroKit package:**
```bash
cd /home/kudzy/Projects/AnthroKit
pip install -e .
```

**2. Install dependencies:**
```bash
cd XAIagent
pip install -r requirements.txt
```

**3. Configure environment:**
```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

## Running Study Conditions

**High Anthropomorphism (Condition 1):**
```bash
streamlit run src/app_v1.py
```

**Low Anthropomorphism (Condition 2):**
```bash
streamlit run src/app_condition_5.py
```

**Personality-Adapted (Condition 3):**
- Collects TIPI survey at start
- Applies personality-based adjustments via `apply_personality_to_preset()`
- Uses same base app as Condition 1

## Data Collection

**Session tracking:**
- Personality traits (TIPI scores)
- Applied preset configuration
- User interactions and outcomes
- Logged to `data/session_tracking.jsonl`

**Outcome measures:**
- Social presence (5-point scale)
- Trust ratings
- Satisfaction ratings

## Key Dependencies

- **AnthroKit**: Core framework (personality module, presets)
- **Streamlit**: Web application
- **OpenAI GPT-4**: Natural language generation
- **scikit-learn**: Loan classification model
- **SHAP**: Feature importance explanations

## Related Files

See parent [README.md](../README.md) for AnthroKit framework overview.
