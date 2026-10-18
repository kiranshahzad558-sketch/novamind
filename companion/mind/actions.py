"""Action execution engine for NovaMind Companion.

Bridges conversational intent with NovaMind's core systems:
- Phase 1 Analyzer: runs full deep-decode on requested YouTube channels.
- memory/: retrieves past channel profiles and benchmarks.
- knowledge/: queries tool alternatives, retention formulas, and rules.
- personalities: switches character modes on voice/text command.
"""
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from analyzer.youtube_client import YTClient
try:
    from analyzer.nokey_client import NoKeyClient
except Exception:
    NoKeyClient = None
from analyzer.decode import decode
from analyzer.reporter import build_report
from memory.store import (
    save_channel_profile,
    load_channel_profile,
    list_channel_profiles,
)
from knowledge.loader import (
    search_tools,
    search_formulas,
    get_rules,
    get_tools_catalog,
)
from companion.personalities.manager import manager as persona_manager


class ActionDispatcher:
    """Dispatches user commands to concrete engine actions."""

    def __init__(self, memory_dir: str = "memory", reports_dir: str = "reports"):
        self.memory_dir = memory_dir
        self.reports_dir = reports_dir

    def handle_decode_channel(self, channel_target: str, max_videos: int = 50) -> Dict[str, Any]:
        """Execute Phase 1 channel deep-decode and save report + memory profile.

        Falls back to NoKeyClient (public HTML scraping, up to 30 videos)
        when YT_API_KEY is not set — no key required for basic analysis.
        """
        key = os.environ.get("YT_API_KEY")
        no_key_mode = False

        if not key:
            if NoKeyClient is None:
                return {
                    "success": False,
                    "message": (
                        "YouTube API key missing (YT_API_KEY) and NoKeyClient could not be loaded. "
                        "Please set YT_API_KEY for full decode."
                    ),
                }
            no_key_mode = True
            max_videos = min(max_videos, 30)  # Public scraping limit

        try:
            if no_key_mode:
                yt = NoKeyClient()
                notice = " [no-key mode: up to 30 videos via public page]"
            else:
                yt = YTClient(key)
                notice = ""
            ch = yt.resolve_channel(channel_target)
            ch_title = ch["snippet"]["title"]
            vids = yt.list_videos(ch, max_results=max_videos)
            d = decode(ch, vids)

            # Build and write markdown report
            os.makedirs(self.reports_dir, exist_ok=True)
            safe = "".join(c if c.isalnum() else "_" for c in d["channel_title"])[:40]
            out_path = os.path.join(self.reports_dir, f"{safe}_decode.md")
            report = build_report(d)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(report)

            # Save to persistent memory
            mem_path = save_channel_profile(d, memory_dir=self.memory_dir)

            summary = (
                f"Channel '{ch_title}' successfully decoded{notice}! "
                f"Analyzed {len(vids)} videos. "
                f"Subscribers: {d.get('subs', 0):,}, Avg views: {int(d.get('avg_views', 0)):,}. "
                f"Found {d.get('breakout_count', 0)} breakout videos. "
                f"Report saved to {out_path} and memory profile saved to {mem_path}."
            )
            return {
                "success": True,
                "channel_title": ch_title,
                "report_file": out_path,
                "memory_file": mem_path,
                "message": summary,
                "data": d,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to decode channel '{channel_target}': {str(e)}"
            }

    def handle_list_memory(self) -> Dict[str, Any]:
        """Retrieve and format summary of all analyzed channels in memory/."""
        profiles = list_channel_profiles(memory_dir=self.memory_dir)
        if not profiles:
            return {
                "success": True,
                "count": 0,
                "message": "NovaMind memory is currently empty. No channels have been decoded yet."
            }

        lines = [f"Found {len(profiles)} channel profile(s) in persistent memory:"]
        for p in profiles:
            sub_k = f"{p.get('subscribers', 0)/1000:.1f}K" if p.get('subscribers', 0) >= 1000 else str(p.get('subscribers', 0))
            avg_v = f"{p.get('avg_views', 0)/1000:.1f}K" if p.get('avg_views', 0) >= 1000 else str(p.get('avg_views', 0))
            lines.append(
                f"- **{p.get('channel_title')}** (ID: `{p.get('channel_id')}`): "
                f"{sub_k} subs · {avg_v} avg views · {p.get('breakouts', 0)} breakouts"
            )

        return {
            "success": True,
            "count": len(profiles),
            "message": "\n".join(lines),
            "profiles": profiles
        }

    def handle_recall_channel(self, identifier: str) -> Dict[str, Any]:
        """Load and summarize a specific channel profile from memory/."""
        profile = load_channel_profile(identifier, memory_dir=self.memory_dir)
        if not profile:
            # Fallback check by matching channel title substring in index
            all_p = list_channel_profiles(memory_dir=self.memory_dir)
            for p in all_p:
                if identifier.lower() in p.get("channel_title", "").lower():
                    profile = load_channel_profile(p["channel_id"], memory_dir=self.memory_dir)
                    break

        if not profile:
            return {
                "success": False,
                "message": f"Could not find channel '{identifier}' in memory."
            }

        stats = profile.get("channel_stats", {})
        titles = profile.get("title_analysis", {})
        pacing = profile.get("caption_pacing_analysis", {})
        summary = (
            f"**{profile.get('channel_title')}** Memory Profile:\n"
            f"- Subscribers: {stats.get('subscribers', 0):,} · Avg views: {int(stats.get('avg_views', 0)):,}\n"
            f"- View/Sub Ratio: {stats.get('view_sub_ratio', 0)}x · Breakouts: {stats.get('breakout_count', 0)}\n"
            f"- Avg Title Length: {titles.get('avg_title_len', 0)} chars\n"
            f"- Speech Pacing: ~{pacing.get('avg_wpm', 150)} WPM · Hook: {pacing.get('hook_strategy', 'N/A')}\n"
            f"- Top Keywords: {', '.join(titles.get('top_keywords', [])[:6])}"
        )
        return {
            "success": True,
            "profile": profile,
            "message": summary
        }

    def handle_query_knowledge(self, query: str) -> Dict[str, Any]:
        """Search knowledge base for tools, formulas, or operational rules."""
        tool_matches = search_tools(query)
        formula_matches = search_formulas(query)

        if not tool_matches and not formula_matches:
            # Check for general keywords like rules or tools
            q = query.lower()
            if "rule" in q or "guardrail" in q:
                rules = get_rules().get("operational_rules", [])
                lines = ["NovaMind Operational Guardrails:"]
                for r in rules:
                    lines.append(f"- [{r.get('severity')}] **{r.get('rule')}**: {r.get('reason')}")
                return {"success": True, "message": "\n".join(lines)}
            elif "tool" in q or "alternative" in q:
                cat = get_tools_catalog()
                lines = ["Known AI Tools & Open-Source Alternatives:"]
                for category, t_list in cat.items():
                    for t in t_list:
                        lines.append(f"- **{t['name']}** ({t.get('pricing')}): Cheaper alternative → `{t.get('cheaper_alternative')}` ({t.get('savings')})")
                return {"success": True, "message": "\n".join(lines[:6])}

            return {
                "success": False,
                "message": f"No direct match for '{query}' in knowledge base."
            }

        lines = []
        if tool_matches:
            lines.append("Tools from Knowledge Base:")
            for t in tool_matches[:3]:
                lines.append(
                    f"- **{t['name']}** ({t.get('tier')}, {t.get('pricing')}): {t.get('pros')}\n"
                    f"  *Cheaper Alternative:* {t.get('cheaper_alternative')} ({t.get('savings')})"
                )
        if formula_matches:
            lines.append("Formulas & Pacing Guidelines:")
            for f in formula_matches[:3]:
                if f.get("type") == "title_formula":
                    lines.append(f"- *{f.get('name')}:* Template: `{f.get('template')}` (e.g. {f.get('example')})")
                else:
                    lines.append(f"- *{f.get('type')} ({f.get('duration')}):* {f.get('guideline')}")

        return {
            "success": True,
            "message": "\n".join(lines)
        }

    def handle_switch_persona(self, target_name: str) -> Dict[str, Any]:
        """Switch active character personality."""
        ok, active_id, msg = persona_manager.switch(target_name)
        return {
            "success": ok,
            "persona_id": active_id,
            "message": msg
        }


# Singleton dispatcher
dispatcher = ActionDispatcher()
