"""Plot Mason Miller's entries while his team leads the series 2-1."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt


PANELS = (
    ("single", "Single Game Manager", "tab:red"),
    ("total", "Total Wins Manager", "tab:green"),
    ("series", "Series Manager", "tab:blue"),
)
FIGURE_SIZE = (12, 4)
# Axes height/width: (2/9 * 15) / (2/3 * 6.1), so jitter boxes are square.
PANEL_ASPECT = 0.819672131148
POINT_SIZE = 4
POINT_ALPHA = 0.25
# Full jitter ranges occupy two-thirds of each out/run cell.
X_JITTER = 0.222222222222
Y_JITTER = 0.666666666667
DPI = 300


def stable_jitter(key: str, amount: float) -> float:
    """Return a reproducible offset between minus and plus half the given width."""
    # Hash the point identifier with unsigned 32-bit arithmetic.
    value = 2166136261
    for character in key:
        value = ((value ^ ord(character)) * 16777619) & 0xFFFFFFFF
    value ^= value >> 16
    value = (value * 2246822507) & 0xFFFFFFFF
    value ^= value >> 13
    value = (value * 3266489909) & 0xFFFFFFFF
    value ^= value >> 16
    return (value / 4294967295 - 0.5) * amount


def main() -> None:
    """Read the entry CSV and save a three-panel PNG."""
    root = Path(__file__).resolve().parents[1]
    points = {manager: ([], []) for manager, _, _ in PANELS}

    # Jitter each appearance separately, including entries with identical states.
    with (root / "results" / "mason_miller_entries.csv").open(newline="", encoding="utf-8") as source:
        for row_number, row in enumerate(csv.DictReader(source), start=1):
            manager = row["manager"]
            key = f"{manager}:{row_number}"
            x, y = points[manager]
            x.append(int(row["inning"]) + int(row["outs"]) / 3 + stable_jitter(f"{key}:x", X_JITTER))
            y.append(int(row["score_margin"]) + stable_jitter(f"{key}:y", Y_JITTER))

    figure, axes = plt.subplots(1, 3, figsize=FIGURE_SIZE, sharex=True, sharey=True,
                               layout="constrained", facecolor="white")

    # Shared limits and styling keep all three managers directly comparable.
    for axis, (manager, title, color) in zip(axes, PANELS):
        axis.scatter(*points[manager], s=POINT_SIZE, color=color, alpha=POINT_ALPHA,
                     edgecolors="none", zorder=3)
        axis.set_title(title)
        axis.set_xlim(4.8, 10.9)
        axis.set_ylim(-7.5, 7.5)
        axis.set_box_aspect(PANEL_ASPECT)
        axis.set_xticks(range(5, 11))
        axis.set_xticks([inning + outs / 3 for inning in range(5, 11) for outs in (1, 2)], minor=True)
        axis.set_yticks(range(-7, 8))
        axis.grid(color="0.9", linewidth=0.5)
        axis.axhline(0, color="0.4", linewidth=0.8, zorder=2)
        axis.spines[["top", "right"]].set_visible(False)

    figure.suptitle("Mason Miller Appearances With 2-1 Series Lead\n", fontweight="bold")
    figure.supxlabel("Inning")
    figure.supylabel("Score Margin")
    output = root / "results" / "mason_miller_entries.png"
    figure.savefig(output, dpi=DPI)
    plt.close(figure)
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
