import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from split_sentence_for_tts import split_sentence_for_tts


logger = logging.getLogger('uvicorn.app')
router = APIRouter(prefix="/v1")


@router.get("/split_sentence",)
async def split_sentence(text: str) -> JSONResponse:
    sentences = split_sentence_for_tts(text)
    for sentence in sentences:
        logger.info(f"- Split Sentence: {len(sentence)=}, {sentence[:20]}")
    return {"sentences": sentences}
