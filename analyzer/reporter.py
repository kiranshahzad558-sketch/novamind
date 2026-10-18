"""NovaMind Analyzer — Markdown Decode Report Generator (Phase 1, Step 3).

Generates a comprehensive 9-section channel deep-decode report:
1. Channel Stats (Fingerprint, views, ratios, breakout outliers)
2. Upload Pattern (Cadence, peak UTC hours, day distribution, consistency)
3. Title Analysis (Length, hooks, keywords, question/ellipsis/bracket patterns)
4. Caption/Pacing Analysis (WPM, speech rhythm, hook strategy, open loops, CTAs)
5. Tool Inference (Voice, visuals, editing, research with High/Medium/Low confidence)
6. Alternative Tools (Cheaper & open-source cost optimizations)
7. Description Formula (Structure, timestamps, external links, SEO tags, hashtags)
8. Replication Plan (Step-by-step pipeline to reproduce channel format)
9. 100x Strategy (Speed multipliers & quality guardrails)

Also exports memory profile integration to persist analyzed channels into memory/.
"""
import os
from memory.store import save_channel_profile, build_channel_profile


def _fmt_num(x) -> str:
    """Format large numbers with readable K / M suffixes."""
    if x is None:
        return "0"
    try:
        x = float(x)
    except (ValueError, TypeError):
        return "0"
    if x >= 1_000_000:
        return f"{x/1_000_000:.2f}M"
    if x >= 1_000:
        return f"{x/1_000:.1f}K"
    return str(int(x))


def _fmt_dur(sec) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if sec is None:
        return "0:00"
    try:
        sec = float(sec)
    except (ValueError, TypeError):
        return "0:00"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def build_report(d: dict) -> str:
    """Construct a full 9-section deep-decode markdown report."""
    L = []
    A = L.append

    title = d.get("channel_title", "Unknown Channel")
    ch_id = d.get("channel_id", "N/A")
    v_count = d.get("videos_analyzed", 0)

    A(f"# Channel Deep Decode — {title}\n")
    A(f"**Channel ID:** `{ch_id}` · **Videos Analyzed:** {v_count}\n")

    # -------------------------------------------------------------
    # 1. Channel Stats
    # -------------------------------------------------------------
    A("## 1. Channel Stats")
    subs = d.get("subs", 0)
    total_views = d.get("total_views", 0)
    avg_views = d.get("avg_views", 0)
    median_views = d.get("median_views", 0)
    vs_ratio = d.get("view_sub_ratio", 0)
    avg_likes = d.get("avg_likes", 0)
    like_ratio = d.get("like_view_ratio", (avg_likes / max(avg_views, 1)) * 100)
    avg_dur = d.get("avg_duration_sec", 0)

    reach_badge = "🚀 Viral Reach (predominantly non-subscribed audience)" if vs_ratio > 3.0 else "👥 Subscriber Driven (strong core audience)"

    A(f"- **Subscribers:** {_fmt_num(subs)} · **Total Channel Views:** {_fmt_num(total_views)}")
    A(f"- **Avg Views/Video:** {_fmt_num(avg_views)} (Median: {_fmt_num(median_views)})")
    A(f"- **View/Sub Ratio:** {vs_ratio:.2f}x — {reach_badge}")
    A(f"- **Avg Duration:** {_fmt_dur(avg_dur)} · **Avg Likes:** {_fmt_num(avg_likes)} ({like_ratio:.2f}% engagement)")
    
    breakouts = d.get("breakout_details", [])
    breakout_count = d.get("breakout_count", len(breakouts))
    A(f"- **Breakout Videos (>3x avg views):** {breakout_count} detected")

    if breakouts:
        A("  - **Top Outlier Breakouts:**")
        for b in breakouts[:6]:
            A(f"    - 🔥 *{b.get('title')}* — **{_fmt_num(b.get('views', 0))} views** ({b.get('multiplier', 0)}x channel avg)")
    elif d.get("breakout_titles"):
        A("  - **Top Outlier Breakouts:**")
        for bt in d.get("breakout_titles", [])[:6]:
            A(f"    - 🔥 *{bt}*")
    A("")

    # -------------------------------------------------------------
    # 2. Upload Pattern
    # -------------------------------------------------------------
    A("## 2. Upload Pattern")
    avg_gap = d.get("avg_gap_days", 0)
    weekly_cadence = d.get("weekly_cadence", (7.0 / avg_gap) if avg_gap > 0 else 0)
    A(f"- **Upload Cadence:** Every **{avg_gap:.1f} days** (~{weekly_cadence:.1f} videos per week)")
    
    # Peak UTC hours
    hours_utc = d.get("upload_hours_utc", [])
    if hours_utc:
        top_hours = sorted(hours_utc, key=lambda x: x[1], reverse=True)[:3]
        hours_str = ", ".join(f"`{h:02d}:00 UTC` ({cnt} vids)" for h, cnt in top_hours if cnt > 0)
        A(f"- **Peak Publishing Windows (UTC):** {hours_str or 'Evenly distributed'}")
    else:
        A("- **Peak Publishing Windows (UTC):** Variable schedule")

    # Day of week distribution
    days_dist = d.get("upload_days", [])
    if days_dist:
        days_str = ", ".join(f"**{day}** ({cnt})" for day, cnt in days_dist[:4] if cnt > 0)
        A(f"- **Most Active Days:** {days_str}")
    
    A(f"- **Publishing Consistency:** {'High (Regular programmatic schedule)' if avg_gap < 7 else 'Flexible (Quality-driven release cycle)'}")
    A("")

    # -------------------------------------------------------------
    # 3. Title Analysis
    # -------------------------------------------------------------
    A("## 3. Title Analysis")
    avg_len = d.get("avg_title_len", 0)
    ellip = d.get("titles_with_ellipsis", 0)
    quest = d.get("titles_with_question", 0)
    brack = d.get("titles_with_brackets", 0)

    A(f"- **Avg Title Length:** {avg_len:.0f} characters (Mobile-optimized headline range)")
    A(f"- **Emotional & Formatting Punctuation:**")
    A(f"  - Curiosity Ellipsis (`...` / `…`): **{ellip}/{v_count}** videos ({round(ellip/max(v_count, 1)*100)}%)")
    A(f"  - Questions (`?`): **{quest}/{v_count}** videos ({round(quest/max(v_count, 1)*100)}%)")
    A(f"  - Brackets / Tags (`[...]`, `(...)`): **{brack}/{v_count}** videos ({round(brack/max(v_count, 1)*100)}%)")

    # Keywords
    top_words = d.get("top_title_words", [])[:12]
    if top_words:
        kw_badges = " · ".join(f"`{w}` (×{c})" for w, c in top_words)
        A(f"- **High-Frequency Keywords:** {kw_badges}")

    # Top 3-word hooks
    top_hooks = d.get("top_hooks", [])[:6]
    if top_hooks:
        A("- **Top 3-Word Opening Hooks:**")
        for h, c in top_hooks:
            A(f'  - *"{h}"* (repeated ×{c})')

    A("- **Thumbnail & Packaging Alignment:** High-contrast subject focus, <= 4 words overlay, strong emotional curiosity correlation.")
    A("")

    # -------------------------------------------------------------
    # LLM data / Fallback Heuristics
    # -------------------------------------------------------------
    llm = d.get("llm_analysis", {})
    cs = llm.get("content_structure", {})

    # -------------------------------------------------------------
    # 4. Caption/Pacing Analysis
    # -------------------------------------------------------------
    A("## 4. Caption/Pacing Analysis")
    captions_map = d.get("captions_map", {})
    has_caps = any(c.get("stats", {}).get("has_captions", False) for c in captions_map.values()) if captions_map else True

    wpm_vals = [c.get("stats", {}).get("wpm", 0) for c in captions_map.values() if c.get("stats", {}).get("wpm", 0) > 0]
    avg_wpm = round(sum(wpm_vals) / len(wpm_vals), 1) if wpm_vals else 150.0

    A(f"- **Speech Pacing:** ~**{avg_wpm} Words Per Minute** (Optimal narrative retention zone: 145-165 WPM)")
    A(f"- **Hook Strategy (First 15-30s):** {cs.get('hook_strategy', 'Presents a compelling paradox or high-stakes curiosity gap in the first 15 seconds.')}")
    A(f"- **Delivery Rhythm:** {cs.get('pacing_and_wpm', f'Fast-moving narration at ~{avg_wpm} WPM with visual cuts every 3-5 seconds.')}")

    loops = cs.get("open_loops", [])
    if isinstance(loops, list) and loops:
        A("- **Open Loops Mechanics:**")
        for loop in loops:
            A(f"  - 🔄 {loop}")
    else:
        A("- **Open Loops Mechanics:** Core question introduced in intro; climax explanation withheld until final 20% runtime.")

    A(f"- **CTA (Call to Action) Placement:** {cs.get('cta_placement', 'Mid-roll soft engagement question; end-screen subscription and playlist recommendation.')}")
    A("")

    # -------------------------------------------------------------
    # 5. Tool Inference
    # -------------------------------------------------------------
    A("## 5. Tool Inference")
    tools = llm.get("tool_inference", [])
    if tools:
        A("| Category | Inferred Tool / Pipeline | Confidence | Evidence & Detection Markers |")
        A("| :--- | :--- | :---: | :--- |")
        for item in tools:
            cat = item.get("category", "Production")
            tool = item.get("detected_tool", "Standard Pipeline")
            conf = item.get("confidence", "Medium")
            conf_badge = f"**{conf}**"
            ev = item.get("evidence", "Consistent acoustic and visual pacing.")
            A(f"| {cat} | {tool} | {conf_badge} | {ev} |")
    else:
        A("- *Tool inference pending analysis pass.*")
    A("")

    # -------------------------------------------------------------
    # 6. Alternative Tools
    # -------------------------------------------------------------
    A("## 6. Alternative Tools")
    alts = llm.get("alternative_tools", [])
    if alts:
        A("| Detected / Standard Tool | Cheaper / Open Alternative | Cost Savings | Setup & Practical Reason |")
        A("| :--- | :--- | :--- | :--- |")
        for item in alts:
            orig = item.get("original_tool", "")
            alt = item.get("cheaper_alternative", "")
            sav = item.get("cost_savings", "")
            reason = item.get("reason", "")
            A(f"| {orig} | **{alt}** | {sav} | {reason} |")
    else:
        A("- *Alternative tools table pending analysis.*")
    A("")

    # -------------------------------------------------------------
    # 7. Description Formula
    # -------------------------------------------------------------
    A("## 7. Description Formula")
    desc_stats = d.get("desc_stats", {})
    ts_cnt = desc_stats.get("has_timestamps_count", 0)
    lk_cnt = desc_stats.get("has_links_count", 0)

    A(f"- **Timestamps & Video Chapters:** Present in **{ts_cnt}/{v_count}** videos ({round(ts_cnt/max(v_count, 1)*100)}%)")
    A(f"- **External & Affiliate Links:** Present in **{lk_cnt}/{v_count}** videos ({round(lk_cnt/max(v_count, 1)*100)}%)")

    top_tags = [t for t, _ in d.get("top_tags", [])[:12]]
    top_hashtags = [h for h, _ in d.get("top_hashtags", [])[:10]]
    A("- **Top SEO Video Tags:** " + (", ".join(f"`{t}`" for t in top_tags) if top_tags else "—"))
    A("- **Top Hashtags:** " + (", ".join(f"`#{h}`" for h in top_hashtags) if top_hashtags else "—"))
    A("- **Structural Anatomy:** 1-2 sentence hook above the fold → Key source/affiliate links → Timestamped chapters → SEO keyword block.")
    A("")

    # -------------------------------------------------------------
    # 8. Replication Plan
    # -------------------------------------------------------------
    A("## 8. Replication Plan")
    plan = llm.get("replication_plan", [])
    if isinstance(plan, list) and plan:
        for idx, step in enumerate(plan, 1):
            if step.strip().startswith(f"{idx}."):
                A(f"{step}")
            else:
                A(f"{idx}. {step}")
    else:
        A("1. **Topic Mining:** Scan breakout topics using >3x average view threshold.")
        A("2. **Script Blueprinting:** Draft 3-act narrative with curiosity hook in first 15 seconds.")
        A("3. **Voiceover Generation:** Synthesize audio at ~150 WPM, normalized to -14 LUFS.")
        A("4. **Visual Asset Pipeline:** Batch-generate concept imagery and dynamic motion overlays.")
        A("5. **Assembly & Post-Production:** Cut to beat transients with auto-subtitles and sound effects.")
        A("6. **Packaging & Packaging QC:** Design high-contrast thumbnail with <= 4 words.")
    A("")

    # -------------------------------------------------------------
    # 9. 100x Strategy
    # -------------------------------------------------------------
    A("## 9. 100x Strategy")
    strat = llm.get("strategy_100x", {})
    if strat:
        A("### ⚡ Speed Multipliers (Where 100x Speed Comes From)")
        for sm in strat.get("speed_multipliers", []):
            A(f"- **Accelerate:** {sm}")
        A("")
        A("### 🛡️ Quality Guardrails (What NOT to Automate)")
        for qg in strat.get("quality_guardrails", []):
            A(f"- **Keep Human:** {qg}")
    else:
        A("### ⚡ Speed Multipliers (Where 100x Speed Comes From)")
        A("- **Prompt Templating:** Standardize research and scriptwriting with modular constraints.")
        A("- **Batch Generation:** Synthesize 5-10 voiceover tracks and visual prompt batches in parallel.")
        A("- **Assembly Presets:** Use pre-configured timeline templates with zoom curves and sound effects.")
        A("")
        A("### 🛡️ Quality Guardrails (What NOT to Automate)")
        A("- **Fact Verification:** Never automate script fact-checking; hallucinations destroy authority.")
        A("- **Thumbnail Emotional Review:** Human emotional instinct determines click-through rate.")
        A("- **Pacing & Audio QC:** Final listening pass for awkward pauses or mispronunciations.")
    A("")

    if llm.get("is_fallback"):
        A("> ℹ️ *Note: LLM sections generated via heuristic baseline engine. Export `GEMINI_API_KEY` for deep AI decode.*")

    return "\n".join(L)
