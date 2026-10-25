"""Tests for skills/finance.py: paycheck, compound, budget, savings."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- paycheck
def test_paycheck_hourly():
    out = _ask("paycheck 25 hourly")
    assert "$25.00/hr" in out and "$1,000.00/week" in out
    assert "$4,333.33/month" in out and "$52,000.00/year" in out


def test_paycheck_yearly_and_custom_hours():
    out = _ask("paycheck 60000 yearly")
    assert "$28.85/hr" in out and "$1,153.85/week" in out
    assert "$5,000.00/month" in out
    out = _ask("paycheck 25 hourly 35")
    assert "35 hrs/week" in out and "$45,500.00/year" in out
    assert "$875.00/week" in out


def test_paycheck_bad():
    assert "Usage" in _ask("paycheck")
    assert "Period must be" in _ask("paycheck 25 daily")
    assert "Hours per week" in _ask("paycheck 25 hourly 200")
    assert "pay amount" in _ask("paycheck abc hourly")


# ---------------------------------------------------------------- compound
def test_compound_no_contribution():
    out = _ask("compound 1000 5 10")
    assert "$1,647.01" in out and "you put in $1,000.00" in out
    assert "growth $647.01" in out


def test_compound_with_contribution_and_zero_rate():
    out = _ask("compound 1000 5 10 100")
    assert "$17,175.24" in out and "you put in $13,000.00" in out
    out = _ask("compound 1000 0 5 100")
    assert "$7,000.00" in out and "growth $0.00" in out


def test_compound_bad():
    assert "Usage" in _ask("compound 1000 5")
    assert "Rate percent" in _ask("compound 1000 -5 10")
    assert "Years must be" in _ask("compound 1000 5 0")


# ---------------------------------------------------------------- budget
def test_budget_breakdown():
    out = _ask("budget 3000 rent 1200 food 400 transport 200")
    assert "rent: $1,200.00 (40% of income)" in out
    assert "Spent: $1,800.00 (60%)" in out
    assert "left: $1,200.00" in out
    assert "Savings rate: 40%" in out


def test_budget_over_and_bad():
    out = _ask("budget 1000 rent 1200")
    assert "Over budget" in out and "left: $-200.00" in out
    assert "Usage" in _ask("budget 3000 rent")
    assert "Usage" in _ask("budget 3000")
    assert "monthly income" in _ask("budget abc rent 100")


# ---------------------------------------------------------------- savings
def test_savings_goal():
    out = _ask("savings 5000 200")
    assert "2 years 1 months" in out and "2028-11" in out
    out = _ask("savings 5000 200 1000")
    assert "1 year 8 months" in out and "2028-06" in out


def test_savings_already_there_and_bad():
    assert "Already there" in _ask("savings 5000 200 6000")
    assert "Usage" in _ask("savings 5000")
    assert "Monthly amount" in _ask("savings 5000 0")
    assert "savings target" in _ask("savings abc 200")
