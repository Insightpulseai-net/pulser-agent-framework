#!/usr/bin/env python3
"""
Unified LLM Client
==================

Abstraction layer for multiple LLM providers (Anthropic, OpenAI, Ollama).
Supports chat, completion, embedding, and tool calls.

Usage:
    from llm_client import LLMClient

    client = LLMClient(provider="anthropic")
    response = client.chat([{"role": "user", "content": "Hello"}])
    embedding = client.embed("Some text to embed")

Environment Variables:
    ANTHROPIC_API_KEY   - Anthropic Claude API key
    OPENAI_API_KEY      - OpenAI API key
    OLLAMA_BASE_URL     - Ollama server URL (default: http://localhost:11434)
    DEFAULT_LLM_PROVIDER - Default provider (anthropic, openai, ollama)
"""

import os
import time
import json
import logging
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Logging
logger = logging.getLogger(__name__)


class Provider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"
    AZURE = "azure"


class RequestType(str, Enum):
    """Types of LLM requests."""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    TOOL_CALL = "tool_call"


@dataclass
class LLMResponse:
    """Standardized response from LLM."""
    text: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0
    cost_usd: float = 0.0
    success: bool = True
    error: Optional[str] = None
    raw_response: Optional[Dict] = None
    tool_calls: Optional[List[Dict]] = None


@dataclass
class EmbeddingResponse:
    """Response from embedding request."""
    embedding: List[float]
    model: str
    provider: str
    dimensions: int = 0
    input_tokens: int = 0
    latency_ms: float = 0
    cost_usd: float = 0.0
    success: bool = True
    error: Optional[str] = None


# Pricing per 1K tokens (approximate, as of 2024)
PRICING = {
    "anthropic": {
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    },
    "openai": {
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "text-embedding-3-large": {"input": 0.00013, "output": 0},
        "text-embedding-3-small": {"input": 0.00002, "output": 0},
    },
    "ollama": {},  # Local, no cost
}


class LLMClient:
    """
    Unified client for multiple LLM providers.

    Supports:
    - Chat completions
    - Text completions
    - Embeddings
    - Tool/function calls
    """

    def __init__(
        self,
        provider: Union[str, Provider] = None,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        **kwargs
    ):
        self.provider = Provider(provider or os.getenv("DEFAULT_LLM_PROVIDER", "openai"))
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.kwargs = kwargs

        self._init_client()

    def _init_client(self):
        """Initialize the provider-specific client."""
        if self.provider == Provider.ANTHROPIC:
            self._init_anthropic()
        elif self.provider == Provider.OPENAI:
            self._init_openai()
        elif self.provider == Provider.OLLAMA:
            self._init_ollama()
        elif self.provider == Provider.AZURE:
            self._init_azure()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _init_anthropic(self):
        """Initialize Anthropic client."""
        try:
            import anthropic
            self.api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = self.model or "claude-3-5-sonnet-20241022"
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            import openai
            self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self.client = openai.OpenAI(api_key=self.api_key)
            self.model = self.model or "gpt-4o-mini"
            self.embedding_model = "text-embedding-3-large"
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def _init_ollama(self):
        """Initialize Ollama client."""
        self.base_url = self.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = self.model or "llama3.2"
        self.embedding_model = self.kwargs.get("embedding_model", "nomic-embed-text")
        self.client = None  # Use requests directly

    def _init_azure(self):
        """Initialize Azure OpenAI client."""
        try:
            import openai
            self.api_key = self.api_key or os.getenv("AZURE_OPENAI_API_KEY")
            self.base_url = self.base_url or os.getenv("AZURE_OPENAI_ENDPOINT")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

            self.client = openai.AzureOpenAI(
                api_key=self.api_key,
                api_version=api_version,
                azure_endpoint=self.base_url,
            )
            self.model = self.model or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage."""
        provider_pricing = PRICING.get(self.provider.value, {})
        model_pricing = provider_pricing.get(model, {"input": 0, "output": 0})

        input_cost = (input_tokens / 1000) * model_pricing.get("input", 0)
        output_cost = (output_tokens / 1000) * model_pricing.get("output", 0)

        return input_cost + output_cost

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tools: List[Dict] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model override
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            tools: Tool definitions for function calling
        """
        model = model or self.model
        start_time = time.time()

        try:
            if self.provider == Provider.ANTHROPIC:
                return self._chat_anthropic(messages, model, max_tokens, temperature, tools, **kwargs)
            elif self.provider in [Provider.OPENAI, Provider.AZURE]:
                return self._chat_openai(messages, model, max_tokens, temperature, tools, **kwargs)
            elif self.provider == Provider.OLLAMA:
                return self._chat_ollama(messages, model, max_tokens, temperature, **kwargs)
            else:
                raise ValueError(f"Chat not supported for provider: {self.provider}")
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return LLMResponse(
                text="",
                model=model,
                provider=self.provider.value,
                success=False,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )

    def _chat_anthropic(
        self, messages, model, max_tokens, temperature, tools, **kwargs
    ) -> LLMResponse:
        """Anthropic chat implementation."""
        start_time = time.time()

        # Extract system message
        system_message = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                chat_messages.append(msg)

        request_kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": chat_messages,
        }

        if system_message:
            request_kwargs["system"] = system_message

        if tools:
            # Convert to Anthropic tool format
            request_kwargs["tools"] = tools

        response = self.client.messages.create(**request_kwargs)

        latency_ms = (time.time() - start_time) * 1000
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # Extract text and tool calls
        text = ""
        tool_calls = []
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text
            elif hasattr(block, "type") and block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input,
                })

        return LLMResponse(
            text=text,
            model=model,
            provider=self.provider.value,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            cost_usd=self._calculate_cost(model, input_tokens, output_tokens),
            tool_calls=tool_calls if tool_calls else None,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else None,
        )

    def _chat_openai(
        self, messages, model, max_tokens, temperature, tools, **kwargs
    ) -> LLMResponse:
        """OpenAI/Azure chat implementation."""
        start_time = time.time()

        request_kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if tools:
            request_kwargs["tools"] = tools

        response = self.client.chat.completions.create(**request_kwargs)

        latency_ms = (time.time() - start_time) * 1000
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        text = response.choices[0].message.content or ""
        tool_calls = None

        if response.choices[0].message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                }
                for tc in response.choices[0].message.tool_calls
            ]

        return LLMResponse(
            text=text,
            model=model,
            provider=self.provider.value,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            cost_usd=self._calculate_cost(model, input_tokens, output_tokens),
            tool_calls=tool_calls,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else None,
        )

    def _chat_ollama(self, messages, model, max_tokens, temperature, **kwargs) -> LLMResponse:
        """Ollama chat implementation."""
        import requests

        start_time = time.time()

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                },
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = (time.time() - start_time) * 1000

        # Ollama doesn't always return token counts
        input_tokens = data.get("prompt_eval_count", 0)
        output_tokens = data.get("eval_count", 0)

        return LLMResponse(
            text=data.get("message", {}).get("content", ""),
            model=model,
            provider=self.provider.value,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            cost_usd=0.0,  # Local, no cost
            raw_response=data,
        )

    def embed(
        self,
        text: Union[str, List[str]],
        model: str = None,
    ) -> Union[EmbeddingResponse, List[EmbeddingResponse]]:
        """
        Generate embeddings for text.

        Args:
            text: Single string or list of strings
            model: Model override
        """
        if self.provider == Provider.ANTHROPIC:
            # Anthropic doesn't have embeddings, fall back to OpenAI
            backup_client = LLMClient(provider="openai")
            return backup_client.embed(text, model)
        elif self.provider in [Provider.OPENAI, Provider.AZURE]:
            return self._embed_openai(text, model)
        elif self.provider == Provider.OLLAMA:
            return self._embed_ollama(text, model)
        else:
            raise ValueError(f"Embeddings not supported for provider: {self.provider}")

    def _embed_openai(
        self, text: Union[str, List[str]], model: str = None
    ) -> Union[EmbeddingResponse, List[EmbeddingResponse]]:
        """OpenAI embedding implementation."""
        model = model or getattr(self, "embedding_model", "text-embedding-3-large")
        start_time = time.time()

        is_single = isinstance(text, str)
        texts = [text] if is_single else text

        response = self.client.embeddings.create(
            model=model,
            input=texts,
        )

        latency_ms = (time.time() - start_time) * 1000
        input_tokens = response.usage.total_tokens

        results = []
        for embedding_data in response.data:
            results.append(EmbeddingResponse(
                embedding=embedding_data.embedding,
                model=model,
                provider=self.provider.value,
                dimensions=len(embedding_data.embedding),
                input_tokens=input_tokens // len(texts),
                latency_ms=latency_ms / len(texts),
                cost_usd=self._calculate_cost(model, input_tokens // len(texts), 0),
            ))

        return results[0] if is_single else results

    def _embed_ollama(
        self, text: Union[str, List[str]], model: str = None
    ) -> Union[EmbeddingResponse, List[EmbeddingResponse]]:
        """Ollama embedding implementation."""
        import requests

        model = model or getattr(self, "embedding_model", "nomic-embed-text")
        start_time = time.time()

        is_single = isinstance(text, str)
        texts = [text] if is_single else text

        results = []
        for t in texts:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": model, "prompt": t},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            results.append(EmbeddingResponse(
                embedding=data["embedding"],
                model=model,
                provider=self.provider.value,
                dimensions=len(data["embedding"]),
                latency_ms=(time.time() - start_time) * 1000 / len(texts),
                cost_usd=0.0,
            ))

        return results[0] if is_single else results


# Convenience functions
def get_client(provider: str = None, **kwargs) -> LLMClient:
    """Get an LLM client for the specified provider."""
    return LLMClient(provider=provider, **kwargs)


def chat(messages: List[Dict], **kwargs) -> LLMResponse:
    """Quick chat completion with default provider."""
    client = get_client()
    return client.chat(messages, **kwargs)


def embed(text: Union[str, List[str]], **kwargs) -> Union[EmbeddingResponse, List[EmbeddingResponse]]:
    """Quick embedding with default provider."""
    client = get_client(provider="openai")  # Default to OpenAI for embeddings
    return client.embed(text, **kwargs)


if __name__ == "__main__":
    # Quick test
    import sys

    print("Testing LLM Client...")

    # Test with OpenAI (if available)
    try:
        client = LLMClient(provider="openai", model="gpt-4o-mini")
        response = client.chat([{"role": "user", "content": "Say 'Hello, World!' and nothing else."}])
        print(f"OpenAI response: {response.text}")
        print(f"Tokens: {response.total_tokens}, Cost: ${response.cost_usd:.6f}")
    except Exception as e:
        print(f"OpenAI test failed: {e}")

    # Test embeddings
    try:
        client = LLMClient(provider="openai")
        embedding = client.embed("This is a test sentence.")
        print(f"Embedding dimensions: {embedding.dimensions}")
    except Exception as e:
        print(f"Embedding test failed: {e}")
