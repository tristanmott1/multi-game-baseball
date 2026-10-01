# How Important Is Winning Today?

Optimizing Baseball Management Across Multiple Games

This repository contains the data for an experiment comparing three baseball
management objectives over five consecutive games:

- **Single:** maximize the probability of winning the current game.
- **Total:** maximize expected wins over the remaining games.
- **Series:** maximize the probability of winning at least three games.

Each home manager faces each away manager in 65,536 simulated sequences, for
589,824 sequences and 2,949,120 games. All five games are played, even if a team
clinches early.
Series managers switch to single-game policies once either team clinches;
all managers use single-game policies in game five.

## Data

| Location | Contents |
| --- | --- |
| [data/inputs/](data/inputs/) | Matchup probabilities, batting orders, and pitching constraints |
| [data/simulations/](data/simulations/) | Play-by-play, game summaries, rest transitions, and run metadata |
| [results/](results/) | Manager comparison matrices and extracted Mason Miller entries |
| [config.json](config.json) | Experiment settings and original computing allocations |
| [analysis/](analysis/) | Standalone analysis of simulation records |

See the [data dictionary](docs/data.md) for columns, player IDs, and team
perspectives. Matrix rows are home managers and columns are away managers.
The matrices report game-one home-win percentage, mean home wins over five
games, and the percentage of sequences with at least three home wins.

The published constraints omit unused columns and the all-zero defense tables.
Retained values match the original inputs. The data dictionary describes the
omitted settings; original input hashes remain in the simulation metadata.

## Methods

There are no off days, venue changes, or batting substitutions. Lineups reset
between games; bullpen rest and series standings carry forward. Terminal ties
are assigned a winner by a fair coin. Current-game policies use ten innings
and a score-deficit cutoff of eight under regular-season rules. Continuation
values use simplified dynamics and eleven innings.

Each policy assumes the opponent shares its objective. Mixed-manager results
compare these policies; they are not cross-objective equilibrium solutions.

## Availability

Matchup probabilities and simulation records are included. Model training code,
optimization solvers, and generated policies are private. See
[analysis/](analysis/) for the Mason Miller entry extraction command.
Historical decision case studies will be added separately.

A license has not yet been selected.
