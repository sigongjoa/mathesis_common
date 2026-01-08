from abc import ABC, abstractmethod
from typing import List, Dict, Optional, AsyncIterator, Any
import asyncio
from pathlib import Path
import base64
import json

class LLMClient(ABC):
    """Common interface for all LLM providers"""

    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """Chat completion"""
        pass

    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Simple text generation"""
        pass

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Text embedding"""
        pass

    @abstractmethod
    def analyze_image(self, image_path: str, prompt: str) -> str:
        """Image analysis (VLM)"""
        pass

    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Streaming response"""
        pass

class OllamaClient(LLMClient):
    """Integrated Ollama client supporting both sync and async modes"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
        async_mode: bool = False,
        timeout: int = 120,
        retry_config: Optional[Dict] = None,
        **kwargs
    ):
        self.base_url = base_url
        self.model = model
        self.async_mode = async_mode
        self.timeout = timeout
        self.retry_config = retry_config or {"max_attempts": 3, "backoff": 1.0}
        self.default_options = kwargs

        if async_mode:
            import httpx
            self.client = httpx.AsyncClient(timeout=timeout)
        else:
            import ollama
            self.client = ollama.Client(host=base_url)

    def chat(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        format: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        if self.async_mode:
            raise RuntimeError("Use async_chat() in async mode")

        options = self.default_options.copy()
        if temperature is not None:
            options["temperature"] = temperature
        options.update(kwargs.get("options", {}))
        
        # Merge other top-level kwargs into options if they belong there
        # but for ollama-python client, 'options' is a specific dict
        
        response = self.client.chat(
            model=model or self.model,
            messages=messages,
            format=format,
            options=options,
            **{k: v for k, v in kwargs.items() if k != "options"}
        )
        return response['message']['content']

    async def async_chat(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        format: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        options = self.default_options.copy()
        if temperature is not None:
            options["temperature"] = temperature
        # payload for async (REST) expect options at root? No, usually in options dict
        
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
            "options": options,
            **kwargs
        }
        if format:
            payload["format"] = format

        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return result.get("message", {}).get("content", "")

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        format: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        return self.chat(messages, model=model, format=format, temperature=temperature, **kwargs)

    def embed(self, text: str, model: str = "nomic-embed-text:latest") -> List[float]:
        if self.async_mode:
            raise RuntimeError("Use async_embed() in async mode")

        import ollama
        response = ollama.embeddings(model=model, prompt=text)
        return response['embedding']

    async def async_embed(self, text: str, model: str = "nomic-embed-text:latest") -> List[float]:
        response = await self.client.post(
            f"{self.base_url}/api/embeddings",
            json={"model": model, "prompt": text}
        )
        response.raise_for_status()
        return response.json()['embedding']

    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        model: str = "llama3.2-vision:11b"
    ) -> str:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        messages = [
            {
                "role": "user",
                "content": prompt,
                "images": [image_data]
            }
        ]

        return self.chat(messages, model=model)

    async def stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        if not self.async_mode:
            raise RuntimeError("Streaming requires async mode")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": True,
            **kwargs
        }

        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "message" in data:
                        yield data["message"].get("content", "")

    def health_check(self) -> bool:
        try:
            if self.async_mode:
                return asyncio.run(self._async_health_check())
            else:
                import ollama
                ollama.list()
                return True
        except Exception:
            return False

    async def _async_health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

def create_ollama_client(
    base_url: str = "http://localhost:11434",
    model: str = "llama3.1:8b",
    async_mode: bool = False,
    **kwargs
) -> OllamaClient:
    return OllamaClient(base_url, model, async_mode, **kwargs)
