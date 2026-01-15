# AnthroKit

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A research framework for personality-adaptive anthropomorphism in conversational AI systems.

## Overview

AnthroKit enables researchers to systematically manipulate anthropomorphic design elements in AI interactions and study their effects on user experience. The framework supports:

- **Personality Assessment**: Big 5 trait collection via TIPI questionnaire
- **Adaptive Anthropomorphism**: Dynamic tone adjustment based on personality profiles
- **Experimental Control**: Fixed or personalized anthropomorphism conditions
- **Interaction Logging**: Structured data collection for empirical analysis

## Key Features

### Three Anthropomorphism Levels
- **NoA** (None): Formal, system-focused (warmth=0.00, empathy=0.00, formality=0.85)
- **LowA** (Low): Professional, minimal warmth (warmth=0.25, empathy=0.15, formality=0.70)
- **HighA** (High): Conversational, personified (warmth=0.70, empathy=0.55, formality=0.55)

### Personality-Based Personalization
- Maps Big 5 traits to tone parameters (e.g., Extraversion → warmth, Agreeableness → empathy)
- Applies bounded adjustments (±0.30) to base anthropomorphism presets
- Maintains experimental validity through controlled personalization ranges

### Data Collection
- Session-based interaction logging with GitHub API integration
- Captures tone configurations, generation metadata, and user interactions
- Supports prolific ID validation for online study deployment

## Installation

```bash
git clone https://github.com/ksauka/Anthrokit.git
cd AnthroKit
pip install -e .
```

## Quick Start

```python
from anthrokit import load_preset
from anthrokit.personality import apply_personality_to_preset

# Load base preset
base_preset = load_preset("HighA")

# Apply personality adjustments (if personality data available)
personality = {"extraversion": 0.8, "agreeableness": 0.6}
final_preset = apply_personality_to_preset(base_preset, personality)

# Use preset for LLM interaction
print(f"Warmth: {final_preset['warmth']}")
print(f"Empathy: {final_preset['empathy']}")
```

## Project Structure

```
AnthroKit/
├── anthrokit/              # Core framework package
│   ├── personality.py      # TIPI survey & trait mapping
│   ├── config.py           # Preset management
│   ├── adaptive.py         # Optimization algorithms
│   └── anthrokit.yaml      # Preset definitions
├── XAIagent/               # Example application
│   ├── src/                # Streamlit apps (6 experimental conditions)
│   ├── models/             # ML models for loan prediction task
│   └── tests/              # Unit tests
├── setup.py
├── pyproject.toml
└── requirements.txt
```

## Experimental Conditions

The framework supports 6 experimental conditions (3 anthropomorphism levels × 2 adaptation modes):

| Condition | Anthropomorphism | Personalization | Entry Point |
|-----------|-----------------|-----------------|-------------|
| NoA Fixed | None | Disabled | `app_nonanthro.py` |
| NoA Adaptive | None | Enabled | `app_nonanthro_personalize.py` |
| LowA Fixed | Low | Disabled | `app_condition_5.py` |
| LowA Adaptive | Low | Enabled | `app_condition_5_personality.py` |
| HighA Fixed | High | Disabled | `app_v1.py` |
| HighA Adaptive | High | Enabled | `app_v1_personality.py` |

### Related Publications

*Publications list to be updated upon publication.*

## Acknowledgements

This framework builds upon foundational research in human-computer interaction, personality psychology, and conversational AI. 

### Theoretical Foundation
- The TIPI questionnaire by Gosling et al. (2003) for accessible personality assessment
- The PERSONAGE framework by Mairesse & Walker (2007, 2010, 2011)  for personality-driven language generation
- Social Cues for Conversational Agents by Feine etal (2019)


### Implementation & Data
- **[XAgent](https://github.com/bach1292/XAgent)** by bach1292 - Original XAI agent framework and Adult dataset integration
- **Adult Dataset** from [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/adult) via XAgent implementation
- **Question-Intent Dataset** (`data_questions/Median_4.csv`) curated by XAgent, adapted from original work by Liao et al. (2020)

## License

MIT License - See [LICENSE](LICENSE) for details.

## Citation

```bibtex
@software{anthrokit2026,
  title = {AnthroKit: Personality-Adaptive Anthropomorphism Framework},
  author = {Sauka, Kudzai},
  year = {2026},
  url = {https://github.com/ksauka/Anthrokit}
}
```

## Contact

Kudzai Sauka - [GitHub](https://github.com/ksauka)
