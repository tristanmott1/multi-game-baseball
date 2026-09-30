# Data dictionary

## Perspectives and identifiers

`top` and `bot` identify halves of an inning, not teams:

| File | Batting / fielding perspective |
| --- | --- |
| `matchups_top.csv` | Away batters against home pitchers |
| `matchups_bot.csv` | Home batters against away pitchers |
| `top_batting_constraints.csv` | Away lineup and bench |
| `bot_batting_constraints.csv` | Home lineup and bench |
| `top_bullpen_constraints.csv` | Home pitchers |
| `bot_bullpen_constraints.csv` | Away pitchers |

Player IDs are the numeric identifiers in `BATTER` and `PITCHER`; the adjacent
name columns provide their lookup. Matchup tables can include players who are
not eligible under the constraints. ID `0` is a special placeholder: the
pitcher batting slot in batter data, or the replacement pitcher in pitcher
data. It is not a real player. Use the field's role when interpreting it.

Series targets are offensive. Before a game, bottom-half target wins equal
`3 - home_wins_before`, and top-half target wins equal
`3 - away_wins_before`. These targets apply while neither team has clinched.

## Matchup probabilities

Each row is a conditional distribution over the next base/out state. These
are model outputs, not raw historical plate appearances or trained weights.

| Columns | Meaning |
| --- | --- |
| `BATTER`, `BATTER_NAME` | Batter ID and name |
| `BAT_HAND_R` | Batting right-handed: `1`; left-handed: `0` |
| `PITCHER`, `PITCHER_NAME` | Pitcher ID and name |
| `PIT_HAND_R` | Pitching right-handed: `1`; left-handed: `0` |
| `PITCHER_REST` | Pitcher rest category for the matchup |
| `TIMES_THROUGH_ORDER` | One-based times-through-order category |
| `CURRENT_STATE24` | Starting state encoded as `outs-third-second-first` |
| `0-0-0-0` through `2-1-1-1` | Probabilities of the 24 live next states, in increasing binary base-mask order for each out count |
| `END_INNING-0` through `END_INNING-3` | Probabilities of inning-ending outcomes with the indicated runs scored |

In textual states, base indicators are `0` or `1`. The integer equivalent is
`8 * outs + 4 * third + 2 * second + first`. Integer states `0..23` are live;
`24` is an end-of-inning marker. Live-state column names encode bases and outs,
not a separate number of runs scored.

## Batting constraints

| Columns | Meaning |
| --- | --- |
| `BATTER_NAME`, `BATTER` | Player name and ID |
| `HANDEDNESS` | `R`, `L`, or `S` for right, left, or switch |
| `CAN_PLAY`, `MUST_STAY_IN` | Eligibility and must-remain-in-lineup flags |
| `BATTING_ORDER_1` through `BATTING_ORDER_5` | Initial batting slot for that game: `1..9`; `0` means bench |
| `INIT_POSITION` | Initial defensive position; `NA` for a bench player |
| `DH`, `C`, `1B`, `2B`, `3B`, `SS`, `LF`, `CF`, `RF` | Position eligibility flags |

Boolean constraint fields use `0`/`1`. Both bench players remain in the data,
but `solver.batter_subs = 0` prevents batting and defensive player substitutions.
The original order-optimization flags (`CAN_BAT_1..9`, `CAN_BE_BENCHED`)
were all zero and are omitted. Empty `PREREQUISITES` lists are also omitted.

## Bullpen constraints and rest

Pitcher metadata repeats across rest rows. `IS_STARTER = 0` identifies a
reliever; positive values designate the starter's game. Rest vectors use
distinct relievers in first-appearance order in the corresponding bullpen CSV.
There are six relievers per team, with separate rows for rest values `0` and `1`.

| Columns | Meaning |
| --- | --- |
| `PITCHER_NAME`, `PITCHER`, `HANDEDNESS` | Pitcher name, ID, and throwing hand |
| `CAN_PITCH` | Eligibility flag |
| `IS_STARTER` | Starter game; zero for a reliever |
| `FIRST_GAME_ALLOWED`, `LAST_GAME_ALLOWED` | Inclusive game availability bounds |
| `INIT_REST` | Rest at the start of the sequence |
| `REST_VALUE` | Rest category described by this row |
| `MIN_REST`, `MAX_REST` | Bounds for rest updates |
| `END_INNING_MAX_BATTERS_FACED` | BF threshold used for inning-end removal |
| `LOWER_MAX_BATTERS_FACED`, `UPPER_MAX_BATTERS_FACED` | Within-game fatigue/removal bounds, including the solver's fatigue-notice rules |
| `MIN_INNING` | Earliest entry inning for this rest row |
| `RESTED_DISTRIBUTION` | Probabilities indexed by rest increment for an unused pitcher |
| `USED_DISTRIBUTION` | Probabilities indexed by rest decrement for a used pitcher |

The published tables omit unused fields from the original input format:
`OPENER` and `PREREQUISITES` were empty lists; `WARMUP_BATTERS` was zero;
`LOW_BF_BRANCH`, `HIGH_BF_BRANCH`, `HIGH_BF_USED_DISTRIBUTION`,
`WARMUP_DOWNGRADE_PROBS`, and `WARMUP_HOLD_PROBS` were blank.

Distribution entries are probabilities of a change, not absolute next-rest
values. Add the sampled index for an unused pitcher, subtract it for a used
pitcher, then clamp to the rest bounds. In these inputs, an unavailable
reliever recovers with probability `0.9`; an available, used reliever remains
available with probability `0.3`. An available, unused reliever stays available.
Pitchers who enter count as used, including the active pitcher at termination.
Within-game fatigue is distinct from these between-game rest draws.

Each starter is available for its assigned game only. Its end-inning/lower/upper
BF settings are `21/18/24`. No rest draw occurs after the fifth game.

## Defense

All defensive values were zero. The original `top_defense.csv` and
`bot_defense.csv` tables are therefore omitted. Position eligibility remains
in the batting constraints.

## Result matrices

All three CSVs have header `home_manager,single,total,series`. Rows are home
managers; columns are away managers, ordered `single`, `total`, `series`.
Values are always from the home team's perspective.

| Filename | Quantity | Range |
| --- | --- | --- |
| `game_1_home_win_pct.csv` | Percentage of sequences where home wins game one | `0..100` |
| `mean_home_wins.csv` | Mean home wins across all five games | `0..5` |
| `series_home_win_pct.csv` | Percentage of sequences where home wins at least three games | `0..100` |

All three matrices use the same sequences. Percentages are not fractions.

## Simulation records

Files retain the original schema-2 [pairing and batch layout](../data/simulations/README.md).
All IDs below are player IDs unless described as internal references.
Lists and structured objects are compact
JSON inside CSV fields; booleans are `0`/`1`, and absent optional values are
empty CSV fields.

### `plays.csv.gz`

One gzip-compressed CSV row represents the state immediately before an accepted
decision. Outcome fields describe what happened after that decision. Rows do
not contain child actions, alternatives, counterfactual values, or player names.

| Fields | Meaning |
| --- | --- |
| `sequence`, `game`, `decision` | One-based sequence, actual game, and within-game decision numbers |
| `owner`, `inning`, `half` | Decision owner (`home`/`away`), inning, and `top`/`bot` |
| `home_score`, `away_score` | Actual pre-decision scores |
| `state24` | Integer base/out encoding defined above |
| `home_order`, `away_order`, `batter` | Zero-based batting slots and active batter ID |
| `home_lineup`, `away_lineup` | Ordered lists of player IDs |
| `home_positions`, `away_positions` | Defensive positions aligned with each lineup |
| `home_pitcher`, `away_pitcher`, `home_bf`, `away_bf` | Current pitchers and batters faced |
| `home_can_sub`, `away_can_sub` | Pitcher-substitution eligibility |
| `home_fatigue`, `away_fatigue` | Current within-game fatigue probabilities |
| `home_warming_pitcher`, `away_warming_pitcher`, `home_warmup_level`, `away_warmup_level` | Warmup state; warmup requirements are zero in this experiment |
| `home_bench`, `away_bench` | Remaining bench-player IDs |
| `home_bullpen`, `away_bullpen` | Remaining pitcher options, including options not yet eligible by minimum inning |
| `action`, `entering_player`, `exiting_player` | Realized action and applicable entering/exiting IDs |
| `details`, `handedness`, `current_warmup`, `future_warmup` | Action-specific details and selected hand/warmup choices |
| `outcome` | Internal sampled outcome index, not a portable baseball outcome code |
| `runs_scored`, `terminal_result` | Realized runs and optional `home_win`, `away_win`, or `tie` terminal result |

The `owner` field identifies the main decision's owner. A finish-PA record can
also contain the batting manager's handedness and the next pitching manager's
future warmup choice. Do not attribute every nested choice to the main owner.
Internal outcome indexes and any internal references inside action details
must not be interpreted without their original private policy context.

### `games.csv`

Five rows per sequence:

- `sequence`, `game`: sequence and actual game numbers.
- `policies`: JSON mapping of manager objective to its top/bottom policy IDs;
  these are opaque provenance references, not links to published solutions.
- `home_initial_rest`, `away_initial_rest`: JSON rest vectors in the corresponding
  metadata's reliever order.
- `home_wins_before`, `away_wins_before`: standing before the game.
- `home_score`, `away_score`: final actual scores.
- `terminal_result`: original `home_win`, `away_win`, or `tie` result.
- `winner`: assigned `home` or `away` winner, including the fair coin for ties.
- `post_clinch`: whether either team had already clinched before this game.
- `decisions`: number of accepted decision rows for the game.

### `rest.csv`

The exact fields are `sequence,after_game,team,player,starting_rest,used,next_rest`.
Each row records one reliever's sampled transition after game `1..4`.
There are 48 rows per sequence: four boundaries, two teams, six relievers.
`used` records actual entry during the game, not absence from a final bullpen list.

### `metadata.json`

Pairing metadata contains `identity`, `identity_sha256`, `batch_size`, `players`,
`relievers`, `policy_keys`, and `seed_rule`.

`identity` contains `schema` (2), `home`, `away`, `source_sha256`,
`scientific_config`, `simulation` (sequence count and seed), `provenance`
(source/dependency information), and `solutions` (policy completion provenance).
`identity_sha256` hashes compact, sorted-key JSON for this identity.

`players` maps IDs to names, while `relievers` defines each team's rest-vector
ordering. `policy_keys` names private key files; those files are not published.
Hashes and file references identify the original computation, not access to
the implementation. The seed convention derives independent streams from
`[seed, home_manager, away_manager, sequence, purpose]` using SHA-256.

Original simulation input hashes refer to the full input format with Linux
line endings; the public constraints omit the unused fields listed above.
