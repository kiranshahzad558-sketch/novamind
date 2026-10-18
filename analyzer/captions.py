"""Caption/transcript fetching for analyzed videos.

Supports youtube-transcript-api v1.x (YouTubeTranscriptApi().fetch) and
older 0.x (YouTubeTranscriptApi.get_transcript). Returns timestamped
segments so the decoder can measure pacing, segment count and narration
rhythm. Falls back gracefully: a video with no captions (or an IP-blocked
transcript endpoint) returns [] instead of crashing the analysis run.
"""

try:
    from youtube_transcript_api import YouTubeTranscriptApi as _YTA
    _HAS_YTA = True
except ImportError:
    _YTA = None
    _HAS_YTA = False


def _fetch_raw(video_id: str, languages):
    if not _HAS_YTA:
        return []
    langs = list(languages)
    # v1.x: instance method .fetch() -> snippet objects
    try:
        api = _YTA()
        if hasattr(api, "fetch"):
            return list(api.fetch(video_id, languages=langs))
    except Exception:
        pass
    # 0.x: classmethod .get_transcript() -> dicts
    try:
        if hasattr(_YTA, "get_transcript"):
            return _YTA.get_transcript(video_id, languages=langs)
    except Exception:
        pass
    return []


def _norm(snippet):
    # snippet may be a dict (0.x) or an object with .text/.start/.duration (1.x)
    if isinstance(snippet, dict):
        text = snippet.get("text", "")
        start = snippet.get("start", 0)
        dur = snippet.get("duration", 0)
    else:
        text = getattr(snippet, "text", "")
        start = getattr(snippet, "start", 0)
        dur = getattr(snippet, "duration", 0)
    text = text.strip() if isinstance(text, str) else ""
    return {"start": float(start or 0), "dur": float(dur or 0), "text": text}


def get_segments(video_id: str, languages=("en",)) -> list:
    """Return [{start, dur, text}] for a video, or [] if unavailable."""
    try:
        raw = _fetch_raw(video_id, languages)
    except Exception:
        return []
    segs = [_norm(s) for s in (raw or [])]
    return [s for s in segs if s["text"]]


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
