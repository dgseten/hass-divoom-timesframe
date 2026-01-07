from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import DEFAULT_PORT


class DivoomApiError(Exception):
    """Raised when the device returns an error or cannot be reached."""


class DivoomClient:
    def __init__(self, host: str, port: int = DEFAULT_PORT) -> None:
        self._url = f"http://{host}:{port}/divoom_api"

    async def request(self, session: aiohttp.ClientSession, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with session.get(self._url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                # algunos firmwares devuelven JSON, otros texto; intenta JSON
                data = await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            raise DivoomApiError(f"Request failed: {e}") from e

        # estándar típico de Divoom
        if isinstance(data, dict) and data.get("ReturnCode") not in (None, 0):
            raise DivoomApiError(f"Device error: {data}")

        return data if isinstance(data, dict) else {"raw": data}

    async def set_screen(self, session: aiohttp.ClientSession, on: bool) -> dict[str, Any]:
        return await self.request(
            session,
            {"Command": "Channel/OnOffScreen", "OnOff": 1 if on else 0},
        )
    
    async def set_brightness(self, session, value: int) -> dict:
        value = max(0, min(100, value))
        return await self.request(
            session,
            {
                "Command": "Channel/SetBrightness",
                "Brightness": value,
            },
        )

    async def ping(self, session: aiohttp.ClientSession) -> None:
        # No tenemos endpoint de estado; hacemos un “ping” barato:
        # intentamos encender pantalla (no es ideal, pero sirve para validar conectividad)
        # Alternativa: llamar a algún comando inocuo si lo encuentras.
        await self.set_screen(session, True)
