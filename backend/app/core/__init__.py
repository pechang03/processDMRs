"""Core functionality for DMR analysis system."""

from .rb_domination import (
    greedy_rb_domination,
    calculate_dominating_set,
)

__all__ = [
    "greedy_rb_domination",
    "calculate_dominating_set",
]
