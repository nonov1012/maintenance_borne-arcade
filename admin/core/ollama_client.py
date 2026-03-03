"""
Wrapper Ollama (stdlib uniquement, pas de dépendance externe).
Adapté pour l'appli admin de la borne d'arcade.
"""
from __future__ import annotations

import base64
import json
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union


class OllamaError(RuntimeError):
    pass

class OllamaConnectionError(OllamaError):
    pass

class OllamaResponseError(OllamaError):
    pass


@dataclass(frozen=True, slots=True)
class OllamaGenerateResult:
    response: str
    model: Optional[str] = None
    done: Optional[bool] = None
    total_duration: Optional[int] = None
    eval_count: Optional[int] = None


class OllamaWrapper:
    def __init__(self, base_url: str = "http://10.22.28.190:11434", timeout_s: float = 180.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_s = timeout_s

    def is_server_running(self) -> bool:
        try:
            self.get_version()
            return True
        except OllamaConnectionError:
            return False
        except OllamaResponseError:
            return True

    def get_version(self) -> str:
        payload = self._request("GET", "/api/version", body=None)
        version = payload.get("version")
        if not isinstance(version, str):
            raise OllamaResponseError(f"Réponse inattendue: {payload!r}")
        return version

    def list_models(self) -> List[str]:
        payload = self._request("GET", "/api/tags", body=None)
        models = payload.get("models", [])
        return [m["name"] for m in models if isinstance(m, dict) and "name" in m]

    def generate_text(
        self,
        *,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[Mapping[str, Any]] = None,
    ) -> OllamaGenerateResult:
        body: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
        if system:
            body["system"] = system
        if options:
            body["options"] = dict(options)

        payload = self._request("POST", "/api/generate", body=body)
        response_text = payload.get("response")
        if not isinstance(response_text, str):
            raise OllamaResponseError(f"Réponse inattendue: {payload!r}")

        return OllamaGenerateResult(
            response=response_text,
            model=payload.get("model") if isinstance(payload.get("model"), str) else None,
            done=payload.get("done") if isinstance(payload.get("done"), bool) else None,
            total_duration=payload.get("total_duration") if isinstance(payload.get("total_duration"), int) else None,
            eval_count=payload.get("eval_count") if isinstance(payload.get("eval_count"), int) else None,
        )

    def _request(self, method: str, path: str, *, body: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        import urllib.error
        import urllib.request

        url = self._base_url + "/" + path.lstrip("/")
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        data = json.dumps(body).encode("utf-8") if body is not None else None

        req = urllib.request.Request(url=url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                raw = resp.read()
        except (urllib.error.URLError, TimeoutError) as e:
            raise OllamaConnectionError(f"Impossible de joindre Ollama à {url}: {e}") from e

        try:
            payload = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as e:
            raise OllamaResponseError(f"Réponse non-JSON: {raw[:200]!r}") from e

        if not isinstance(payload, dict):
            raise OllamaResponseError(f"JSON inattendu: {payload!r}")
        return payload
