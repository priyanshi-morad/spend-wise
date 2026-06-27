"""charts.py - Matplotlib chart generators for SpendWise Expense Tracker.

This module is intentionally standalone and does not modify the website behavior.
It provides helper functions to create charts from expense and budget data.
"""

from __future__ import annotations

from io import BytesIO
from typing import Dict, Iterable, List, Sequence, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np


def _save_figure(fig, save_path: str | None = None, fmt: str = "png") -> bytes | None:
    """Save a figure to disk or return raw image bytes."""
    if save_path:
        fig.savefig(save_path, format=fmt, bbox_inches="tight")
        plt.close(fig)
        return None

    buffer = BytesIO()
    fig.savefig(buffer, format=fmt, bbox_inches="tight")
    buffer.seek(0)
    plt.close(fig)
    return buffer.getvalue()


def category_pie_chart(
    category_totals: Dict[str, float],
    title: str = "Spending by Category",
    save_path: str | None = None,
    fmt: str = "png",
) -> bytes | None:
    """Create a pie chart from category totals."""
    labels = list(category_totals.keys())
    values = [float(category_totals[label]) for label in labels]

    if not values or sum(values) == 0:
        raise ValueError("Category totals must contain at least one positive value.")

    fig, ax = plt.subplots(figsize=(8, 6))
    cmap = plt.get_cmap("tab20c")
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct="%.1f%%",
        startangle=140,
        colors=cmap(np.linspace(0, 1, len(values))),
        textprops={"color": "w"},
    )
    ax.axis("equal")
    ax.set_title(title, pad=20)
    for text in texts + autotexts:
        text.set_color("#f4f4f4")
    fig.patch.set_facecolor("#1f1f1f")
    ax.set_facecolor("#1f1f1f")
    return _save_figure(fig, save_path, fmt)


def monthly_trend_chart(
    monthly_data: Sequence[Tuple[str, float]],
    title: str = "Monthly Spending Trend",
    save_path: str | None = None,
    fmt: str = "png",
) -> bytes | None:
    """Create a line/bar trend chart for monthly totals."""
    if not monthly_data:
        raise ValueError("monthly_data must contain at least one month total.")

    months, totals = zip(*monthly_data)
    totals = [float(value) for value in totals]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(months, totals, marker="o", linewidth=2, color="#63ace5")
    ax.fill_between(months, totals, color="#63ace5", alpha=0.15)
    ax.set_title(title, pad=16)
    ax.set_xlabel("Month")
    ax.set_ylabel("Amount")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_facecolor("#1f1f1f")
    fig.patch.set_facecolor("#1f1f1f")
    ax.tick_params(colors="#dcdcdc")
    ax.xaxis.label.set_color("#dcdcdc")
    ax.yaxis.label.set_color("#dcdcdc")
    return _save_figure(fig, save_path, fmt)


def budget_vs_actual_chart(
    categories: Sequence[str],
    budgets: Sequence[float],
    actuals: Sequence[float],
    title: str = "Budget vs Actual",
    save_path: str | None = None,
    fmt: str = "png",
) -> bytes | None:
    """Create a grouped bar chart comparing budgets to actuals."""
    if not categories or len(categories) != len(budgets) or len(categories) != len(actuals):
        raise ValueError("categories, budgets, and actuals must be the same length.")

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - width / 2, budgets, width, label="Budget", color="#5cb85c")
    ax.bar(x + width / 2, actuals, width, label="Actual", color="#f0ad4e")
    ax.set_title(title, pad=16)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha="right")
    ax.set_ylabel("Amount")
    ax.legend(frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    ax.set_facecolor("#1f1f1f")
    fig.patch.set_facecolor("#1f1f1f")
    ax.tick_params(colors="#dcdcdc")
    ax.xaxis.label.set_color("#dcdcdc")
    ax.yaxis.label.set_color("#dcdcdc")
    return _save_figure(fig, save_path, fmt)


def save_chart_bytes(fig, fmt: str = "png") -> bytes:
    """Return image bytes for an existing Matplotlib figure."""
    return _save_figure(fig, None, fmt)


__all__ = [
    "category_pie_chart",
    "monthly_trend_chart",
    "budget_vs_actual_chart",
    "save_chart_bytes",
]


if __name__ == "__main__":
    sample_categories = {"Food": 420.0, "Rent": 1200.0, "Travel": 310.0, "Other": 150.0}
    sample_trend = [("2024-01", 890.0), ("2024-02", 760.0), ("2024-03", 980.0), ("2024-04", 1020.0)]
    sample_months = ["Food", "Rent", "Utilities"]
    sample_budgets = [500.0, 1200.0, 320.0]
    sample_actuals = [450.0, 1200.0, 290.0]

    category_pie_chart(sample_categories, save_path="category_chart.png")
    monthly_trend_chart(sample_trend, save_path="trend_chart.png")
    budget_vs_actual_chart(sample_months, sample_budgets, sample_actuals, save_path="budget_chart.png")
    print("Generated sample charts: category_chart.png, trend_chart.png, budget_chart.png")