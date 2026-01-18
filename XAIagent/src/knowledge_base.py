"""
Knowledge Base for Conversational Help System

Loads knowledge from knowledge_base.yaml for easier maintenance.
Provides search functions and intent detection for routing user questions.
"""

import yaml
import os
from typing import Dict, Any, Optional

# Load knowledge base from YAML file
_knowledge_cache = None

def _load_knowledge_base() -> Dict[str, Any]:
    """Load knowledge base from YAML file (cached)"""
    global _knowledge_cache
    if _knowledge_cache is not None:
        return _knowledge_cache
    
    # Get path to YAML file (same directory as this script)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, 'knowledge_base.yaml')
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            _knowledge_cache = yaml.safe_load(f)
        return _knowledge_cache
    except FileNotFoundError:
        print(f"ERROR: knowledge_base.yaml not found at {yaml_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse knowledge_base.yaml: {e}")
        return {}


# Intent Detection Methods
def get_intent_type(user_input: str) -> str:
    """
    Classify user intent for proper routing.
    
    Returns one of:
    - 'help_question': User asking about features, SHAP, dataset, model
    - 'field_answer': User providing information for current field
    - 'xai_request': User requesting XAI explanation (what-if, why, counterfactual)
    - 'navigation': User wants to review, check status, quit
    - 'meta_question': User asking "why do you need this?"
    - 'general': General conversation or unclear intent
    """
    user_lower = user_input.lower().strip()
    
    # Navigation commands
    nav_keywords = ['review', 'check', 'status', 'progress', 'quit', 'exit', 'stop', 'cancel']
    if user_lower in nav_keywords:
        return 'navigation'
    
    # XAI explanation requests
    xai_keywords = ['what if', 'why did', 'explain decision', 'explain prediction',
                   'explain the', 'how did', 'which factors', 'feature importance', 'counterfactual',
                   'what would happen', 'what changes', 'why was', 'why am i']
    if any(keyword in user_lower for keyword in xai_keywords):
        return 'xai_request'
    
    # Help questions about system, features, SHAP
    help_keywords = ['what is', 'what does', 'what are', 'tell me about', 
                    'what mean', 'how to read', 'how to interpret',
                    'what shap', 'explain shap', 'dataset', 'how does the model']
    if any(keyword in user_lower for keyword in help_keywords):
        return 'help_question'
    
    # Meta questions (why do you need X?)
    meta_keywords = ['why do you need', 'why do i need', 'why is this', 
                    'why does this matter', 'why ask', 'why are you asking']
    if any(keyword in user_lower for keyword in meta_keywords):
        return 'meta_question'
    
    # General help
    if user_lower in ['help', 'help me', 'stuck', 'confused', '?']:
        return 'help_question'
    
    # Default: assume it's a field answer or general conversation
    return 'field_answer'


def is_help_question(user_input: str) -> bool:
    """Check if user is asking a help/knowledge question"""
    return get_intent_type(user_input) == 'help_question'


def is_field_answer(user_input: str) -> bool:
    """Check if user is providing field information"""
    return get_intent_type(user_input) == 'field_answer'


def is_xai_request(user_input: str) -> bool:
    """Check if user is requesting XAI explanation"""
    return get_intent_type(user_input) == 'xai_request'


def is_meta_question(user_input: str) -> bool:
    """Check if user is asking why we need a field"""
    return get_intent_type(user_input) == 'meta_question'


def is_navigation(user_input: str) -> bool:
    """Check if user wants to navigate (review, quit, etc.)"""
    return get_intent_type(user_input) == 'navigation'


def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """
    Simple keyword-based search through knowledge base.
    Returns relevant sections based on query terms.
    
    Args:
        query: User's question or search terms
        top_k: Number of relevant sections to return
    
    Returns:
        Concatenated relevant knowledge sections
    """
    KNOWLEDGE_BASE = _load_knowledge_base()
    if not KNOWLEDGE_BASE:
        return "Knowledge base unavailable."
    
    query_lower = query.lower()
    results = []
    
    # Check for dataset questions
    dataset_keywords = ['dataset', 'data', 'census', 'adult income', 'training data', 'where', 'source']
    if any(kw in query_lower for kw in dataset_keywords):
        results.append(("Dataset Overview", KNOWLEDGE_BASE.get("dataset_overview", "")))
    
    # Check for SHAP/explanation questions
    shap_keywords = ['shap', 'explanation', 'interpret', 'understand', 'mean', 'value', 'positive', 'negative', 'how to read']
    if any(kw in query_lower for kw in shap_keywords):
        results.append(("SHAP Explanation", KNOWLEDGE_BASE.get("shap_explanation", "")))
    
    # Check for model questions
    model_keywords = ['model', 'algorithm', 'random forest', 'how does it work', 'accuracy', 'performance', 'train']
    if any(kw in query_lower for kw in model_keywords):
        results.append(("Model Details", KNOWLEDGE_BASE.get("model_details", "")))
    
    # Check for prediction questions
    prediction_keywords = ['prediction', 'decision', 'how was', 'calculated', 'probability', 'confidence']
    if any(kw in query_lower for kw in prediction_keywords):
        results.append(("Prediction Explanation", KNOWLEDGE_BASE.get("prediction_explanation", "")))
    
    # Check for specific feature questions
    features = KNOWLEDGE_BASE.get("features", {})
    for feature_name, feature_info in features.items():
        feature_keywords = [feature_name, feature_name.replace('_', ' '), feature_name.replace('_', '-')]
        if any(kw in query_lower for kw in feature_keywords):
            feature_text = f"""**{feature_name.replace('_', ' ').title()}**

{feature_info.get('description', '')}

**Why This Matters:**
{feature_info.get('why_important', '')}

**Typical Values:**
{feature_info.get('typical_values', '')}

**Model Behavior:**
{feature_info.get('model_behavior', '')}
"""
            results.append((f"Feature: {feature_name}", feature_text))
    
    # Check for "why" questions about specific features
    why_questions = KNOWLEDGE_BASE.get("why_questions", {})
    for key, answer in why_questions.items():
        feature = key.replace("why_", "")
        if feature in query_lower or f"why {feature}" in query_lower or f"why do you need {feature}" in query_lower:
            results.append((f"Why {feature}?", answer))
    
    # If no results, provide general help
    if not results:
        results.append(("General Help", """
I can answer questions about:
- **Features**: What each piece of information means (age, education, occupation, etc.) and why it matters
- **SHAP Explanations**: How to interpret the feature importance values
- **Dataset**: Information about the Adult Census Income dataset
- **Model**: How the prediction model works
- **Your Prediction**: How your specific result was calculated

Try asking:
- "What is [feature name]?" (e.g., "What is occupation?")
- "Why do you need my [feature]?" (e.g., "Why do you need my education?")
- "What does a SHAP value mean?"
- "Tell me about the dataset"
- "How does the model work?"
"""))
    
    # Combine results (limit to top_k)
    combined = "\n\n---\n\n".join([f"## {title}\n\n{content}" for title, content in results[:top_k]])
    return combined


def get_feature_help(field_name: str) -> str:
    """
    Get specific help text for a feature field.
    
    Args:
        field_name: Name of the field (e.g., 'age', 'education')
    
    Returns:
        Help text explaining the field
    """
    KNOWLEDGE_BASE = _load_knowledge_base()
    if not KNOWLEDGE_BASE:
        return f"Help text for {field_name} unavailable."
    
    features = KNOWLEDGE_BASE.get("features", {})
    if field_name in features:
        feature = features[field_name]
        return f"""{feature.get('description', '')}

**Why we need this**: {feature.get('why_important', '')}

**Examples**: {feature.get('typical_values', '')}"""
    
    return f"This field helps us understand your profile better for income assessment."

