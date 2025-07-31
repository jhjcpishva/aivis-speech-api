# aivis-speech-api

## Overview

- Aivis Speech FastAPI is a simple API that allows you to convert text into speech using the AivisSpeech Engine.
  - AivisSpeech-Engine: https://github.com/Aivis-Project/AivisSpeech-Engine
- Use this wrapper to easy convert text to audio
- Supports audio output `mp3` and `wav` formats.

## .env

```.env
AIVIS_SPEECH_ENGINE_URL="http://localhost:10101/"
AIVIS_SPEECH_ENGINE_SPEAKER_ID="888753760"

PORT="8000"
PREFIX_PATH="/"
```

## Documentation

- API documentation is available at `/docs` or `/redoc`.
- `GET /synthesis`
  - Generate audio response from provided `text`
  - Responses `audio/mp3` or `audio/wav` for `format=wav`
- `GET /split_sentence`
  - Utility function to split text input to sentence array by Japanese characters `。` `！` `？`.

## Run

### Docker

```sh
docker run --rm \
  -e AIVIS_SPEECH_ENGINE_URL="http://host.docker.internal:10101" \
  -p 8000:8000 \
  ghcr.io/jhjcpishva/aivis-speech-api:latest
```

### Docker Compose

```yaml
services:
  fastapi:
    # build: .
    image: ghcr.io/jhjcpishva/aivis-speech-api:latest
    environment:
      - AIVIS_SPEECH_ENGINE_URL=http://aivisspeech-engine:10101/
    depends_on:
      aivisspeech-engine:
        condition: service_healthy
    ports:
      - 8000:8000

  aivisspeech-engine:
    image: ghcr.io/aivis-project/aivisspeech-engine:cpu-latest
    # ports:
    #   - 10101:10101
    volumes:
      - ./docker/aivisspeech-engine:/home/user/.local/share/AivisSpeech-Engine-Dev
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:10101/version"]
      interval: 5s
      timeout: 10s
      retries: 20

```
