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
python -m analyzer.cli "https://www.youtube.com/@SomeChannel" --max 50
# report: reports/<channel>_decode.md
```

Get a free API key: Google Cloud Console → enable "YouTube Data API v3" →
Credentials → API key. Free quota is enough for channel analysis.

## Project layout
```
analyzer/    Phase 1 — channel deep-decode (youtube_client, decode, reporter, cli)
companion/   Phase 2 — desktop shell (scaffold)
factory/     Phase 3 — autonomous video pipeline (scaffold)
memory/      the mind's persistent memory (all phases share this)
reports/     analyzer output (git-ignored in real use)
```

## Opening in Antigravity
This is a plain Python project — open `~/workspace/novamind` as a folder
in Antigravity (or any IDE) and keep building from here. No lock-in.
