import io
import logging
import wave
from enum import Enum

import httpx
from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel, Field

import config
from convert_to_mp3 import convert_to_mp3
from split_sentence_for_tts import split_sentence_for_tts


logger = logging.getLogger('uvicorn.app')
router = APIRouter(prefix="/v1")

# Default values
SILENCE_DURATION = 0.2  # seconds
DEFAULT_VOLUME = 0.5
DEFAULT_PITCH = 0.0
DEFAULT_SPEED = 1.0


def build_silence(duration: float, params) -> bytes:
    """Generate raw PCM silence for the given duration based on WAV params."""
    n_channels, sampwidth, framerate, *_ = params
    frame_count = int(framerate * duration)
    return b'\x00' * frame_count * n_channels * sampwidth


class Sentence(BaseModel):
    """Single sentence TTS parameters."""
    text: str = Field(...,
                      description="Sentence text to synthesize (required).")
    volume: float | None = Field(
        None,
        description=f"Volume scale (0.0-1.0). If omitted, previous sentence's volume is reused. (default: {DEFAULT_VOLUME})",
    )
    pitch: float | None = Field(
        None,
        description=f"Pitch offset in semitones. Inherits the previous value when omitted. (default: {DEFAULT_PITCH})",
    )
    speed: float | None = Field(
        None,
        description=f"Speaking speed multiplier. Inherits the previous value when omitted. (default: {DEFAULT_SPEED})",
    )
    speaker: str | None = Field(
        None,
        description=f"Speaker ID. Inherits the previous value when omitted. (default: {config.AIVIS_SPEECH_ENGINE_SPEAKER_ID})",
    )


class AudioFormat(str, Enum):
    WAV = "wav"
    MP3 = "mp3"


class RequestBody(BaseModel):
    """Payload for multi-sentence TTS synthesis."""
    format: AudioFormat = Field(
        AudioFormat.MP3,
        description="Output audio format. Either `wav` or `mp3`.",
    )
    silence_duration: float = Field(
        SILENCE_DURATION,
        description="Duration of silence (in seconds) inserted between sentences.",
    )
    sentences: list[Sentence] = Field(
        ...,
        description="Ordered list of sentences to synthesize. "
                    "Parameters omitted in a sentence inherit the value "
                    "defined in its immediate predecessor.",
    )


@router.post(
    "/synthesis",
    summary="Multi-sentence TTS synthesis",
    response_description="Binary audio (WAV or MP3)",
)
async def synthesis(body: RequestBody):
    """Concatenate TTS audio for multiple sentences.

    Each sentence in `body.sentences` is converted to speech in order.
    For sentences after the first, any of `volume`, `pitch`, `speed`,
    or `speaker` that are omitted will inherit the value used for the
    previous sentence.  A silence of `silence_duration` seconds is
    automatically inserted between each sentence before concatenation.
    """
    format = body.format
    silence_duration = body.silence_duration
    buffer = io.BytesIO()
    wave_writer = None
    wave_params = None
    wave_pos: float = 0

    logger.info(f"- Request {len(body.sentences)=} {format=}")

    num_sentences = len(body.sentences)
    silence_wave: bytes | None = None

    volume = body.sentences[0].volume or DEFAULT_VOLUME
    pitch = body.sentences[0].pitch or DEFAULT_PITCH
    speed = body.sentences[0].speed or DEFAULT_SPEED
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
            # 前後の無音期間をなくす
            audio_query["prePhonemeLength"] = 0
            audio_query["postPhonemeLength"] = 0
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
            wave_sec = wf.getnframes() / wf.getframerate()

            if idx > 0:
                # ループ2週目以降であれば先頭に空白を挿入
                if silence_wave is None:
                    silence_wave = build_silence(silence_duration, wave_params)
                wave_writer.writeframes(silence_wave)
                wave_pos += silence_duration
            logger.info(f"  Timing start={wave_pos:.3f}, end={(wave_pos+wave_sec):.3f}, length={wave_sec:.3f}sec")

            wave_writer.writeframes(frames)
            wave_pos += wave_sec

    wave_writer.close()
    full_wav = buffer.getvalue()

    if format == AudioFormat.WAV:
        logger.info(f"- Returning WAV. size: {len(full_wav)/1024:.1f}KB")
        return Response(io.BytesIO(full_wav).getvalue(), media_type="audio/wav")

    encoded = convert_to_mp3(full_wav)  # convert to mp3
    logger.info(f"- MP3 Encoded. mp3 size: {len(encoded)/1024:.1f}KB")

    return Response(io.BytesIO(encoded).getvalue(), media_type="audio/mpeg")
