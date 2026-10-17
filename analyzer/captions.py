"""Caption/transcript fetching for analyzed videos.

Uses `youtube-transcript-api` (pip). Returns timestamped segments so the
decoder can measure pacing, segment count and narration rhythm.
Falls back gracefully: a video with no captions returns [] instead of
crashing the whole analysis run.
"""
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound


def get_segments(video_id: str, languages=("en",)) -> list:
    """Return [{start, dur, text}] for a video, or [] if unavailable."""
    try:
        raw = YouTubeTranscriptApi.get_transcript(video_id, languages=list(languages))
    except (TranscriptsDisabled, NoTranscriptFound):
        return []
    except Exception:
        return []
    return [{"start": float(s["start"]), "dur": float(s.get("duration", 0)),
             "text": s["text"].strip()} for s in raw if s["text"].strip()]


def get_text(video_id: str, languages=("en",)) -> str:
    """Plain-text transcript for LLM passes."""
    return " ".join(s["text"] for s in get_segments(video_id, languages))


def caption_stats(segments: list) -> dict:
    """Pacing signals: segment count, words/min, avg segment length."""
    words = sum(len(s["text"].split()) for s in segments)
    total_sec = (segments[-1]["start"] + segments[-1]["dur"]) if segments else 0
    n = len(segments)
    return {
        "segments": n,
        "words": words,
        "wpm": round(words / (total_sec / 60), 1) if total_sec else 0,
        "avg_seg_sec": round(total_sec / n, 1) if n else 0,
        "has_captions": n > 0,
    }
