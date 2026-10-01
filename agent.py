# Core Monico Agent - Uncensored Jarvis
"""Command routing + skill registry.

Keyless by design: every skill runs locally on the box, no API keys,
no network calls, no secrets. Agent logic is a real command router over
a plugin-style skill registry (see skills/).
"""
from __future__ import annotations

import time as _time
from typing import Any

from skills.base import SkillRegistry
from skills import builtin

VERSION = "2.0.0"
BOOT_TIME = _time.time()

_FALLBACK_SUGGESTIONS = (
    "I don't have a skill for that yet. Try `help` to see what I can do, "
    "or one of: time, date, calc, echo, note, status."
)


class MonicoAgent:
    def __init__(self) -> None:
        self.registry = SkillRegistry()
        builtin.register_all(self.registry)

    def respond(self, text: str) -> dict[str, Any]:
        """Route one user message to a skill. Always returns a JSON-safe dict."""
        cleaned = " ".join(text.split())
        parts = cleaned.split(" ", 1)
        trigger = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        skill = self.registry.find(trigger)
        if skill is None:
            return {
                "ok": False,
                "skill": "fallback",
                "response": _FALLBACK_SUGGESTIONS,
                "suggestion": "help",
            }
        try:
            reply = skill.run(trigger, args)
        except Exception as exc:  # never 500 on a skill bug
            return {
                "ok": False,
                "skill": skill.name,
                "response": f"The `{skill.name}` skill hit an error: {exc}.",
            }
        return {"ok": True, "skill": skill.name, "response": reply}

    def list_skills(self) -> list[dict[str, Any]]:
        return [
            {
                "name": s.name,
                "description": s.description,
                "usage": s.usage,
                "triggers": s.triggers,
                "examples": s.examples,
            }
            for s in self.registry.all()
        ]

    def capabilities(self) -> dict[str, Any]:
        return {
            "service": "monico-jarvis",
            "version": VERSION,
            "booted_at": BOOT_TIME,
            "mode": "local-keyless",
            "network_calls": False,
            "api_keys_required": False,
            "skills": self.list_skills(),
            "implemented": [s["name"] for s in self.list_skills()],
            "not_implemented": [
                "LLM-backed conversation (needs a model key or local model — not bundled)",
                "web browsing / search (no network in keyless mode)",
                "smart-home or device control (no integrations configured)",
                "scheduled reminders (no scheduler attached)",
            ],
        }


agent = MonicoAgent()
print('Monico Jarvis initialized - ready for business tasks')
