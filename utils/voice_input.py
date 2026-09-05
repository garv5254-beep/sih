"""Optional voice input adapter; text chat remains available when unsupported."""

from __future__ import annotations

from io import BytesIO


def transcribe_audio(audio_bytes: bytes, language: str | None = None) -> dict[str, str | None]:
    if not audio_bytes:
        return {"text": None, "status": "empty", "message": "No audio was provided."}
    try:
        import speech_recognition as sr
    except ImportError:
        return {"text": None, "status": "unavailable", "message": "Voice input is currently unavailable in this environment. Please type your question instead."}
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language=language or "en-IN")
        return {"text": text, "status": "success", "message": None}
    except Exception:
        return {"text": None, "status": "failed", "message": "Voice transcription failed. Please edit or type your question instead."}
