"""Knowledge base loader — feeds expert sources to LLM and provides
tool/formula/rules query APIs for NovaMind Companion.

Usage:
    from knowledge.loader import get_context, search_tools, search_formulas
    ctx = get_context(max_chars=60000)   # full markdown context for LLM
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE = Path(__file__).resolve().parent
SOURCES = BASE / "sources"
KNOWLEDGE_DIR = str(BASE)


# ──────────────────────────────────────────────
# Source-file loading (for LLM context injection)
# ──────────────────────────────────────────────

def list_sources() -> list:
    """Return [(source_name, [md files])]."""
    out = []
    if not SOURCES.exists():
        return out
    for d in sorted(p for p in SOURCES.iterdir() if p.is_dir()):
        files = sorted(p for p in d.rglob("*.md") if p.name != "SOURCES.md")
        out.append((d.name, files))
    return out


def get_context(max_chars: int = 60000) -> str:
    """Combine all knowledge sources into one markdown context string."""
    parts = []
    total = 0
    for name, files in list_sources():
        for f in files:
            try:
                text = f.read_text(encoding="utf-8")
            except Exception:
                continue
            chunk = f"\n\n# SOURCE: {name}/{f.name}\n{text}"
            if total + len(chunk) > max_chars:
                break
            parts.append(chunk)
            total += len(chunk)
    return "".join(parts)


# ──────────────────────────────────────────────
# JSON catalogue loading (for Companion queries)
# ──────────────────────────────────────────────

def _load_json(filename: str) -> Dict[str, Any]:
    """Load a JSON file from the knowledge directory."""
    path = os.path.join(KNOWLEDGE_DIR, filename)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_tools_catalog() -> Dict[str, Any]:
    """Return catalog of tools, costs, and open-source alternatives."""
    return _load_json("tools_catalog.json")


def get_formulas() -> Dict[str, Any]:
    """Return viral formulas, retention benchmarks, and hook patterns."""
    return _load_json("formulas.json")


def get_rules() -> Dict[str, Any]:
    """Return operational quality guardrails."""
    return _load_json("rules.json")


def search_tools(query: str) -> List[Dict[str, Any]]:
    """Search tools catalog by keyword."""
    catalog = get_tools_catalog()
    q = query.lower().strip()
    matches = []
    for category, tools in catalog.items():
        for tool in tools:
            name = tool.get("name", "").lower()
            cat = tool.get("category", "").lower()
            alt = tool.get("cheaper_alternative", "").lower()
            pros = tool.get("pros", "").lower()
            if q in name or q in cat or q in alt or q in pros:
                matches.append(tool)
    return matches


def search_formulas(query: str) -> List[Dict[str, Any]]:
    """Search formulas by keyword."""
    formulas = get_formulas()
    q = query.lower().strip()
    matches = []
    for title in formulas.get("title_formulas", []):
        if q in title.get("name", "").lower() or q in title.get("template", "").lower():
            matches.append({"type": "title_formula", **title})
    for hook in formulas.get("hook_structures", []):
        if q in hook.get("type", "").lower() or q in hook.get("guideline", "").lower():
            matches.append({"type": "hook_structure", **hook})
    return matches


if __name__ == "__main__":
    for name, files in list_sources():
        print(f"{name}: {len(files)} files")
    ctx = get_context()
    print(f"context chars: {len(ctx)}")
