#!/bin/bash
# Deploy HicXAI to Hugging Face Spaces
# Usage: ./deploy_to_huggingface.sh YOUR_HF_USERNAME [organization]

set -e

# Check if logged in
if ! command -v huggingface-cli &> /dev/null; then
    echo "⚠️  huggingface-cli not found. Installing..."
    pip install huggingface_hub
fi

# Check authentication
if ! huggingface-cli whoami &> /dev/null; then
    echo "❌ Not logged in to Hugging Face"
    echo ""
    echo "Please login first:"
    echo "  huggingface-cli login"
    echo ""
    echo "Get your token at: https://huggingface.co/settings/tokens"
    exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: ./deploy_to_huggingface.sh YOUR_HF_USERNAME [organization]"
    echo ""
    echo "Examples:"
    echo "  ./deploy_to_huggingface.sh myusername"
    echo "  ./deploy_to_huggingface.sh myusername/my-org"
    exit 1
fi

HF_USERNAME="$1"
PROJECT_DIR="/home/kudzy/Projects/HicXAI_agent"
DEPLOY_DIR="/tmp/hf_deploy"

# Condition configurations: number:app_file:description
CONDITIONS=(
    "1:app_v0.py:No Explanation, Low Anthropomorphism"
    "2:app_condition_2.py:No Explanation, High Anthropomorphism"
    "3:app_condition_3.py:Counterfactual Explanation, Low Anthropomorphism"
    "4:app_condition_4.py:Counterfactual Explanation, High Anthropomorphism"
    "5:app_condition_5.py:SHAP Explanation, Low Anthropomorphism"
    "6:app_v1.py:SHAP Explanation, High Anthropomorphism"
)

CURRENT_USER=$(huggingface-cli whoami | grep 'username:' | awk '{print $2}')

echo "🚀 Deploying HicXAI to Hugging Face Spaces"
echo "Logged in as: $CURRENT_USER"
echo "Deploying to: $HF_USERNAME"
echo ""
echo "💡 For anonymous deployment, consider:"
echo "   1. Use organization: ./deploy_to_huggingface.sh your-org"
echo "   2. Create anonymous account"
echo "   3. Make spaces private after deployment"
echo ""

mkdir -p "$DEPLOY_DIR"

for condition in "${CONDITIONS[@]}"; do
    IFS=':' read -r num app_file desc <<< "$condition"
    
    SPACE_NAME="hicxai-condition-$num"
    SPACE_DIR="$DEPLOY_DIR/$SPACE_NAME"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 Deploying Condition $num: $desc"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Clone or pull space (using HF token for authentication)
    HF_TOKEN=$(cat ~/.cache/huggingface/token 2>/dev/null || cat ~/.huggingface/token 2>/dev/null)
    
    if [ -d "$SPACE_DIR" ]; then
        echo "   Updating existing space..."
        cd "$SPACE_DIR"
        git pull
    else
        echo "   Cloning space repository..."
        cd "$DEPLOY_DIR"
        git clone "https://$HF_USERNAME:$HF_TOKEN@huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME" || {
            echo "❌ Failed to clone. Make sure the space exists at:"
            echo "   https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"
            echo ""
            echo "Create it first at: https://huggingface.co/new-space"
            continue
        }
        cd "$SPACE_NAME"
    fi
    
    echo "   Copying application files..."
    
    # Copy source code (excluding __pycache__, test files, etc.)
    rsync -av --delete \
        --exclude='__pycache__/' \
        --exclude='*.pyc' \
        --exclude='test_*.py' \
        --exclude='.pytest_cache/' \
        "$PROJECT_DIR/src/" ./src/
    
    # Copy the actual streamlit app file as src/streamlit_app.py (HF template expects this location)
    cp "$PROJECT_DIR/$app_file" ./src/streamlit_app.py
    
    # Copy only essential data files (adult.data for the ML model)
    mkdir -p ./data
    if [ -f "$PROJECT_DIR/data/adult.data" ]; then
        cp "$PROJECT_DIR/data/adult.data" ./data/
    fi
    
    # Copy data_questions directory (required for NLU model) - includes CSV and agent profile images
    rsync -av --delete "$PROJECT_DIR/data_questions/" ./data_questions/
    
    # Copy models (will use Git LFS)
    rsync -av --delete "$PROJECT_DIR/models/" ./models/
    
    # Copy dataset info
    rsync -av --delete "$PROJECT_DIR/dataset_info/" ./dataset_info/
    
    # Copy requirements
    cp "$PROJECT_DIR/requirements.txt" ./
    
    # Copy .streamlit directory (template only, not secrets)
    mkdir -p .streamlit
    if [ -f "$PROJECT_DIR/.streamlit/secrets.toml.template" ]; then
        cp "$PROJECT_DIR/.streamlit/secrets.toml.template" ./.streamlit/
    fi
    
    # Create .streamlit/config.toml to set correct port for HF
    cat > .streamlit/config.toml << 'CONFIGEOF'
[server]
port = 7860
headless = true
address = "0.0.0.0"

[browser]
gatherUsageStats = false
CONFIGEOF
    
    # Create custom Dockerfile to override HF template and set correct port
    cat > Dockerfile << 'DOCKEREOF'
FROM python:3.13.5-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

# Copy application files
COPY src/ ./src/
COPY data/ ./data/
COPY data_questions/ ./data_questions/
COPY models/ ./models/
COPY dataset_info/ ./dataset_info/
COPY .streamlit/ ./.streamlit/

# Expose port 7860 for HF Spaces
EXPOSE 7860

# Run Streamlit with explicit port setting
CMD ["streamlit", "run", "src/streamlit_app.py", "--server.port=7860", "--server.address=0.0.0.0"]
DOCKEREOF
    
    echo "   Creating README.md..."
    
    # Create Hugging Face README with metadata for Docker
    cat > README.md << EOF
---
title: HicXAI Research - Condition $num
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# AI Loan Assistant - Research Study

**Condition $num**: $desc

This is an interactive AI loan assistant for research purposes studying the effects of explainable AI (XAI) methods and conversational anthropomorphism in credit decision systems.

## Features

- Interactive loan application process
- ML-based credit assessment
- Natural language conversation
- $(if [[ $num -ge 3 ]]; then echo "Explainable AI insights"; else echo "Decision feedback"; fi)
- $(if [[ $num == 2 ]] || [[ $num == 4 ]] || [[ $num == 6 ]]; then echo "High anthropomorphism (warm, conversational)"; else echo "Low anthropomorphism (professional, technical)"; fi)

**Note**: This application is for research purposes only and does not make real credit decisions.

## Research Context

Part of the HicXAI research project investigating human-AI interaction in high-stakes decision-making contexts.
EOF
    
    echo "   Setting up Git LFS for large model files and images..."
    git lfs install
    git lfs track "*.pkl" "*.pth"
    git lfs track "*.png" "*.jpg" "*.jpeg"
    
    echo "   Committing changes..."
    git add .gitattributes
    git add .
    
    if git diff --staged --quiet; then
        echo "   ℹ️  No changes to commit"
    else
        git commit -m "Update to v1.1-chatty-luna ($(date +%Y-%m-%d))"
        echo "   Pushing to Hugging Face..."
        git push
        echo "   ✅ Condition $num deployed successfully!"
    fi
    
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Deployment complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Your apps are available at:"
for i in {1..6}; do
    echo "  Condition $i: https://huggingface.co/spaces/$HF_USERNAME/hicxai-condition-$i"
done
echo ""
echo "⚠️  IMPORTANT: Next steps for each space:"
echo ""
echo "1️⃣  Add Secrets (Settings → Variables and secrets):"
echo "   - OPENAI_API_KEY = your-key"
echo "   - HICXAI_OPENAI_MODEL = gpt-4o-mini"
echo "   - HICXAI_TEMPERATURE = 0.7"
echo "   - HICXAI_GENAI = on"
echo ""
echo "2️⃣  For Anonymous Deployment (Settings → Visibility):"
echo "   - Make space Private"
echo "   - Share direct embed URL: https://[space-name].hf.space"
echo "   - Participants won't see creator info"
echo ""
echo "3️⃣  Optional: Disable Community Features"
echo "   - Go to Settings → Discussions → Disable"
echo "   - Removes social features, looks more professional"
echo ""
