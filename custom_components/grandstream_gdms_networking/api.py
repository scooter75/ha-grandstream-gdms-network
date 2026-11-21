"""Async API client for Grandstream GDMS / GWN OpenAPI v1.0.0."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any
from urllib.parse import urlencode

import aiohttp

from .const import (
    API_AP_LIST_PATH,
    API_CLIENT_LIST_PATH,
    API_NETWORK_LIST_PATH,
    API_TOKEN_PATH,
)


class GrandstreamApiError(Exception):
    """Base exception for Grandstream GDMS API errors."""


class GrandstreamAuthError(GrandstreamApiError):
    """Authentication or signature failure."""


class GrandstreamGdmsClient:
    """Client for Grandstream GDMS Networking & GWN OpenAPI."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        app_id: str,
        secret_key: str,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._app_id = app_id.strip()
        self._secret_key = secret_key.strip()
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    async def _ensure_token(self) -> str:
        """Fetch or refresh the OAuth2 client_credentials access token."""
        if self._access_token and time.time() < (self._token_expires_at - 60):
            return self._access_token

        url = f"{self._base_url}{API_TOKEN_PATH}"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self._app_id,
            "client_secret": self._secret_key,
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with self._session.post(url, data=payload, headers=headers) as resp:
            if resp.status in (401, 403):
                raise GrandstreamAuthError("Invalid Client/App ID or Secret Key")
            resp.raise_for_status()
            data = await resp.json()

        token = data.get("access_token")
        if not token:
            raise GrandstreamAuthError(
                f"Failed to obtain access token: {data.get('error_description', data)}"
            )

        expires_in = int(data.get("expires_in", 7200))
        self._access_token = token
        self._token_expires_at = time.time() + expires_in
        return token

    def _sign_request(
        self,
        access_token: str,
        timestamp_ms: int,
        body_json: str | None = None,
    ) -> str:
        """Compute the Grandstream OpenAPI SHA-256 signature."""
        params = {
            "access_token": access_token,
            "appID": self._app_id,
            "secretKey": self._secret_key,
            "timestamp": str(timestamp_ms),
        }
        sorted_query = "&".join(f"{k}={params[k]}" for k in sorted(params))

        if body_json:
            body_hash = hashlib.sha256(body_json.encode("utf-8")).hexdigest()
            raw_sig = f"&{sorted_query}&{body_hash}&"
        else:
            raw_sig = f"&{sorted_query}&"

        return hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()

    async def _post(
        self, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a signed POST request against the GDMS/GWN OpenAPI."""
        token = await self._ensure_token()
        timestamp_ms = int(time.time() * 1000)
        body_json = json.dumps(body, separators=(",", ":")) if body else None
        signature = self._sign_request(token, timestamp_ms, body_json)

        query = urlencode(
            {
                "access_token": token,
                "appID": self._app_id,
                "timestamp": timestamp_ms,
                "signature": signature,
            }
        )
        url = f"{self._base_url}{path}?{query}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        async with self._session.post(url, data=body_json, headers=headers) as resp:
            resp.raise_for_status()
            payload = await resp.json()

        ret_code = payload.get("retCode")
        if ret_code not in (0, None):
            if ret_code in (40001, 40002, 40003):
                self._access_token = None
                raise GrandstreamAuthError(
                    f"API auth/signature error ({ret_code}): {payload.get('msg')}"
                )
            raise GrandstreamApiError(
                f"API returned error {ret_code}: {payload.get('msg')}"
            )

        return payload.get("data") or {}

    async def get_networks(self) -> list[dict[str, Any]]:
        """Retrieve all networks/sites accessible to the API credentials."""
        data = await self._post(API_NETWORK_LIST_PATH, {"pageNum": 1, "pageSize": 100})
        if isinstance(data, list):
            return data
        return data.get("result") or data.get("list") or []

    async def get_access_points(self, network_id: int | str) -> list[dict[str, Any]]:
        """Retrieve GWN access points / routers / switches for a network."""
        data = await self._post(
            API_AP_LIST_PATH,
            {"networkId": network_id, "pageNum": 1, "pageSize": 200},
        )
        if isinstance(data, list):
            return data
        return data.get("result") or data.get("list") or []

    async def get_connected_clients(self, network_id: int | str) -> list[dict[str, Any]]:
        """Retrieve currently connected wireless/wired clients with live RSSI/rates."""
        data = await self._post(
            API_CLIENT_LIST_PATH,
            {
                "networkId": network_id,
                "untilNow": 0,
                "pageNum": 1,
                "pageSize": 500,
            },
        )
        if isinstance(data, list):
            return data
        return data.get("result") or data.get("list") or []
