# Database Design Notes

## Why SQLite is a good fit right now

SQLite is a strong choice for the current phase of this game because:

- The game is primarily local/single-user, and SQLite is embedded (no separate server process).
- Reads are fast for roster/team lookups when indexed (`Players.TeamID`, `Players.Position`, `Teams.Team Name`).
- It keeps install complexity low for contributors and players.
- It is reliable and ACID-compliant for save/load operations.

When to re-evaluate: if you need many simultaneous online writers (multiplayer backend, hosted league service), consider PostgreSQL.

## Current core schema (Teams + Players)

### Teams
- `TeamID` (TEXT, PK)
- `Team Name` (TEXT)
- `Location` (TEXT)
- `ConfrenceID` (TEXT)
- `CoachID` (TEXT)
- `Wins`, `Losses`, `Ties` (INTEGER)

### Players
- `PlayerID` (TEXT, PK)
- `TeamID` (TEXT, FK -> `Teams.TeamID`)
- `Fname`, `Lname` (TEXT)
- `Position` (TEXT)
- `Overall`, `Potential`, `Age` (INTEGER)
- `Year` (TEXT)
- `PlayerStatus` (TEXT)

## Relationships

- One team has many players (`Teams` 1 -> N `Players`).
- Deleting a team sets child `Players.TeamID` to null in newly initialized schemas (`ON DELETE SET NULL`).

## CRUD coverage in repository

`cfbSimulation.data.repository.DatabaseRepository` now supports:

- Team CRUD: `create_team`, `get_team`, `list_teams`, `update_team`, `delete_team`
- Player CRUD: `create_player`, `get_player`, `get_players_for_team`, `update_player`, `delete_player`
- Schema setup: `initialize_schema`

## Validation approach

`tests/test_database_crud.py` validates:

- Team CRUD round-trip.
- Player CRUD round-trip.
- Mock high-volume dataset insertion and lookup performance.
