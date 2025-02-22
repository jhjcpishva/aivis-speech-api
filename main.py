import io
import logging
from enum import Enum

import httpx
from fastapi import FastAPI
from fastapi.responses import Response

import config
from convert_to_mp3 import convert_to_mp3
from split_sentence_for_tts import split_sentence_for_tts

logger = logging.getLogger('uvicorn.app')

app = FastAPI()


class AudioFormat(str, Enum):
    WAV = "wav"
    MP3 = "mp3"
    

@app.get(f"{config.CONTEXT_PATH}synthesis")
async def speech(
    text: str="吾輩は猫である。名前はまだ無い",
    volume: float = 0.5,
    pitch: float = 0,
    speed: float = 1,
    speaker: str = config.AIVIS_ENGINE_SPEAKER_ID,
    format: AudioFormat = AudioFormat.MP3):

    logger.info(f"🐶 Request {text = } {volume = } {pitch = } {speed = } {format = }")
    # AivisSpeech で音声を作成する
    async with httpx.AsyncClient() as client:
        audio_query = (await client.post(f"{config.AIVIS_ENGINE_URL}/audio_query?text={text}&speaker={speaker}")).json()
        audio_query["volumeScale"] = volume
        audio_query["pitchScale"] = pitch
        audio_query["speedScale"] = speed
        audio = await client.post(f"{config.AIVIS_ENGINE_URL}/synthesis?speaker={speaker}", json=audio_query, timeout=None)
    logger.info(f"🐶 TTS Complete. wav size: {len(audio.content)/1024:.1f}KB")

    if format == AudioFormat.WAV:
        return Response(audio.content, media_type="audio/wav")

    encoded = convert_to_mp3(audio.content)  # convert to mp3
    logger.info(f"🐶 MP3 Encoded. mp3 size: {len(encoded)/1024:.1f}KB")

    return Response(io.BytesIO(encoded).getvalue(), media_type="audio/mpeg")

@app.get(f"{config.CONTEXT_PATH}split_sentence")
async def split_sentence(text: str):
    sentences = split_sentence_for_tts(text)
    for sentence in sentences:
        logger.info(f"🐶 Split Sentence: {len(sentence) = }, {sentence[:20]}")
    return { "sentences": sentences }


if __name__ == '__main__':
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
