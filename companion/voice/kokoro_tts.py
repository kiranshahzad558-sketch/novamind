"""Kokoro neural TTS backend — natural AI voice for Minu.

Uses kokoro-onnx (pip install kokoro-onnx soundfile).
Model files expected at ~/.novamind/kokoro/:
  - kokoro-v1.0.onnx   (~310 MB)
  - voices-v1.0.bin    (~28 MB)
Download: https://github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0)
Or run: python3 -m companion.voice.setup_kokoro

If the package or model files are missing, is_available() returns False and
callers should fall back to the system TTS engine.
"""
import os
import platform
import subprocess
import tempfile
import threading
from typing import Optional, Tuple

MODEL_DIR = os.path.join(os.path.expanduser("~"), ".novamind", "kokoro")
ONNX_NAME = "kokoro-v1.0.onnx"
VOICES_NAME = "voices-v1.0.bin"

# Map companion/system voice names -> Kokoro neural voice IDs
VOICE_MAP = {
    "samantha": "af_sarah",    # Minu / Nova (warm female)
    "victoria": "af_bella",    # Mindy (bright female)
    "daniel": "am_adam",       # Jarvis (calm male)
    "karen": "af_nicole",      # Aura (soft female)
    "zira": "af_sarah",
    "david": "am_adam",
}
DEFAULT_KOKORO_VOICE = "af_sarah"  # Minu's voice

_kokoro_instance = None
_kokoro_lock = threading.Lock()
_availability = None  # tri-state: None = not checked yet


def model_paths() -> Tuple[str, str]:
    return (os.path.join(MODEL_DIR, ONNX_NAME),
            os.path.join(MODEL_DIR, VOICES_NAME))


def is_available() -> bool:
    """True when kokoro-onnx is installed AND both model files exist."""
    global _availability
    if _availability is not None:
        return _availability
    try:
        import kokoro_onnx  # noqa: F401
        import soundfile  # noqa: F401
    except ImportError:
        _availability = False
        return False
    onnx_path, voices_path = model_paths()
    _availability = os.path.isfile(onnx_path) and os.path.isfile(voices_path)
    return _availability


def kokoro_voice_for(companion_voice: Optional[str]) -> str:
    """Map a companion voice name (e.g. 'Samantha') to a Kokoro voice ID."""
    if companion_voice:
        return VOICE_MAP.get(companion_voice.lower().strip(), DEFAULT_KOKORO_VOICE)
    return DEFAULT_KOKORO_VOICE


def _get_kokoro():
    global _kokoro_instance
    with _kokoro_lock:
        if _kokoro_instance is None:
            from kokoro_onnx import Kokoro
            onnx_path, voices_path = model_paths()
            _kokoro_instance = Kokoro(onnx_path, voices_path)
    return _kokoro_instance


def _play_wav(wav_path: str) -> bool:
    """Play a wav file with the OS-native player. Returns True on success."""
    system = platform.system()
    try:
        if system == "Darwin":
            proc = subprocess.run(
                ["afplay", wav_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return proc.returncode == 0
        elif system == "Windows":
            ps = (f"Add-Type -AssemblyName System.Windows.Forms; "
                  f"(New-Object System.Media.SoundPlayer '{wav_path}').PlaySync()")
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return proc.returncode == 0
        else:
            for player in ("aplay", "paplay", "play"):
                try:
                    proc = subprocess.run(
                        [player, wav_path],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if proc.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
            return False
    except Exception:
        return False


def speak(text: str,
          voice: Optional[str] = None,
          speed: float = 1.0,
          lang: str = "en-us",
          blocking: bool = True) -> bool:
    """Speak text with the Kokoro neural voice. Returns True on success."""
    if not text or not text.strip():
        return False
    if not is_available():
        return False
    try:
        import soundfile as sf
        kokoro = _get_kokoro()
        kvoice = kokoro_voice_for(voice)
        samples, sample_rate = kokoro.create(
            text.strip(), voice=kvoice, speed=speed, lang=lang)
        if samples is None or len(samples) == 0:
            return False
        fd, wav_path = tempfile.mkstemp(suffix=".wav", prefix="minu-")
        os.close(fd)
        try:
            sf.write(wav_path, samples, sample_rate)
            if blocking:
                return _play_wav(wav_path)
            t = threading.Thread(target=_play_wav, args=(wav_path,), daemon=True)
            t.start()
            return True
        finally:
            if blocking:
                try:
                    os.remove(wav_path)
                except OSError:
                    pass
    except Exception:
        return False
