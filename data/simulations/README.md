# Simulation data

The nine `home_{manager}_away_{manager}` directories cover all pairings of
`single`, `total`, and `series`. Each contains 65,536 sequences in 512 batches
of 128 sequences. The complete dataset occupies approximately 5.88 GiB.

```text
home_single_away_single/
  metadata.json
  batch_000001_000128/
    plays.csv.gz
    games.csv
    rest.csv
    complete.json
```

Sequence numbers are one-based and local to a pairing. Batch names give
inclusive sequence bounds. Each sequence contains five games and four rest
boundaries, including games played after a series clinch.

`plays.csv.gz` contains accepted decisions and realized outcomes. `games.csv`
contains final scores and winners. `rest.csv` records between-game reliever
rest. Pairing metadata identifies the run, players, and policies.
`complete.json` preserves the original batch counts and file statistics;
its timestamps refer to the cluster files, not the downloaded copies.

See the [data dictionary](../../docs/data.md) for field definitions.
