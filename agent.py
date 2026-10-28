# Core Monico Agent - Uncensored Jarvis
"""Command routing + skill registry.

Keyless by design: every skill runs locally on the box, no API keys,
no network calls, no secrets. Agent logic is a real command router over
a plugin-style skill registry (see skills/).
"""
from __future__ import annotations

import logging
import time as _time
from typing import Any

from skills.base import SkillRegistry
from skills import builtin, everyday, finance, household, life, moretools, practical, productivity, texttools, utilities

log = logging.getLogger("monico-jarvis.agent")

VERSION = "2.8.0"
BOOT_TIME = _time.time()

_FALLBACK_SUGGESTIONS = (
    "I don't have a skill for that yet. Try `help` to see what I can do, "
    "or one of: time, calc, timer, todo, convert, dice, coin, password, note, status."
)


class MonicoAgent:
    def __init__(self, disabled: tuple[str, ...] = ()) -> None:
        self.registry = SkillRegistry()
        builtin.register_all(self.registry)
        productivity.register_all(self.registry)
        texttools.register_all(self.registry)
        utilities.register_all(self.registry)
        moretools.register_all(self.registry)
        everyday.register_all(self.registry)
        finance.register_all(self.registry)
        household.register_all(self.registry)
        life.register_all(self.registry)
        practical.register_all(self.registry)
        self.disabled = {d.lower() for d in disabled}
        if self.disabled:
            log.info("disabled skills: %s", sorted(self.disabled))

    def respond(self, text: str) -> dict[str, Any]:
        """Route one user message to a skill. Always returns a JSON-safe dict."""
        cleaned = " ".join(text.split())
        parts = cleaned.split(" ", 1)
        trigger = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        skill = self.registry.find(trigger)
        if skill is None or skill.name in self.disabled:
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
                "disabled": s.name in self.disabled,
            }
            for s in self.registry.all()
        ]

    def capabilities(self) -> dict[str, Any]:
        skills = self.list_skills()
        active = [s for s in skills if not s["disabled"]]
        return {
            "service": "monico-jarvis",
            "version": VERSION,
            "booted_at": BOOT_TIME,
            "mode": "local-keyless",
            "network_calls": False,
            "api_keys_required": False,
            "skills": skills,
            "implemented": [s["name"] for s in active],
            "disabled": sorted(self.disabled),
            "not_implemented": [
                "LLM-backed conversation (needs a model key or local model — not bundled)",
                "web browsing / search (no network in keyless mode)",
                "smart-home or device control (no integrations configured)",
                "live currency/weather/stock prices (offline snapshots only — keyless)",
                "push-notification reminders (no scheduler attached — use `reminders` to check)",
            ],
        }


def _disabled_from_env() -> tuple[str, ...]:
    try:
        from config import settings
    except Exception:  # config importable in every normal path; stay safe
        return ()
    return tuple(settings.disabled_skills)


agent = MonicoAgent(disabled=_disabled_from_env())
log.info("Monico Jarvis v%s initialized — %d skills ready",
         VERSION, len(agent.list_skills()))
