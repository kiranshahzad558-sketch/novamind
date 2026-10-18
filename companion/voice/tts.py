"""Cross-platform Text-To-Speech (TTS) engine.

Supports macOS (native /usr/bin/say), Windows (PowerShell System.Speech / SAPI),
and Linux (spd-say / espeak), with graceful fallback to console output.
"""
import os
import platform
import subprocess
import threading
from typing import List, Optional


class TTSEngine:
    """Manages audio speech synthesis across macOS, Windows, and Linux."""

    def __init__(self, default_rate: int = 180, enabled: bool = True):
        self.system = platform.system()
        self.default_rate = default_rate
        self.enabled = enabled
        self._lock = threading.Lock()
        self._current_process: Optional[subprocess.Popen] = None

    def speak(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
        blocking: bool = True,
    ) -> bool:
        """Speak the given text out loud.
        
        Args:
            text: The sentence or paragraph to vocalize.
            voice: Voice name (e.g. 'Samantha' on macOS, 'Zira' on Windows).
            rate: Speech rate in words-per-minute (approx 150-200).
            blocking: If True, blocks until speech is finished.
        """
        if not self.enabled or not text or not text.strip():
            return False

        clean_text = text.replace('"', '\\"').replace("\n", " ").strip()
        speech_rate = rate or self.default_rate

        if blocking:
            return self._speak_sync(clean_text, voice=voice, rate=speech_rate)
        else:
            t = threading.Thread(
                target=self._speak_sync,
                args=(clean_text, voice, speech_rate),
                daemon=True,
            )
            t.start()
            return True

    def _speak_sync(self, clean_text: str, voice: Optional[str], rate: int) -> bool:
        with self._lock:
            try:
                if self.system == "Darwin":
                    return self._speak_macos(clean_text, voice=voice, rate=rate)
                elif self.system == "Windows":
                    return self._speak_windows(clean_text, voice=voice, rate=rate)
                else:
                    return self._speak_linux(clean_text, rate=rate)
            except Exception as e:
                # Speech failed; silent fallback
                return False

    def _speak_macos(self, text: str, voice: Optional[str], rate: int) -> bool:
        cmd = ["say"]
        if voice:
            cmd.extend(["-v", voice])
        if rate:
            cmd.extend(["-r", str(rate)])
        cmd.append(text)
        
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return proc.returncode == 0

    def _speak_windows(self, text: str, voice: Optional[str], rate: int) -> bool:
        # Convert WPM rate (100-250) to Windows rate (-10 to 10)
        # 175 WPM corresponds to rate ~ 0
        win_rate = max(-10, min(10, int((rate - 175) / 10)))
        
        escaped = text.replace("'", "''")
        voice_select = f"try {{ $synth.SelectVoice('{voice}') }} catch {{}};" if voice else ""
        ps_cmd = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.Rate = {win_rate}; "
            f"{voice_select} "
            f"$synth.Speak('{escaped}')"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return proc.returncode == 0

    def _speak_linux(self, text: str, rate: int) -> bool:
        # Try spd-say first, then espeak
        for binary in ("spd-say", "espeak"):
            if subprocess.call(["which", binary], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                if binary == "spd-say":
                    proc = subprocess.run(["spd-say", "-r", str(rate), text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc = subprocess.run(["espeak", "-s", str(rate), text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return proc.returncode == 0
        return False

    def list_available_voices(self) -> List[str]:
        """Return a list of installed voices on the operating system."""
        voices = []
        try:
            if self.system == "Darwin":
                out = subprocess.check_output(["say", "-v", "?"], text=True)
                for line in out.splitlines():
                    if line.strip():
                        name = line.split()[0]
                        voices.append(name)
            elif self.system == "Windows":
                ps_cmd = (
                    "Add-Type -AssemblyName System.Speech; "
                    "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    "$synth.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }"
                )
                out = subprocess.check_output(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                    text=True,
                )
                for line in out.splitlines():
                    if line.strip():
                        voices.append(line.strip())
        except Exception:
            pass
        return voices


# Global singleton instance for easy import
tts = TTSEngine()
speak = tts.speak
