import pytest
import requests

from app.llm.ollama_client import OllamaClient, OllamaGenerationError, OllamaGenerationOptions


class FakeResponse:
    ok = True

    def raise_for_status(self):
        return None

    def json(self):
        return {"response": "safe explanation"}


def test_ollama_client_sends_cpu_safe_options(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    client = OllamaClient(
        base_url="http://localhost:11434/",
        model="gemma3:1b",
        timeout_seconds=45,
        options=OllamaGenerationOptions(num_predict=200, num_ctx=2048, keep_alive="1m"),
    )

    assert client.generate("Explain this report") == "safe explanation"
    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["timeout"] == 45
    assert captured["json"]["model"] == "gemma3:1b"
    assert captured["json"]["stream"] is False
    assert captured["json"]["keep_alive"] == "1m"
    assert captured["json"]["options"]["num_predict"] == 200
    assert captured["json"]["options"]["num_ctx"] == 2048


def test_ollama_client_timeout_has_clear_message(monkeypatch):
    def fake_post(url, json, timeout):
        raise requests.Timeout("too slow")

    monkeypatch.setattr(requests, "post", fake_post)

    client = OllamaClient(base_url="http://localhost:11434", model="gemma3:1b")

    with pytest.raises(OllamaGenerationError, match="timed out"):
        client.generate("Explain this report")
