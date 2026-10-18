"""NovaMind LLM Engine — Gemini API integration for deep-decode.

Generates:
1. Tool inference with confidence labels (High / Medium / Low)
2. Cheaper & open-source alternative tools
3. Content structure (hooks, pacing/WPM, open loops, CTA placement)
4. Tailor-made replication plan
5. 100x speed strategy (speed multipliers + quality guardrails)
"""
import json
import os
import re
import sys
import warnings
import requests

# Suppress urllib3 LibreSSL warning on macOS
warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL.*")

# NovaMind knowledge base (expert sources like Higgsfield Academy).
# Loaded as LLM context so Jarvis answers as a trained expert.
def _get_knowledge_context(max_chars: int = 40000) -> str:
    try:
        kb_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge")
        sys.path.insert(0, kb_dir)
        import loader as kb_loader
        return kb_loader.get_context(max_chars=max_chars)
    except Exception:
        return ""

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def get_gemini_api_key(api_key: str = None) -> str:
    """Return explicit key or check standard environment variables."""
    return api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""


def _call_gemini_api(prompt: str, api_key: str, model: str = DEFAULT_MODEL) -> str:
    """Make HTTP POST request to Google Generative Language REST endpoint."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json"
        }
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=180)
    except requests.RequestException as e:
        raise RuntimeError(f"Gemini API network request failed: {e}") from e

    if resp.status_code != 200:
        # If responseMimeType is not supported on certain legacy models, retry without it
        if "responseMimeType" in resp.text:
            del payload["generationConfig"]["responseMimeType"]
            resp = requests.post(url, json=payload, headers=headers, timeout=180)
        
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {resp.text}")

    data = resp.json()
    try:
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError(f"No candidates returned: {data}")
        return candidates[0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected response structure from Gemini API: {data}") from e


def _extract_json(text: str) -> dict:
    """Extract and parse JSON from LLM output, handling markdown fences if present."""
    text = text.strip()
    # Match ```json ... ``` or ``` ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()
    return json.loads(text)


def _build_prompt(decoded: dict, sample_videos: list, captions_map: dict) -> str:
    """Prepare rich reverse-engineering prompt for Gemini."""
    vids_meta = []
    for v in (sample_videos or [])[:5]:
        sn = v.get("snippet", {})
        st = v.get("statistics", {})
        vid_id = v.get("id", "")
        if isinstance(vid_id, dict):
            vid_id = vid_id.get("videoId", "")
        
        v_captions = (captions_map or {}).get(vid_id, {})
        transcript_snippet = v_captions.get("text", "")[:1200]  # First ~1200 chars
        stats = v_captions.get("stats", {})

        vids_meta.append({
            "title": sn.get("title", ""),
            "views": st.get("viewCount", "0"),
            "description_sample": sn.get("description", "")[:400],
            "tags": sn.get("tags", [])[:8],
            "transcript_sample": transcript_snippet,
            "pacing_stats": stats
        })

    prompt = f"""You are the core intelligence of NovaMind — an elite reverse-engineering system for YouTube automation channels.
Analyze the following YouTube channel fingerprint, video metadata, and transcript samples.

Channel Summary:
- Title: {decoded.get('channel_title')}
- Subscribers: {decoded.get('subs', 0)}
- Total Views: {decoded.get('total_views', 0)}
- Average Views/Video: {decoded.get('avg_views', 0):.0f}
- View/Sub Ratio: {decoded.get('view_sub_ratio', 0):.1f}x
- Upload Cadence: Every {decoded.get('avg_gap_days', 0):.1f} days
- Breakout Titles: {json.dumps(decoded.get('breakout_titles', [])[:5])}
- Top Title Keywords: {json.dumps([w for w, _ in decoded.get('top_title_words', [])[:10]])}
- Top 3-Word Hooks: {json.dumps([h for h, _ in decoded.get('top_hooks', [])[:6]])}

Sample Videos with Captions/Transcripts:
{json.dumps(vids_meta, indent=2)}

EXPERT KNOWLEDGE BASE (Higgsfield AI Academy + saved expert sources):
You have been trained on the following expert course material. Use its
frameworks, prompt patterns, and workflows when generating the replication
plan and 100x strategy below — cite specific techniques where relevant.
{_get_knowledge_context()}

TASK:
Perform a deep decode and return STRICT JSON with these EXACT 5 top-level keys:

1. "tool_inference": List of objects with:
   - "category": ("Voice / Narration", "Imagery & Visuals", "Editing & Motion", "Scriptwriting & Research")
   - "detected_tool": specific tool or method detected (e.g., "ElevenLabs AI Voice (Adam / George)", "Stock Footage (Storyblocks/Envato)", "Midjourney/Flux AI Images + Ken Burns", "CapCut / Premiere Pro templates")
   - "confidence": Exactly one of ("High", "Medium", "Low")
   - "evidence": Specific concrete reasoning (cadence, breath sounds, tags, visual rhythm, description credits)

2. "alternative_tools": List of objects with:
   - "original_tool": The inferred paid or proprietary tool
   - "cheaper_alternative": Open-source, free, or significantly cheaper tool (e.g., Piper TTS, Edge-TTS, Kokoro, Flux.1 Schnell, DaVinci Resolve Free, CapCut Free, Audacity, YouTube Audio Library)
   - "reason": Why it's a suitable replacement
   - "cost_savings": Estimated savings (e.g., "$50/month -> $0/month (Free/Self-hosted)")

3. "content_structure": Object with:
   - "hook_strategy": How the first 15-30 seconds grab viewers (curiosity gap, high-stakes question, shocking statement)
   - "pacing_and_wpm": Analysis of words per minute, speech rhythm, cut frequency
   - "open_loops": List of open loops planted early and resolved late to maximize watch time
   - "cta_placement": Where and how Call-To-Actions (likes, subscribe, comments, sponsors) are positioned

4. "replication_plan": List of step-by-step actionable phases to reproduce this channel format from scratch:
   (Step 1: Outlier Research, Step 2: Scripting & Hook Blueprint, Step 3: Voice Generation, Step 4: Visual Asset Generation, Step 5: Assembly & Motion, Step 6: Packaging & Thumbnail)

5. "strategy_100x": Object with:
   - "speed_multipliers": List of speed levers (templates, prompt batching, parallel asset generation, automated transcription)
   - "quality_guardrails": List of things that MUST NOT be automated (human script review, fact-checking, thumbnail emotional instinct, final QC review)

Return ONLY valid JSON.
"""
    return prompt


def _fallback_heuristic_analysis(decoded: dict, captions_map: dict = None) -> dict:
    """Smart heuristic fallback when no LLM API key is present."""
    avg_gap = decoded.get("avg_gap_days", 0)
    avg_views = decoded.get("avg_views", 0)
    top_words = [w for w, _ in decoded.get("top_title_words", [])[:8]]

    # Inspect captions if available
    wpm_list = []
    has_caps = False
    if captions_map:
        for vid_id, c in captions_map.items():
            st = c.get("stats", {})
            if st.get("has_captions"):
                has_caps = True
                wpm = st.get("wpm", 0)
                if wpm > 0:
                    wpm_list.append(wpm)

    avg_wpm = round(sum(wpm_list) / len(wpm_list), 1) if wpm_list else 150.0

    return {
        "is_fallback": True,
        "notice": "Generated via offline heuristic engine. Export GEMINI_API_KEY to activate deep LLM decode.",
        "tool_inference": [
            {
                "category": "Voice / Narration",
                "detected_tool": "AI Voice (ElevenLabs / WellSaid) or Studio Mic Narration",
                "confidence": "Medium",
                "evidence": f"Pacing averages ~{avg_wpm} WPM. Consistent cadence across upload schedule ({avg_gap:.1f}d gap)."
            },
            {
                "category": "Imagery & Visuals",
                "detected_tool": "AI Generated Art (Midjourney / Flux) + Motion Pan/Zoom",
                "confidence": "Medium",
                "evidence": "High-volume visual storytelling inferred from keywords: " + ", ".join(top_words[:4])
            },
            {
                "category": "Editing & Motion",
                "detected_tool": "CapCut / Premiere Pro Template Pipeline",
                "confidence": "High",
                "evidence": "Consistent title and description formatting indicates templated post-production."
            },
            {
                "category": "Scriptwriting & Research",
                "detected_tool": "LLM Assisted Scripting (Claude / ChatGPT Structured Research)",
                "confidence": "Medium",
                "evidence": "Systematic 3-word opening hook repetition detected in metadata."
            }
        ],
        "alternative_tools": [
            {
                "original_tool": "ElevenLabs ($22-$99/mo)",
                "cheaper_alternative": "Piper TTS / Edge-TTS / Kokoro",
                "reason": "High quality offline neural TTS voices with zero API token costs.",
                "cost_savings": "Save $250+/year in voice synthesis tokens"
            },
            {
                "original_tool": "Midjourney ($30-$60/mo)",
                "cheaper_alternative": "Flux.1 Schnell / Stable Diffusion XL (Local/ComfyUI)",
                "reason": "Open-weight image generation with photorealistic prompt adherence.",
                "cost_savings": "Save $360+/year in cloud generation subscriptions"
            },
            {
                "original_tool": "Epidemic Sound / Artlist ($15-$40/mo)",
                "cheaper_alternative": "YouTube Audio Library / Free Music Archive",
                "reason": "Direct royalty-free catalog with zero copyright strike risk.",
                "cost_savings": "Save $180+/year"
            },
            {
                "original_tool": "Adobe Premiere Pro ($239/yr)",
                "cheaper_alternative": "DaVinci Resolve (Free) + FFmpeg automation",
                "reason": "DaVinci Resolve offers industry-standard timeline and color grading for $0.",
                "cost_savings": "Save $239/year"
            }
        ],
        "content_structure": {
            "hook_strategy": "Opening 15s curiosity hook leveraging high-contrast keywords and emotional stakes.",
            "pacing_and_wpm": f"Estimated speech delivery: ~{avg_wpm} words/min with visual scene transitions every 3-4 seconds.",
            "open_loops": [
                "Primary premise question asked in the first 20 seconds",
                "Key revelation or climax withheld until the final 20% of runtime"
            ],
            "cta_placement": "Soft engagement ask midway through video; hard subscription and playlist CTA in the outro."
        },
        "replication_plan": [
            "1. Outlier Topic Mining: Filter top breakout topics using the >3x average view threshold.",
            "2. Script Blueprint: Write modular 3-act scripts using the top 3-word hook patterns.",
            "3. Voiceover Generation: Produce voice tracks normalized to -14 LUFS.",
            "4. Visual Asset Generation: Batch-generate thematic images and B-roll using prompt templates.",
            "5. Video Assembly: Cut video to audio beats with dynamic captions and sound effects.",
            "6. Packaging: Apply high-contrast title formula and minimalist thumbnail composition."
        ],
        "strategy_100x": {
            "speed_multipliers": [
                "Prompt Templates: Standardize scriptwriting prompts with fixed pacing constraints.",
                "Batch Processing: Generate 5-10 voiceover tracks and image sets in single batch runs.",
                "Assembly Presets: Create timeline presets in DaVinci Resolve / Premiere with preset zoom keyframes."
            ],
            "quality_guardrails": [
                "DO NOT automate script fact-checking: hallucinations destroy channel credibility.",
                "DO NOT automate thumbnail concept selection: human emotional instinct determines CTR.",
                "DO NOT bypass final audio review: check for mispronunciations and abrupt cuts."
            ]
        }
    }


def analyze_channel(decoded: dict, sample_videos: list = None, captions_map: dict = None,
                    api_key: str = None, model: str = DEFAULT_MODEL) -> dict:
    """Main entrypoint: analyzes channel data and transcripts using Gemini API.
    
    Falls back gracefully to heuristic engine if API key is not configured
    or if request encounters an error.
    """
    key = get_gemini_api_key(api_key)
    if not key:
        return _fallback_heuristic_analysis(decoded, captions_map)

    prompt = _build_prompt(decoded, sample_videos, captions_map)
    try:
        raw_output = _call_gemini_api(prompt, key, model=model)
        parsed = _extract_json(raw_output)
        parsed["is_fallback"] = False
        parsed["model_used"] = model
        return parsed
    except Exception as e:
        print(f"[Warning] Gemini API analysis failed: {e}. Falling back to heuristic baseline.")
        fb = _fallback_heuristic_analysis(decoded, captions_map)
        fb["api_error"] = str(e)
        return fb
