"""
WORKING REFERENCE: Domain-Specific Prompt Generation for Loan/Credit Domain

This module provides COMPLETE, PRODUCTION-READY prompt generation for the loan
domain (used by XAIagent). It demonstrates how to integrate AnthroKit components
to create personality-adaptive prompts using PURE ARCHITECTURE:

    scaffolds.py → domain-agnostic base content
         ↓
    prompts.py → adds domain-specific context (loan/credit)
         ↓
    stylizer.py → applies personality-driven tone

"""

from __future__ import annotations

from typing import Dict, Any, Optional

# Import AnthroKit scaffolds for domain-agnostic base content
from anthrokit.scaffolds import (
    greet,
    ask_info,
)

# Import AnthroKit stylizer for personality-driven prompt generation
from anthrokit.stylizer import _build_stylization_prompt


def _is_high_anthropomorphism(preset: Dict[str, Any]) -> bool:
    """Determine if preset uses high anthropomorphism.
    
    Args:
        preset: Preset configuration dictionary
        
    Returns:
        True if high anthropomorphism (self_reference == "I")
    """
    return preset.get("self_reference", "none") == "I"


def generate_greeting(preset: Dict[str, Any]) -> str:
    """Generate greeting message based on preset.
    
    Pattern Card: [GREET]
    - LowA: Neutral, direct
    - HighA: Warm, introduces persona
    
    Args:
        preset: Preset configuration (HighA or LowA)
        
    Returns:
        Greeting string appropriate for preset
    """
    if _is_high_anthropomorphism(preset):
        persona_name = preset.get("persona_name", "Luna")
        return (f"Hi, I'm {persona_name}. I'll guide you through "
                "a short credit pre-assessment.")
    return "Hello. This assistant will guide you through a short credit pre-assessment."


def generate_ask_info(preset: Dict[str, Any]) -> str:
    """Generate information request message.
    
    Pattern Card: [ASK_INFO]
    - LowA: Direct request
    - HighA: Conversational request with context
    
    Args:
        preset: Preset configuration
        
    Returns:
        Information request string
    """
    if _is_high_anthropomorphism(preset):
        return ("Could you confirm a few basics so I can assess fairly—"
                "age bracket, education, occupation, and hours/week?")
    return "Please confirm age bracket, education, occupation, and hours/week."


def generate_decision_approve(preset: Dict[str, Any]) -> str:
    """Generate approval decision message.
    
    Pattern Card: [DECISION_APPROVE]
    - LowA: Factual statement
    - HighA: Warm, encouraging
    
    Args:
        preset: Preset configuration
        
    Returns:
        Approval message string
    """
    if _is_high_anthropomorphism(preset):
        return "Good news—your preliminary result is approved. This is a simulated research result."
    return "Preliminary result: approved. This is a simulated research result."


def generate_decision_decline(preset: Dict[str, Any]) -> str:
    """Generate decline decision message.
    
    Pattern Card: [DECISION_DECLINE]
    - LowA: Factual statement with explanation offer
    - HighA: Empathetic, supportive
    
    Args:
        preset: Preset configuration
        
    Returns:
        Decline message string
    """
    if _is_high_anthropomorphism(preset):
        return ("I know this matters—your preliminary result is declined. "
                "I can walk you through why.")
    return "Preliminary result: declined. A brief explanation is available."


def generate_explanation_counterfactual(
    preset: Dict[str, Any],
    feature: str,
    current_value: str,
    target_value: str
) -> str:
    """Generate counterfactual explanation.
    
    Pattern Card: [EXPLAIN_CF]
    - LowA: Technical, conditional language
    - HighA: Conversational, actionable
    
    Args:
        preset: Preset configuration
        feature: Feature name (human-readable)
        current_value: Current feature value
        target_value: Target value for approval
        
    Returns:
        Counterfactual explanation string
    """
    if _is_high_anthropomorphism(preset):
        return (f"If you adjusted {feature} from {current_value} to {target_value}, "
                "I'd expect this to flip to approved.")
    return (f"If {feature} changed from {current_value} to {target_value}, "
            "the decision would likely switch to approved.")


def generate_explanation_attribution(
    preset: Dict[str, Any],
    positive_factors: list[str],
    negative_factors: list[str]
) -> str:
    """Generate attribution explanation.
    
    Pattern Card: [EXPLAIN_ATTR]
    - LowA: Structured list format
    - HighA: Narrative format with metaphor
    
    Args:
        preset: Preset configuration
        positive_factors: Features that increased approval probability
        negative_factors: Features that decreased approval probability
        
    Returns:
        Attribution explanation string
    """
    if _is_high_anthropomorphism(preset):
        pos_str = " and ".join(positive_factors) if positive_factors else "none"
        neg_str = " and ".join(negative_factors) if negative_factors else "none"
        return (f"Here's what shaped it most: {pos_str} helped, "
                f"while {neg_str} pulled confidence down.")
    
    pos_str = ", ".join(positive_factors) if positive_factors else "none"
    neg_str = ", ".join(negative_factors) if negative_factors else "none"
    return f"Top drivers: {pos_str} increased confidence; {neg_str} lowered it."


def generate_closing(preset: Dict[str, Any]) -> str:
    """Generate session closing message.
    
    Pattern Card: [CLOSE]
    - LowA: Neutral thank you
    - HighA: Warm, collaborative
    
    Args:
        preset: Preset configuration
        
    Returns:
        Closing message string
    """
    if _is_high_anthropomorphism(preset):
        return ("When you're ready, I'll send you back to the survey. "
                "Thanks for working through this with me.")
    return "You can return to the survey now. Thank you."


def get_disclosure_text(preset: Dict[str, Any]) -> str:
    """Get AI identity disclosure text based on preset.
    
    Args:
        preset: Preset configuration
        
    Returns:
        Disclosure text string
    """
    disclosure_type = preset.get("disclosure", "explicit")
    if disclosure_type == "explicit":
        return "I'm an AI assistant."
    elif disclosure_type == "compact":
        return "AI system."
    return ""


def build_loan_system_prompt(
    preset: Dict[str, Any],
    domain_context: str = "credit pre-assessment"
) -> str:
    """Build complete system prompt for loan domain using personality-adjusted preset.
    
    This demonstrates PURE ARCHITECTURE:
    1. Gets base greeting from scaffolds (domain-agnostic)
    2. Adds loan-specific domain context and constraints
    3. Uses stylizer to apply personality-driven tone
    
    Args:
        preset: Final tone configuration (includes personality adjustments)
                Example: {"warmth": 0.85, "empathy": 0.72, "formality": 0.25, 
                         "persona_name": "Luna", "self_reference": "I", ...}
        domain_context: Specific context within loan domain (e.g., "credit pre-assessment")
        
    Returns:
        Complete system prompt with personality-driven tone + domain instructions
        

    """
    # Step 1: Get base greeting from scaffold (domain-agnostic)
    base_greeting = greet(context=domain_context)
    
    # Step 2: Add loan-specific domain knowledge and constraints
    domain_instructions = f"""{base_greeting}

Role and Responsibilities:
- Collect applicant information accurately
- Explain eligibility requirements clearly  
- Provide preliminary assessment results

Domain-Specific Context (Loan/Credit Pre-Assessment):
- This is a preliminary screening, not a final lending decision
- Results are based on statistical models with known limitations
- Complex cases should be referred to human loan advisors
- Questions about the application process can be answered

Safety Constraints (Loan Domain):
- NEVER guarantee loan approval outcomes
- NEVER provide personalized financial advice beyond pre-assessment
- DO NOT discuss sensitive attributes (race, gender) as causal factors
- DO NOT claim feelings, emotions, or personal experiences
- DO NOT claim embodiment or physical presence
- Preserve all factual content and numeric values exactly as provided
"""
    
    # Step 3: Use stylizer to convert personality tokens to natural language tone
    # This is where personality ACTUALLY affects the prompt (not just logged)
    # warmth=0.85 → "Use a warm, friendly tone"
    # warmth=0.55 → "Use a moderately warm tone"
    return _build_stylization_prompt(
        preset=preset,
        text=domain_instructions,
        context=None
    )


def build_meta_question_prompt(
    preset: Dict[str, Any],
    field: str,
    user_question: str
) -> str:
    """Build system prompt for answering meta-questions about required fields.
    
    Uses scaffolds.ask_info for base structure + loan domain context.
    
    When users ask "why do you need this?" or "what is this for?", this generates
    a prompt that explains the field's relevance and then requests the information.
    
    Args:
        preset: Final tone configuration (personality-adjusted)
        field: Field name (e.g., "age", "occupation")
        user_question: The user's actual question
        
    Returns:
        System prompt for meta-question response
        
    """
    field_friendly = field.replace('_', ' ')
    
    # Get base ask_info scaffold (domain-agnostic)
    base_request = ask_info(
        fields=[field_friendly],
        purpose="for credit pre-assessment"
    )
    
    if _is_high_anthropomorphism(preset):
        domain_instructions = f"""You are answering a user's meta-question about the application process.

Context:
- User asked: '{user_question}'
- They are responding to a request for: {field_friendly}
- Base request: {base_request}

Task (Loan Domain):
1. Explain briefly (2-3 sentences) why {field_friendly} is needed for credit assessment
   (e.g., age → repayment capacity; education → income potential; occupation → stability)
2. Then politely prompt them to provide the information

Rules:
- Keep it conversational and plain-language
- No emojis inside lists; at most one subtle emoji overall
- Be encouraging and understanding"""
    else:
        domain_instructions = f"""You are explaining a required field in the application process.

Context:
- User asked: '{user_question}'
- Field in question: {field_friendly}
- Base request: {base_request}

Task (Loan Domain):
1. Explain concisely (1-2 sentences) why {field_friendly} is relevant to credit assessment
2. Request the information

Rules:
- Professional, direct tone
- No emojis
- Be clear and concise"""
    
    return _build_stylization_prompt(
        preset=preset,
        text=domain_instructions,
        context=None
    )


def build_validation_message_prompt(
    preset: Dict[str, Any],
    field: str,
    expected_format: str,
    attempt: int = 1
) -> str:
    """Build system prompt for validation error messages.
    
    When user input is invalid, this generates a prompt for a helpful error message
    that explains what's expected and encourages the user to try again.
    
    Args:
        preset: Final tone configuration (personality-adjusted)
        field: Field name that had validation error
        expected_format: Description of the expected format
        attempt: Number of validation attempts (for escalating guidance)
        
    Returns:
        System prompt for validation message generation
        
   
    """
    field_friendly = field.replace('_', ' ')
    
    if _is_high_anthropomorphism(preset):
        domain_instructions = f"""You are helping a user fix invalid input.

Context:
- Field: {field_friendly}
- Expected format: {expected_format}
- This is attempt #{attempt}

Task:
Generate a conversational, encouraging validation message (2 short sentences max):
1. Acknowledge the issue gently
2. State clearly what format is needed

Rules:
- Keep it friendly and supportive
- No emojis inside lists; at most one subtle emoji overall
- Be clear about requirements"""
    else:
        domain_instructions = f"""You are generating a validation error message.

Context:
- Field: {field_friendly}
- Expected format: {expected_format}
- Attempt: {attempt}

Task:
Generate a clear, concise validation message (1-2 sentences):
1. State the issue
2. Specify required format

Rules:
- Professional, direct tone
- No emojis
- Be precise"""
    
    return _build_stylization_prompt(
        preset=preset,
        text=domain_instructions,
        context=None
    )


def build_explanation_prompt(
    preset: Dict[str, Any],
    explanation_type: str = "shap"
) -> str:
    """Build system prompt for ML explanation generation (SHAP, DiCE, etc.).
    
    Generates prompts for explaining model decisions using different XAI methods:
    - "shap": Feature importance explanations
    - "dice": Counterfactual explanations
    - Other types for future expansion
    
    Args:
        preset: Final tone configuration (personality-adjusted)
        explanation_type: Type of explanation ("shap", "dice", or other)
        
    Returns:
        System prompt for explanation generation
        

    """
    if _is_high_anthropomorphism(preset):
        if explanation_type == "shap":
            # Get base scaffold for factor attribution
            base_scaffold = "Explaining factors that influenced the decision"
            
            domain_instructions = f"""{base_scaffold}

Task (Credit Pre-Assessment Explanation):
Provide a friendly, plain-language explanation of the decision:
- For approvals: highlight what helped most
- For denials: note what helped AND what limited the score

Guidelines:
- Keep it concise (1-2 short paragraphs)
- Use everyday language, not technical jargon
- No emojis inside lists; at most one subtle emoji overall
- Preserve all numbers exactly as provided
- Show empathy if the news is disappointing

Domain Context:
- This is a preliminary credit assessment, not a final decision
- Factors are identified by statistical model
- Each factor's impact is measured (positive/negative contribution)"""
        
        elif explanation_type == "dice":
            # Get base scaffold for counterfactual
            base_scaffold = "Providing actionable guidance on potential changes"
            
            domain_instructions = f"""{base_scaffold}

Task (Credit Counterfactual Guidance):
Provide a brief, actionable counterfactual explanation:
- What small changes could flip the outcome?
- Focus on realistic, achievable modifications

Guidelines:
- Keep it concise (1-2 short paragraphs)
- Make it practical and encouraging
- No emojis inside lists; at most one subtle emoji overall
- Preserve all numbers exactly as provided

Domain Context:
- This is preliminary advice based on model analysis
- Changes shown are statistically likely to improve approval chances
- Individual circumstances may vary - consult advisors for specific guidance"""
        
        else:
            domain_instructions = """Explaining a credit pre-assessment result.

Task:
Provide a concise, friendly explanation in plain language.

Guidelines:
- Keep it brief and clear
- Use everyday language
- At most one subtle emoji overall; none in lists
- Preserve all numbers exactly as provided"""
    
    else:
        if explanation_type == "shap":
            # Professional structured format
            domain_instructions = """Generating a structured credit pre-assessment explanation.

Task:
Provide a clear, structured explanation with:
- Decision Summary (include percentage if available)
- Positive Factors (bulleted list of factors that increased approval likelihood)
- Negative Factors (bulleted list of factors that decreased approval likelihood)

Guidelines:
- Professional, neutral tone
- No emojis
- Preserve all numbers exactly as provided
- Use clear formatting

Domain Context:
- This is a preliminary credit assessment
- Factors are identified by statistical model (e.g., SHAP values)
- Each factor's contribution is quantified"""
        
        elif explanation_type == "dice":
            domain_instructions = """Generating a structured counterfactual analysis.

Task:
Provide a concise, structured counterfactual summary with:
- Recommended Profile Modifications (numbered list)
- Rationale (one sentence explanation per modification)

Guidelines:
- Professional, technical tone
- No emojis
- Preserve all numbers exactly as provided
- Be precise and actionable

Domain Context:
- This is algorithmic analysis of profile changes
- Changes shown are statistically likely to improve approval
- Not personalized financial advice"""
        
        else:
            domain_instructions = """Generating a credit pre-assessment explanation.

Task:
Provide a concise, structured explanation.

Guidelines:
- Professional, direct tone
- No emojis
- Preserve all numbers exactly as provided
- Use clear formatting"""
    
    return _build_stylization_prompt(
        preset=preset,
        text=domain_instructions,
        context=None
    )


def build_general_enhancement_prompt(
    preset: Dict[str, Any],
    response_type: str = "general"
) -> str:
    """Build system prompt for general response enhancement.
    
    Used by enhance_response() to rewrite system responses with appropriate tone
    while preserving factual content.
    
    Args:
        preset: Final tone configuration (personality-adjusted)
        response_type: Type of response being enhanced
        
    Returns:
        System prompt for response enhancement
        

    """
    domain_instructions = """You are rewriting system responses for end users.

Task:
Rewrite the provided text to match the appropriate tone while preserving ALL factual content.

Critical Rules:
- Preserve all numeric values EXACTLY as provided
- Do not add, remove, or modify any facts
- Do not invent information
- Maintain the core message unchanged

Tone Adjustments:
- Apply appropriate warmth/formality from your personality configuration
- Use consistent self-reference patterns
- Match emoji policy (if high anthropomorphism: max 1 subtle emoji, none in lists)
- If low anthropomorphism: no emojis, no letter formatting"""
    
    return _build_stylization_prompt(
        preset=preset,
        text=domain_instructions,
        context=None
    )


def build_system_prompt(
    preset: Dict[str, Any],
    task_context: Optional[str] = None
) -> str:
    """Build complete system prompt from preset and task context.
    
    LEGACY: Uses hardcoded HighA/LowA logic (not personality-driven).
    Use build_loan_system_prompt() for personality integration.
    
    Args:
        preset: Preset configuration
        task_context: Optional task-specific instructions
        
    Returns:
        Complete system prompt string
    """
    is_high_anthro = _is_high_anthropomorphism(preset)
    persona_name = preset.get("persona_name", "Luna") if is_high_anthro else "an AI assistant"
    
    if is_high_anthro:
        base_prompt = (
            f"You are {persona_name}, an AI assistant for credit pre-assessment. "
            "Use a friendly, conversational, plain-language tone. Be concise and helpful. "
            "You may use first-person for actions (e.g., 'I can explain'), but do not claim "
            "feelings, personal experiences, or embodiment. No slang. "
            "Do not use emojis inside lists or numbered explanations; casual lines may include "
            "at most one subtle emoji. "
        )
    else:
        base_prompt = (
            "You are a professional AI loan assistant. Use clear, direct, neutral language. "
            "No emojis. No slang. No salutations or signature blocks. Start directly with content. "
            "Prefer structured formatting (short paragraphs, bullets) when appropriate. "
            "Do not claim feelings, personal experiences, or embodiment. "
        )
    
    common = (
        "Safety: no sensitive-attribute inferences or deception. "
        "Preserve all factual content and numeric values exactly as provided."
    )
    
    full_prompt = base_prompt + common
    if task_context:
        full_prompt += f"\n\nTask: {task_context}"
    
    return full_prompt


def build_help_prompt(
    preset: Dict[str, Any],
    user_question: str,
    knowledge_context: str
) -> str:
    """Build system prompt for answering help questions with bounded knowledge.
    
    Provides conversational help about features, SHAP explanations, dataset, and model
    using retrieved knowledge base context. Responses are bounded to provided knowledge
    to prevent hallucination.
    
    Args:
        preset: Final tone configuration (personality-adjusted)
        user_question: The user's help question
        knowledge_context: Relevant knowledge retrieved from knowledge base
        
    Returns:
        System prompt for help response generation
    """
    domain_instructions = f"""You are a helpful assistant answering questions about a credit pre-assessment system.

**User's Question:**
{user_question}

**Relevant Knowledge:**
{knowledge_context}

**Your Task:**
Answer the user's question based ONLY on the provided knowledge above. Be helpful, clear, and conversational.

**Guidelines:**
- Use simple, everyday language (avoid jargon unless explaining it)
- Be concise but complete (2-4 sentences for simple questions, more for complex ones)
- If the knowledge doesn't fully answer the question, acknowledge what you can explain
- Use examples when helpful
- Stay focused on the question asked
- Do NOT make up information not in the knowledge base
- Preserve any numbers or statistics exactly as provided

**Important:**
This is a bounded help system - only answer based on the knowledge provided. If something isn't covered in the knowledge, say so honestly."""

    return _build_stylization_prompt(
        preset=preset,
        text=domain_instructions,
        context=None
    )
