"""Personality system for NovaMind Companion."""
from companion.personalities.profiles import PERSONALITY_PROFILES, get_profile, list_profiles
from companion.personalities.manager import PersonalityManager, manager

__all__ = ["PERSONALITY_PROFILES", "get_profile", "list_profiles", "PersonalityManager", "manager"]
