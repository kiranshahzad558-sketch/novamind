# NovaMind

Stonic-AI-class desktop companion + autonomous YouTube replication factory —
with a persistent mind (memory + reasoning + reflection).

## Status
- **Phase 1 — Analyzer:** building (working CLI, needs `YT_API_KEY`)
- **Phase 2 — Companion:** scaffolded
- **Phase 3 — Factory:** scaffolded

Read `ARCHITECTURE.md` first — it explains what "human mind" actually means
here, honestly, and what will NOT be built.

## Quick start (Analyzer)

```bash
cd ~/workspace/novamind
pip install -r requirements.txt
export YT_API_KEY="tumhari_youtube_data_api_v3_key"
export GEMINI_API_KEY="optional_gemini_api_key"   # optional: falls back to smart heuristics if omitted

python -m analyzer.cli "https://www.youtube.com/@SomeChannel" --max 50
# Markdown report: reports/<channel>_decode.md (9 comprehensive sections)
# Memory profile:  memory/<channel>.json (persistent profile + memory/index.json)
```

Get a free API key: Google Cloud Console → enable "YouTube Data API v3" →
Credentials → API key. Free quota is enough for channel analysis.

### Report Sections (Step 3)
1. **Channel Stats:** Subscribers, total views, avg views, view/sub ratio, viral reach vs subscriber-driven badge, breakouts.
2. **Upload Pattern:** Upload gap, weekly cadence, peak UTC publishing hours, most active days.
3. **Title Analysis:** Length stats, hook words, curiosity ellipsis (`...`), question (`?`), and brackets markers.
4. **Caption/Pacing Analysis:** Words Per Minute (WPM), retention hooks, open loop mechanics, CTA placement.
5. **Tool Inference:** Detected voice, visual, and editing tools with confidence labels (High/Medium/Low).
6. **Alternative Tools:** Cheaper and open-source alternatives (Kokoro TTS, ComfyUI, etc.) for cost optimization.
7. **Description Formula:** Chapter timestamps, external links, top SEO video tags, hashtags.
8. **Replication Plan:** Step-by-step actionable recipe to mirror and beat the target channel.
9. **100x Strategy:** Automation speed multipliers and strict quality guardrails (what NOT to automate).

## Project layout
```
analyzer/    Phase 1 — channel deep-decode (youtube_client, decode, captions, llm, reporter, cli)
companion/   Phase 2 — desktop shell (scaffold)
factory/     Phase 3 — autonomous video pipeline (scaffold)
memory/      the mind's persistent memory (profiles JSON, index.json, store API)
reports/     analyzer output (git-ignored in real use)
```

## Opening in Antigravity
This is a plain Python project — open `~/workspace/novamind` as a folder
in Antigravity (or any IDE) and keep building from here. No lock-in.
