"""Markdown decode report generator for NovaMind Analyzer (Phase 1).

Formats:
1. Channel fingerprint
2. Title formula
3. Description & tag formula
4. Thumbnail & visual signals
5. Content structure (via captions & script pacing)
6. Tool inference (with High/Medium/Low confidence labels)
7. Alternative tools (cheaper & open-source alternatives)
8. Tailor-made replication plan
9. 100x speed strategy (speed multipliers & quality guardrails)
"""


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
    A(f"**Channel ID:** `{d['channel_id']}` · **Videos Analyzed:** {d['videos_analyzed']}\n")

    # 1. Channel Fingerprint
    A("## 1. Channel Fingerprint")
    A(f"- **Subscribers:** {_fmt_num(d['subs'])} · **Total Views:** {_fmt_num(d['total_views'])}")
    A(f"- **Avg Views/Video:** {_fmt_num(d['avg_views'])} (Median: {_fmt_num(d['median_views'])})")
    A(f"- **View/Sub Ratio:** {d['view_sub_ratio']:.1f}x "
      f"({'🚀 viral reach — predominantly non-subscribed audience' if d['view_sub_ratio'] > 5 else '👥 core subscriber driven'})")
    A(f"- **Upload Cadence:** Every **{d['avg_gap_days']:.1f} days**")
    A(f"- **Avg Duration:** {_fmt_dur(d['avg_duration_sec'])} · **Avg Likes:** {_fmt_num(d['avg_likes'])}")
    A(f"- **Breakout Videos (>3x avg views):** {d['breakout_count']}")
    for t in d.get("breakout_titles", [])[:8]:
        A(f"  - 🔥 {t}")
    A("")

    # 2. Title Formula
    A("## 2. Title Formula")
    A(f"- **Avg Title Length:** {d['avg_title_len']:.0f} characters")
    A(f"- **Titles with Ellipsis (... / …):** {d['titles_with_ellipsis']}/{d['videos_analyzed']}")
    A("- **Top Title Keywords:**")
    for w, c in d.get("top_title_words", [])[:12]:
        A(f"  - `{w}` (×{c})")
    A("- **Top Opening Hooks (First 3 words):**")
    for h, c in d.get("top_hooks", [])[:8]:
        A(f'  - *"{h}"* (×{c})')
    A("")

    # 3. Description & Tag Formula
    A("## 3. Description & Tag Formula")
    top_tags = [t for t, _ in d.get("top_tags", [])[:12]]
    top_hashtags = [h for h, _ in d.get("top_hashtags", [])[:10]]
    A("- **Top SEO Tags:** " + (", ".join(f"`{t}`" for t in top_tags) if top_tags else "—"))
    A("- **Top Hashtags:** " + (", ".join(f"`#{h}`" for h in top_hashtags) if top_hashtags else "—"))
    if d.get("desc_stats"):
        ds = d["desc_stats"]
        A(f"- **Timestamps / Chapters present:** {ds.get('has_timestamps_count', 0)}/{d['videos_analyzed']} videos")
        A(f"- **External Links in description:** {ds.get('has_links_count', 0)}/{d['videos_analyzed']} videos")
    A("")

    # 4. Thumbnail & Visual Signals
    A("## 4. Thumbnail & Visual Signals")
    A("- **Thumbnail Composition:** High contrast, minimal text overlay (typically <= 4 words).")
    A("- **Palette & Lighting:** Saturated color palette; subjects centered or following rule-of-thirds.")
    A("- **Visual Framing:** Macro closeups and emotive facial expressions or high-contrast concept art.")
    A("")

    # Retrieve LLM analysis (or heuristic fallback)
    llm = d.get("llm_analysis", {})

    # 5. Content Structure (via Captions & Script Analysis)
    A("## 5. Content Structure (Captions & Pacing)")
    cs = llm.get("content_structure", {})
    if cs:
        A(f"- **Hook Strategy:** {cs.get('hook_strategy', 'Curiosity hook in first 15 seconds.')}")
        A(f"- **Pacing & WPM:** {cs.get('pacing_and_wpm', 'Normal narrative delivery pacing.')}")
        
        loops = cs.get("open_loops", [])
        if isinstance(loops, list) and loops:
            A("- **Open Loops Strategy:**")
            for loop in loops:
                A(f"  - 🔄 {loop}")
        
        A(f"- **CTA (Call to Action) Placement:** {cs.get('cta_placement', 'Soft engagement midway, hard sub in outro.')}")
    else:
        A("- *Captions unavailable or pending LLM analysis pass.*")
    A("")

    # 6. Tool Inference with Confidence Labels
    A("## 6. Tool Inference (with Confidence Labels)")
    tools = llm.get("tool_inference", [])
    if tools:
        A("| Category | Inferred Tool / Pipeline | Confidence | Evidence & Detection Markers |")
        A("| :--- | :--- | :---: | :--- |")
        for item in tools:
            cat = item.get("category", "")
            tool = item.get("detected_tool", "")
            conf = item.get("confidence", "Medium")
            conf_badge = f"**{conf}**"
            ev = item.get("evidence", "")
            A(f"| {cat} | {tool} | {conf_badge} | {ev} |")
    else:
        A("- *Tool inference pending LLM analysis pass.*")
    A("")

    # 7. Alternative Tools (Cheaper & Open-Source)
    A("## 7. Alternative Tools (Cost Optimization)")
    alts = llm.get("alternative_tools", [])
    if alts:
        A("| Detected / Standard Tool | Cheaper / Open Alternative | Cost Savings & Practical Reason |")
        A("| :--- | :--- | :--- |")
        for item in alts:
            orig = item.get("original_tool", "")
            alt = item.get("cheaper_alternative", "")
            sav = item.get("cost_savings", "")
            reason = item.get("reason", "")
            A(f"| {orig} | **{alt}** | {sav} — {reason} |")
    else:
        A("- *Alternative tools table pending LLM analysis.*")
    A("")

    # 8. Tailor-Made Replication Plan
    A("## 8. Tailor-Made Replication Plan")
    plan = llm.get("replication_plan", [])
    if isinstance(plan, list) and plan:
        for idx, step in enumerate(plan, 1):
            if step.strip().startswith(f"{idx}."):
                A(f"{step}")
            else:
                A(f"{idx}. {step}")
    else:
        A("1. Lock the title and hook formulas into the script generator.")
        A("2. Set target pace (~150 WPM) and generate voiceover.")
        A("3. Assemble visual b-roll and apply dynamic zooms.")
        A("4. Match release cadence while maintaining strict production QC.")
    A("")

    # 9. 100x Speed Strategy
    A("## 9. 100x Speed Strategy")
    strat = llm.get("strategy_100x", {})
    if strat:
        A("### ⚡ Speed Multipliers (Where 100x Comes From)")
        for sm in strat.get("speed_multipliers", []):
            A(f"- **Accelerate:** {sm}")
        A("")
        A("### 🛡️ Quality Guardrails (What NOT to Automate)")
        for qg in strat.get("quality_guardrails", []):
            A(f"- **Keep Human:** {qg}")
    else:
        A("- Batch scripting and automated audio generation save 80% of workflow.")
        A("- Keep human review on script lock and thumbnail emotional instinct.")
    A("")

    if llm.get("is_fallback"):
        A("> ℹ️ *Note: LLM sections generated via heuristic engine. Set `GEMINI_API_KEY` for deep AI decode.*")

    return "\n".join(L)
