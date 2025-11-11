"""
AI Analysis router - LLM-powered analysis using GROQ
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.logger import get_logger
from core.config import settings
import os

logger = get_logger("ai_analysis")
router = APIRouter()

# Try to import GROQ client
try:
    from groq import Groq
    GROQ_AVAILABLE = bool(settings.GROQ_API_KEY)
    if GROQ_AVAILABLE:
        groq_client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("GROQ client initialized successfully")
    else:
        logger.warning("GROQ API key not found")
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("GROQ library not installed")
except Exception as e:
    GROQ_AVAILABLE = False
    logger.error(f"Error initializing GROQ: {e}")


class AnalysisRequest(BaseModel):
    """AI analysis request"""
    query: str
    context: dict = {}


class AnalysisResponse(BaseModel):
    """AI analysis response"""
    query: str
    analysis: str
    model_used: str
    timestamp: datetime


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_metrics(request: AnalysisRequest):
    """
    Analyze metrics using AI (GROQ)
    Provides intelligent insights about system performance
    """
    logger.info(f"Analyzing: {request.query}")
    
    if not GROQ_AVAILABLE:
        return AnalysisResponse(
            query=request.query,
            analysis="AI analysis is currently unavailable. Please configure GROQ API key.",
            model_used="none",
            timestamp=datetime.utcnow()
        )
    
    try:
        # Build context-aware prompt
        context_str = ""
        if request.context:
            context_str = f"\n\nCurrent system metrics:\n"
            for key, value in request.context.items():
                context_str += f"- {key}: {value}\n"
        
        system_prompt = """You are an expert system administrator and DevOps engineer specializing in system performance analysis.
Analyze the given metrics and provide:
1. Current status assessment
2. Potential issues or concerns
3. Actionable recommendations
4. Predictions for near-future performance

Be concise, technical, and actionable. Focus on practical insights."""
        
        user_prompt = f"{request.query}{context_str}"
        
        # Call GROQ API
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=settings.GROQ_MODEL,
            temperature=0.7,
            max_tokens=500
        )
        
        analysis = chat_completion.choices[0].message.content
        
        logger.info(f"AI analysis completed successfully")
        
        return AnalysisResponse(
            query=request.query,
            analysis=analysis,
            model_used=settings.GROQ_MODEL,
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        return AnalysisResponse(
            query=request.query,
            analysis=f"Error generating analysis: {str(e)}",
            model_used="error",
            timestamp=datetime.utcnow()
        )


@router.post("/anomaly-explanation")
async def explain_anomaly(
    metric_name: str,
    value: float,
    mean: float,
    threshold: float
):
    """Get AI explanation of anomaly"""
    logger.info(f"Explaining anomaly for {metric_name}")
    
    if not GROQ_AVAILABLE:
        return {
            "metric_name": metric_name,
            "explanation": "AI explanation unavailable - GROQ API not configured",
            "possible_causes": ["API key not set"],
            "recommended_actions": ["Configure GROQ_API_KEY environment variable"]
        }
    
    try:
        prompt = f"""Analyze this system metric anomaly:

Metric: {metric_name}
Current Value: {value}%
Historical Average: {mean}%
Alert Threshold: {threshold}%

Provide:
1. Brief explanation of why this is anomalous
2. 3-4 possible root causes
3. 3-4 recommended actions to investigate/resolve

Be concise and technical."""

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a system performance expert providing concise anomaly analysis."},
                {"role": "user", "content": prompt}
            ],
            model=settings.GROQ_MODEL,
            temperature=0.7,
            max_tokens=300
        )
        
        explanation = chat_completion.choices[0].message.content
        
        return {
            "metric_name": metric_name,
            "explanation": explanation,
            "value": value,
            "mean": mean,
            "threshold": threshold,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error explaining anomaly: {e}")
        return {
            "metric_name": metric_name,
            "explanation": f"Error: {str(e)}",
            "possible_causes": ["API error"],
            "recommended_actions": ["Check logs"]
        }


@router.post("/incident-summary")
async def generate_incident_summary(incident_id: str):
    """Generate AI summary of incident (placeholder)"""
    logger.info(f"Generating summary for incident: {incident_id}")
    
    return {
        "incident_id": incident_id,
        "summary": "AI-generated incident summary",
        "recommendations": [],
        "timestamp": datetime.utcnow()
    }


@router.get("/models")
async def list_available_models():
    """List available AI models"""
    return {
        "groq": {
            "status": "available" if GROQ_AVAILABLE else "unavailable",
            "model": settings.GROQ_MODEL if GROQ_AVAILABLE else "not configured",
            "api_key_set": bool(settings.GROQ_API_KEY)
        },
        "timestamp": datetime.utcnow().isoformat()
    }

