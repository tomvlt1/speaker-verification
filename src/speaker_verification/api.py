"""Thin wrapper around the Azure Speaker Recognition HTTP API."""

from __future__ import annotations

import http.client
import json
from typing import Any

from .config import AZURE_HOST, get_azure_key


def request(
    method: str,
    path: str,
    body: bytes | str | None = None,
    content_type: str = "application/json",
) -> dict[str, Any] | None:
    """Make an authenticated request against the Azure Speech endpoint.

    Returns the decoded JSON response, or None on failure.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": get_azure_key(),
        "Content-Type": content_type,
    }
    conn = http.client.HTTPSConnection(AZURE_HOST)
    try:
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        raw = response.read().decode()
        if not raw:
            return None
        return json.loads(raw)
    except Exception as exc:
        print(f"[api] request failed: {exc}")
        return None
    finally:
        conn.close()
