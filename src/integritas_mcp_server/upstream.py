# upstream.py
import httpx
from typing import Any, Dict, Optional
from .config import AppConfig, API_KEY_PROVIDER

class UpstreamClient:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.client = httpx.Client(base_url=str(cfg.base_url), timeout=30)

    def _headers(self) -> Dict[str, str]:
        api_key = self.cfg.api_key or API_KEY_PROVIDER.get()
        if not api_key:
            # Let callers convert to a user-friendly MCP error
            raise RuntimeError("Missing API key. Set via env, keyring, or the auth_set_api_key tool.")
        # If your API expects x-api-key instead, switch below:
        return {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> Any:
        headers = kwargs.pop("headers", {})
        headers.update(self._headers())
        resp = self.client.request(method, path, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()

    # Example endpoints:
    def stamp_data(self, payload: dict):        return self._request("POST", "/v1/stamps", json=payload)
    def verify_data(self, hash_hex: str):     return self._request("GET",  f"/v1/stamps/{hash_hex}")
