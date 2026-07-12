import json
import math
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings

from apps.ai_platform.models import AIProviderType


@dataclass
class ProviderResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    raw: dict | None = None
    finish_reason: str = "stop"
    embedding: list[float] | None = None


class BaseAIProvider:
    provider_type = ""

    def __init__(self, provider_record, model_configuration):
        self.provider_record = provider_record
        self.model_configuration = model_configuration

    def generate_text(self, *, messages, max_tokens=None, temperature=None, tools=None) -> ProviderResult:
        raise NotImplementedError

    def stream_text(self, *, messages, max_tokens=None, temperature=None):
        result = self.generate_text(messages=messages, max_tokens=max_tokens, temperature=temperature)
        for token in result.text.split(" "):
            yield token + " "

    def embed(self, *, text: str) -> ProviderResult:
        vector = deterministic_embedding(text)
        return ProviderResult(text="", raw={"embedding": vector}, embedding=vector, input_tokens=max(len(text.split()), 1))

    def classify(self, *, text: str, labels: list[str]) -> ProviderResult:
        label = labels[0] if labels else "unknown"
        return ProviderResult(text=label, raw={"label": label}, input_tokens=max(len(text.split()), 1), output_tokens=1)


class MockAIProvider(BaseAIProvider):
    provider_type = AIProviderType.MOCK

    def generate_text(self, *, messages, max_tokens=None, temperature=None, tools=None) -> ProviderResult:
        user_content = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                user_content = message.get("content", "")
                break
        text = f"Mock AI response: {user_content[:500]}"
        return ProviderResult(
            text=text,
            input_tokens=sum(max(len(message.get("content", "").split()), 1) for message in messages),
            output_tokens=max(len(text.split()), 1),
            raw={"provider": "mock", "tools": tools or []},
        )


class OpenAIProvider(BaseAIProvider):
    provider_type = AIProviderType.OPENAI

    def generate_text(self, *, messages, max_tokens=None, temperature=None, tools=None) -> ProviderResult:
        if not getattr(settings, "OPENAI_API_KEY", ""):
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=self.model_configuration.timeout_seconds)
        payload = {
            "model": self.model_configuration.model_name,
            "messages": messages,
            "max_tokens": max_tokens or self.model_configuration.max_tokens,
            "temperature": float(temperature if temperature is not None else self.model_configuration.temperature),
        }
        if tools:
            payload["tools"] = tools
        response = client.chat.completions.create(**payload)
        choice = response.choices[0]
        usage = getattr(response, "usage", None)
        return ProviderResult(
            text=choice.message.content or "",
            input_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            output_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
            raw=response.model_dump() if hasattr(response, "model_dump") else {},
            finish_reason=choice.finish_reason or "stop",
        )

    def stream_text(self, *, messages, max_tokens=None, temperature=None):
        if not getattr(settings, "OPENAI_API_KEY", ""):
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=self.model_configuration.timeout_seconds)
        stream = client.chat.completions.create(
            model=self.model_configuration.model_name,
            messages=messages,
            max_tokens=max_tokens or self.model_configuration.max_tokens,
            temperature=float(temperature if temperature is not None else self.model_configuration.temperature),
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if getattr(delta, "content", None):
                yield delta.content


class OpenAICompatibleProvider(BaseAIProvider):
    default_base_url = ""
    api_key_setting = ""

    def _base_url(self):
        return self.provider_record.configuration.get("base_url") or self.default_base_url

    def _api_key(self):
        configured_key = self.provider_record.configuration.get("api_key", "")
        return configured_key or getattr(settings, self.api_key_setting, "")

    def _post_json(self, path, payload, headers=None):
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self._base_url().rstrip('/')}/{path.lstrip('/')}",
            data=body,
            headers={"Content-Type": "application/json", **(headers or {})},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.model_configuration.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def generate_text(self, *, messages, max_tokens=None, temperature=None, tools=None) -> ProviderResult:
        api_key = self._api_key()
        if not self._base_url():
            raise RuntimeError(f"{self.provider_record.provider_type} base_url is not configured.")
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": self.model_configuration.model_name,
            "messages": messages,
            "max_tokens": max_tokens or self.model_configuration.max_tokens,
            "temperature": float(temperature if temperature is not None else self.model_configuration.temperature),
        }
        if tools:
            payload["tools"] = tools
        data = self._post_json("/v1/chat/completions", payload, headers)
        choice = (data.get("choices") or [{}])[0]
        usage = data.get("usage") or {}
        return ProviderResult(
            text=((choice.get("message") or {}).get("content") or choice.get("text") or ""),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            raw=data,
            finish_reason=choice.get("finish_reason") or "stop",
        )


class AzureOpenAIProvider(OpenAICompatibleProvider):
    provider_type = AIProviderType.AZURE_OPENAI
    api_key_setting = "AZURE_OPENAI_API_KEY"

    def generate_text(self, *, messages, max_tokens=None, temperature=None, tools=None) -> ProviderResult:
        endpoint = self.provider_record.configuration.get("endpoint") or getattr(settings, "AZURE_OPENAI_ENDPOINT", "")
        deployment = self.provider_record.configuration.get("deployment") or self.model_configuration.model_name
        api_version = self.provider_record.configuration.get("api_version", "2024-02-15-preview")
        api_key = self.provider_record.configuration.get("api_key", "") or getattr(settings, "AZURE_OPENAI_API_KEY", "")
        if not endpoint or not api_key:
            raise RuntimeError("Azure OpenAI endpoint/API key is not configured.")
        payload = {
            "messages": messages,
            "max_tokens": max_tokens or self.model_configuration.max_tokens,
            "temperature": float(temperature if temperature is not None else self.model_configuration.temperature),
        }
        if tools:
            payload["tools"] = tools
        url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
        request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", "api-key": api_key}, method="POST")
        with urllib.request.urlopen(request, timeout=self.model_configuration.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
        choice = (data.get("choices") or [{}])[0]
        usage = data.get("usage") or {}
        return ProviderResult(text=(choice.get("message") or {}).get("content", ""), input_tokens=usage.get("prompt_tokens", 0), output_tokens=usage.get("completion_tokens", 0), raw=data, finish_reason=choice.get("finish_reason") or "stop")


class AnthropicProvider(BaseAIProvider):
    provider_type = AIProviderType.ANTHROPIC

    def generate_text(self, *, messages, max_tokens=None, temperature=None, tools=None) -> ProviderResult:
        api_key = self.provider_record.configuration.get("api_key", "") or getattr(settings, "ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured.")
        system = "\n".join(message["content"] for message in messages if message.get("role") == "system")
        user_messages = [message for message in messages if message.get("role") != "system"]
        payload = {
            "model": self.model_configuration.model_name,
            "max_tokens": max_tokens or self.model_configuration.max_tokens,
            "temperature": float(temperature if temperature is not None else self.model_configuration.temperature),
            "system": system,
            "messages": user_messages,
        }
        if tools:
            payload["tools"] = tools
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.model_configuration.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = "".join(part.get("text", "") for part in data.get("content", []) if part.get("type") == "text")
        usage = data.get("usage") or {}
        return ProviderResult(text=text, input_tokens=usage.get("input_tokens", 0), output_tokens=usage.get("output_tokens", 0), raw=data, finish_reason=data.get("stop_reason") or "stop")


class GeminiProvider(BaseAIProvider):
    provider_type = AIProviderType.GOOGLE_GEMINI

    def generate_text(self, *, messages, max_tokens=None, temperature=None, tools=None) -> ProviderResult:
        api_key = self.provider_record.configuration.get("api_key", "") or getattr(settings, "GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        prompt = "\n".join(f"{message.get('role')}: {message.get('content')}" for message in messages)
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": max_tokens or self.model_configuration.max_tokens, "temperature": float(temperature if temperature is not None else self.model_configuration.temperature)}}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_configuration.model_name}:generateContent?key={api_key}"
        request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=self.model_configuration.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
        candidate = (data.get("candidates") or [{}])[0]
        parts = ((candidate.get("content") or {}).get("parts") or [])
        text = "".join(part.get("text", "") for part in parts)
        usage = data.get("usageMetadata") or {}
        return ProviderResult(text=text, input_tokens=usage.get("promptTokenCount", 0), output_tokens=usage.get("candidatesTokenCount", 0), raw=data, finish_reason=candidate.get("finishReason") or "stop")


class LocalProvider(OpenAICompatibleProvider):
    provider_type = AIProviderType.LOCAL
    default_base_url = "http://localhost:11434"


def deterministic_embedding(text: str, dimensions: int = 16) -> list[float]:
    values = [0.0 for _ in range(dimensions)]
    for index, byte in enumerate(text.encode("utf-8")):
        values[index % dimensions] += (byte % 31) / 31
    norm = math.sqrt(sum(value * value for value in values)) or 1
    return [round(value / norm, 6) for value in values]


PROVIDER_CLASSES = {
    AIProviderType.MOCK: MockAIProvider,
    AIProviderType.OPENAI: OpenAIProvider,
    AIProviderType.ANTHROPIC: AnthropicProvider,
    AIProviderType.GOOGLE_GEMINI: GeminiProvider,
    AIProviderType.AZURE_OPENAI: AzureOpenAIProvider,
    AIProviderType.LOCAL: LocalProvider,
}


def estimate_cost(model_configuration, input_tokens: int, output_tokens: int) -> Decimal:
    input_cost = Decimal(input_tokens) * model_configuration.input_token_cost
    output_cost = Decimal(output_tokens) * model_configuration.output_token_cost
    return (input_cost + output_cost).quantize(Decimal("0.000001"))
