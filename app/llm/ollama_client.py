"""Local LLM integration."""
from __future__ import annotations

from dataclasses import dataclass

import requests


class OllamaGenerationError(RuntimeError):
    """Raised when Ollama cannot produce a response safely."""


@dataclass(frozen=True)
class OllamaGenerationOptions:
    """CPU-safe default generation options for local Ollama models."""

    temperature: float = 0.2
    top_p: float = 0.9
    num_predict: int = 350
    num_ctx: int = 2048
    keep_alive: str = "1m"


class OllamaClient:
    """Minimal Ollama client for local Gemma analysis.

    The defaults are intentionally conservative for CPU-only laptops. Without an
    output cap, a local model can run for a long time and make the machine hot.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: int = 60,
        options: OllamaGenerationOptions | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.options = options or OllamaGenerationOptions()

    def healthcheck(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            return response.ok
        except requests.RequestException:
            return False

    def generate(self, prompt: str) -> str:
        """Generate one CPU-safe explanation from Ollama.

        This intentionally does not retry generation. If the local machine times
        out once, retrying usually heats the CPU further and makes the UX worse.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.options.keep_alive,
            "options": {
                "temperature": self.options.temperature,
                "top_p": self.options.top_p,
                "num_predict": self.options.num_predict,
                "num_ctx": self.options.num_ctx,
            },
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise OllamaGenerationError(
                "Gemma timed out. Try a smaller model such as gemma3:1b, reduce "
                "OLLAMA_NUM_PREDICT, or run without --use-gemma."
            ) from exc
        except requests.RequestException as exc:
            raise OllamaGenerationError(f"Ollama generation failed: {exc}") from exc

        return response.json().get("response", "").strip()

    def unload_model(self) -> bool:
        """Ask Ollama to unload this model from memory."""
        payload = {"model": self.model, "prompt": "", "keep_alive": 0}
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=15,
            )
            return response.ok
        except requests.RequestException:
            return False
