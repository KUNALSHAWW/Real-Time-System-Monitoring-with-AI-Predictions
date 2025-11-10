"""
LLM Integration Manager
Supports GROQ API, Ollama local models, and Hugging Face transformers
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import aiohttp
import requests
from transformers import pipeline
import logging

logger = logging.getLogger(__name__)


class LLMManager:
    """
    Unified LLM interface supporting multiple model providers
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.groq_client = None
        self.ollama_session = None
        self.hf_pipeline = None
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize all LLM models"""
        try:
            # Initialize GROQ
            if self.config.get("GROQ_API_KEY"):
                from groq import Groq
                self.groq_client = Groq(api_key=self.config["GROQ_API_KEY"])
                logger.info("✅ GROQ client initialized")
        except Exception as e:
            logger.warning(f"⚠️  GROQ initialization failed: {str(e)}")
        
        try:
            # Initialize Ollama session
            self.ollama_session = requests.Session()
            logger.info("✅ Ollama session initialized")
        except Exception as e:
            logger.warning(f"⚠️  Ollama initialization failed: {str(e)}")
        
        try:
            # Initialize Hugging Face pipeline
            self.hf_pipeline = pipeline(
                "text-classification",
                model=self.config.get("HF_MODEL_NAME", "distilbert-base-uncased"),
                device=self.config.get("HF_MODEL_DEVICE", "cpu")
            )
            logger.info("✅ Hugging Face pipeline initialized")
        except Exception as e:
            logger.warning(f"⚠️  HuggingFace initialization failed: {str(e)}")
    
    async def analyze_with_groq(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Analyze using GROQ API
        High-speed inference with Mixtral and Llama models
        """
        if not self.groq_client:
            raise RuntimeError("GROQ client not initialized")
        
        try:
            message = self.groq_client.messages.create(
                model=self.config.get("GROQ_MODEL", "llama2-70b-4096"),
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": "You are an expert system administrator analyzing infrastructure monitoring data."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
        
        except Exception as e:
            logger.error(f"GROQ analysis error: {str(e)}")
            raise
    
    async def analyze_with_ollama(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Analyze using local Ollama model
        Requires Ollama running locally on http://localhost:11434
        """
        if not self.ollama_session:
            raise RuntimeError("Ollama session not initialized")
        
        model = model or self.config.get("OLLAMA_MODEL", "llama2")
        base_url = self.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
        
        try:
            response = self.ollama_session.post(
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                raise Exception(f"Ollama error: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Ollama analysis error: {str(e)}")
            raise
    
    async def classify_with_huggingface(self, text: str) -> Dict[str, Any]:
        """
        Classify text using Hugging Face transformer
        Useful for sentiment analysis and metric interpretation
        """
        if not self.hf_pipeline:
            raise RuntimeError("Hugging Face pipeline not initialized")
        
        try:
            result = self.hf_pipeline(text)
            return {
                "text": text,
                "classification": result[0]["label"],
                "confidence": result[0]["score"]
            }
        except Exception as e:
            logger.error(f"HuggingFace classification error: {str(e)}")
            raise
    
    async def smart_analyze(
        self,
        prompt: str,
        method: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Intelligent routing between different LLM providers
        
        Parameters:
        - prompt: Analysis prompt
        - method: "auto" (choose best), "groq", "ollama", "huggingface"
        """
        
        if method == "auto":
            # Use GROQ by default (fastest), fallback to Ollama
            if self.groq_client:
                method = "groq"
            elif self.ollama_session:
                method = "ollama"
            else:
                raise RuntimeError("No LLM provider available")
        
        try:
            if method == "groq":
                analysis = await self.analyze_with_groq(prompt, **kwargs)
                return {
                    "method": "groq",
                    "analysis": analysis,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            elif method == "ollama":
                analysis = await self.analyze_with_ollama(prompt, **kwargs)
                return {
                    "method": "ollama",
                    "analysis": analysis,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            elif method == "huggingface":
                analysis = await self.classify_with_huggingface(prompt)
                return {
                    "method": "huggingface",
                    "analysis": analysis,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            else:
                raise ValueError(f"Unknown method: {method}")
        
        except Exception as e:
            logger.error(f"Smart analyze error: {str(e)}")
            raise
    
    async def batch_analyze(
        self,
        prompts: list,
        method: str = "auto"
    ) -> list:
        """Analyze multiple prompts concurrently"""
        
        tasks = [
            self.smart_analyze(prompt, method)
            for prompt in prompts
        ]
        
        return await asyncio.gather(*tasks)


# Global LLM manager instance
_llm_manager: Optional[LLMManager] = None


def get_llm_manager(config: Optional[Dict[str, Any]] = None) -> LLMManager:
    """Get or create global LLM manager"""
    global _llm_manager
    
    if _llm_manager is None:
        if config is None:
            from core.config import settings
            config = {
                "GROQ_API_KEY": settings.GROQ_API_KEY,
                "GROQ_MODEL": settings.GROQ_MODEL,
                "OLLAMA_BASE_URL": settings.OLLAMA_BASE_URL,
                "OLLAMA_MODEL": settings.OLLAMA_MODEL,
                "HF_MODEL_NAME": settings.HF_MODEL_NAME,
                "HF_MODEL_DEVICE": settings.HF_MODEL_DEVICE,
                "HUGGINGFACE_API_TOKEN": settings.HUGGINGFACE_API_TOKEN
            }
        
        _llm_manager = LLMManager(config)
    
    return _llm_manager
