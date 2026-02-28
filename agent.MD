# CFB-Football-Sim Repository Quick Reference

This file is a high-level map of the repository so an agent (or contributor) can quickly understand where things live, what is actively used, and what appears to be legacy/in-progress.

## Project purpose
- College football simulation project with:
  - a **modern CLI game simulator**,
  - a **Tkinter coach career GUI**,
  - database-backed team/player data,
  - and older prototype modules/scripts still present in the repo.

## Current runtime entry points (active)

### 1) Main app entrypoint
- **`cfbSimulation/main.py`**
  - Parses CLI options.
  - Launches GUI when `--gui` is passed.
  - Otherwise runs a single game simulation using `GameSimulator`.
  - Supports listing teams (`--list-teams`) and seeded runs (`--seed`).

### 2) GUI (coach career mode)
- **`cfbSimulation/gui.py`**
  - Tkinter app with:
    - coach creation,
    - team selection,
    - load/save career,
    - play-next-game loop,
    - start new season.
  - Uses `CareerManager` + `DatabaseRepository` + `format_scoreboard`.

## Core domain modules (active)

### Data layer
- **`cfbSimulation/data/repository.py`**
  - Read-only wrapper around SQLite DB at:
    - `datafiles/saveData/theDatabase.db`
  - Key API:
    - `health_check()`
    - `list_teams()`
    - `get_team()`
    - `get_players_for_team()`
    - `get_two_random_team_ids()`
    - `iter_team_ids()`
  - Dataclasses:
    - `TeamRecord`
    - `PlayerRecord`

### Game simulation layer
- **`cfbSimulation/logic/simulator.py`**
  - Core single-game simulation engine.
  - Dataclasses:
    - `TeamSnapshot`
    - `GameResult`
  - `GameSimulator`:
    - builds team snapshots from DB players,
    - computes offense/defense/special team ratings,
    - simulates drives and OT,
    - returns structured `GameResult`.
  - `format_scoreboard(result)` for display output.

### Career mode layer
- **`cfbSimulation/logic/career.py`**
  - Coach career state and progression.
  - Dataclasses:
    - `ScheduledGame`
    - `CoachCareer`
  - `CareerManager` handles:
    - career creation + validation,
    - random schedule generation,
    - next game simulation,
    - record updates,
    - season reset,
    - save/load JSON.
  - Save file default:
    - `datafiles/saveData/career_save.json`

## Test coverage
- **`tests/test_simulation.py`**
  - sanity checks for DB team listing and single-game sim output.
- **`tests/test_career_mode.py`**
  - validates schedule generation/save and play-next-game progression.

## Data and assets

### Data sources / generated content
- **`datafiles/`**
  - name pools / cities / conference names.
- **`datafiles/saveData/`**
  - CSV exports and primary SQLite DB.
  - includes:
    - `teams.csv`, `players.csv`, `coaches.csv`, `conferences.csv`,
    - `theDatabase.db`.

### Art assets
- **`assets/`**
  - currently contains menu icon/image resources and PSD files.

## Utility and generation scripts

### Utility constants/helpers
- **`cfbSimulation/utils/utils.py`**
  - team/player generation constants.
  - global player counter helpers.
  - `positionNumbers` lineup shape definitions.

### Data generation scripts (mostly bootstrap/prototype)
- **`scripts/intTeamsGen.py`**
- **`scripts/intPlayerGen.py`**
- **`scripts/intConferenceGen.py`**
- **`scripts/intCoachesGen.py`**
- **`scripts/intTeamLineups.py`**

These scripts appear intended to generate initial CSV/database content. Several use legacy relative paths and may require cleanup before use in current layout.

## Legacy / prototype modules (not primary flow)
- **`cfbSimulation/logic/gameLogic.py`**
- **`cfbSimulation/logic/singleGameSim.py`**
- **`cfbSimulation/logic/menu.py`**
- **`cfbSimulation/logic/mainMenu.py`**
- **`cfbSimulation/logic/positionAdjustment.py`**

Notes:
- These files include older simulation/pygame/interactive logic and direct DB usage patterns.
- Some have hard-coded paths or immediate-execution loops.
- They are useful as reference material but do not appear to be the main path used by `python -m cfbSimulation.main`.

## Typical workflows
- Install deps:
  - `python -m pip install -r requirements.txt`
- GUI career mode:
  - `python -m cfbSimulation.main --gui`
- CLI single game:
  - `python -m cfbSimulation.main --home tID8 --away tID3 --seed 7`
- List team IDs:
  - `python -m cfbSimulation.main --list-teams --team-limit 25`
- Run tests:
  - `pytest -q`

## Working conventions for future changes
- Prefer adding new features into the **active stack**:
  - `cfbSimulation/main.py`
  - `cfbSimulation/gui.py`
  - `cfbSimulation/data/repository.py`
  - `cfbSimulation/logic/simulator.py`
  - `cfbSimulation/logic/career.py`
- Treat older `logic/*.py` prototype files as legacy unless explicitly reviving them.
- Keep data access centralized through `DatabaseRepository` where possible.
- Keep deterministic behavior available via explicit random seeds for reproducibility/tests.


## Recent updates (agent-maintained)
- Career mode now includes lightweight progression stats (`coach_level`, `prestige`, `morale`) and decision scenarios that apply temporary modifiers to weekly outcomes.
- Season mode now includes a playoff bracket phase (semifinal + championship) after regular-season games complete.
- GUI exposes a **Make Decision** action in career mode and shows playoff phase/status in season mode.
- Added strategy planning support with predefined profiles plus per-week custom game plans in career mode; strategy choices now feed simulation scoring tendencies.
- Added lineup/starter planning hooks and roster management UI to preview player details and set starters for tactical boosts.
- Expanded ratings visibility with per-player impact ratings in roster view and strategy-aware simulation logs/CLI options.
- Replaced the Tkinter GUI with a PySide6-based interface featuring a dedicated Main Menu dashboard, persistent sidebar navigation, and mode-specific pages for Single Game, Season, and Career workflows.
- Added adaptive AI difficulty levels (`Easy`, `Normal`, `Hard`, `Heisman`) in career mode that influence opponent ratings and counter-strategy behavior.
- Added AI strategy memory in career mode so CPU teams adapt when the user repeatedly uses the same game plan.
- Added persistent player season statistics tracking (`player_stats.json`) and integrated automatic stat updates after simulated games.
- Added player stats viewing/comparison tools in both GUI (Career page "Player Stats") and CLI (`--player-stats`, `--compare-players`).
- Added career-mode scouting and recruiting workflows: coaches can spend scouting points to discover randomized recruits (with inferred potential notes), then submit NIL-style offers that can be accepted/rejected based on team reputation, offer level, and recruit aspirations.
- Added career roster dynamics with weekly progression/regression and offseason churn (graduation/draft departures, offseason rating changes, and signed recruits joining next season) plus offseason summary logging in the GUI.
- Expanded database repository capabilities with explicit Teams/Players schema initialization, full CRUD support, and dedicated CRUD/performance tests plus design notes in `docs/database_design.md`.
- Career mode UI now keeps the console at the top of the career panel, persists scouting tables between openings, supports sending offers directly from scouting, and tracks recruiting budget/progress feedback based on prior-season record.

- Career recruiting flow now runs fully through the scouting screen (no separate Make Offer action), with improved offer defaults and easier recruit acceptance tuning.
- Career decisions are now triggered randomly during week progression and include new player-development outcomes that can boost recruiting leverage and roster potential growth.
- Career team ratings panel now refreshes from the evolving career roster so OVR/OFF/DEF/ST reflect progression changes in-season.
- Added automatic best-player starter selection for career weeks, expanded lineup coverage to all major positions (QB/RB/WR/TE/OL/DL/LB/DB/K/P), and use auto-starters when no manual plan is saved.
- Added career-mode coaching staff management (coordinators, position coaches, and head scout) with offseason hiring pool, role swaps, coach-influenced auto-starters/development, and scout-quality effects on scouting accuracy/point regeneration.
- Added advanced team rating support with potential-driven metrics and position-based unit ratings, surfaced in both CLI and team selection previews.
- Added a configurable boom/bust framework spec (`spec/boom_bust.yaml`) and integrated per-game effective-rating multipliers in the active simulator flow via a new boom/bust engine.
- Added program structure modeling with generated FBS/FCS division assignment, program tier profiles, and AP/FCS poll tracking that updates from simulated season games; recruiting offer reputation now factors in division visibility and program-tier interest multipliers.
- Added a configurable recruiting/scouting system design spec (`spec/recruiting_sim.yaml`) covering difficulty visibility, head-scout modeling, progressive reveal, scouting/recruiting actions, and commitment dynamics.
