# Analysis

## Mason Miller entries

From the repository root, run with Python 3.12 or later:

```bash
python analysis/mason_miller_entries.py
```

The script reads the single/single, total/total, and series/series simulations.
It selects game four when Miller's team (away) leads the series 2-1, then
records each pitching substitution bringing him into the game. It uses only
the Python standard library.

Output: [../results/mason_miller_entries.csv](../results/mason_miller_entries.csv).

| Column | Meaning |
| --- | --- |
| `manager` | `single`, `total`, or `series` |
| `inning` | Inning of entry, starting at one |
| `outs` | Outs immediately before entry |
| `score_margin` | Away score minus home score immediately before entry; positive means Miller's team is ahead |

Each row is one appearance. Separate appearances with identical values remain
separate rows. Games where Miller never enters contribute no rows. Rows follow
manager order (`single`, `total`, `series`), then source sequence/event order.
The script streams compressed play records one batch at a time and prints
counts after each pairing. Rerunning replaces the CSV only after all three
pairings succeed; source data remains unchanged.

Run the focused tests with:

```bash
python -m unittest discover -s analysis -p "test_*.py"
```

## Usage figure

Install Matplotlib in your Python environment, then plot the extracted CSV:

```bash
python -m pip install matplotlib
python analysis/plot_mason_miller_entries.py
```

Output: [../results/mason_miller_entries.png](../results/mason_miller_entries.png).
The 300-DPI figure shows single-game, total-wins, and series managers in red,
green, and blue. Each dot represents one Miller entry with his team leading
the series 2-1. All three panels share the same scales; positive score margins
mean his team is ahead. Minor horizontal ticks mark individual outs.

Deterministic jitter fills two-thirds of each out/run cell in both directions:
up to 1/9 inning horizontally and 1/3 run vertically from each entry's position.
A fixed panel aspect ratio makes these jitter boxes square. Offsets are
reproducible, using manager, CSV row number, and axis as identifiers.
This affects only point placement, not the CSV values.
There is no save-situation distinction. Rerunning replaces the PNG; plotting
settings are near the top of the script.
