"""No-API-key YouTube client — parses public channel page HTML.

No Cloud Console, no API key, no quota. Reads the same public page any
browser loads and shapes the data exactly like youtube_client.YTClient
so decode.py / reporter.py / cli.py work unchanged.

Limitations vs the API: view counts are the public rounded figures,
publish dates are derived from relative labels ("3 weeks ago"),
descriptions/tags/likes are not on the listing page (left empty).
"""
import json
import re
from datetime import datetime, timedelta, timezone

import requests
import yt_dlp

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def _find(o, key, out):
    if isinstance(o, dict):
        if key in o:
            out.append(o[key])
        for v in o.values():
            _find(v, key, out)
    elif isinstance(o, list):
        for v in o:
            _find(v, key, out)


def _txt(x) -> str:
    if isinstance(x, dict):
        if "content" in x and isinstance(x["content"], str):
            return x["content"]
        if "text" in x and isinstance(x["text"], str):
            return x["text"]
        runs = x.get("runs")
        if runs:
            return "".join(r.get("text", "") for r in runs)
    return str(x or "")


def _parse_views(label: str) -> int:
    label = (label or "").lower().replace("views", "").replace("view", "").strip()
    if not label or label in ("no", "none"):
        return 0
    m = re.fullmatch(r"([\d.]+)\s*(thousand|million|billion|k|m|b)?", label)
    if not m:
        return 0
    num, unit = float(m.group(1)), (m.group(2) or "")
    mult = {"thousand": 1e3, "k": 1e3, "million": 1e6, "m": 1e6,
            "billion": 1e9, "b": 1e9}.get(unit, 1)
    return int(num * mult)


def _parse_relative(label: str) -> str:
    # "3 weeks ago" -> approx ISO date
    m = re.fullmatch(r"(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago", (label or "").lower())
    if not m:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    n, unit = int(m.group(1)), m.group(2)
    days = {"second": 0, "minute": 0, "hour": 0, "day": 1, "week": 7,
            "month": 30, "year": 365}[unit]
    dt = datetime.now(timezone.utc) - timedelta(days=n * days)
    return dt.isoformat().replace("+00:00", "Z")


def _parse_dur(label: str) -> str:
    # "35:38" or "1:02:10" -> ISO 8601
    parts = (label or "").strip().split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        return "PT0S"
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0, parts[0], parts[1]
    else:
        return "PT0S"
    out = "PT"
    if h:
        out += f"{h}H"
    if m:
        out += f"{m}M"
    return out + f"{s}S"


def _videos_url(url_or_id: str) -> str:
    u = url_or_id.strip()
    if re.fullmatch(r"UC[\w-]{22}", u):
        return f"https://www.youtube.com/channel/{u}/videos"
    if "/videos" not in u and "/streams" not in u and "/shorts" not in u:
        u = u.rstrip("/") + "/videos"
    return u


def _page_data(url: str) -> dict:
    r = requests.get(url, headers={"User-Agent": _UA}, timeout=30)
    r.raise_for_status()
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", r.text, re.S)
    if not m:
        raise RuntimeError("Channel page parse failed (no ytInitialData)")
    return json.loads(m.group(1))


class NoKeyClient:
    def resolve_channel(self, url_or_id: str) -> dict:
        url = _videos_url(url_or_id)
        # channel id + subs via yt-dlp flat (works, no bot wall on playlists)
        cid, subs, title = "", 0, ""
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True,
                                   "extract_flat": True, "playlistend": 1,
                                   "user_agent": _UA}) as ydl:
                info = ydl.extract_info(url, download=False)
            cid = info.get("channel_id") or ""
            subs = info.get("channel_follower_count") or 0
            title = info.get("channel") or ""
        except Exception:
            pass
        if not title or not cid:
            data = _page_data(url)
            if not title:
                t = []
                _find(data, "title", t)
                title = _txt(t[0]) if t else "Unknown"
        m = re.search(r"UC[\w-]{22}", url_or_id)
        if m:
            cid = m.group(0)
        return {"id": cid,
                "snippet": {"title": title or "Unknown"},
                "statistics": {"subscriberCount": str(subs or 0),
                               "viewCount": "0"}}

    def list_videos(self, channel: dict, max_results: int = 30) -> list:
        data = _page_data(_videos_url(channel.get("id") or ""))
        items = []
        _find(data, "richItemRenderer", items)
        out = []
        for item in items[:max_results]:
            try:
                vm = item["content"]["lockupViewModel"]
            except (KeyError, TypeError):
                continue
            meta = vm.get("metadata", {}).get("lockupMetadataViewModel", {})
            title = _txt(meta.get("title", {}))
            if not title:
                continue
            rows = (meta.get("metadata", {})
                        .get("contentMetadataViewModel", {})
                        .get("metadataRows", []))
            views_label, age_label = "", ""
            if rows:
                parts = rows[0].get("metadataParts", [])
                if len(parts) > 0:
                    views_label = parts[0].get("accessibilityLabel", "")
                if len(parts) > 1:
                    age_label = parts[1].get("accessibilityLabel", "")
            # video id
            ids = []
            _find(vm, "videoId", ids)
            vid = ids[0] if ids else ""
            # duration from thumbnail overlay badge
            dur_label = ""
            badges = []
            _find(vm, "thumbnailBadgeViewModel", badges)
            for b in badges:
                t = b.get("text", "")
                if re.fullmatch(r"[\d:]+", str(t)):
                    dur_label = str(t)
                    break
            out.append({
                "id": vid,
                "snippet": {
                    "title": title,
                    "description": "",
                    "publishedAt": _parse_relative(age_label),
                    "tags": [],
                },
                "statistics": {
                    "viewCount": str(_parse_views(views_label)),
                    "likeCount": "0",
                },
                "contentDetails": {"duration": _parse_dur(dur_label)},
            })
        return out
