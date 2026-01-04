"""FastAPI service for AnthroKit.

REST API endpoints for text stylization, scaffold generation, and validation.

Run with:
    uvicorn anthrokit.api.main:app --reload --port 8001

Example:
    curl -X POST "http://localhost:8001/v1/stylize" \\
      -H "Content-Type: application/json" \\
      -d '{"text":"Preliminary result: declined.","preset":"HighA"}'
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from anthrokit import __version__
from anthrokit.api.schemas import (
    StylizeRequest,
    StylizeResponse,
    ScaffoldRequest,
    ScaffoldResponse,
    ValidateRequest,
    ValidateResponse,
    HealthResponse,
)
from anthrokit.stylizer import stylize_text, _get_llm_client
from anthrokit.scaffolds import get_scaffold
from anthrokit.validators import validate_guardrails, limit_emojis, post_process_response
from anthrokit.config import load_preset


# Initialize FastAPI app
app = FastAPI(
    title="AnthroKit API",
    description="Token-based anthropomorphism design system for conversational AI",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "message": "AnthroKit API",
        "version": __version__,
        "docs": "/docs"
    }


@app.get("/healthz", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint.
    
    Returns service status and capabilities.
    """
    llm_available = _get_llm_client() is not None
    
    return HealthResponse(
        status="ok",
        version=__version__,
        llm_available=llm_available
    )


@app.post("/v1/stylize", response_model=StylizeResponse, tags=["Stylization"])
async def stylize(request: StylizeRequest):
    """Stylize text with anthropomorphic tone.
    
    Applies tone modulation based on preset configuration using LLM
    (if available) or pattern-based fallback.
    
    Args:
        request: Stylization request with text and preset
        
    Returns:
        Stylized text response
        
    Raises:
        HTTPException: If preset is invalid
    """
    # Validate preset
    valid_presets = ["HighA", "LowA"]
    if request.preset not in valid_presets:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preset: {request.preset}. Must be one of {valid_presets}"
        )
    
    # Load preset
    try:
        preset = load_preset(request.preset)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load preset: {str(e)}"
        )
    
    # Check if LLM is available
    llm_available = _get_llm_client() is not None
    used_llm = request.use_llm and llm_available
    
    # Stylize text
    try:
        styled_text = stylize_text(
            text=request.text,
            preset=preset,
            context=request.context,
            use_llm=used_llm,
            model=request.model
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Stylization failed: {str(e)}"
        )
    
    return StylizeResponse(
        text=styled_text,
        preset=request.preset,
        model="llm" if used_llm else "pattern-based",
        used_fallback=not used_llm
    )


@app.post("/v1/scaffold", response_model=ScaffoldResponse, tags=["Scaffolds"])
async def generate_scaffold(request: ScaffoldRequest):
    """Generate base content scaffold.
    
    Returns neutral base content for a given pattern card.
    
    Args:
        request: Scaffold request with pattern name and arguments
        
    Returns:
        Base scaffold text
        
    Raises:
        HTTPException: If pattern is invalid
    """
    try:
        text = get_scaffold(request.pattern, **request.kwargs)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scaffold generation failed: {str(e)}"
        )
    
    return ScaffoldResponse(
        pattern=request.pattern,
        text=text
    )


@app.post("/v1/validate", response_model=ValidateResponse, tags=["Validation"])
async def validate_text(request: ValidateRequest):
    """Validate text against anthropomorphism guardrails.
    
    Checks for emoji policy violations, forbidden phrases, and
    returns cleaned text.
    
    Args:
        request: Validation request with text and preset
        
    Returns:
        Validation results with cleaned text
    """
    # Load preset
    try:
        preset = load_preset(request.preset)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load preset: {str(e)}"
        )
    
    # Check guardrails
    violations = validate_guardrails(request.text)
    
    # Count emojis
    import re
    emoji_pattern = re.compile(
        r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U00002600-\U000026FF]"
    )
    emoji_count = len(emoji_pattern.findall(request.text))
    
    # Clean text
    cleaned = post_process_response(request.text, preset)
    
    return ValidateResponse(
        valid=len(violations) == 0,
        violations=violations,
        emoji_count=emoji_count,
        cleaned_text=cleaned
    )


@app.get("/v1/presets", tags=["Configuration"])
async def list_presets():
    """List available presets.
    
    Returns:
        Dictionary of available presets with their configurations
    """
    try:
        high_a = load_preset("HighA")
        low_a = load_preset("LowA")
        
        return {
            "presets": {
                "HighA": high_a,
                "LowA": low_a
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load presets: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
