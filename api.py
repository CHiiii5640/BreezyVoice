# OpenAI API Spec. Reference: https://platform.openai.com/docs/api-reference/audio/createSpeech
# Modified by CHiiii5640 (2026): authorized style-bank selection and prompt caching.

from contextlib import asynccontextmanager
from io import BytesIO

import torchaudio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from g2pw import G2PWConverter
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from cosyvoice.utils.file_utils import load_wav
from single_inference import CustomCosyVoice, get_bopomofo_rare
from style_registry import StyleBankError, StyleRegistry


class Settings(BaseSettings):
    api_key: str = Field(
        default="", description="Specifies the API key used to authenticate the user."
    )

    model_path: str = Field(
        default="MediaTek-Research/BreezyVoice",
        description="Specifies the model used for speech synthesis.",
    )
    style_bank_root: str = Field(
        default="./data/style_bank",
        description="Root of authorized references: {style}/{intensity}.wav and .txt.",
    )


class SpeechRequest(BaseModel):
    model: str = ""
    voice: str = ""
    input: str = Field(
        description="The content that will be synthesized into speech. You can include phonetic symbols if needed, though they should be used sparingly.",
        examples=["今天天氣真好"],
    )
    response_format: str = ""
    speed: float = 1.0
    style: str = "neutral"
    intensity: int = Field(default=2, ge=1, le=3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = Settings()
    app.state.cosyvoice = CustomCosyVoice(app.state.settings.model_path)
    app.state.bopomofo_converter = G2PWConverter()
    app.state.style_registry = StyleRegistry(app.state.settings.style_bank_root, load_wav)
    app.state.style_registry.preload()
    yield
    del app.state.cosyvoice
    del app.state.bopomofo_converter


app = FastAPI(lifespan=lifespan, root_path="/v1")


@app.get("/models")
async def get_models(request: Request):
    return {
        "object": "list",
        "data": [
            {
                "id": request.app.state.settings.model_path,
                "object": "model",
                "created": 0,
                "owned_by": "local",
            }
        ],
    }


@app.post("/audio/speech")
async def speach_endpoint(request: Request, payload: SpeechRequest):
    # normalization
    try:
        prompt = request.app.state.style_registry.resolve(payload.style, payload.intensity)
    except StyleBankError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    speaker_prompt_text_transcription = (
        request.app.state.cosyvoice.frontend.text_normalize_new(
            prompt.transcript, split=False
        )
    )
    content_to_synthesize = request.app.state.cosyvoice.frontend.text_normalize_new(
        payload.input, split=False
    )
    speaker_prompt_text_transcription_bopomo = get_bopomofo_rare(
        speaker_prompt_text_transcription, request.app.state.bopomofo_converter
    )

    content_to_synthesize_bopomo = get_bopomofo_rare(
        content_to_synthesize, request.app.state.bopomofo_converter
    )
    output = request.app.state.cosyvoice.inference_zero_shot_no_normalize(
        content_to_synthesize_bopomo,
        speaker_prompt_text_transcription_bopomo,
        prompt.prompt_speech_16k,
    )
    audio_buffer = BytesIO()
    torchaudio.save(audio_buffer, output["tts_speech"], 22050, format="wav")
    audio_buffer.seek(0)
    return StreamingResponse(
        audio_buffer,
        media_type="audio/wav",
        headers={
            "Content-Disposition": "attachment; filename=output.wav",
            "X-BreezyVoice-Style": prompt.style,
            "X-BreezyVoice-Intensity": str(prompt.intensity),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8080)
