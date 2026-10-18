"""NovaMind Companion (Phase 2).

Cross-platform (macOS & Windows) desktop voice & text assistant:
- voice: Speech-to-Text (STT) and Text-to-Speech (TTS)
- personalities: Character profiles (Nova, Mindy, Jarvis, Aura)
- mind: Conversational reasoning loop, memory & knowledge linking
- ui: Terminal and voice interactive console
"""
from companion.voice.tts import tts, speak
from companion.voice.stt import stt
from companion.personalities.manager import manager as persona_manager
from companion.mind.brain import brain
from companion.mind.actions import dispatcher

__all__ = [
    "tts",
    "speak",
    "stt",
    "persona_manager",
    "brain",
    "dispatcher",
]
