"""Environment-based configuration for Monico Jarvis.

Keyless by design: every setting has a safe default, so the app boots with
zero configuration. Anything listed here can be overridden with an env var
(see .env.example) without touching code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _getenv(name: str, default: str) -> str:
    return os.environ.get(name, default).strip() or default


def _getenv_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _getenv_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _getenv_list(name: str, default: list[str]) -> list[str]:
    raw = os.environ.get(name, "")
    if not raw.strip():
        return default
    return [part.strip() for part in raw.split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    """All runtime settings. Read once at import; override via env vars."""

    # network
    host: str = field(default_factory=lambda: _getenv("MONICO_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _getenv_int("MONICO_PORT", 8000))

    # storage
    data_dir: Path = field(
        default_factory=lambda: Path(
            _getenv(
                "MONICO_DATA_DIR",
                str(Path(__file__).resolve().parent / "data"),
            )
        )
    )

    # api protection
    cors_origins: list[str] = field(
        default_factory=lambda: _getenv_list("MONICO_CORS_ORIGINS", ["*"])
    )
    # max /chat requests per window, per client IP (0 disables)
    rate_limit_per_minute: int = field(
        default_factory=lambda: _getenv_int("MONICO_RATE_LIMIT_PER_MIN", 60)
    )

    # behavior
    log_level: str = field(
        default_factory=lambda: _getenv("MONICO_LOG_LEVEL", "info").upper()
    )
    # comma-separated skill names to disable, e.g. "password,dice"
    disabled_skills: list[str] = field(
        default_factory=lambda: [s.lower() for s in _getenv_list("MONICO_DISABLED_SKILLS", [])]
    )
    # currency table freshness marker (offline rates are a snapshot)
    currency_rates_date: str = field(
        default_factory=lambda: _getenv("MONICO_CURRENCY_RATES_DATE", "2026-10-20")
    )

    def masked(self) -> dict:
        """Safe-to-log view of the settings (no secrets — there are none)."""
        return {
            "host": self.host,
            "port": self.port,
            "data_dir": str(self.data_dir),
            "cors_origins": self.cors_origins,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "log_level": self.log_level,
            "disabled_skills": self.disabled_skills,
            "currency_rates_date": self.currency_rates_date,
        }


settings = Settings()
