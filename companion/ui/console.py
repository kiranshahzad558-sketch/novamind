"""Interactive terminal and voice console for NovaMind Companion.

Supports:
- Text chatting with real-time TTS voice output.
- Microphone push-to-talk speech input (/mic).
- Continuous hands-free voice loop (--voice-loop).
- Slash commands for memory, knowledge, and personality switching.
"""
import os
import sys
import time
from typing import Optional

from companion.mind.brain import brain
from companion.personalities.manager import manager as persona_manager
from companion.voice.tts import tts
from companion.voice.stt import stt


class CompanionConsole:
    """Console chat session manager with integrated voice I/O."""

    def __init__(
        self,
        voice_output: bool = True,
        initial_persona: str = "nova",
        voice_record_secs: float = 4.0,
    ):
        self.voice_output = voice_output
        self.voice_record_secs = voice_record_secs
        persona_manager.switch(initial_persona)
        tts.enabled = self.voice_output

    def banner(self):
        """Display stylish terminal header."""
        persona = persona_manager.active_profile
        mic_ok, mic_msg = stt.is_available()
        mic_status = "🟢 Ready" if mic_ok else f"🟡 {mic_msg}"
        tts_status = "🟢 Enabled" if self.voice_output else "⚪ Muted"

        banner_text = f"""
===============================================================
               NOVAMIND COMPANION (PHASE 2)
===============================================================
  Active Persona : {persona['name']} ({persona['title']})
  Voice Output   : {tts_status} [Voice: {persona_manager.get_voice() or 'System Default'}]
  Mic Input (STT): {mic_status}
---------------------------------------------------------------
  Commands:
    /mic            → Speak into microphone (Push-To-Talk)
    /voice [on/off] → Toggle Text-To-Speech output
    /persona <name> → Switch persona (nova, mindy, jarvis, aura)
    /memory         → View decoded channel memory
    /knowledge <q>  → Search AI tools & retention formulas
    /exit           → Exit companion
===============================================================
"""
        print(banner_text)
        # Speak initial greeting
        if self.voice_output:
            greeting = persona.get("greeting", "NovaMind companion online.")
            tts.speak(
                greeting,
                voice=persona_manager.get_voice(),
                rate=persona_manager.get_speech_rate(),
                blocking=False,
            )

    def run_interactive(self):
        """Run interactive text + voice chat session."""
        self.banner()

        while True:
            try:
                p_name = persona_manager.active_name
                user_input = input(f"\n[{p_name}] You > ").strip()

                if not user_input:
                    continue

                # Handle quick slash commands
                if user_input.startswith("/"):
                    should_continue = self._handle_slash_command(user_input)
                    if not should_continue:
                        break
                    continue

                # Process natural input
                self._respond_to(user_input)

            except (KeyboardInterrupt, EOFError):
                print("\nExiting NovaMind Companion. Systems offline.")
                break

    def run_voice_loop(self):
        """Continuous hands-free voice loop: listen → think → speak."""
        self.banner()
        print("\n[Voice Loop Mode] Speak into your mic after the beep. Press Ctrl+C to stop.\n")

        while True:
            try:
                print("\n🎤 Listening... (Speak now)")
                text = stt.listen_and_transcribe(
                    duration=self.voice_record_secs,
                    on_done=lambda: print("⏳ Transcribing audio..."),
                )

                if not text:
                    print("  [Didn't catch that — say something or press Ctrl+C]")
                    time.sleep(0.5)
                    continue

                print(f"👤 Heard: \"{text}\"")

                if text.lower() in ["exit", "quit", "stop", "bye"]:
                    print("Goodbye!")
                    break

                self._respond_to(text)

            except KeyboardInterrupt:
                print("\nVoice loop paused.")
                break

    def _handle_slash_command(self, cmd_line: str) -> bool:
        """Handle console commands starting with '/'."""
        parts = cmd_line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ["/exit", "/quit", "/q"]:
            print("Shutting down companion. Until next time!")
            return False

        elif cmd == "/mic":
            avail, msg = stt.is_available()
            if not avail:
                print(f"❌ Microphone unavailable: {msg}")
                return True

            print(f"🎤 Recording for {self.voice_record_secs} seconds... Speak now!")
            transcribed = stt.listen_and_transcribe(duration=self.voice_record_secs)
            if transcribed:
                print(f"👤 Heard: \"{transcribed}\"")
                self._respond_to(transcribed)
            else:
                print("❌ No speech recognized or audio was silent.")
            return True

        elif cmd == "/voice":
            if arg.lower() in ["on", "enable", "1"]:
                self.voice_output = True
                tts.enabled = True
                print("🔊 Voice output enabled.")
                tts.speak("Voice output enabled.", voice=persona_manager.get_voice(), blocking=False)
            elif arg.lower() in ["off", "disable", "mute", "0"]:
                self.voice_output = False
                tts.enabled = False
                print("🔇 Voice output muted.")
            else:
                state = "enabled" if self.voice_output else "muted"
                print(f"Voice output is currently {state}. Use '/voice on' or '/voice off'.")
            return True

        elif cmd in ["/persona", "/switch"]:
            if not arg:
                all_p = persona_manager.list_all()
                print("Available Personalities:")
                for p in all_p:
                    active = "★" if p["is_active"] else " "
                    print(f"  {active} {p['id'].ljust(8)}: {p['name']} — {p['title']} ({p['tagline']})")
                return True

            ok, pid, msg = persona_manager.switch(arg)
            print(f"\n{msg}")
            if self.voice_output:
                tts.speak(
                    msg,
                    voice=persona_manager.get_voice(),
                    rate=persona_manager.get_speech_rate(),
                    blocking=False,
                )
            return True

        elif cmd == "/memory":
            from companion.mind.actions import dispatcher
            res = dispatcher.handle_list_memory()
            print(f"\n{res['message']}")
            return True

        elif cmd in ["/knowledge", "/k"]:
            if not arg:
                print("Usage: /knowledge <keyword> (e.g., /knowledge kokoro or /knowledge formulas)")
                return True
            from companion.mind.actions import dispatcher
            res = dispatcher.handle_query_knowledge(arg)
            print(f"\n{res['message']}")
            return True

        elif cmd in ["/decode", "/analyze"]:
            if not arg:
                print("Usage: /decode <YouTube Channel URL, @handle, or ID>")
                return True
            from companion.mind.actions import dispatcher
            print(f"Analyzing {arg}...")
            res = dispatcher.handle_decode_channel(arg)
            print(f"\n{res['message']}")
            if self.voice_output:
                tts.speak(
                    res["message"],
                    voice=persona_manager.get_voice(),
                    rate=persona_manager.get_speech_rate(),
                    blocking=False,
                )
            return True

        elif cmd in ["/help", "/h"]:
            self._respond_to("help")
            return True

        else:
            print(f"Unknown command '{cmd}'. Type /help for assistance.")
            return True

    def _respond_to(self, text: str):
        """Send input to brain, print reply, and speak aloud if voice is enabled."""
        p_name = persona_manager.active_name
        reply = brain.process_input(text)
        print(f"\n✨ {p_name}: {reply}")

        if self.voice_output:
            # Speak asynchronously so user can continue immediately
            tts.speak(
                reply,
                voice=persona_manager.get_voice(),
                rate=persona_manager.get_speech_rate(),
                blocking=False,
            )
