"""No-model API contract checks for the forked endpoint.

Run with the BreezyVoice runtime Python; it imports the real FastAPI app but
does not enter the model-loading lifespan.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from fastapi import HTTPException

import api
from style_registry import StyleBankError


class RejectingRegistry:
    def resolve(self, style: str, intensity: int):
        raise StyleBankError(f"missing authorized WAV: {style}/{intensity}.wav")


async def assert_request_rejected(style: str, intensity: int) -> None:
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(style_registry=RejectingRegistry())))
    try:
        await api.speach_endpoint(request, api.SpeechRequest(input="測試", style=style, intensity=intensity))
    except HTTPException as error:
        assert error.status_code == 422
    else:
        raise AssertionError("missing reference must return HTTP 422")


assert "/v1/audio/speech" in [route.path for route in api.app.routes]
assert api.SpeechRequest(input="測試").style == "neutral"
assert api.SpeechRequest(input="測試").intensity == 2
asyncio.run(assert_request_rejected("neutral", 2))
print("API contract smoke passed")
