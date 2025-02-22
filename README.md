# AivisSpeechFastAPI

## Overview

- Aivis Speech FastAPI is a simple API that allows you to convert text into speech using the AivisSpeech Engine.
  - AivisSpeech-Engine: https://github.com/Aivis-Project/AivisSpeech-Engine
- Use this wrapper to easy convert text to audio
- Supports audio output `mp3` and `wav` formats.

## .env

```.env
AIVIS_ENGINE_URL="http://localhost:10101/"
AIVIS_ENGINE_SPEAKER_ID="888753760"

PORT="8000"
CONTEXT_PATH="/"
```

## Documentation

- API documentation is available at `/docs`.
- Swagger UI is accessible at `/redoc`.
- `GET /synthesis`
  - Generate audio response from provided `text`
  - Responses `audio/mp3` or `audio/wav` for `format=wav`
- `GET /split_sentence`
  - Utility function to split text input to sentence array by Japanese characters `。` `！` `？`.
