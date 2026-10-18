# YouTube Ideation Decoder — source tracking

User-supplied expert prompt (Oct 18 2026): a "decoder prompt" that extracts the
reward ENGINE from any niche's winning videos and generates evidence-ranked
video ideas using live research (YouTube/Reddit/news/trends).

Role in NovaMind: this is the ideation brain. When Jarvis analyzes a channel
(Phase 1 analyzer) or plans replication (Phase 3 factory), it uses this
prompt's PROCESS (Steps A–F) to turn decode data into video ideas — never
guessing, research first, outliers weighted 3x.

## Files
- `ideation-decoder-prompt.md` — the full prompt, verbatim (reusable template)

## Status
- [x] Saved to knowledge base (Oct 18 2026)
- [x] Auto-loaded by knowledge/loader.py → fed to LLM as expert context
- [ ] Wired as the default ideation template in analyzer (Phase 1 Step 3)
