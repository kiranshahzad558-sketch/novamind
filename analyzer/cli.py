"""NovaMind Analyzer CLI — Phase 1.
Usage:  YT_API_KEY=... [GEMINI_API_KEY=...] python -m analyzer.cli "<channel url>" [--max 50]
Needs:
- YouTube Data API v3 key: https://console.cloud.google.com/apis/library/youtube.googleapis.com
- Optional Gemini API key: export GEMINI_API_KEY=... (falls back to smart heuristics if omitted)
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.youtube_client import YTClient
from analyzer.decode import decode
from analyzer.captions import get_segments, caption_stats
from analyzer.llm import analyze_channel
from analyzer.reporter import build_report
from memory.store import save_channel_profile


def main():
    ap = argparse.ArgumentParser(description="NovaMind channel deep-decode")
    ap.add_argument("channel", help="Channel URL, @handle, or channel ID")
    ap.add_argument("--max", type=int, default=50, help="Videos to analyze (default 50)")
    ap.add_argument("--out", default=None, help="Report path (default reports/<title>.md)")
    ap.add_argument("--memory-dir", default="memory", help="Directory for persistent channel profiles (default: memory/)")
    ap.add_argument("--gemini-key", default=None, help="Gemini API Key (or set GEMINI_API_KEY env var)")
    ap.add_argument("--gemini-model", default=None, help="Gemini Model (default gemini-1.5-flash)")
    ap.add_argument("--languages", default="en,hi,ur", help="Comma-separated caption languages (default: en,hi,ur)")
    ap.add_argument("--no-llm", action="store_true", help="Skip LLM analysis pass")
    args = ap.parse_args()

    key = os.environ.get("YT_API_KEY")
    if not key:
        sys.exit("YT_API_KEY env var missing. Get a key from Google Cloud Console "
                 "(YouTube Data API v3) and export YT_API_KEY=...")

    yt = YTClient(key)
    print("Resolving channel...")
    ch = yt.resolve_channel(args.channel)
    print(f"Channel: {ch['snippet']['title']}")
    print(f"Fetching {args.max} videos...")
    vids = yt.list_videos(ch, max_results=args.max)
    print(f"Got {len(vids)} videos. Decoding formula...")
    d = decode(ch, vids)

    # Fetch captions for top breakout & high-view videos
    langs = tuple(lang.strip() for lang in args.languages.split(",") if lang.strip())
    sorted_vids = sorted(vids, key=lambda x: int(x.get("statistics", {}).get("viewCount", 0)), reverse=True)
    sample_vids = sorted_vids[:5]

    print(f"Fetching captions for {len(sample_vids)} sample/breakout videos...")
    captions_map = {}
    for v in sample_vids:
        vid_id = v.get("id")
        if isinstance(vid_id, dict):
            vid_id = vid_id.get("videoId")
        if not vid_id:
            continue
        try:
            segments = get_segments(vid_id, languages=langs)
            text = " ".join(s["text"] for s in segments)
            stats = caption_stats(segments)
            captions_map[vid_id] = {
                "text": text,
                "segments": segments,
                "stats": stats
            }
        except Exception as e:
            print(f"  [Notice] Could not fetch captions for video {vid_id}: {e}")
            captions_map[vid_id] = {"text": "", "segments": [], "stats": {"has_captions": False}}

    d["captions_map"] = captions_map

    # Run Gemini LLM analysis pass
    if not args.no_llm:
        print("Running Gemini LLM reverse-engineering pass...")
        gemini_model = args.gemini_model or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        llm_res = analyze_channel(
            d,
            sample_videos=sample_vids,
            captions_map=captions_map,
            api_key=args.gemini_key,
            model=gemini_model
        )
        d["llm_analysis"] = llm_res

    report = build_report(d)

    os.makedirs("reports", exist_ok=True)
    safe = "".join(c if c.isalnum() else "_" for c in d["channel_title"])[:40]
    out = args.out or f"reports/{safe}_decode.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report written: {out}")

    # Save to persistent NovaMind memory
    mem_path = save_channel_profile(d, memory_dir=args.memory_dir)
    print(f"Memory profile saved: {mem_path}")


if __name__ == "__main__":
    main()
