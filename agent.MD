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
