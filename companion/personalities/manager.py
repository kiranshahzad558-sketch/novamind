import platform
from typing import Any, Dict, List, Optional, Tuple
from companion.personalities.profiles import PERSONALITY_PROFILES, get_profile


class PersonalityManager:
    """Handles character state and platform-specific voice selection."""

    def __init__(self, default_id: str = "minu"):
        self._active_id = default_id if default_id in PERSONALITY_PROFILES else "minu"
        self._os_name = platform.system()

    @property
    def active_id(self) -> str:
        return self._active_id

    @property
    def active_profile(self) -> Dict[str, Any]:
        return get_profile(self._active_id)

    @property
    def active_name(self) -> str:
        return self.active_profile.get("name", "Nova")

    @property
    def active_prompt(self) -> str:
        return self.active_profile.get("system_prompt", "")

    def get_voice(self) -> Optional[str]:
        """Get the preferred voice name for the current operating system."""
        prof = self.active_profile
        if self._os_name == "Darwin":
            return prof.get("voice_macos", "Samantha")
        elif self._os_name == "Windows":
            return prof.get("voice_windows", "Microsoft Zira Desktop")
        return None

    def get_speech_rate(self) -> int:
        """Get the character's tailored speech rate."""
        return int(self.active_profile.get("speech_rate", 180))

    def switch(self, personality_id: str) -> Tuple[bool, str, str]:
        """Switch active character to given ID or name."""
        pid = personality_id.lower().strip()
        # Check by ID or display name
        matched = None
        for k, v in PERSONALITY_PROFILES.items():
            if k == pid or v["name"].lower() == pid:
                matched = k
                break

        if matched:
            self._active_id = matched
            greeting = self.active_profile.get("greeting", f"Switched to {self.active_name}.")
            return True, matched, greeting
        else:
            avail = ", ".join(PERSONALITY_PROFILES.keys())
            return False, self._active_id, f"Unknown persona '{personality_id}'. Available: {avail}"

    def list_all(self) -> List[Dict[str, str]]:
        """List summary info for all available personalities."""
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "title": p["title"],
                "tagline": p["tagline"],
                "is_active": p["id"] == self._active_id,
            }
            for p in PERSONALITY_PROFILES.values()
        ]


# Type alias helper
Tuple_Switch_Result = tuple


# Global singleton
manager = PersonalityManager()
