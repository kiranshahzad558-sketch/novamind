"""Cross-platform Speech-To-Text (STT) engine.

Uses sounddevice for reliable cross-platform microphone recording (macOS & Windows),
and speech_recognition for transcribing audio via Google STT (with Urdu/English support).
Works with or without numpy.
"""
import io
import os
import wave
from typing import Optional, Tuple

try:
    import sounddevice as sd
    HAVE_SOUNDDEVICE = True
except Exception:
    HAVE_SOUNDDEVICE = False

try:
    import numpy as np
    HAVE_NUMPY = True
except Exception:
    HAVE_NUMPY = False

try:
    import speech_recognition as sr
    HAVE_SR = True
except Exception:
    HAVE_SR = False


class STTEngine:
    """Manages audio recording from microphone and transcription to text."""

    def __init__(self, sample_rate: int = 16000, default_language: str = "en-US"):
        self.sample_rate = sample_rate
        self.default_language = default_language
        self.recognizer = sr.Recognizer() if HAVE_SR else None

    def is_available(self) -> Tuple[bool, str]:
        """Check if audio input hardware and libraries are available."""
        if not HAVE_SR:
            return False, "SpeechRecognition library missing."
        if not HAVE_SOUNDDEVICE:
            return False, "sounddevice library missing."
        try:
            devices = sd.query_devices()
            input_devs = [d for d in devices if d.get("max_input_channels", 0) > 0]
            if not input_devs:
                return False, "No audio input microphone detected."
            return True, "Microphone and STT available."
        except Exception as e:
            return False, f"Audio query failed: {e}"

    def record_audio_bytes(self, duration: float = 4.0) -> Optional[bytes]:
        """Record audio from the default microphone and return standard 16-bit WAV bytes."""
        if not HAVE_SOUNDDEVICE:
            return None

        try:
            # If numpy is available, use high-level sd.rec
            if HAVE_NUMPY:
                num_frames = int(duration * self.sample_rate)
                recording = sd.rec(
                    num_frames,
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="int16",
                )
                sd.wait()
                raw_bytes = recording.tobytes()
            else:
                # Fallback to RawInputStream (zero numpy dependency)
                frames = []
                num_bytes_to_read = int(duration * self.sample_rate * 2)  # 2 bytes per sample
                bytes_read = 0

                def callback(indata, frame_count, time_info, status):
                    nonlocal bytes_read
                    frames.append(bytes(indata))
                    bytes_read += len(indata)

                with sd.RawInputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="int16",
                    callback=callback,
                ):
                    sd.sleep(int(duration * 1000))

                raw_bytes = b"".join(frames)

            # Pack into standard WAV format
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(raw_bytes)

            return buffer.getvalue()
        except Exception as e:
            print(f"[Voice Notice] Recording error: {e}")
            return None

    def transcribe_bytes(self, wav_bytes: bytes, language: Optional[str] = None) -> Optional[str]:
        """Transcribe in-memory WAV bytes to text."""
        if not self.recognizer or not wav_bytes:
            return None

        lang = language or self.default_language
        try:
            with io.BytesIO(wav_bytes) as audio_file:
                with sr.AudioFile(audio_file) as source:
                    audio_data = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio_data, language=lang)
                    return text.strip()
        except sr.UnknownValueError:
            # Speech was unintelligible
            return None
        except sr.RequestError as e:
            print(f"[Voice Notice] STT service request error: {e}")
            return None
        except Exception as e:
            print(f"[Voice Notice] Transcription error: {e}")
            return None

    def transcribe_file(self, filepath: str, language: Optional[str] = None) -> Optional[str]:
        """Transcribe an existing WAV file on disk."""
        if not os.path.exists(filepath):
            return None
        with open(filepath, "rb") as f:
            return self.transcribe_bytes(f.read(), language=language)

    def listen_and_transcribe(
        self,
        duration: float = 4.0,
        language: Optional[str] = None,
        on_start: Optional[callable] = None,
        on_done: Optional[callable] = None,
    ) -> Optional[str]:
        """Record for specified duration and transcribe speech."""
        if on_start:
            on_start()

        wav_bytes = self.record_audio_bytes(duration=duration)

        if on_done:
            on_done()

        if not wav_bytes:
            return None

        return self.transcribe_bytes(wav_bytes, language=language)


# Global singleton instance for easy import
stt = STTEngine()
