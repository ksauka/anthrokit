# AnthroKit: Personality-Adaptive Anthropomorphism Framework

**A research framework for personality-driven anthropomorphic AI interactions.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

**AnthroKit** is a research framework for operationalizing personality-adaptive anthropomorphism in conversational AI systems. The framework enables researchers to:

- Collect Big 5 personality traits via validated TIPI survey (Gosling et al., 2003)
- Map personality traits to anthropomorphic tone adjustments based on PERSONAGE (Mairesse & Walker, 2007)
- Apply adaptive optimization for user-specific anthropomorphism levels
- Track and analyze the relationship between personality, anthropomorphism, and user outcomes

## Research Context

**Paper:** "AnthroKit: A Framework for Personality-Adaptive Anthropomorphism"  
**Status:** Framework validation study in progress (N=20-30)  


### Core Research Question
Do personality traits moderate the relationship between anthropomorphism and social presence in AI interactions?

### Framework Components

**1. Personality Collection (TIPI/Big 5)**
- 10-item survey measuring Extraversion, Agreeableness, Conscientiousness, Neuroticism, Openness
- Session-cached responses with validation
- Reverse-coded scoring and trait averaging

**2. Trait-to-Token Mapping**
- Research-grounded mappings (e.g., Extraversion → warmth, Agreeableness → empathy)
- Equal weights (0.5/0.5) as theoretically neutral initial coefficients
- Personalization emerges from individual TIPI score differences
- Post-hoc optimization via regression on validation study data

**3. Anthropomorphism Presets**
- **HighA**: Warm, conversational tone with persona (warmth=0.70, empathy=0.55)
- **LowA**: Professional, neutral, system-focused (warmth=0.25, empathy=0.15)
- Personality adjustments: ±0.30 range based on centered trait scores

**4. Adaptive Optimization**
- Multi-armed bandit approach for real-time personalization
- Thompson Sampling with Beta priors
- Session tracking and outcome logging for post-hoc analysis

## Project Structure

```
AnthroKit/
├── anthrokit/              # Core Python package
│   ├── personality.py      # TIPI collection & trait-to-token mapping
│   ├── config.py           # Preset loading and management
│   ├── adaptive.py         # Thompson Sampling optimizer
│   ├── tracking.py         # Session and outcome logging
│   └── validators.py       # Safety guardrails
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
│
└── XAIagent/               # Validation study implementation
    ├── src/                # Streamlit applications
    │   ├── app_v1.py       # High anthropomorphism condition
    │   ├── app_condition_5.py  # Low anthropomorphism condition
    │   └── app_adaptive.py # Adaptive optimization demo
    ├── config/             # System prompts and presets
    └── data/               # Study datasets

```

## Installation

```bash
# Clone repository
git clone https://github.com/ksauka/Anthrokit.git
cd AnthroKit

# Install package
pip install -e .
```

## Usage Example

```python
from anthrokit.personality import collect_personality_once, apply_personality_to_preset
from anthrokit.config import load_preset

# Step 1: Collect personality traits (TIPI survey)
personality = collect_personality_once()
# {'extraversion': 6.5, 'agreeableness': 5.5, 'conscientiousness': 5.0, ...}

# Step 2: Load base preset
base_preset = load_preset("HighA")

# Step 3: Apply personality-based adjustments
personalized_preset = apply_personality_to_preset(base_preset, personality)
# Adjusts warmth, empathy, formality based on individual trait scores
```

## Validation Study

See [XAIagent/](XAIagent/) for the framework validation study implementation:
- **Domain**: Loan pre-assessment chatbot
- **Design**: Within-subjects (N=20-30)
- **Conditions**: Low Anthropomorphism, High Anthropomorphism, Personality-Adapted
- **Measures**: Social Presence Scale, Trust, Satisfaction
- **Platform**: Streamlit with session tracking

## Citation

If you use AnthroKit in your research, please cite:

```bibtex
@software{anthrokit2026,
  author = {Sauka, Kudzai},
  title = {AnthroKit: A Framework for Personality-Adaptive Anthropomorphism},
  year = {2026},
  url = {https://github.com/ksauka/Anthrokit}
}
```

### Key References

- **TIPI Scale**: Gosling, S. D., Rentfrow, P. J., & Swann, W. B., Jr. (2003). A very brief measure of the Big-Five personality domains. *Journal of Research in Personality*, 37(6), 504-528.
- **PERSONAGE**: Mairesse, F., & Walker, M. (2007). PERSONAGE: Personality generation for dialogue. *ACL '07*.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contact

Kudzai Sauka - [GitHub](https://github.com/ksauka)

---

*This is a research framework under active development. Framework validation study in progress.*

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


---

*This is a research framework under active development. Framework validation study in progress.*
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
