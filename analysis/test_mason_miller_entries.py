"""Tests for the standalone Mason Miller entry extraction."""

import contextlib
import csv
import gzip
import io
import json
import tempfile
import unittest
from pathlib import Path

from mason_miller_entries import MANAGERS, MILLER_ID, OUTPUT_FIELDS, extract


GAME_FIELDS = ("sequence", "game", "home_wins_before", "away_wins_before")
PLAY_FIELDS = ("sequence", "game", "action", "entering_player", "owner", "half",
               "inning", "state24", "home_score", "away_score")


def write_games(path: Path, rows: list[list[int]]) -> None:
    """Write a small game-summary fixture."""
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(GAME_FIELDS)
        writer.writerows(rows)


def write_plays(path: Path, rows: list[list]) -> None:
    """Write compressed decision records."""
    with gzip.open(path, "wt", encoding="utf-8", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(PLAY_FIELDS)
        writer.writerows(rows)


class MillerEntriesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "results").mkdir()
        self.output = self.root / "results" / "mason_miller_entries.csv"
        self.games = [[sequence, 4, 1, 2] for sequence in range(1, 6)] + [[6, 4, 2, 1]]
        self.plays = [
            [1, 4, "pitcher_sub", MILLER_ID, "away", "bot", 6, 0, 1, 4],
            [2, 4, "pitcher_sub", MILLER_ID, "away", "bot", 6, 0, 1, 4],
            [3, 4, "pitcher_sub", MILLER_ID, "away", "bot", 7, 11, 2, 2],
            [4, 4, "pitcher_sub", MILLER_ID, "away", "bot", 8, 23, 5, 3],
            [6, 4, "pitcher_sub", MILLER_ID, "away", "bot", 8, 0, 0, 0],
            [1, 3, "pitcher_sub", MILLER_ID, "away", "bot", 8, 0, 0, 0],
            [1, 4, "pitcher_sub", 123, "away", "bot", 8, 0, 0, 0],
            [1, 4, "finish_pa", MILLER_ID, "away", "bot", 8, 0, 0, 0],
        ]

        # Sequence five qualifies but has no Miller entry; sequence six does not qualify.
        for manager in MANAGERS:
            batch = self.batch(manager)
            batch.mkdir(parents=True)
            metadata = {
                "identity": {"home": manager, "away": manager,
                             "simulation": {"sequences_per_pairing": 6}},
                "players": {str(MILLER_ID): "Mason Miller"},
                "relievers": {"home": [123], "away": [MILLER_ID]},
            }
            (batch.parent / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
            write_games(batch / "games.csv", self.games)
            write_plays(batch / "plays.csv.gz", self.plays)

    def batch(self, manager: str = "single") -> Path:
        """Return the first batch directory for a pairing."""
        return self.root / "data" / "simulations" / f"home_{manager}_away_{manager}" / "batch_000001_000006"

    def run_extraction(self) -> dict[str, int]:
        """Suppress command output during fixture checks."""
        with contextlib.redirect_stdout(io.StringIO()):
            return extract(self.root)

    def test_entries_and_rerun(self) -> None:
        self.assertEqual(self.run_extraction(), dict.fromkeys(MANAGERS, 4))
        with self.output.open(newline="") as source:
            rows = list(csv.reader(source))
        expected = [list(OUTPUT_FIELDS)]
        for manager in MANAGERS:
            expected.extend([[manager, "6", "0", "3"], [manager, "6", "0", "3"],
                             [manager, "7", "1", "0"], [manager, "8", "2", "-2"]])
        self.assertEqual(rows, expected)
        original = self.output.read_bytes()
        self.run_extraction()
        self.assertEqual(self.output.read_bytes(), original)

    def test_missing_files_preserve_output(self) -> None:
        # Fail after earlier pairings have already written their temporary output.
        for filename in ("metadata.json", "games.csv", "plays.csv.gz"):
            with self.subTest(filename=filename):
                base = self.batch("series")
                path = (base.parent if filename == "metadata.json" else base) / filename
                contents = path.read_bytes()
                path.unlink()
                self.output.write_bytes(b"existing result\n")
                with self.assertRaises(FileNotFoundError):
                    self.run_extraction()
                self.assertEqual(self.output.read_bytes(), b"existing result\n")
                self.assertEqual(list(self.output.parent.glob(".mason_miller_*")), [])
                path.write_bytes(contents)

    def test_invalid_summary_coverage(self) -> None:
        cases = ((self.games + [self.games[0]], "duplicate"),
                 (self.games[:-1], "expected 6"),
                 ([[1, 4, 2, 2]] + self.games[1:], "standing"))
        for games, message in cases:
            with self.subTest(message=message):
                write_games(self.batch() / "games.csv", games)
                with self.assertRaisesRegex(ValueError, message):
                    self.run_extraction()

    def test_duplicate_across_batches(self) -> None:
        batch = self.batch().parent / "batch_000007_000012"
        batch.mkdir()
        write_games(batch / "games.csv", self.games)
        write_plays(batch / "plays.csv.gz", [])
        with self.assertRaisesRegex(ValueError, "duplicate game-four"):
            self.run_extraction()

    def test_invalid_entry_fields(self) -> None:
        for column, value in (("owner", "home"), ("half", "top"), ("inning", "bad"),
                              ("inning", 0), ("state24", 24), ("home_score", -1)):
            with self.subTest(column=column, value=value):
                rows = [row[:] for row in self.plays]
                rows[0][PLAY_FIELDS.index(column)] = value
                write_plays(self.batch() / "plays.csv.gz", rows)
                with self.assertRaises(ValueError):
                    self.run_extraction()

    def test_missing_columns(self) -> None:
        write_plays(self.batch() / "plays.csv.gz", [])
        with gzip.open(self.batch() / "plays.csv.gz", "wt") as target:
            target.write("sequence,game\n")
        with self.assertRaisesRegex(ValueError, "missing play-by-play columns"):
            self.run_extraction()

    def test_incorrect_metadata(self) -> None:
        path = self.batch().parent / "metadata.json"
        metadata = json.loads(path.read_text())
        metadata["relievers"] = {"home": [MILLER_ID], "away": [123]}
        path.write_text(json.dumps(metadata), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Mason Miller must be away"):
            self.run_extraction()


if __name__ == "__main__":
    unittest.main()
