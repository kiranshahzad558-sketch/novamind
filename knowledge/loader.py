"""Knowledge base loader — feeds saved expert sources to the LLM as context.

Usage:
    from knowledge.loader import get_context
    ctx = get_context(max_chars=60000)   # markdown text of all sources
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCES = BASE / "sources"


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


if __name__ == "__main__":
    for name, files in list_sources():
        print(f"{name}: {len(files)} files")
    ctx = get_context()
    print(f"context chars: {len(ctx)}")
