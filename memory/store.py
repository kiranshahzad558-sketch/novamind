"""Persistent memory layer for NovaMind.

Stores analyzed YouTube channel profiles as structured JSON documents.
Survives restarts and provides the knowledge base for:
- Phase 1: Analyzer (historical benchmarks & comparisons)
- Phase 2: Companion (context awareness of analyzed channels)
- Phase 3: Factory (direct execution blueprints & tool constraints)
"""
import json
import os
import re
from datetime import datetime, timezone


def _safe_filename(name: str, channel_id: str = "") -> str:
    """Generate a clean filesystem-safe filename for channel memory."""
    safe = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    safe = re.sub(r"[-\s]+", "_", safe)
    if not safe:
        safe = channel_id or "channel"
    return safe[:50].strip("_")


def build_channel_profile(d: dict) -> dict:
    """Build a normalized, persistent JSON profile from decoded channel data."""
    llm = d.get("llm_analysis", {})
    cs = llm.get("content_structure", {})
    strat = llm.get("strategy_100x", {})
    desc_stats = d.get("desc_stats", {})

    # Determine caption presence and WPM
    captions_map = d.get("captions_map", {})
    wpm_vals = [
        c.get("stats", {}).get("wpm", 0)
        for c in captions_map.values()
        if c.get("stats", {}).get("wpm", 0) > 0
    ]
    avg_wpm = round(sum(wpm_vals) / len(wpm_vals), 1) if wpm_vals else 150.0

    return {
        "schema_version": "1.0",
        "channel_id": d.get("channel_id", ""),
        "channel_title": d.get("channel_title", "Unknown Channel"),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "channel_stats": {
            "subscribers": int(d.get("subs", 0)),
            "total_views": int(d.get("total_views", 0)),
            "videos_analyzed": int(d.get("videos_analyzed", 0)),
            "avg_views": round(float(d.get("avg_views", 0)), 1),
            "median_views": float(d.get("median_views", 0)),
            "view_sub_ratio": round(float(d.get("view_sub_ratio", 0)), 2),
            "avg_likes": round(float(d.get("avg_likes", 0)), 1),
            "like_view_ratio": round(float(d.get("like_view_ratio", 0)), 2),
            "avg_duration_sec": round(float(d.get("avg_duration_sec", 0)), 1),
            "breakout_count": int(d.get("breakout_count", 0)),
            "breakout_titles": d.get("breakout_titles", [])[:10],
            "breakout_details": d.get("breakout_details", [])[:8],
        },
        "upload_pattern": {
            "avg_gap_days": round(float(d.get("avg_gap_days", 0)), 2),
            "weekly_cadence": round(float(d.get("weekly_cadence", 0)), 2),
            "peak_hours_utc": [h for h, _ in sorted(d.get("upload_hours_utc", []), key=lambda x: x[1], reverse=True)[:4]],
            "upload_days_distribution": dict(d.get("upload_days", [])),
        },
        "title_analysis": {
            "avg_title_len": round(float(d.get("avg_title_len", 0)), 1),
            "titles_with_ellipsis": int(d.get("titles_with_ellipsis", 0)),
            "titles_with_question": int(d.get("titles_with_question", 0)),
            "titles_with_brackets": int(d.get("titles_with_brackets", 0)),
            "top_keywords": [w for w, _ in d.get("top_title_words", [])[:20]],
            "top_hooks": [h for h, _ in d.get("top_hooks", [])[:10]],
        },
        "caption_pacing_analysis": {
            "has_captions": any(c.get("stats", {}).get("has_captions", False) for c in captions_map.values()) if captions_map else True,
            "avg_wpm": avg_wpm,
            "hook_strategy": cs.get("hook_strategy", "Curiosity hook in first 15 seconds."),
            "pacing_and_wpm": cs.get("pacing_and_wpm", f"Delivery pacing at ~{avg_wpm} WPM."),
            "open_loops": cs.get("open_loops", []),
            "cta_placement": cs.get("cta_placement", "Soft engagement mid-video, subscription outro."),
        },
        "tool_inference": llm.get("tool_inference", []),
        "alternative_tools": llm.get("alternative_tools", []),
        "description_formula": {
            "top_tags": [t for t, _ in d.get("top_tags", [])[:15]],
            "top_hashtags": [h for h, _ in d.get("top_hashtags", [])[:10]],
            "has_timestamps_count": desc_stats.get("has_timestamps_count", 0),
            "has_links_count": desc_stats.get("has_links_count", 0),
        },
        "replication_plan": llm.get("replication_plan", []),
        "strategy_100x": {
            "speed_multipliers": strat.get("speed_multipliers", []),
            "quality_guardrails": strat.get("quality_guardrails", []),
        },
    }


def save_channel_profile(d: dict, memory_dir: str = "memory") -> str:
    """Save an analyzed channel's profile into memory/ as JSON.
    
    Also maintains a memory/index.json registry for rapid lookup.
    Returns the relative path to the saved file.
    """
    os.makedirs(memory_dir, exist_ok=True)
    profile = build_channel_profile(d)

    safe_name = _safe_filename(profile["channel_title"], profile["channel_id"])
    filename = f"{safe_name}.json"
    filepath = os.path.join(memory_dir, filename)

    # Write the full channel profile JSON
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    # Update memory/index.json
    index_path = os.path.join(memory_dir, "index.json")
    index = {}
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
        except Exception:
            index = {}

    index[profile["channel_id"]] = {
        "channel_title": profile["channel_title"],
        "channel_id": profile["channel_id"],
        "file": filename,
        "analyzed_at": profile["analyzed_at"],
        "subscribers": profile["channel_stats"]["subscribers"],
        "avg_views": profile["channel_stats"]["avg_views"],
        "breakouts": profile["channel_stats"]["breakout_count"],
    }

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    return filepath


def load_channel_profile(identifier: str, memory_dir: str = "memory") -> dict:
    """Load a channel profile by channel_id, filename, or safe title."""
    # 1. Direct path check
    candidate = os.path.join(memory_dir, identifier if identifier.endswith(".json") else f"{identifier}.json")
    if os.path.exists(candidate):
        with open(candidate, "r", encoding="utf-8") as f:
            return json.load(f)

    # 2. Check index.json
    index_path = os.path.join(memory_dir, "index.json")
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
            if identifier in index:
                file_target = os.path.join(memory_dir, index[identifier]["file"])
                if os.path.exists(file_target):
                    with open(file_target, "r", encoding="utf-8") as f:
                        return json.load(f)
        except Exception:
            pass

    return {}


def list_channel_profiles(memory_dir: str = "memory") -> list:
    """Return summary list of all channel profiles recorded in memory."""
    index_path = os.path.join(memory_dir, "index.json")
    if not os.path.exists(index_path):
        return []
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
            return list(index.values())
    except Exception:
        return []
