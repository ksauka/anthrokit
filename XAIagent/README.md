# XAI Loan Assistant - Anthropomorphism Research Study

Research implementation for studying anthropomorphic design in XAI systems using AnthroKit.

## Project Structure

```
XAIagent/
├── src/                    # Application source code
│   ├── app.py             # Main Streamlit application
│   ├── loan_assistant.py  # Loan assessment logic
│   ├── natural_conversation.py  # LLM integration
│   ├── ab_config.py       # Experiment configuration
│   ├── app_v0.py          # Entry point: v0 (minimal)
│   ├── app_v1.py          # Entry point: v1 (full features)
│   └── app_condition_*.py # Entry points for specific conditions
│
├── config/                 # Configuration files
│   ├── anthrokit.py       # AnthroKit helper (legacy)
│   ├── system_prompt*.txt # System prompts
│   └── developer_prompt.txt
│
├── data/                   # Datasets
├── models/                 # Trained models (pickled)
├── assets/                 # UI assets (images, avatars)
├── logs/                   # Experiment logs
├── feedback/               # User feedback data
│
├── tests/                  # Test suite
│   ├── test_integration.py
│   ├── test_validation_messages.py
│   └── ...
│
├── scripts/                # Utility scripts
│   ├── deployment/        # Deployment scripts
│   └── test_all_conditions.sh
│
├── docs/                   # Documentation
│   ├── README.md          # Project overview
│   ├── DEPLOYMENT_GUIDE.md
│   ├── ANTHROPOMORPHISM_OPERATIONALIZATION.md
│   └── ...
│
├── environments/           # Conda environment configs
│   ├── environment.yml
│   └── environment_rtx5070.yml
│
├── .streamlit/            # Streamlit configuration
├── .github/               # GitHub workflows
├── .huggingface/          # HuggingFace config
│
├── requirements.txt       # Python dependencies
├── runtime.txt           # Python version (Streamlit Cloud)
└── packages.txt          # System packages
```

## Setup

### 1. Install AnthroKit Package

From the project root:
```bash
cd /home/kudzy/Projects/AnthroKit
pip install -e .
```

### 2. Install XAI Dependencies

```bash
cd XAIagent
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and set your OpenAI API key:
```bash
cp .env.example .env
# Edit .env and add OPENAI_API_KEY=your_key_here
```

## Running the Application

### Run Specific Condition

```bash
# High anthropomorphism, full features (v1)
ANTHROKIT_ANTHRO=high streamlit run src/app_v1.py

# Low anthropomorphism, minimal features (v0)
ANTHROKIT_ANTHRO=low streamlit run src/app_v0.py

# Custom condition
ANTHROKIT_EXPLANATION=counterfactual ANTHROKIT_ANTHRO=high streamlit run src/app.py
```

### Test All Conditions

```bash
bash scripts/test_all_conditions.sh
```

## Experiment Conditions

3 × 2 factorial design:
- **Explanation**: none | counterfactual | feature_importance
- **Anthropomorphism**: low | high

## Development

### Run Tests

```bash
cd XAIagent
pytest tests/
```

### Code Style

Follows PEP8 with 100-character line limit:
```bash
black --line-length 100 src/
flake8 src/ --max-line-length=100
```

## Deployment

### Streamlit Cloud

See [docs/STREAMLIT_CLOUD_SETUP.md](docs/STREAMLIT_CLOUD_SETUP.md)

### HuggingFace Spaces

See [docs/HUGGINGFACE_DEPLOYMENT.md](docs/HUGGINGFACE_DEPLOYMENT.md)

## Dependencies

- **AnthroKit**: Core anthropomorphism design system (installed from parent directory)
- **Streamlit**: Web application framework
- **OpenAI**: LLM integration for natural conversation
- **SHAP**: Feature importance explanations
- **DiCE**: Counterfactual explanations
- **scikit-learn**: ML models

## License

MIT License - See LICENSE file for details
