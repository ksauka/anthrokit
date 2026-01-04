"""Pydantic schemas for AnthroKit API.

Request/response models for the AnthroKit REST API service.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class StylizeRequest(BaseModel):
    """Request model for text stylization.
    
    Attributes:
        text: Base text to stylize
        preset: Preset name ("HighA" or "LowA")
        context: Optional context dictionary
        use_llm: Whether to attempt LLM stylization
        model: LLM model name
    """
    text: str = Field(..., description="Base text to stylize")
    preset: str = Field("LowA", description="Preset name (HighA or LowA)")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional context for stylization"
    )
    use_llm: bool = Field(
        default=True,
        description="Whether to use LLM stylization"
    )
    model: str = Field(
        default="gpt-4o-mini",
        description="LLM model name"
    )


class StylizeResponse(BaseModel):
    """Response model for text stylization.
    
    Attributes:
        text: Stylized text
        preset: Preset used
        model: Stylization method used
        used_fallback: Whether fallback stylization was used
    """
    text: str = Field(..., description="Stylized text")
    preset: str = Field(..., description="Preset used")
    model: str = Field(..., description="Stylization method (llm or pattern-based)")
    used_fallback: bool = Field(..., description="Whether pattern-based fallback was used")


class ScaffoldRequest(BaseModel):
    """Request model for scaffold generation.
    
    Attributes:
        pattern: Pattern card name
        kwargs: Pattern-specific arguments
    """
    pattern: str = Field(..., description="Pattern card name")
    kwargs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Pattern-specific arguments"
    )


class ScaffoldResponse(BaseModel):
    """Response model for scaffold generation.
    
    Attributes:
        pattern: Pattern card used
        text: Base scaffold text
    """
    pattern: str = Field(..., description="Pattern card used")
    text: str = Field(..., description="Base scaffold text")


class ValidateRequest(BaseModel):
    """Request model for text validation.
    
    Attributes:
        text: Text to validate
        preset: Preset to validate against
    """
    text: str = Field(..., description="Text to validate")
    preset: str = Field("LowA", description="Preset for validation rules")


class ValidateResponse(BaseModel):
    """Response model for text validation.
    
    Attributes:
        valid: Whether text passed all validations
        violations: List of guardrail violations
        emoji_count: Number of emojis found
        cleaned_text: Post-processed text
    """
    valid: bool = Field(..., description="Whether text passed all validations")
    violations: List[str] = Field(
        default_factory=list,
        description="List of guardrail violations"
    )
    emoji_count: int = Field(..., description="Number of emojis in text")
    cleaned_text: str = Field(..., description="Post-processed text")


class HealthResponse(BaseModel):
    """Health check response.
    
    Attributes:
        status: Service status
        version: AnthroKit version
        llm_available: Whether LLM client is available
    """
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="AnthroKit version")
    llm_available: bool = Field(..., description="Whether LLM client is available")


__all__ = [
    "StylizeRequest",
    "StylizeResponse",
    "ScaffoldRequest",
    "ScaffoldResponse",
    "ValidateRequest",
    "ValidateResponse",
    "HealthResponse",
]
