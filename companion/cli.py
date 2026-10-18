"""NovaMind Companion CLI — Phase 2 Desktop Voice & Text Assistant.

Usage:
  python -m companion.cli                      # Interactive text + voice mode
  python -m companion.cli --persona mindy       # Start with Mindy personality
  python -m companion.cli --no-voice            # Text-only mode (TTS muted)
  python -m companion.cli --voice-loop          # Continuous hands-free voice loop
"""
import argparse
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from companion.ui.console import CompanionConsole
from companion.personalities.manager import manager as persona_manager
from companion.mind.brain import brain


def main():
    ap = argparse.ArgumentParser(description="NovaMind Desktop Companion (Phase 2)")
    ap.add_argument(
        "--persona",
        default="nova",
        choices=["nova", "mindy", "jarvis", "aura"],
        help="Initial personality character (default: nova)",
    )
    ap.add_argument(
        "--no-voice",
        action="store_true",
        help="Disable Text-To-Speech audio output (text-only mode)",
    )
    ap.add_argument(
        "--voice-loop",
        action="store_true",
        help="Run in continuous hands-free microphone listening mode",
    )
    ap.add_argument(
        "--duration",
        type=float,
        default=4.0,
        help="Microphone listen duration in seconds (default: 4.0)",
    )
    ap.add_argument(
        "--gemini-key",
        default=None,
        help="Gemini API Key for advanced conversation (or export GEMINI_API_KEY)",
    )

    args = ap.parse_args()

    if args.gemini_key:
        brain.api_key = args.gemini_key

    console = CompanionConsole(
        voice_output=not args.no_voice,
        initial_persona=args.persona,
        voice_record_secs=args.duration,
    )

    if args.voice_loop:
        console.run_voice_loop()
    else:
        console.run_interactive()


if __name__ == "__main__":
    main()
