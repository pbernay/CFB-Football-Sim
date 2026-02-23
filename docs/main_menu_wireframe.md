# Main Menu Wireframe (PySide6 Overhaul)

## Goals
- Fast, clear navigation to all major game modes.
- A central landing page with mode descriptions and one-click access.
- Consistent visual hierarchy with sidebar navigation + content workspace.

## Wireframe Sketch

```text
+--------------------------------------------------------------------------------------+
| CFB Football Sim                                                                      |
+----------------------------+---------------------------------------------------------+
| [Main Menu]                | Welcome to CFB Football Sim                            |
| [Single Game]              | Choose a mode to jump into simulation gameplay.       |
| [Season Mode]              |                                                         |
| [Career Mode]              | +--------------------+ +-----------------------------+ |
|                            | | Single Game        | | Season Mode                 | |
| Tip: Start from Main Menu  | | - quick matchup    | | - full season progression   | |
| for quick actions.         | | [Open Single Game] | | [Open Season Mode]          | |
|                            | +--------------------+ +-----------------------------+ |
|                            | +-----------------------------------------------------+ |
|                            | | Career Mode                                         | |
|                            | | - coach progression, planning, decisions           | |
|                            | | [Open Career Mode]                                 | |
|                            | +-----------------------------------------------------+ |
+----------------------------+---------------------------------------------------------+
```

## Navigation behavior
- Sidebar is persistent across all pages.
- Main Menu cards route users to Single Game, Season Mode, and Career Mode.
- Users can return to Main Menu at any time from the sidebar.

## Validation checklist
- [x] Main menu links open the correct mode pages.
- [x] Major features remain reachable from top-level navigation.
- [x] Team selection preview remains visible for each mode where relevant.
