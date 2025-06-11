import io
import logging
import wave
from enum import Enum

import httpx
from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

import config
from convert_to_mp3 import convert_to_mp3
from split_sentence_for_tts import split_sentence_for_tts


logger = logging.getLogger('uvicorn.app')
router = APIRouter(prefix="/v1")

SILENCE_DURATION = 1.0  # seconds


def build_silence(duration: float, params) -> bytes:
    """Generate raw PCM silence for the given duration based on WAV params."""
    n_channels, sampwidth, framerate, *_ = params
    frame_count = int(framerate * duration)
    return b'\x00' * frame_count * n_channels * sampwidth


class Sentence(BaseModel):
    text: str
    volume: float | None = None
    pitch: float | None = None
    speed: float | None = None
    speaker: str | None = None


class AudioFormat(str, Enum):
    WAV = "wav"
    MP3 = "mp3"


class RequestBody(BaseModel):
    format: AudioFormat = AudioFormat.MP3
    silence_duration: float = SILENCE_DURATION
    sentences: list[Sentence]


@router.post("/synthesis")
async def synthesis(body: RequestBody):
    format = body.format
    silence_duration = body.silence_duration
    buffer = io.BytesIO()
    wave_writer = None
    wave_params = None

    logger.info(f"- Request {len(body.sentences)=} {format=}")

    num_sentences = len(body.sentences)
    silence_wave: bytes | None = None

    volume = body.sentences[0].volume or 0.5
    pitch = body.sentences[0].pitch or 0
    speed = body.sentences[0].speed or 1
    speaker = body.sentences[0].speaker or config.AIVIS_SPEECH_ENGINE_SPEAKER_ID

    for idx, sentence in enumerate(body.sentences):
        text = sentence.text
        volume = sentence.volume or volume
        pitch = sentence.pitch or pitch
        speed = sentence.speed or speed
        speaker = sentence.speaker or speaker

        logger.info(
            f"- [{idx+1} / {num_sentences}] TTS {text=} {volume=} {pitch=} {speed=} {speaker=}")
        # AivisSpeech で音声を作成する
        async with httpx.AsyncClient() as client:
            audio_query = (await client.post(f"{config.AIVIS_SPEECH_ENGINE_URL}/audio_query?text={text}&speaker={speaker}")).json()
            audio_query["volumeScale"] = volume
            audio_query["pitchScale"] = pitch
            audio_query["speedScale"] = speed
            audio = await client.post(f"{config.AIVIS_SPEECH_ENGINE_URL}/synthesis?speaker={speaker}", json=audio_query, timeout=None)
        logger.info(
            f"  TTS Complete. wav size: {len(audio.content)/1024:.1f}KB")

        with wave.open(io.BytesIO(audio.content), 'rb') as wf:
            if wave_params is None:
                # First chunk: capture parameters and open writer
                wave_params = wf.getparams()
                wave_writer = wave.open(buffer, 'wb')
                wave_writer.setparams(wave_params)

            frames = wf.readframes(wf.getnframes())

            if idx > 0:
                # ループ2週目以降であれば先頭に空白を挿入
                if silence_wave is None:
                    silence_wave = build_silence(silence_duration, wave_params)
                wave_writer.writeframes(silence_wave)

            wave_writer.writeframes(frames)

    wave_writer.close()
    full_wav = buffer.getvalue()

    if format == AudioFormat.WAV:
        logger.info(f"- Returning WAV. size: {len(full_wav)/1024:.1f}KB")
        return Response(io.BytesIO(full_wav).getvalue(), media_type="audio/wav")

    encoded = convert_to_mp3(full_wav)  # convert to mp3
    logger.info(f"- MP3 Encoded. mp3 size: {len(encoded)/1024:.1f}KB")

    return Response(io.BytesIO(encoded).getvalue(), media_type="audio/mpeg")
