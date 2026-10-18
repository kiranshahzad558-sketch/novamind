"""Loader and query interface for NovaMind Knowledge Base."""
import json
import os
from typing import Any, Dict, List, Optional

KNOWLEDGE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_json(filename: str) -> Dict[str, Any]:
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
    return load_json("tools_catalog.json")


def get_formulas() -> Dict[str, Any]:
    """Return viral formulas, retention benchmarks, and hook patterns."""
    return load_json("formulas.json")


def get_rules() -> Dict[str, Any]:
    """Return operational quality guardrails."""
    return load_json("rules.json")


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
