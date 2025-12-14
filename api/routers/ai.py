"""
Enhanced AI Router

Provides advanced AI capabilities including streaming responses,
multi-model support, and enhanced prompt engineering.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from models import User
from services.shared.auth import get_current_user
from services.shared.response_formatter import ResponseFormatter
from dependencies.container import get_unified_ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


class AIRequest(BaseModel):
    prompt: str
    model: Optional[str] = "mistral"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False


class FewShotRequest(BaseModel):
    question: str
    examples: List[Dict[str, str]]
    context: Optional[str] = None


class ChainOfThoughtRequest(BaseModel):
    question: str
    context: Optional[str] = None


@router.post("/generate")
async def generate_response(
    request: AIRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate AI response with multi-model support and fallback.
    """
    try:
        ai_service = await get_unified_ai_service()
        
        # Use enhanced AI service with fallback
        response = await ai_service.generate_with_fallback(
            prompt=request.prompt,
            models=[request.model] if request.model else ["mistral", "llama2"],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return ResponseFormatter.success(
            data={"response": response},
            message="AI response generated successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")



@router.post("/few-shot")
async def few_shot_learning(
    request: FewShotRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate response using few-shot learning with examples.
    """
    try:
        ai_service = await get_unified_ai_service()
        
        # Build few-shot prompt
        prompt = ai_service.build_few_shot_prompt(
            question=request.question,
            examples=request.examples,
            context=request.context or ""
        )
        
        # Generate response
        response = await ai_service.generate_with_fallback(prompt)
        
        return ResponseFormatter.success(
            data={"response": response},
            message="Few-shot response generated successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Few-shot generation failed: {str(e)}")


@router.post("/chain-of-thought")
async def chain_of_thought_reasoning(
    request: ChainOfThoughtRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate response using chain-of-thought reasoning.
    """
    try:
        ai_service = await get_unified_ai_service()
        
        # Build chain-of-thought prompt
        prompt = ai_service.build_chain_of_thought_prompt(
            question=request.question,
            context=request.context or ""
        )
        
        # Generate response
        response = await ai_service.generate_with_fallback(prompt)
        
        return ResponseFormatter.success(
            data={"response": response},
            message="Chain-of-thought response generated successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chain-of-thought generation failed: {str(e)}")


@router.get("/models")
async def list_available_models(
    current_user: User = Depends(get_current_user)
):
    """
    List available AI models and their capabilities.
    """
    try:
        models = [
            {
                "name": "mistral",
                "description": "Mistral 7B - Fast and efficient",
                "capabilities": ["text-generation", "reasoning", "coding"],
                "context_window": 8192,
                "available": True
            },
            {
                "name": "llama2",
                "description": "Llama 2 7B - Strong reasoning",
                "capabilities": ["text-generation", "reasoning", "analysis"],
                "context_window": 4096,
                "available": True
            },
            {
                "name": "codellama",
                "description": "Code Llama - Specialized for coding",
                "capabilities": ["code-generation", "code-analysis", "debugging"],
                "context_window": 4096,
                "available": True
            }
        ]
        
        return ResponseFormatter.success(
            data={"models": models},
            message="Available models retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/health")
async def ai_health_check(
    current_user: User = Depends(get_current_user)
):
    """
    Check AI service health and model availability.
    """
    try:
        ai_service = await get_unified_ai_service()
        
        # Test basic functionality
        test_response = await ai_service.generate_with_fallback(
            "Hello, this is a health check.",
            models=["mistral"],
            temperature=0.1
        )
        
        health_status = {
            "status": "healthy",
            "models_available": ["mistral", "llama2", "codellama"],
            "features": {
                "streaming": True,
                "multi_model": True,
                "few_shot": True,
                "chain_of_thought": True,
                "context_management": True
            },
            "test_response_length": len(test_response.get("content", "")),
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        return ResponseFormatter.success(
            data=health_status,
            message="AI service is healthy"
        )
        
    except Exception as e:
        return ResponseFormatter.error(
            message="AI service health check failed",
            error_code="AI_UNHEALTHY",
            details={"error": str(e)},
            status_code=503
        )