"""Markdown decode report generator."""


def _fmt_num(x):
    if x >= 1_000_000:
        return f"{x/1_000_000:.2f}M"
    if x >= 1_000:
        return f"{x/1_000:.1f}K"
    return str(int(x))


def _fmt_dur(sec):
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def build_report(d: dict) -> str:
    L = []
    A = L.append
    A(f"# Channel Deep Decode — {d['channel_title']}\n")
    A(f"Channel ID: `{d['channel_id']}` · Videos analyzed: {d['videos_analyzed']}\n")

    A("## 1. Channel fingerprint")
    A(f"- Subscribers: **{_fmt_num(d['subs'])}** · Total views: **{_fmt_num(d['total_views'])}**")
    A(f"- Avg views/video: **{_fmt_num(d['avg_views'])}** (median {_fmt_num(d['median_views'])})")
    A(f"- View/sub ratio: **{d['view_sub_ratio']:.1f}x** "
      f"({'viral reach — non-subscribed audience' if d['view_sub_ratio'] > 10 else 'core audience driven'})")
    A(f"- Avg upload gap: **{d['avg_gap_days']:.1f} days**")
    A(f"- Avg duration: **{_fmt_dur(d['avg_duration_sec'])}** · Avg likes: **{_fmt_num(d['avg_likes'])}**")
    A(f"- Breakout videos (>3x avg views): **{d['breakout_count']}**")
    for t in d["breakout_titles"]:
        A(f"  - {t}")
    A("")

    A("## 2. Title formula")
    A(f"- Avg title length: **{d['avg_title_len']:.0f} chars**")
    A(f"- Titles with ellipsis: **{d['titles_with_ellipsis']}/{d['videos_analyzed']}**")
    A("- Top title keywords:")
    for w, c in d["top_title_words"][:15]:
        A(f"  - {w} ×{c}")
    A("- Top opening hooks (first 3 words):")
    for h, c in d["top_hooks"][:10]:
        A(f'  - "{h}" ×{c}')
    A("")

    A("## 3. Tags & hashtags")
    A("- Top tags: " + (", ".join(t for t, _ in d["top_tags"][:12]) or "—"))
    A("- Top hashtags: " + (", ".join("#" + h for h, _ in d["top_hashtags"][:12]) or "—"))
    A("")

    A("## 4. Upload timing (UTC hours)")
    A("- " + (", ".join(f"{h}:00 ×{c}" for h, c in d["upload_hours_utc"]) or "—"))
    A("")

    A("## 5. Tool inference (heuristic — verify manually)")
    A("- Voice: check 2-3 videos — consistent robotic cadence = AI voice; "
      "breath/mic variation = human.")
    A("- Imagery: ultra-consistent lighting + impossible camera moves = AI generated; "
      "watermarks/grain = stock.")
    A("- Pacing: rigid equal-length segments suggest templated AI pipeline.")
    A("")

    A("## 6. Replication plan (template)")
    A("1. Lock the title formula above into a title generator.")
    A("2. Match avg duration + segment rhythm from captions (Phase 1b).")
    A("3. Mirror description structure: hook para → hashtags → related bullets → keyword line.")
    A("4. Beat-strategy: out-publish on their avg gap ("
      f"{d['avg_gap_days']:.1f}d) while holding their quality bar — "
      "speed without the bar is spam.")
    A("")
    return "\n".join(L)
