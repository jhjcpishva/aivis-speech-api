import logging

from fastapi import FastAPI

import config
from api.basic import router as basic_router
from api.sentence import router as sentence_router
from api.multi_sentence_tts import router as multi_sentence_tts_router

logger = logging.getLogger('uvicorn.app')

app = FastAPI()
app.include_router(basic_router, prefix=config.CONTEXT_PATH)
app.include_router(sentence_router, prefix=config.CONTEXT_PATH)
app.include_router(multi_sentence_tts_router, prefix=config.CONTEXT_PATH)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
