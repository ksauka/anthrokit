# AnthroKit: Personality-Adaptive Anthropomorphism Framework

**A research framework for personality-driven anthropomorphic AI interactions.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Research Grade](https://img.shields.io/badge/status-research--grade-success.svg)]()

---

## 🎯 Project Focus: Framework Paper (2026)

**Paper:** "AnthroKit: A Framework for Personality-Adaptive Anthropomorphism"  
**Target:** IUI 2026, UIST 2026, CHI Late-Breaking Work  
**Status:** Writing phase (validation study planned)

This repo focuses on:
- ✅ Personality trait collection (TIPI/Big 5)
- ✅ Trait-to-token mapping algorithm
- ✅ Adaptive anthropomorphism optimization
- ⏳ Framework validation (N=20-30)

**For comprehensive XAI study:** See [HciAXI](../HciAXI) repo (planned for later)

---

## Overview

**AnthroKit** is a research framework for personality-adaptive anthropomorphism in conversational AI. It provides:

- 🎛️ **Token-based control** of 11 anthropomorphic dimensions
- 🧠 **Personality integration** (Big 5 → token adjustments)
- 🔄 **Adaptive optimization** (multi-armed bandit)
- 🔬 **Separation of content from tone** (scaffolds + stylizer)
- 🌐 **Domain-agnostic** (validated on loan application scenario)
- 📊 **Research-ready tracking** (session + outcome logging)

## Key Features

### 1. Personality Collection (TIPI/Big 5)
```python
from anthrokit.personality import collect_personality_once

# Collect Big 5 traits (10-item survey)
personality = collect_personality_once()
# {'extraversion': 6.5, 'agreeableness': 5.5, ...}
```

### 2. Trait-to-Token Mapping
```python
from anthrokit.personality import map_traits_to_token_adjustments

# Map traits to anthropomorphism adjustments
adjustments = map_traits_to_token_adjustments(personality)
# {'warmth': +0.30, 'empathy': +0.25, ...}
```

### 3. Preset Personalization
```python
from anthrokit.personality import apply_personality_to_preset
from anthrokit.config import load_preset

# Load base preset and personalize
base = load_preset("HighA")
personalized = apply_personality_to_preset(base, personality)
# warmth: 0.70 → 1.00 (adjusted for extraverted user)
```

### 4. Adaptive Optimization
```python
from anthrokit.adaptive import ThresholdOptimizer

# Create optimizer exploring warmth range
optimizer = ThresholdOptimizer(
    tokens=["warmth", "empathy"],
    threshold_range=(0.6, 0.8),
    base_preset="HighA"
)

# Get next condition to test
preset = optimizer.get_next_condition()

# Record outcome with personality
optimizer.record_outcome(preset, outcomes, personality)
```

--- Project Structure

```
AnthroKit/
├── anthrokit/              # Core reusable package
│   ├── scaffolds.py        # Domain-neutral content patterns
│   ├── stylizer.py         # LLM + pattern-based tone application
│   ├── config.py           # Load presets from YAML
│   ├── prompts.py          # Legacy pattern-based interface
│   ├── validators.py       # Emoji policy & guardrails
│   ├── anthrokit.yaml      # Token definitions
│   └── api/                # Optional FastAPI service
│       ├── main.py         # REST endpoints
│       └── schemas.py      # Request/response models
│
├── XAIagent/               # Example: XAI research study
│   ├── src/                # Loan assistant application
│   ├── data/               # Datasets
│   ├── models/             # ML models
│   ├── tests/              # Test suite
│   └── docs/               # Study documentation
│
├── setup.py                # Package installation
├── pyproject.toml          # Package metadata (PEP 517/518)
└── README.md               # This file
```

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/anthrokit.git
cd AnthroKit

# Install core package
pip install -e .

# Install with LLM stylization support
pip install -e ".[llm]"

# Install with API service
pip install -e ".[api]"

# Install everything
pip install -e ".[all]"
```

### Basic Usage: Scaffolds + Stylizer

```python
from anthrokit import load_preset, stylize_text
from anthrokit.scaffolds import greet, decide, inform

# Generate domain-neutral base content
greeting = greet(context="order inquiry")
print(greeting)
# Output: "This assistant can help with your order inquiry."

# Apply anthropomorphic tone
preset_high = load_preset("HighA")
styled = stylize_text(greeting, preset_high)
print(styled)
# Output: "Hi! I'm Luna, and I can help with your order inquiry."

# Compare with low anthropomorphism
preset_low = load_preset("LowA")
styled_low = stylize_text(greeting, preset_low)
print(styled_low)
# Output: "This assistant can help with your order inquiry."
```

### Domain-Agnostic Examples

**E-Commerce:**
```python
from anthrokit import stylize_text, load_preset
from anthrokit.scaffolds import inform, error_message

# Order status update
status = inform("Your order has shipped", category="update")
styled = stylize_text(status, load_preset("HighA"))
# "Good news — your order has shipped!"

# Error handling
error = error_message("item out of stock")
styled = stylize_text(error, load_preset("HighA"))
# "I'm sorry — error: item out of stock. Let me help you find an alternative."
```

**Healthcare:**
```python
from anthrokit.scaffolds import decide, acknowledge

# Appointment confirmation
decision = decide("appointment confirmed", explanation_available=True)
styled = stylize_text(decision, load_preset("HighA"))
# "Great — your appointment is confirmed! I can walk you through what to expect."

# Patient information acknowledged
ack = acknowledge("insurance information")
styled = stylize_text(ack, load_preset("LowA"))
# "Confirmed: insurance information"
```

**Customer Support:**
```python
from anthrokit.scaffolds import explain_factors

# Troubleshooting explanation
factors = explain_factors(
    supporting_factors=["updated drivers", "stable connection"],
    opposing_factors=["outdated firmware"]
)
styled = stylize_text(factors, load_preset("HighA"))
# "Here's what I found: updated drivers and stable connection are helping, 
#  but outdated firmware might be causing issues."
```

**Education:**
```python
from anthrokit.scaffolds import explain_impact

# Assessment feedback
impact = explain_impact(
    factor_impacts={
        "essay_structure": 0.8,
        "grammar": -0.3,
        "argumentation": 0.6
    },
    outcome_label="final grade"
)
styled = stylize_text(impact, load_preset("HighA"))
# "Let me break this down: essay structure really boosted your grade, 
#  and argumentation helped too, but grammar brought it down a bit."
```

### Legacy Pattern-Based Interface

For direct prompt generation without scaffolds:

```python
from anthrokit import load_preset, generate_greeting, generate_closing

preset = load_preset("HighA")
greeting = generate_greeting(preset)
closing = generate_closing(preset)
```

## Advanced: REST API Service

Run AnthroKit as a microservice for remote stylization:

```bash
# Install API dependencies
pip install -e ".[api]"

# Start service
uvicorn anthrokit.api.main:app --reload --port 8001
```

**API Endpoints:**

```bash
# Health check
curl http://localhost:8001/healthz

# Stylize text
curl -X POST "http://localhost:8001/v1/stylize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your request has been processed",
    "preset": "HighA",
    "use_llm": true
  }'

# Get base scaffold
curl -X POST "http://localhost:8001/v1/scaffold" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "inform",
    "kwargs": {
      "content": "Order shipped",
      "category": "update"
    }
  }'

# Validate text
curl -X POST "http://localhost:8001/v1/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I feel happy about this result! 😊😘🎉",
    "preset": "HighA"
  }'
```

See API documentation at `http://localhost:8001/docs` after starting the service.

## Available Scaffolds

| Scaffold | Purpose | Parameters | Example Use Case |
|----------|---------|------------|------------------|
| `greet` | Initial welcome | context | "order inquiry", "technical support" |
| `ask_info` | Request information | fields, purpose | Form filling, data collection |
| `inform` | Deliver information | content, category | Status updates, notifications |
| `acknowledge` | Confirm understanding | content | User input confirmation |
| `decide` | Communicate outcome | outcome, explanation_available | Decision results, status changes |
| `explain_counterfactual` | What-if explanation | factor, current/target values | "If X changed to Y, outcome would be Z" |
| `explain_factors` | Factor attribution | supporting/opposing factors | Feature importance, cause analysis |
| `explain_impact` | Impact analysis | factor_impacts, outcome_label | SHAP values, contribution scores |
| `error_message` | Handle errors | error_type | Error recovery, troubleshooting |
| `close_conversation` | End interaction | summary | Session closure, handoff |
| `disclosure_statement` | AI identity | specificity | Transparency, ethical disclosure |

## Token System

AnthroKit defines **11 measurable tokens**:

| Token | Type | Range | Description |
|-------|------|-------|-------------|
| `warmth` | float | 0-1 | Friendliness and care language |
| `formality` | float | 0-1 | Professional vs casual tone |
| `empathy` | float | 0-1 | Acknowledgment of user stakes |
| `self_reference` | enum | none/we/I | First-person pronoun usage |
| `hedging` | float | 0-1 | Qualification language |
| `humor` | float | 0-0.2 | Light metaphors (minimal) |
| `emoji` | enum | none/subtle | Emoji usage policy |
| `persona_name` | string | - | Named identity (e.g., "Luna") |
| `greeting_style` | enum | neutral/warm | Initial contact tone |
| `closing_style` | enum | neutral/warm | Session end tone |
| `disclosure` | enum | explicit/compact | AI identity disclosure |

## Presets

### HighA (High Anthropomorphism)

Warm, conversational, plain-language tone with persona:
```yaml
warmth: 0.70
formality: 0.55
empathy: 0.55
self_reference: "I"
emoji: "subtle"
persona_name: "Luna"
temperature: 0.6
```

### LowA (Low Anthropomorphism)

Professional, neutral, direct tone without persona:
```yaml
warmth: 0.25
formality: 0.70
empathy: 0.15
self_reference: "none"
emoji: "none"
persona_name: ""
temperature: 0.3
```

## Safety Guardrails

AnthroKit enforces ethical guidelines to prevent harmful anthropomorphism:

### Forbidden Claims
- ❌ Feelings or emotions ("I feel worried", "I'm excited")
- ❌ Lived experiences ("In my experience", "As someone who...")
- ❌ Physical embodiment ("I see", "I understand" when literal)
- ❌ Sensitive attribute inferences (race, gender, religion)

### Enforced Policies
- ✅ Explicit AI identity disclosure
- ✅ Emoji limits (max 1 in HighA, none in numbered lists)
- ✅ No deceptive language
- ✅ Factual content preservation
- ✅ Professional boundaries

### Validation Example

```python
from anthrokit.validators import validate_guardrails, post_process_response

# Check for violations
text = "I feel really happy about your approval! 😊🎉✨"
violations = validate_guardrails(text)
print(violations)
# Output: ["Forbidden phrase: 'I feel'"]

# Auto-clean
preset = load_preset("HighA")
cleaned = post_process_response(text, preset)
print(cleaned)
# Output: "I'm glad about your approval! 🙂"
```

## Use Cases

### Production Applications
- 🛒 **E-commerce**: Order tracking, product recommendations
- 🏥 **Healthcare**: Appointment scheduling, symptom checkers
- 📞 **Customer Support**: Ticket management, troubleshooting
- 🎓 **Education**: Tutoring systems, assessment feedback
- 💰 **Finance**: Account inquiries, transaction explanations

### Research Applications
- 📊 Manipulation checks for anthropomorphism studies
- 🔬 A/B testing of conversational tone
- 📈 Social presence in HCI research
- 🧪 Explainable AI (XAI) communication

## Example: XAI Research Study

The **XAIagent/** folder demonstrates AnthroKit in a real research context:

- **Domain**: Loan pre-assessment chatbot
- **Design**: 3×2 factorial (Explanation × Anthropomorphism)
- **Validated**: Manipulation checks (d ≥ 0.6)
- **Platform**: Streamlit with Prolific integration

See [XAIagent/README.md](XAIagent/README.md) for implementation details.

## Development

### Run Tests

```bash
cd XAIagent
pytest tests/ -v
```

### Code Style

```bash
# Format code (PEP8, 100-char lines)
black --line-length 100 anthrokit/

# Lint
flake8 anthrokit/ --max-line-length=100

# Type check
mypy anthrokit/
```

## Citation

If you use AnthroKit in your research, please cite:

```bibtex
@software{anthrokit2026,
  title = {AnthroKit: Research-Grade Anthropomorphism Design System for Conversational AI},
  author = {AnthroKit Contributors},
  year = {2026},
  url = {https://github.com/your-org/anthrokit},
  note = {Domain-agnostic token-based framework for promoting social presence 
          in conversational AI through controlled anthropomorphism}
}
```

## Academic Grounding

AnthroKit is grounded in established HCI and psychology research:

- **HAX Guidelines** (Microsoft, CHI 2019 / TOCHI 2022) - Responsible AI interaction design
- **Three-Factor Anthropomorphism Theory** (Epley et al., 2007) - Psychological mechanisms
- **CASA Framework** (Nass & Moon, 2000) - Computers as social actors
- **Social Presence Theory** (Short et al., 1976) - Mediated communication
- **Recent Chatbot Research** (2022-2024) - Tone effects in conversational AI

### Key Publications
- Seering et al. (2019). "Designing User Interface Elements to Improve the Quality of Conversation"
- Candello et al. (2017). "Evaluating the conversation of conversational agents"
- Følstad & Brandtzæg (2020). "Chatbots: Changing user needs and motivations"

See [XAIagent/docs/ACADEMIC_GROUNDING.md](XAIagent/docs/ACADEMIC_GROUNDING.md) for complete references.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Maintainers

- AnthroKit Contributors

## Links

- 📚 [Documentation](https://anthrokit.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/your-org/anthrokit/issues)
- 💬 [Discussions](https://github.com/your-org/anthrokit/discussions)
