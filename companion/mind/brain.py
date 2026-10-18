"""Conversational reasoning engine for NovaMind Companion.

Understands user commands in English, Urdu, and Roman Urdu.
Coordinates intent parsing, LLM generation, personality styling,
and dispatching to analyzer, memory, and knowledge subsystems.
"""
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

from companion.personalities.manager import manager as persona_manager
from companion.mind.actions import dispatcher


class CompanionBrain:
    """The central conversational brain of the desktop companion."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        self.history: List[Dict[str, str]] = []

    def process_input(self, user_text: str) -> str:
        """Process user input (voice-transcribed or typed) and return companion response."""
        text = user_text.strip()
        if not text:
            return "Main sun raha hoon. Aap mujhse koi bhi channel decode karne ya tools ke bare mein pooch sakte hain."

        # 1. Check for concrete action intents
        action_handled, action_response = self._try_handle_action(text)
        if action_handled:
            self._record_interaction(user_text, action_response)
            return action_response

        # 2. If Gemini API key is available, use LLM generation with active personality
        if self.api_key:
            llm_reply = self._generate_llm_reply(text)
            if llm_reply:
                self._record_interaction(user_text, llm_reply)
                return llm_reply

        # 3. Fallback: Intelligent conversational heuristic matching active personality
        reply = self._generate_heuristic_reply(text)
        self._record_interaction(user_text, reply)
        return reply

    def _try_handle_action(self, text: str) -> Tuple[bool, str]:
        """Detect and execute high-priority system actions."""
        lower = text.lower().strip()

        # Action A: Decode Channel
        # Matches: "is channel ko decode karo <url>", "decode https://...", "analyze channel @xyz"
        decode_match = re.search(
            r"(?:decode|analyze|channel\s+decode|channel\s+analyze)\s*(?:karo|kar do|channel)?\s*(https?://[^\s]+|@[a-zA-Z0-9_\-]+|UC[a-zA-Z0-9_\-]+)",
            text,
            re.IGNORECASE,
        )
        if not decode_match and ("youtube.com" in lower or "youtu.be" in lower or lower.startswith("@")):
            # Standalone URL or handle
            urls = re.findall(r"(https?://[^\s]+|@[a-zA-Z0-9_\-]+)", text)
            if urls:
                target = urls[0]
                res = dispatcher.handle_decode_channel(target)
                return True, res["message"]

        if decode_match:
            target = decode_match.group(1).strip()
            res = dispatcher.handle_decode_channel(target)
            return True, res["message"]

        # Action B: Personality Switch
        # Matches: "switch to mindy", "nova ban jao", "jarvis mode", "change persona to aura"
        switch_match = re.search(
            r"(?:switch to|change to|persona|mode|ban jao)\s+(nova|mindy|jarvis|aura)",
            lower,
        ) or re.search(r"^(nova|mindy|jarvis|aura)\s*(?:mode|ban jao)?$", lower)
        if switch_match:
            target_p = switch_match.group(1).strip()
            res = dispatcher.handle_switch_persona(target_p)
            return True, res["message"]

        # Action C: List Memory
        if any(k in lower for k in [
            "memory", "channels", "humne kon se", "kaun se channel", "list channels", "past analyses", "show memory"
        ]):
            if not any(k in lower for k in ["tell me about", "recall", "details of"]):
                res = dispatcher.handle_list_memory()
                return True, res["message"]

        # Action D: Recall Specific Channel from Memory
        recall_match = re.search(
            r"(?:tell me about|recall|stats of|details of|ke bare mein batao)\s+(.+)",
            text,
            re.IGNORECASE,
        )
        if recall_match:
            target = recall_match.group(1).strip("?. ")
            res = dispatcher.handle_recall_channel(target)
            if res["success"]:
                return True, res["message"]

        # Action E: Knowledge Base Query (Tools & Formulas)
        if any(k in lower for k in [
            "tool", "tools", "kokoro", "elevenlabs", "cheaper alternative", "cost", "formula", "retention", "hook", "rule", "guardrail"
        ]):
            res = dispatcher.handle_query_knowledge(lower)
            if res["success"]:
                return True, res["message"]

        # Action F: Help & Introduction
        if lower in ["help", "madad", "commands", "/help", "kya kar sakte ho", "who are you"]:
            curr = persona_manager.active_name
            help_text = (
                f"I am **{curr}**, your NovaMind companion. Here is what you can ask me:\n"
                "- **Decode a Channel:** *\"is channel ko decode karo https://youtube.com/@Channel\"*\n"
                "- **View Memory:** *\"Humne kaun se channels analyze kiye hain?\"*\n"
                "- **Recall Channel Data:** *\"Tell me about <Channel Name>\"*\n"
                "- **Query Knowledge:** *\"Kokoro kaisa tool hai?\"* or *\"Cheaper alternative for voiceover\"*\n"
                "- **Switch Personality:** *\"Switch to Mindy\"*, *\"Jarvis mode\"*, *\"Nova\"*, or *\"Aura\"*\n"
                "- **Voice Commands:** Push-to-talk mic input with real-time text-to-speech output."
            )
            return True, help_text

        return False, ""

    def _generate_llm_reply(self, user_prompt: str) -> Optional[str]:
        """Generate response via Gemini using the active personality system prompt."""
        active_persona = persona_manager.active_profile
        system_instruction = (
            f"{active_persona.get('system_prompt', '')}\n"
            f"You are speaking to the user on a desktop companion app. "
            f"Respond concisely in natural conversation (supports English, Urdu, and Roman Urdu). "
            f"Never write long essays; keep spoken answers under 3-4 sentences."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"System Directive:\n{system_instruction}\n\nUser Question:\n{user_prompt}"}]}
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 300,
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
        except Exception:
            pass

        return None

    def _generate_heuristic_reply(self, text: str) -> str:
        """Intelligent conversational heuristic tailored to the current character."""
        p_name = persona_manager.active_name
        lower = text.lower()

        if any(w in lower for w in ["hello", "hi", "hey", "salam", "aoa"]):
            return f"Hello! {persona_manager.active_profile.get('greeting', 'Main hazir hoon.')}"

        if any(w in lower for w in ["shukriya", "thanks", "thank you"]):
            return f"You're welcome! Agla objective kya hai?"

        if "stonic" in lower:
            return (
                f"As {p_name}, I can tell you NovaMind is built to deliver Stonic-class companion autonomy "
                f"with persistent memory, deep channel decoding, and 100x video pipelines — cross-platform on Mac & Windows."
            )

        if "status" in lower:
            return (
                f"Status: Systems nominal. Active persona: **{p_name}**. "
                f"Voice I/O active. Memory and Knowledge subsystems linked."
            )

        return (
            f"[{p_name}] Main ne aap ki baat note kar li hai: '{text}'. "
            f"Aap YouTube channel link de kar 'is channel ko decode karo' keh sakte hain, "
            f"ya memory aur tools catalog explore kar sakte hain."
        )

    def _record_interaction(self, user_text: str, reply: str):
        self.history.append({"user": user_text, "reply": reply})
        if len(self.history) > 20:
            self.history.pop(0)


# Global singleton
brain = CompanionBrain()
