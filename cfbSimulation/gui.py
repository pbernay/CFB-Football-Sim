"""Tkinter GUI for single game, season mode, and coach career mode."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from cfbSimulation.data.repository import DatabaseRepository
from cfbSimulation.logic.career import CareerManager, CoachCareer, DecisionScenario
from cfbSimulation.logic.season import SeasonManager, SeasonPhase, SeasonState
from cfbSimulation.logic.simulator import GameSimulator, StrategyProfile, TeamSnapshot, format_scoreboard


class TeamSelectorPreview:
    def __init__(
        self,
        parent: ttk.Frame,
        title: str,
        teams: list,
        simulator: GameSimulator,
        on_change=None,
    ) -> None:
        self.simulator = simulator
        self.on_change = on_change
        self.team_options = {f"{team.team_id} - {team.name}": team.team_id for team in teams}

        frame = ttk.LabelFrame(parent, text=title, padding=8)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)
        self.frame = frame

        self.choice_var = tk.StringVar()
        self.combo = ttk.Combobox(
            frame,
            textvariable=self.choice_var,
            values=list(self.team_options.keys()),
            state="readonly",
            width=36,
        )
        self.combo.pack(anchor="w")
        self.combo.bind("<<ComboboxSelected>>", self._handle_change)

        self.canvas = tk.Canvas(frame, width=160, height=95, bg="#f7f7f7", highlightthickness=0)
        self.canvas.pack(anchor="w", pady=8)

        self.ratings_label = ttk.Label(frame, text="Ratings: -")
        self.ratings_label.pack(anchor="w")

        ttk.Label(frame, text="Top Players:").pack(anchor="w", pady=(6, 0))
        self.players_list = tk.Listbox(frame, height=5, width=48)
        self.players_list.pack(fill=tk.X, pady=(2, 0))

        if self.team_options:
            self.combo.current(0)
            self.refresh_preview()

    def _handle_change(self, _event=None) -> None:
        self.refresh_preview()
        if self.on_change:
            self.on_change()

    def get_selected_team_id(self) -> str | None:
        return self.team_options.get(self.choice_var.get())

    def set_team(self, team_id: str) -> None:
        for label, tid in self.team_options.items():
            if tid == team_id:
                self.choice_var.set(label)
                self.refresh_preview()
                return

    def refresh_preview(self) -> None:
        team_id = self.get_selected_team_id()
        if not team_id:
            return

        snapshot = self.simulator.build_team_snapshot(team_id)
        self._draw_helmet(snapshot)
        self.ratings_label.config(
            text=(
                f"OVR {snapshot.overall_rating} | OFF {snapshot.offensive_rating} | "
                f"DEF {snapshot.defensive_rating} | ST {snapshot.special_teams_rating}"
            )
        )

        self.players_list.delete(0, tk.END)
        for player in snapshot.players[:5]:
            self.players_list.insert(
                tk.END,
                f"{player.first_name} {player.last_name} ({player.position}) - {player.overall}",
            )

    def _draw_helmet(self, snapshot: TeamSnapshot) -> None:
        self.canvas.delete("all")
        color = self._color_for_team(snapshot.team_id)
        self.canvas.create_oval(20, 15, 125, 80, fill=color, outline="#222", width=2)
        self.canvas.create_rectangle(94, 40, 150, 60, fill="#d9d9d9", outline="#222", width=2)
        self.canvas.create_line(96, 44, 149, 44, fill="#222", width=2)
        self.canvas.create_line(96, 52, 149, 52, fill="#222", width=2)
        self.canvas.create_line(96, 60, 149, 60, fill="#222", width=2)
        initials = "".join([word[0] for word in snapshot.name.split()[:2]]).upper()
        self.canvas.create_text(68, 47, text=initials[:3], fill="white", font=("Arial", 16, "bold"))

    @staticmethod
    def _color_for_team(team_id: str) -> str:
        value = sum(ord(ch) for ch in team_id)
        return f"#{(value * 123457) % 0xFFFFFF:06x}"


class CFBGameGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CFB Football Sim")
        self.root.geometry("1200x760")

        self.repository = DatabaseRepository()
        self.simulator = GameSimulator(repository=self.repository)
        self.career_manager = CareerManager(repository=self.repository, simulator=self.simulator)
        self.season_manager = SeasonManager(repository=self.repository, simulator=self.simulator)

        self.career: CoachCareer | None = None
        self.season_state: SeasonState | None = None

        self.teams = self.repository.list_teams(limit=None)
        self.strategy_options = self.simulator.predefined_strategies()
        self.single_home_starters: dict[str, str] = {}
        self.single_away_starters: dict[str, str] = {}

        self.main = ttk.Frame(root, padding=12)
        self.main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self.main, text="CFB Football Sim", font=("Arial", 18, "bold")).pack(anchor="w")

        mode_row = ttk.Frame(self.main)
        mode_row.pack(fill=tk.X, pady=(8, 10))
        ttk.Label(mode_row, text="Game Mode:").pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="Single Game")
        mode_picker = ttk.Combobox(
            mode_row,
            textvariable=self.mode_var,
            state="readonly",
            values=["Single Game", "Season Mode", "Career Mode"],
            width=18,
        )
        mode_picker.pack(side=tk.LEFT, padx=8)
        mode_picker.bind("<<ComboboxSelected>>", lambda _e: self.render_mode())

        self.mode_container = ttk.Frame(self.main)
        self.mode_container.pack(fill=tk.BOTH, expand=True)

        self.render_mode()

    def clear_mode(self) -> None:
        for widget in self.mode_container.winfo_children():
            widget.destroy()

    def render_mode(self) -> None:
        self.clear_mode()
        mode = self.mode_var.get()
        if mode == "Single Game":
            self.build_single_game_mode()
        elif mode == "Season Mode":
            self.build_season_mode()
        else:
            self.build_career_mode()

    def build_single_game_mode(self) -> None:
        selectors = ttk.Frame(self.mode_container)
        selectors.pack(fill=tk.X)

        self.single_home = TeamSelectorPreview(selectors, "Home Team", self.teams, self.simulator)
        self.single_away = TeamSelectorPreview(selectors, "Away Team", self.teams, self.simulator)

        actions = ttk.Frame(self.mode_container)
        actions.pack(fill=tk.X, pady=10)

        ttk.Label(actions, text="Home Strategy:").pack(side=tk.LEFT)
        self.single_home_strategy = tk.StringVar(value="Balanced")
        ttk.Combobox(actions, textvariable=self.single_home_strategy, values=list(self.strategy_options), width=16, state="readonly").pack(side=tk.LEFT, padx=(4, 12))

        ttk.Label(actions, text="Away Strategy:").pack(side=tk.LEFT)
        self.single_away_strategy = tk.StringVar(value="Balanced")
        ttk.Combobox(actions, textvariable=self.single_away_strategy, values=list(self.strategy_options), width=16, state="readonly").pack(side=tk.LEFT, padx=(4, 12))

        ttk.Button(actions, text="Edit Home Starters", command=lambda: self.open_lineup_dialog(self.single_home, "home")).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Edit Away Starters", command=lambda: self.open_lineup_dialog(self.single_away, "away")).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Simulate Single Game", command=self.play_single_game).pack(side=tk.LEFT, padx=8)

        self.single_output = tk.Text(self.mode_container, height=20, wrap="word")
        self.single_output.pack(fill=tk.BOTH, expand=True)

    def play_single_game(self) -> None:
        home_id = self.single_home.get_selected_team_id()
        away_id = self.single_away.get_selected_team_id()
        if not home_id or not away_id:
            messagebox.showerror("Missing Team", "Choose both home and away teams.")
            return
        if home_id == away_id:
            messagebox.showerror("Invalid Matchup", "Home and away teams must be different.")
            return

        result = self.simulator.simulate_single_game(
            home_id,
            away_id,
            home_strategy=self.strategy_options[self.single_home_strategy.get()],
            away_strategy=self.strategy_options[self.single_away_strategy.get()],
            home_starters=self.single_home_starters,
            away_starters=self.single_away_starters,
        )
        lines = [format_scoreboard(result)]
        if result.drives_log:
            lines.extend(["", "Scoring Summary:"])
            lines.extend([f"- {line}" for line in result.drives_log])
        self.single_output.delete("1.0", tk.END)
        self.single_output.insert(tk.END, "\n".join(lines))


    def open_lineup_dialog(self, selector: TeamSelectorPreview, side: str = "home") -> None:
        team_id = selector.get_selected_team_id()
        if not team_id:
            messagebox.showinfo("No Team", "Select a team first.")
            return

        players = self.repository.get_players_for_team(team_id)
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Set Starters - {team_id}")
        dialog.grab_set()

        ttk.Label(dialog, text="Choose one starter per position for bonus impact.").pack(anchor="w", padx=10, pady=(10, 6))
        positions = ["QB", "RB", "WR", "TE", "LB", "CB", "S", "K"]

        current = self.single_home_starters if side == "home" else self.single_away_starters
        selected: dict[str, tk.StringVar] = {}
        by_pos = {pos: [p for p in players if p.position == pos] for pos in positions}

        table = ttk.Frame(dialog)
        table.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        for pos in positions:
            row = ttk.Frame(table)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=f"{pos}:", width=6).pack(side=tk.LEFT)
            opts = [f"{p.player_id} | {p.first_name} {p.last_name} ({p.overall})" for p in by_pos.get(pos, [])][:8]
            value = tk.StringVar(value=opts[0] if opts else "")
            if pos in current and opts:
                match = next((o for o in opts if o.startswith(current[pos])), opts[0])
                value.set(match)
            selected[pos] = value
            combo = ttk.Combobox(row, textvariable=value, values=opts, state="readonly", width=42)
            combo.pack(side=tk.LEFT)

        def apply_lineup() -> None:
            plan = {}
            for pos, var in selected.items():
                raw = var.get().strip()
                if raw:
                    plan[pos] = raw.split("|", 1)[0].strip()
            if side == "home":
                self.single_home_starters = plan
            else:
                self.single_away_starters = plan
            dialog.destroy()

        controls = ttk.Frame(dialog)
        controls.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(controls, text="Apply", command=apply_lineup).pack(side=tk.LEFT)
        ttk.Button(controls, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=8)

    def open_strategy_dialog(self) -> None:
        if self.career is None:
            messagebox.showinfo("No Career", "Create or load a career first.")
            return

        next_game = self.career_manager.get_next_game(self.career)
        if next_game is None:
            messagebox.showinfo("No Games", "Season is complete. Start a new season.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Game Plan - Week {next_game.week}")
        dialog.grab_set()

        ttk.Label(dialog, text=f"Opponent: {next_game.opponent_name}", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        ttk.Label(dialog, text="Strategy:").pack(anchor="w", padx=10)

        strategy_var = tk.StringVar(value=self.career.strategy_plan.get(next_game.week, "Balanced"))
        ttk.Combobox(dialog, textvariable=strategy_var, values=list(self.strategy_options), state="readonly", width=24).pack(anchor="w", padx=10, pady=(0, 8))

        ttk.Label(dialog, text="Planned starters (optional):").pack(anchor="w", padx=10)
        players = self.repository.get_players_for_team(self.career.team_id)
        positions = ["QB", "RB", "WR", "TE", "LB", "CB", "S", "K"]
        selected = {}
        existing = self.career.starter_plan.get(next_game.week, {})
        for pos in positions:
            row = ttk.Frame(dialog)
            row.pack(anchor="w", padx=10, pady=1)
            ttk.Label(row, text=f"{pos}", width=6).pack(side=tk.LEFT)
            opts = ["(No change)"] + [f"{p.player_id} | {p.first_name} {p.last_name} ({p.overall})" for p in players if p.position == pos][:8]
            default = "(No change)"
            if pos in existing:
                default = next((o for o in opts if o.startswith(existing[pos])), "(No change)")
            var = tk.StringVar(value=default)
            selected[pos] = var
            ttk.Combobox(row, textvariable=var, values=opts, state="readonly", width=42).pack(side=tk.LEFT)

        def apply_plan() -> None:
            self.career_manager.set_week_strategy(self.career, next_game.week, strategy_var.get())
            starters = {}
            for pos, var in selected.items():
                if var.get() != "(No change)":
                    starters[pos] = var.get().split("|", 1)[0].strip()
            self.career_manager.set_week_starters(self.career, next_game.week, starters)
            self.career_log.insert(tk.END, f"Game plan set for Week {next_game.week}: {strategy_var.get()}\n{'-' * 70}\n")
            self.career_log.see(tk.END)
            self.refresh_career_view()
            dialog.destroy()

        controls = ttk.Frame(dialog)
        controls.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(controls, text="Save Plan", command=apply_plan).pack(side=tk.LEFT)
        ttk.Button(controls, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=8)

    def build_season_mode(self) -> None:
        top = ttk.Frame(self.mode_container)
        top.pack(fill=tk.X)

        self.season_team = TeamSelectorPreview(top, "Your Team", self.teams, self.simulator)

        controls = ttk.Frame(self.mode_container)
        controls.pack(fill=tk.X, pady=10)
        ttk.Button(controls, text="Start Season", command=self.start_season_mode).pack(side=tk.LEFT)
        ttk.Button(controls, text="Play Next Week", command=self.play_season_week).pack(side=tk.LEFT, padx=8)

        self.season_status = ttk.Label(self.mode_container, text="Start a season to begin.", font=("Arial", 11, "bold"))
        self.season_status.pack(anchor="w", pady=(0, 8))

        content = ttk.Frame(self.mode_container)
        content.pack(fill=tk.BOTH, expand=True)

        self.season_schedule = tk.Listbox(content, width=68)
        self.season_schedule.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.season_log = tk.Text(content, wrap="word")
        self.season_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

    def start_season_mode(self) -> None:
        team_id = self.season_team.get_selected_team_id()
        if not team_id:
            messagebox.showerror("Missing Team", "Please choose a team.")
            return

        next_year = 1 if self.season_state is None else self.season_state.season + 1
        self.season_state = self.season_manager.start_season(team_id=team_id, season_number=next_year)
        self.season_log.delete("1.0", tk.END)
        self.refresh_season_view()

    def refresh_season_view(self) -> None:
        if self.season_state is None:
            return

        next_game = self.season_manager.get_next_game(self.season_state)
        if next_game:
            label = "Playoff" if self.season_state.phase != SeasonPhase.REGULAR else "Week"
            upcoming = f"{label} {next_game.week} vs {next_game.opponent_name} ({'Home' if next_game.is_home else 'Away'})"
        elif self.season_state.phase == SeasonPhase.COMPLETE:
            upcoming = "Champion!" if self.season_state.champion else "Eliminated in playoffs"
        else:
            upcoming = "Awaiting playoffs"

        self.season_status.config(
            text=(
                f"Season {self.season_state.season} | {self.season_state.team_name} "
                f"Record: {self.season_state.wins}-{self.season_state.losses} | "
                f"Playoffs: {self.season_state.playoff_wins}-{self.season_state.playoff_losses} | "
                f"Phase: {self.season_state.phase.value.title()} | Next: {upcoming}"
            )
        )

        self.season_schedule.delete(0, tk.END)
        for game in self.season_state.schedule:
            marker = game.result_summary if game.played else f"vs {game.opponent_name}"
            site = "Home" if game.is_home else "Away"
            self.season_schedule.insert(tk.END, f"Week {game.week:>2} | {site:<4} | {marker}")

        for game in self.season_state.playoff_schedule:
            marker = game.result_summary if game.played else f"vs {game.opponent_name}"
            self.season_schedule.insert(tk.END, f"Playoff {game.week:>2} | Away | {marker}")

    def play_season_week(self) -> None:
        if self.season_state is None:
            messagebox.showinfo("No Season", "Start a season first.")
            return
        if self.season_state.phase == SeasonPhase.COMPLETE:
            messagebox.showinfo("Season Complete", "Start a new season to continue.")
            return

        self.season_state, result, played_game = self.season_manager.play_next_game(self.season_state)
        out = [played_game.result_summary, "", format_scoreboard(result)]
        self.season_log.insert(tk.END, "\n".join(out) + "\n" + ("-" * 70) + "\n")
        self.season_log.see(tk.END)
        self.refresh_season_view()

    def build_career_mode(self) -> None:
        setup = ttk.Frame(self.mode_container)
        setup.pack(fill=tk.X)

        left = ttk.Frame(setup)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        ttk.Label(left, text="Coach Name:").pack(anchor="w")
        self.coach_name_var = tk.StringVar()
        ttk.Entry(left, textvariable=self.coach_name_var, width=28).pack(anchor="w", pady=(2, 8))

        ttk.Label(left, text="Coach Style:").pack(anchor="w")
        self.coach_style_var = tk.StringVar(value="Balanced")
        ttk.Combobox(
            left,
            textvariable=self.coach_style_var,
            values=["Balanced", "Run Heavy", "Pass Heavy", "Defensive Minded"],
            state="readonly",
            width=25,
        ).pack(anchor="w", pady=(2, 8))

        buttons = ttk.Frame(left)
        buttons.pack(anchor="w", pady=(6, 0))
        ttk.Button(buttons, text="Start Career", command=self.start_career_mode).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Load Career", command=self.load_career_mode).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="Play Next Week", command=self.play_career_week).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="Set Game Plan", command=self.open_strategy_dialog).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="Roster", command=self.open_roster_manager).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="Make Decision", command=self.make_career_decision).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="New Season", command=self.new_career_season).pack(side=tk.LEFT, padx=6)

        self.career_team = TeamSelectorPreview(setup, "Career Team", self.teams, self.simulator)

        self.career_status = ttk.Label(self.mode_container, text="Create or load a coach career.", font=("Arial", 11, "bold"))
        self.career_status.pack(anchor="w", pady=(10, 8))

        content = ttk.Frame(self.mode_container)
        content.pack(fill=tk.BOTH, expand=True)
        self.career_schedule = tk.Listbox(content, width=68)
        self.career_schedule.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.career_log = tk.Text(content, wrap="word")
        self.career_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        loaded = self.career_manager.load()
        if loaded:
            self.career = loaded
            self.career_team.set_team(loaded.team_id)
            self.coach_name_var.set(loaded.coach_name)
            self.coach_style_var.set(loaded.coach_style)
            self.refresh_career_view()

    def start_career_mode(self) -> None:
        team_id = self.career_team.get_selected_team_id()
        if not team_id:
            messagebox.showerror("Missing Team", "Please choose a team.")
            return

        try:
            self.career = self.career_manager.create_new_career(
                coach_name=self.coach_name_var.get(),
                coach_style=self.coach_style_var.get(),
                team_id=team_id,
            )
        except ValueError as error:
            messagebox.showerror("Invalid Career", str(error))
            return

        self.career_log.delete("1.0", tk.END)
        self.refresh_career_view()

    def load_career_mode(self) -> None:
        loaded = self.career_manager.load()
        if not loaded:
            messagebox.showinfo("No Save", "No existing career save found.")
            return
        self.career = loaded
        self.career_team.set_team(loaded.team_id)
        self.coach_name_var.set(loaded.coach_name)
        self.coach_style_var.set(loaded.coach_style)
        self.refresh_career_view()

    def refresh_career_view(self) -> None:
        if self.career is None:
            return

        next_game = self.career_manager.get_next_game(self.career)
        if next_game:
            planned = self.career.strategy_plan.get(next_game.week, "Balanced")
            upcoming = f"Week {next_game.week} vs {next_game.opponent_name} ({'Home' if next_game.is_home else 'Away'}) [{planned}]"
        else:
            upcoming = "Season complete."

        self.career_status.config(
            text=(
                f"Coach {self.career.coach_name} ({self.career.coach_style}) | "
                f"Lvl {self.career.coach_level} Prestige {self.career.prestige} Morale {self.career.morale} | "
                f"{self.career.team_name} | Season {self.career.season} | "
                f"Record {self.career.wins}-{self.career.losses} | Next: {upcoming}"
            )
        )

        self.career_schedule.delete(0, tk.END)
        for game in self.career.schedule:
            marker = game.result_summary if game.played else f"vs {game.opponent_name}"
            site = "Home" if game.is_home else "Away"
            self.career_schedule.insert(tk.END, f"Week {game.week:>2} | {site:<4} | {marker}")

    def play_career_week(self) -> None:
        if self.career is None:
            messagebox.showinfo("No Career", "Create or load a career first.")
            return
        if self.career_manager.get_next_game(self.career) is None:
            messagebox.showinfo("Season Complete", "Start a new season.")
            return

        self.career, result, played_game = self.career_manager.play_next_game(self.career)
        lines = [played_game.result_summary, "", format_scoreboard(result)]
        self.career_log.insert(tk.END, "\n".join(lines) + "\n" + ("-" * 70) + "\n")
        self.career_log.see(tk.END)
        self.refresh_career_view()

    def open_roster_manager(self) -> None:
        team_id = self.career.team_id if self.career else self.career_team.get_selected_team_id()
        if not team_id:
            messagebox.showinfo("No Team", "Select a team first.")
            return

        players = self.repository.get_players_for_team(team_id)
        if not players:
            messagebox.showinfo("No Players", "No roster found for selected team.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Team Roster")
        dialog.geometry("760x500")
        dialog.grab_set()

        current_week = self.career.current_week if self.career else 1
        starters = self.career.starter_plan.get(current_week, {}) if self.career else {}

        columns = ("player_id", "name", "position", "overall", "impact", "starter")
        tree = ttk.Treeview(dialog, columns=columns, show="headings", height=16)
        for col, width in [("player_id", 90), ("name", 180), ("position", 70), ("overall", 70), ("impact", 70), ("starter", 90)]:
            tree.heading(col, text=col.replace("_", " ").title())
            tree.column(col, width=width, anchor="w")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def player_impact(position: str, overall: int) -> int:
            weight = {"QB": 1.2, "RB": 1.05, "WR": 1.0, "TE": 0.95, "LB": 1.0, "CB": 1.0, "S": 0.95, "K": 0.9}.get(position, 0.92)
            return int(round(overall * weight))

        for p in players:
            starter = "Yes" if p.player_id in starters.values() else "No"
            tree.insert("", tk.END, values=(p.player_id, f"{p.first_name} {p.last_name}", p.position, p.overall, player_impact(p.position, p.overall), starter))

        detail = tk.StringVar(value="Select a player to view details.")
        ttk.Label(dialog, textvariable=detail, wraplength=730).pack(anchor="w", padx=10, pady=(0, 8))

        def show_details(_event=None) -> None:
            selected = tree.selection()
            if not selected:
                return
            vals = tree.item(selected[0], "values")
            detail.set(f"{vals[1]} ({vals[2]}) | Overall: {vals[3]} | Impact Rating: {vals[4]} | Starter Week {current_week}: {vals[5]}")

        tree.bind("<<TreeviewSelect>>", show_details)

    def make_career_decision(self) -> None:
        if self.career is None:
            messagebox.showinfo("No Career", "Create or load a career first.")
            return

        scenarios = self.career_manager.list_decision_scenarios()
        if not scenarios:
            messagebox.showinfo("No Scenarios", "No decision scenarios are available.")
            return

        scenario = self.career_manager.get_weekly_scenario(self.career)
        choice = self._choose_decision_option(scenario)
        if choice is None:
            return

        self.career_log.insert(tk.END, f"Decision: {scenario.title} -> {choice}\n{'-' * 70}\n")
        self.career_log.see(tk.END)
        self.refresh_career_view()

    def _choose_decision_option(self, scenario: DecisionScenario) -> str | None:
        dialog = tk.Toplevel(self.root)
        dialog.title(scenario.title)
        dialog.grab_set()

        ttk.Label(dialog, text=scenario.description, wraplength=440).pack(anchor="w", padx=12, pady=(12, 8))
        selected = tk.StringVar(value=scenario.options[0].key)
        label_map = {item.key: item.label for item in scenario.options}

        for option in scenario.options:
            ttk.Radiobutton(dialog, text=option.label, variable=selected, value=option.key).pack(anchor="w", padx=16, pady=2)

        result = {"value": None}

        def confirm() -> None:
            result["value"] = label_map[selected.get()]
            self.career_manager.apply_decision(self.career, scenario.key, selected.get())
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        controls = ttk.Frame(dialog)
        controls.pack(fill=tk.X, padx=12, pady=12)
        ttk.Button(controls, text="Apply", command=confirm).pack(side=tk.LEFT)
        ttk.Button(controls, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=8)

        dialog.wait_window()
        return result["value"]

    def new_career_season(self) -> None:
        if self.career is None:
            messagebox.showinfo("No Career", "Create or load a career first.")
            return
        self.career = self.career_manager.reset_for_new_season(self.career)
        self.career_log.insert(tk.END, f"Started Season {self.career.season}.\n{'-' * 70}\n")
        self.refresh_career_view()


def launch_gui() -> None:
    root = tk.Tk()
    CFBGameGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
