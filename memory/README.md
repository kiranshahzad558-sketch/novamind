# NovaMind Core — Persistent Memory Store

This directory stores persistent, structured JSON profiles of analyzed YouTube channels, as well as core memory for NovaMind companion and factory modules.

## Architecture

- **`memory/store.py`**: Storage engine for saving, loading, and cataloging channel profiles.
- **`memory/<channel_name>.json`**: Individual channel deep-decode profiles.
- **`memory/index.json`**: Fast lookup catalog mapping channel IDs and titles to profiles.

## Profile Schema

Each channel profile contains:
1. `channel_stats`: Subscribers, total views, average views, median views, view-to-sub ratio, engagement rate, breakout outliers.
2. `upload_pattern`: Upload cadence (days), weekly volume, peak UTC publishing hours, day-of-week distribution.
3. `title_analysis`: Length metrics, curiosity ellipsis, questions, brackets, high-frequency keywords, 3-word opening hooks.
4. `caption_pacing_analysis`: Words per minute (WPM), speech delivery rhythm, intro hook strategy, open loops, CTA placement.
5. `tool_inference`: Inferred tools for voice, imagery, editing, scriptwriting, with confidence ratings (`High`, `Medium`, `Low`).
6. `alternative_tools`: Cost-optimized open-source and cheaper alternatives.
7. `description_formula`: Chapters, links, tags, hashtags, and description anatomy.
8. `replication_plan`: Step-by-step phased pipeline to reproduce the channel's format.
9. `strategy_100x`: Speed multipliers and human quality guardrails.
