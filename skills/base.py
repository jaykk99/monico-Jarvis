"""Skill interface for Monico Jarvis. Keyless: every skill runs locally."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Skill:
    """A single command skill.

    triggers: first-word commands that route to this skill, e.g. ["calc"].
    run: takes (trigger, args) — the matched trigger word and the text after
    it — and returns reply text.
    """

    name: str
    description: str
    usage: str
    triggers: list[str]
    run: Callable[[str, str], str]
    examples: list[str] = field(default_factory=list)


@dataclass
class SkillResult:
    ok: bool
    skill: str
    response: str


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: list[Skill] = []
        self._by_trigger: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills.append(skill)
        for trigger in skill.triggers:
            self._by_trigger[trigger.lower()] = skill

    def find(self, first_word: str) -> Optional[Skill]:
        return self._by_trigger.get(first_word.lower())

    def all(self) -> list[Skill]:
        return list(self._skills)
