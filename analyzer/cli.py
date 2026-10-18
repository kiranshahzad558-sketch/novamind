"""NovaMind Analyzer CLI — Phase 1.
Usage:  YT_API_KEY=... python -m analyzer.cli "<channel url>" [--max 50]
Needs a YouTube Data API v3 key: https://console.cloud.google.com/apis/library/youtube.googleapis.com
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.youtube_client import YTClient
from analyzer.decode import decode
from analyzer.reporter import build_report


def main():
    ap = argparse.ArgumentParser(description="NovaMind channel deep-decode")
    ap.add_argument("channel", help="Channel URL, @handle, or channel ID")
    ap.add_argument("--max", type=int, default=50, help="Videos to analyze (default 50)")
    ap.add_argument("--out", default=None, help="Report path (default reports/<title>.md)")
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
    report = build_report(d)

    os.makedirs("reports", exist_ok=True)
    safe = "".join(c if c.isalnum() else "_" for c in d["channel_title"])[:40]
    out = args.out or f"reports/{safe}_decode.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report written: {out}")


if __name__ == "__main__":
    main()
