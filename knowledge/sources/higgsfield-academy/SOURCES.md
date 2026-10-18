# Higgsfield Academy — source tracking

Course catalog: https://higgsfield.ai/academy/courses
Scraped: Oct 18, 2026 (public course pages, no login needed)

## Status
- [x] Full catalog text scrape COMPLETE — 17 courses, 179 lessons
- [ ] Lesson video transcripts — NOT included (each mp4 ~100MB, ~180 videos
      = ~18GB; no subtitle tracks on the CDN files). Video URLs are saved
      per lesson if transcripts are ever needed via speech-to-text.
- [ ] 4 locked lessons in `ai-creation` (Create and Edit Assets, Shot Sizes
      and Prompting, Direct Your Own Scene, Course Field Guide) — require a
      free Higgsfield account; videos not embedded on public pages.

## Courses scraped (one .md file each)
| Course | Lessons | Level |
|---|---|---|
| blockbuster-4k — Blockbuster 4K: The AI Filmmaking Pipeline | 10 | Intermediate |
| santiago-cinematic — Build an Ultra-Realistic Short Film in 4K | 19 | — |
| ai-vfx-real-footage — Add AI VFX to Real Footage | 11 | — |
| ai-animated-short — Make an AI Animated Short | 11 | — |
| seedance-25-ai-filmmaking — How to evaluate AI filmmaking demos | 11 | — |
| ai-ad-3-step — The 3-Step Realistic AI Ad Workflow | 16 | — |
| claude-higgsfield-ai-ad-agency — Build an AI Ad Agency with Claude + Higgsfield | 12 | — |
| cinematic-realism-4k — Seedance 4K: Cinematic Realism | 8 | — |
| brand-visuals-ai — Build a Brand's Visuals with AI | 9 | — |
| cinematic-ad-e2e — Make a Cinematic Ad End-to-End | 10 | — |
| automate-faceless-niche — Automate a Faceless Niche Channel | 11 | — |
| faceless-channel — Build a Faceless Channel | 7 | Beginner |
| mix-ai-real-footage — Mix AI with Real Footage | 10 | — |
| build-3d-games-mcp — Build 3D Games with MCP | 10 | — |
| cinematic-car-commercial — Direct a cinematic AI car commercial | 11 | — |
| direct-ai-fight-scenes — Direct AI fight scenes through controlled iteration | 5 | — |
| ai-creation — AI Creation: First Steps | 8 | — |

Each file holds: title, level, duration, price, description, "what you'll
learn" bullets, and the full lesson list with lesson page + video mp4 URLs.
The knowledge loader (`knowledge/loader.py`) picks up all 17 files
automatically — ~59K chars of expert context for the LLM.
