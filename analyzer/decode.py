"""Formula decode — pure statistics, no LLM needed for v1."""
import re
from collections import Counter
from datetime import datetime, timezone


def _to_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _dur_to_sec(d):
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m:
        return 0
    h, mi, s = m.groups()
    return int(h or 0) * 3600 + int(mi or 0) * 60 + int(s or 0)


STOP = set("the a an and or of to in on for with is are was were it its this that these those "
           "by at from as be has have had will would can you your we our they their he she his her "
           "not no but if then than so such into out up down over under de la el en ka ke ki ko se "
           "mein aur hai hain tha thi".split())


def decode(channel: dict, videos: list) -> dict:
    sn, st = channel["snippet"], channel["statistics"]
    subs = int(st.get("subscriberCount", 0))
    total_views = int(st.get("viewCount", 0))
    n = len(videos)

    views, likes, durs, gaps = [], [], [], []
    title_words, title_lens = Counter(), []
    hooks = Counter()
    prev_dt = None
    desc_tags, desc_hashtags = Counter(), Counter()
    upload_hours = Counter()
    upload_days = Counter()
    has_timestamps = 0
    has_links = 0
    titles_with_question = 0
    titles_with_brackets = 0

    for v in videos:
        s, vs, cd = v["snippet"], v.get("statistics", {}), v.get("contentDetails", {})
        views.append(int(vs.get("viewCount", 0)))
        likes.append(int(vs.get("likeCount", 0)))
        durs.append(_dur_to_sec(cd.get("duration")))
        dt = _to_dt(s["publishedAt"])
        upload_hours[dt.hour] += 1
        upload_days[dt.strftime("%A")] += 1
        if prev_dt:
            gaps.append((prev_dt - dt).total_seconds() / 86400)
        prev_dt = dt

        title = s["title"]
        title_lens.append(len(title))
        if "?" in title:
            titles_with_question += 1
        if any(c in title for c in ("[", "]", "(", ")")):
            titles_with_brackets += 1

        words = [w.strip(".,!?…\"'()").lower() for w in title.split()]
        title_words.update(w for w in words if w and w not in STOP and len(w) > 2)
        first3 = " ".join(words[:3])
        if first3:
            hooks[first3] += 1

        desc = s.get("description", "")
        if re.search(r"\b\d{1,2}:\d{2}\b", desc):
            has_timestamps += 1
        if "http://" in desc or "https://" in desc:
            has_links += 1

        desc_tags.update(t.strip().lower() for t in (v.get("snippet", {}).get("tags") or []))
        desc_hashtags.update(h.lower() for h in re.findall(r"#(\w+)", desc))

    views_sorted = sorted(views)
    avg_gap = sum(gaps) / len(gaps) if gaps else 0
    avg_views = sum(views) / max(n, 1)
    breakout = [v for v in videos
                if int(v.get("statistics", {}).get("viewCount", 0)) > avg_views * 3]

    return {
        "channel_title": sn["title"],
        "channel_id": channel["id"],
        "subs": subs,
        "total_views": total_views,
        "videos_analyzed": n,
        "avg_views": avg_views,
        "median_views": views_sorted[n // 2] if n else 0,
        "view_sub_ratio": avg_views / max(subs, 1),
        "avg_likes": sum(likes) / max(n, 1),
        "like_view_ratio": (sum(likes) / max(sum(views), 1)) * 100,
        "avg_duration_sec": sum(durs) / max(n, 1),
        "avg_gap_days": avg_gap,
        "weekly_cadence": round(7.0 / avg_gap, 2) if avg_gap > 0 else 0,
        "top_title_words": title_words.most_common(25),
        "top_hooks": hooks.most_common(15),
        "avg_title_len": sum(title_lens) / max(len(title_lens), 1),
        "titles_with_ellipsis": sum(1 for v in videos if "…" in v["snippet"]["title"] or "..." in v["snippet"]["title"]),
        "titles_with_question": titles_with_question,
        "titles_with_brackets": titles_with_brackets,
        "top_tags": desc_tags.most_common(20),
        "top_hashtags": desc_hashtags.most_common(15),
        "desc_stats": {
            "has_timestamps_count": has_timestamps,
            "has_links_count": has_links,
        },
        "upload_hours_utc": sorted(upload_hours.items()),
        "upload_days": sorted(upload_days.items(), key=lambda x: x[1], reverse=True),
        "breakout_count": len(breakout),
        "breakout_titles": [v["snippet"]["title"] for v in breakout[:10]],
        "breakout_details": [
            {
                "title": v["snippet"]["title"],
                "views": int(v.get("statistics", {}).get("viewCount", 0)),
                "multiplier": round(int(v.get("statistics", {}).get("viewCount", 0)) / max(avg_views, 1), 1)
            }
            for v in breakout[:8]
        ],
    }

