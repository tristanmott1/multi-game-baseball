"""Extract Mason Miller's pitching entries with his team leading the series 2-1."""

import csv
import gzip
import json
import sys
import tempfile
from pathlib import Path
from typing import TextIO


MANAGERS = ("single", "total", "series")
MILLER_ID = 695243
OUTPUT_FIELDS = ("manager", "inning", "outs", "score_margin")


def game_four_standings(path: Path, sequences: int, seen: set[int]) -> set[int]:
    """Validate game summaries and return qualifying sequence numbers."""
    required = {"sequence", "game", "home_wins_before", "away_wins_before"}
    qualifying = set()
    games = set()
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{path}: missing game-summary columns")

        # Select the standing before game four, including assigned winners of ties.
        for row in reader:
            sequence, game = int(row["sequence"]), int(row["game"])
            if not 1 <= sequence <= sequences or not 1 <= game <= 5:
                raise ValueError(f"{path}: invalid sequence/game {sequence}/{game}")
            if (sequence, game) in games:
                raise ValueError(f"{path}: duplicate game summary {sequence}/{game}")
            games.add((sequence, game))
            if game != 4:
                continue
            if sequence in seen:
                raise ValueError(f"{path}: duplicate game-four summary for {sequence}")
            seen.add(sequence)
            home, away = int(row["home_wins_before"]), int(row["away_wins_before"])
            if home < 0 or away < 0 or home + away != 3:
                raise ValueError(f"{path}: invalid game-four standing for {sequence}")
            if home == 1 and away == 2:
                qualifying.add(sequence)
    return qualifying


def extract_pairing(folder: Path, manager: str, target: TextIO) -> int:
    """Stream one self-play pairing into the output CSV."""
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    identity = metadata["identity"]
    if identity["home"] != manager or identity["away"] != manager:
        raise ValueError(f"{folder}: expected {manager} self-play metadata")
    if (metadata["players"].get(str(MILLER_ID)) != "Mason Miller"
            or MILLER_ID not in metadata["relievers"]["away"]
            or MILLER_ID in metadata["relievers"]["home"]):
        raise ValueError(f"{folder}: Mason Miller must be away reliever {MILLER_ID}")
    sequences = identity["simulation"]["sequences_per_pairing"]
    if type(sequences) is not int or sequences <= 0:
        raise ValueError(f"{folder}: invalid sequence count")

    required = {"sequence", "game", "action", "entering_player", "owner", "half",
                "inning", "state24", "home_score", "away_score"}
    seen = set()
    count = 0
    writer = csv.writer(target)

    # Batch names and their source rows follow sequence and decision order.
    for batch in sorted(folder.glob("batch_*")):
        qualifying = game_four_standings(batch / "games.csv", sequences, seen)
        path = batch / "plays.csv.gz"
        with gzip.open(path, "rt", encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            if not required.issubset(reader.fieldnames or []):
                raise ValueError(f"{path}: missing play-by-play columns")

            # Only substitution events record entry; subsequent plate appearances do not.
            for row in reader:
                if (row["game"] != "4" or row["action"] != "pitcher_sub"
                        or row["entering_player"] != str(MILLER_ID)):
                    continue
                if int(row["sequence"]) not in qualifying:
                    continue
                if row["owner"] != "away" or row["half"] != "bot":
                    raise ValueError(f"{path}: Miller entry must belong to away in the bottom half")
                inning, state = int(row["inning"]), int(row["state24"])
                home, away = int(row["home_score"]), int(row["away_score"])
                if inning < 1 or not 0 <= state < 24 or min(home, away) < 0:
                    raise ValueError(f"{path}: invalid pre-substitution state")

                # Scores and base/out state precede the decision; Miller pitches for away.
                writer.writerow((manager, inning, state // 8, away - home))
                count += 1

    if len(seen) != sequences:
        raise ValueError(f"{folder}: expected {sequences} game-four summaries, found {len(seen)}")
    return count


def extract(root: Path) -> dict[str, int]:
    """Publish the CSV only after all three pairings have been read successfully."""
    output = root / "results" / "mason_miller_entries.csv"
    temporary = None
    counts = {}
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         dir=output.parent, prefix=".mason_miller_",
                                         suffix=".csv", delete=False) as target:
            temporary = Path(target.name)
            writer = csv.writer(target)
            writer.writerow(OUTPUT_FIELDS)

            # Preserve a fixed manager order without combining identical appearances.
            for manager in MANAGERS:
                folder = root / "data" / "simulations" / f"home_{manager}_away_{manager}"
                counts[manager] = extract_pairing(folder, manager, target)
                print(f"{manager}: {counts[manager]} entries", flush=True)
        temporary.replace(output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"Saved {output}")
    return counts


if __name__ == "__main__":
    try:
        extract(Path(__file__).resolve().parents[1])
    except (OSError, ValueError, KeyError, TypeError, EOFError) as error:
        print(f"Mason Miller extraction failed: {error}", file=sys.stderr)
        sys.exit(1)
