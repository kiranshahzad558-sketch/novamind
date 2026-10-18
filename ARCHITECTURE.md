# NovaMind — Architecture Blueprint

> Status: Phase 1 in build. Phases 2-3 scaffolded.
> Goal: Stonic-AI-class desktop companion + autonomous YouTube replication factory,
> with a persistent "mind" (memory + reasoning + reflection loops).

## The honest model of "human mind"

There is no human mind inside software. What NovaMind implements instead —
the engineering equivalent of "thinks like a human" for its job:

1. **Persistent memory** (`memory/`) — facts, preferences, decisions, past analyses.
   Survives restarts. Editable, forgettable. Nothing is re-learned twice.
2. **Reasoning loop** — every task goes: observe → plan → act → verify → reflect.
   Reflection writes lessons back to memory (this is the "learning" part).
3. **Goal stack** — the user states an outcome ("replicate this channel");
   the planner decomposes it into steps and works them in order.
4. **Human checkpoints** — the system ASKS before irreversible actions
   (upload, spend money, delete). This is a safety rail, not a limitation.

It will *feel* like a mind for its job. It will not *be* a human mind.
Anyone promising literal human-like consciousness in a desktop app is selling fantasy.

## System map

```
┌─────────────────────────────────────────────────────────┐
│                    NOVAMIND CORE ("the mind")            │
│  memory/ ←→ reasoning loop ←→ goal stack ←→ reflection │
└──────┬──────────────────┬──────────────────┬────────────┘
       │                  │                  │
┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
│  COMPANION  │    │  ANALYZER   │    │   FACTORY   │
│ (Phase 2)   │    │ (Phase 1)   │    │ (Phase 3)   │
│             │    │  ← BUILDING │    │             │
│ voice I/O   │    │ channel     │    │ script gen  │
│ screen ctl  │    │ deep-decode │    │ image gen   │
│ app control │    │ tool detect │    │ TTS         │
│ characters  │    │ beat-plan   │    │ assembly    │
│ awareness   │    │ 100x strategy│    │ QC loops    │
└─────────────┘    └─────────────┘    │ upload      │
                                     └─────────────┘
```

## Phase 1 — ANALYZER (now building)

Input: a YouTube channel URL.
Output: `reports/<channel>_decode.md` containing:

1. Channel fingerprint — subs, upload cadence, avg views, view/sub ratio,
   outliers (breakout videos).
2. Title formula — patterns, hooks, keywords, length stats, ellipsis/emoji usage.
3. Description formula — structure, hashtags, link blocks, keyword lines.
4. Thumbnail signals — from titles + any available data (no face recognition;
   compositional notes only).
5. Content structure — via captions: pacing, segment count, narration style,
   open loops, CTA placement.
6. Tool inference — AI voice vs human, stock vs AI imagery, editing markers —
   with confidence labels (inferred, not proven).
7. Alternative tools — for each inferred tool, cheaper/open alternatives.
8. Replication plan — step-by-step pipeline to reproduce the format.
9. 100x strategy — where speed comes from (templates, batching, parallel gen)
   and where the quality bar lives (what NOT to automate).

Tech: YouTube Data API v3 (official, needs API key) + caption fetch +
LLM analysis pass. No scraping hacks — API-only, stable.

## Phase 2 — COMPANION (scaffolded)

Stonic-class desktop shell: voice I/O (STT/TTS), screen+app control agent,
characters/personalities, memory UI, themes. Cross-platform: macOS + Windows
from day one (user runs a Mac; reference product is Windows-only, NovaMind
will not be). Python core is portable; platform-specific bits (screen
control, global hotkeys, installers) get per-OS adapters.
Built on the same core mind as Analyzer/Factory — one memory, one voice.

## Phase 3 — FACTORY (scaffolded)

Autonomous replication: script → images → TTS → assembly → QC loops →
upload draft. Human checkpoints at: script lock, thumbnail, final review.
Cost guard: per-video budget cap, kill-switch on runaway spend.
Key rule learned from Stonic's changelog: NEVER let an agent run
unattended without a watchdog — agents stall, loop, and burn budget.

## Non-goals (will NOT be built)

- Literal consciousness / "real human mind" — not possible, not promised.
- Fully unattended publishing with zero human review — unsafe, against
  YouTube policy risk posture.
- Windows-only — must run on macOS AND Windows.

## Cost model (directional, verify per provider)

Analyzer: ~free (YouTube API quota) + one LLM call per channel.
Factory per video: image API calls + TTS + LLM tokens + compute.
Budget cap is a first-class feature, not an afterthought.
