"""LLM providers for text generation."""
import logging
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from openai import OpenAI, AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Returns:
            Dict with keys: answer, model, tokens_prompt, tokens_completion, latency_ms
        """
        pass
    
    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens in text using tiktoken."""
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Failed to count tokens: {e}, using approximation")
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider supporting both OpenAI and Azure."""
    
    def __init__(self):
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        
        if settings.llm_provider == "azure":
            logger.info(f"Initializing Azure OpenAI provider with deployment: {settings.azure_openai_deployment}")
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
            self.model = settings.azure_openai_deployment
        else:
            logger.info(f"Initializing OpenAI provider with model: {self.model}")
            self.client = OpenAI(api_key=settings.openai_api_key)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a response using OpenAI/Azure."""
        start_time = time.time()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            answer = response.choices[0].message.content
            tokens_prompt = response.usage.prompt_tokens if response.usage else 0
            tokens_completion = response.usage.completion_tokens if response.usage else 0
            
            return {
                "answer": answer,
                "model": self.model,
                "tokens_prompt": tokens_prompt,
                "tokens_completion": tokens_completion,
                "latency_ms": latency_ms
            }
        
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise


class DummyProvider(LLMProvider):
    """Dummy provider for testing without API keys."""
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a dummy response."""
        answer = "Esta é uma resposta de teste. O provider real não está configurado."
        
        return {
            "answer": answer,
            "model": "dummy",
            "tokens_prompt": self.count_tokens(prompt),
            "tokens_completion": self.count_tokens(answer),
            "latency_ms": 100
        }


def get_llm_provider() -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    if not settings.openai_api_key and not settings.azure_openai_api_key:
        logger.warning("No API keys configured, using DummyProvider")
        return DummyProvider()
    
    return OpenAIProvider()


