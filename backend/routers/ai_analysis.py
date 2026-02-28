"""
AI Analysis Router - Real Groq LLM Integration
Production-ready for Hugging Face Spaces deployment
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psutil

# ============================================================================
# GROQ CLIENT INITIALIZATION
# ============================================================================

# Initialize Groq client from environment variable
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = None
GROQ_AVAILABLE = False

try:
    from groq import Groq
    if GROQ_API_KEY and GROQ_API_KEY.strip():
        groq_client = Groq(api_key=GROQ_API_KEY)
        GROQ_AVAILABLE = True
        print("✅ GROQ client initialized successfully")
    else:
        print("⚠️ GROQ_API_KEY not set or empty")
except ImportError:
    print("⚠️ groq library not installed - run: pip install groq")
except Exception as e:
    print(f"❌ Error initializing GROQ: {e}")

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter()

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request model for AI analysis"""
    query: str
    context: Optional[Dict[str, Any]] = None
    include_current_metrics: bool = True


class AnalyzeResponse(BaseModel):
    """Response model for AI analysis"""
    query: str
    analysis: str
    model_used: str
    timestamp: str
    metrics_included: bool = False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_system_metrics() -> Dict[str, Any]:
    """Fetch current system metrics using psutil"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_percent": round(disk.percent, 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "process_count": len(psutil.pids())
        }
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return {}


# ============================================================================
# MAIN ENDPOINT - /api/ai/analyze
# ============================================================================

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_with_ai(request: AnalyzeRequest):
    """
    Analyze system metrics using Groq AI (Llama 3)
    
    - Accepts a query string
    - Automatically includes current system metrics
    - Returns AI-powered analysis
    """
    
    # Check if GROQ is available
    if not GROQ_AVAILABLE or groq_client is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "GROQ_API_KEY_MISSING",
                "message": "AI analysis unavailable. GROQ_API_KEY environment variable is not set.",
                "solution": "Add GROQ_API_KEY to your Hugging Face Space secrets."
            }
        )
    
    try:
        # Build context with current system metrics
        context_str = ""
        metrics_included = False
        
        if request.include_current_metrics:
            metrics = get_current_system_metrics()
            if metrics:
                context_str = f"""

CURRENT SYSTEM METRICS (Real-time):
- CPU Usage: {metrics.get('cpu_percent', 'N/A')}%
- Memory Usage: {metrics.get('memory_percent', 'N/A')}% ({metrics.get('memory_used_gb', 'N/A')} GB / {metrics.get('memory_total_gb', 'N/A')} GB)
- Disk Usage: {metrics.get('disk_percent', 'N/A')}% ({metrics.get('disk_used_gb', 'N/A')} GB / {metrics.get('disk_total_gb', 'N/A')} GB)
- Active Processes: {metrics.get('process_count', 'N/A')}
"""
                metrics_included = True
        
        # Add user-provided context if any
        if request.context:
            context_str += "\nADDITIONAL CONTEXT:\n"
            for key, value in request.context.items():
                context_str += f"- {key}: {value}\n"
        
        # System prompt for the AI
        system_prompt = """You are an expert system administrator and DevOps engineer. 
Analyze the following system query strictly and concisely.
Provide actionable insights based on the metrics provided.
Keep your response under 200 words and use clear formatting."""
        
        # User prompt with query and context
        user_prompt = f"USER QUERY: {request.query}{context_str}"
        
        # Call Groq API
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",  # Fast and reliable model
            temperature=0.7,
            max_tokens=500
        )
        
        # Extract response
        ai_response = chat_completion.choices[0].message.content
        
        return AnalyzeResponse(
            query=request.query,
            analysis=ai_response,
            model_used="llama-3.1-8b-instant",
            timestamp=datetime.utcnow().isoformat(),
            metrics_included=metrics_included
        )
    
    except Exception as e:
        print(f"Error in AI analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ANALYSIS_FAILED",
                "message": f"Failed to generate analysis: {str(e)}",
                "solution": "Check your GROQ_API_KEY and try again."
            }
        )


# ============================================================================
# ADDITIONAL ENDPOINTS
# ============================================================================

@router.get("/models")
async def list_available_models():
    """List available AI models and their status"""
    return {
        "groq": {
            "status": "available" if GROQ_AVAILABLE else "unavailable",
            "model": "llama-3.1-8b-instant",
            "api_key_configured": bool(GROQ_API_KEY)
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/anomaly-explanation")
async def explain_anomaly(
    metric_name: str,
    value: float,
    mean: float,
    threshold: float
):
    """Get AI explanation for a detected anomaly"""
    
    if not GROQ_AVAILABLE or groq_client is None:
        raise HTTPException(
            status_code=503,
            detail="AI unavailable - GROQ_API_KEY not configured"
        )
    
    try:
        prompt = f"""Analyze this system anomaly briefly:

Metric: {metric_name}
Current Value: {value}%
Historical Average: {mean}%
Alert Threshold: {threshold}%

Provide:
1. Why this is anomalous (1 sentence)
2. 3 possible causes
3. 2 recommended actions"""

        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a system monitoring expert. Be concise."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.5,
            max_tokens=300
        )
        
        return {
            "metric_name": metric_name,
            "explanation": response.choices[0].message.content,
            "value": value,
            "threshold": threshold,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

