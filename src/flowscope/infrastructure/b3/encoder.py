"""Codificação dos payloads Base64 dos endpoints de fundos listados da B3."""

import base64
import json


def encode_b3_payload(payload: dict[str, object]) -> str:
    """Serializa o payload em JSON compacto e o codifica em Base64."""
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.b64encode(raw).decode()
