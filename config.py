import os

AIVIS_SPEECH_ENGINE_URL = os.getenv("AIVIS_SPEECH_ENGINE_URL", "http://localhost:10101/").rstrip('/')
AIVIS_SPEECH_ENGINE_SPEAKER_ID = os.getenv("AIVIS_SPEECH_ENGINE_SPEAKER_ID", "888753760")

PORT = int(os.getenv("APP_PORT", "8000"))
CONTEXT_PATH = os.getenv("CONTEXT_PATH", "/")
