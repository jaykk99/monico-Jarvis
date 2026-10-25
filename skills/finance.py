"""Personal-finance math: paycheck conversion, compound growth, monthly
budget breakdown, and savings-goal timing.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only, not financial advice: no taxes, fees, or inflation
are modelled, and compound growth assumes a fixed nominal rate.
"""
from __future__ import annotations

import math
import re
from datetime import date

from .base import Skill, SkillRegistry

_WEEKS_PER_YEAR = 52
_MONTHS_PER_YEAR = 12


def _num(token: str) -> float | None:
    """Parse a number, tolerating $ , and a trailing % sign."""
    token = token.replace("$", "").replace(",", "").strip()
    if token.endswith("%"):
        token = token[:-1]
    try:
        return float(token)
    except ValueError:
        return None


def _money(value: float) -> str:
    return f"${value:,.2f}"


# ---------------------------------------------------------------- paycheck


def _run_paycheck(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) < 2:
        return ("Usage: `paycheck <amount> hourly|weekly|monthly|yearly "
                "[hours-per-week]` — e.g. `paycheck 25 hourly`, "
                "`paycheck 60000 yearly`, `paycheck 25 hourly 35`. "
                "Defaults to 40 hours/week.")
    amount = _num(tokens[0])
    period = tokens[1]
    if amount is None or amount <= 0:
        return f"Couldn't read a pay amount from `{tokens[0]}`."
    if period not in ("hourly", "weekly", "monthly", "yearly", "annual"):
        return "Period must be hourly, weekly, monthly, or yearly."
    hours = 40.0
    if len(tokens) > 2:
        hours = _num(tokens[2])
        if hours is None or hours <= 0 or hours > 168:
            return f"Hours per week must be 1–168, got `{tokens[2]}`."
    if period == "hourly":
        yearly = amount * hours * _WEEKS_PER_YEAR
    elif period == "weekly":
        yearly = amount * _WEEKS_PER_YEAR
    elif period == "monthly":
        yearly = amount * _MONTHS_PER_YEAR
    else:
        yearly = amount
    weekly = yearly / _WEEKS_PER_YEAR
    monthly = yearly / _MONTHS_PER_YEAR
    hourly = yearly / (hours * _WEEKS_PER_YEAR)
    return (f"At {hours:g} hrs/week: {_money(hourly)}/hr — "
            f"{_money(weekly)}/week — {_money(monthly)}/month — "
            f"{_money(yearly)}/year (gross, before tax).")


# ---------------------------------------------------------------- compound


def _run_compound(trigger: str, args: str) -> str:
    tokens = (args or "").strip().split()
    if len(tokens) < 3:
        return ("Usage: `compound <principal> <rate-%> <years> "
                "[monthly-contribution]` — e.g. `compound 1000 5 10` or "
                "`compound 1000 5 10 100`. Fixed nominal rate, monthly "
                "compounding; no tax or inflation.")
    principal = _num(tokens[0])
    rate = _num(tokens[1])
    years = _num(tokens[2])
    if principal is None or principal < 0:
        return f"Couldn't read a principal from `{tokens[0]}`."
    if rate is None or rate < 0:
        return f"Rate percent must be >= 0, got `{tokens[1]}`."
    if years is None or years <= 0:
        return f"Years must be > 0, got `{tokens[2]}`."
    monthly = 0.0
    if len(tokens) > 3:
        monthly = _num(tokens[3])
        if monthly is None or monthly < 0:
            return f"Monthly contribution must be >= 0, got `{tokens[3]}`."
    months = int(round(years * 12))
    monthly_rate = rate / 100 / 12
    if monthly_rate == 0:
        total = principal + monthly * months
    else:
        total = (principal * (1 + monthly_rate) ** months
                 + monthly * (((1 + monthly_rate) ** months - 1)
                              / monthly_rate))
    contributed = principal + monthly * months
    growth = total - contributed
    return (f"After {years:g} years at {rate:g}%: {_money(total)} — "
            f"you put in {_money(contributed)}, growth {_money(growth)}.")


# ---------------------------------------------------------------- budget


def _run_budget(trigger: str, args: str) -> str:
    tokens = (args or "").strip().split()
    if len(tokens) < 3 or len(tokens) % 2 == 0:
        return ("Usage: `budget <income> <category> <amount> ...` — e.g. "
                "`budget 3000 rent 1200 food 400 transport 200`. Income and "
                "amounts are monthly.")
    income = _num(tokens[0])
    if income is None or income <= 0:
        return f"Couldn't read a monthly income from `{tokens[0]}`."
    categories: list[tuple[str, float]] = []
    for name, amount_token in zip(tokens[1::2], tokens[2::2]):
        amount = _num(amount_token)
        if amount is None or amount < 0:
            return f"Couldn't read an amount for `{name}` from `{amount_token}`."
        categories.append((name, amount))
    spent = sum(amount for _, amount in categories)
    remaining = income - spent
    lines = [f"Budget on {_money(income)}/month:"]
    for name, amount in categories:
        pct = amount / income * 100
        lines.append(f"  {name}: {_money(amount)} ({pct:.0f}% of income)")
    lines.append(f"Spent: {_money(spent)} ({spent / income * 100:.0f}%) — "
                 f"left: {_money(remaining)}")
    if remaining < 0:
        lines.append("Over budget — spending exceeds income.")
    elif remaining == 0:
        lines.append("Exactly at budget — nothing left over.")
    else:
        lines.append(f"Savings rate: {remaining / income * 100:.0f}% of income.")
    return "\n".join(lines)


# ---------------------------------------------------------------- savings


def _run_savings(trigger: str, args: str) -> str:
    tokens = (args or "").strip().split()
    if len(tokens) < 2:
        return ("Usage: `savings <target> <monthly> [already-saved]` — e.g. "
                "`savings 5000 200` or `savings 5000 200 1000`.")
    target = _num(tokens[0])
    monthly = _num(tokens[1])
    if target is None or target <= 0:
        return f"Couldn't read a savings target from `{tokens[0]}`."
    if monthly is None or monthly <= 0:
        return f"Monthly amount must be > 0, got `{tokens[1]}`."
    have = 0.0
    if len(tokens) > 2:
        have = _num(tokens[2])
        if have is None or have < 0:
            return f"Already-saved must be >= 0, got `{tokens[2]}`."
    if have >= target:
        return f"Already there — {_money(have)} saved against a {_money(target)} goal."
    months = math.ceil((target - have) / monthly)
    today = date.today()
    total_months = (today.year * 12 + today.month - 1) + months
    finish = date(total_months // 12, total_months % 12 + 1, 1)
    years, rem_months = divmod(months, 12)
    span = f"{months} months" if years == 0 else (
        f"{years} year{'s' if years > 1 else ''}"
        + (f" {rem_months} months" if rem_months else ""))
    return (f"Saving {_money(monthly)}/month toward {_money(target)} "
            f"({_money(have)} already saved): {span} — "
            f"goal reached around {finish.strftime('%Y-%m')}.")


# ---------------------------------------------------------------- registry


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="paycheck", description="Hourly/weekly/monthly/yearly pay conversion.",
        usage="paycheck <amount> hourly|weekly|monthly|yearly [hours-per-week]",
        triggers=["paycheck", "salary", "wage"],
        run=_run_paycheck,
        examples=["paycheck 25 hourly", "paycheck 60000 yearly",
                  "paycheck 25 hourly 35"]))
    registry.register(Skill(
        name="compound", description="Compound growth of savings + contributions.",
        usage="compound <principal> <rate-%> <years> [monthly-contribution]",
        triggers=["compound", "interest", "growth"],
        run=_run_compound,
        examples=["compound 1000 5 10", "compound 1000 5 10 100"]))
    registry.register(Skill(
        name="budget", description="Monthly budget breakdown vs income.",
        usage="budget <income> <category> <amount> ...",
        triggers=["budget"],
        run=_run_budget,
        examples=["budget 3000 rent 1200 food 400 transport 200"]))
    registry.register(Skill(
        name="savings", description="Months until a savings goal is reached.",
        usage="savings <target> <monthly> [already-saved]",
        triggers=["savings", "saveup"],
        run=_run_savings,
        examples=["savings 5000 200", "savings 5000 200 1000"]))
