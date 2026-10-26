import logging
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    text: str
    duration_s: float
    confidence: float
    model_name: str


class WhisperService:
    """Wraps faster-whisper for local ASR.

    `faster_whisper` is imported lazily inside `_load_model`, not at module
    import time: it (and its CTranslate2 dependency) is a heavy, optional
    install, and most of the backend -- API routes, agent pipeline, tests
    that feed in text directly -- never needs it loaded. The model itself
    is also lazy-loaded once per process and cached, since loading it is
    the expensive part.
    """

    def __init__(self) -> None:
        self._model = None

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            settings = get_settings()
            logger.info(
                "Loading faster-whisper model=%s device=%s",
                settings.whisper_model_size,
                settings.whisper_device,
            )
            self._model = WhisperModel(
                settings.whisper_model_size,
                device=settings.whisper_device,
                compute_type="int8" if settings.whisper_device == "cpu" else "float16",
            )
        return self._model

    def transcribe(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        model = self._load_model()
        segments, info = model.transcribe(audio_path, language=language, vad_filter=True)
        text_parts = []
        confidences = []
        for segment in segments:
            text_parts.append(segment.text.strip())
            # faster-whisper exposes avg_logprob; convert to a rough 0..1 confidence.
            confidences.append(min(1.0, max(0.0, 1.0 + (segment.avg_logprob / 5.0))))

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        settings = get_settings()
        return TranscriptionResult(
            text=" ".join(text_parts).strip(),
            duration_s=info.duration,
            confidence=round(avg_confidence, 3),
            model_name=f"faster-whisper-{settings.whisper_model_size}",
        )


@lru_cache
def get_whisper_service() -> WhisperService:
    return WhisperService()
