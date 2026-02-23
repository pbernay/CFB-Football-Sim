"""Tkinter GUI for coaching career mode."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from cfbSimulation.data.repository import DatabaseRepository
from cfbSimulation.logic.career import CareerManager, CoachCareer
from cfbSimulation.logic.simulator import format_scoreboard


class CFBGameGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CFB Football Sim - Coach Career")
        self.root.geometry("980x680")

        self.repository = DatabaseRepository()
        self.career_manager = CareerManager(repository=self.repository)
        self.career: CoachCareer | None = None

        self.main_frame = ttk.Frame(self.root, padding=12)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self._build_styles()
        self._build_start_screen()
        self.try_load_existing_career()

    def _build_styles(self) -> None:
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Arial", 16, "bold"))
        style.configure("Subheader.TLabel", font=("Arial", 12, "bold"))

    def _clear_main(self) -> None:
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def _build_start_screen(self) -> None:
        self._clear_main()
        ttk.Label(self.main_frame, text="Create Coach Career", style="Header.TLabel").pack(anchor="w", pady=(0, 12))

        form = ttk.Frame(self.main_frame)
        form.pack(anchor="w", fill=tk.X)

        ttk.Label(form, text="Coach Name:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        self.coach_name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.coach_name_var, width=34).grid(row=0, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Coach Style:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=6)
        self.coach_style_var = tk.StringVar(value="Balanced")
        style_box = ttk.Combobox(
            form,
            textvariable=self.coach_style_var,
            width=31,
            state="readonly",
            values=["Balanced", "Run Heavy", "Pass Heavy", "Defensive Minded"],
        )
        style_box.grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Select Team:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=6)
        teams = self.repository.list_teams(limit=None)
        self.team_options = {f"{team.team_id} - {team.name}": team.team_id for team in teams}
        self.team_choice_var = tk.StringVar()
        team_box = ttk.Combobox(
            form,
            textvariable=self.team_choice_var,
            width=31,
            state="readonly",
            values=list(self.team_options.keys()),
        )
        team_box.grid(row=2, column=1, sticky="w", pady=6)
        if self.team_options:
            team_box.current(0)

        button_row = ttk.Frame(self.main_frame)
        button_row.pack(anchor="w", pady=14)
        ttk.Button(button_row, text="Start New Career", command=self.start_new_career).pack(side=tk.LEFT)
        ttk.Button(button_row, text="Load Existing Career", command=self.load_career).pack(side=tk.LEFT, padx=8)

        info = (
            "Core loop: create a coach, play each scheduled game, and progress through the season.\n"
            "After the schedule ends, start a new season and keep building your legacy."
        )
        ttk.Label(self.main_frame, text=info).pack(anchor="w", pady=(14, 0))

    def try_load_existing_career(self) -> None:
        loaded = self.career_manager.load()
        if loaded:
            self.career = loaded
            self._build_career_screen()

    def start_new_career(self) -> None:
        coach_name = self.coach_name_var.get()
        coach_style = self.coach_style_var.get()
        team_label = self.team_choice_var.get()
        team_id = self.team_options.get(team_label)

        if not team_id:
            messagebox.showerror("Missing Team", "Please choose a team.")
            return

        try:
            self.career = self.career_manager.create_new_career(coach_name, coach_style, team_id)
        except ValueError as error:
            messagebox.showerror("Invalid Career Setup", str(error))
            return

        self._build_career_screen()

    def load_career(self) -> None:
        loaded = self.career_manager.load()
        if not loaded:
            messagebox.showinfo("No Save Found", "No career save found. Create a new one first.")
            return
        self.career = loaded
        self._build_career_screen()

    def _build_career_screen(self) -> None:
        if self.career is None:
            return

        self._clear_main()

        header_text = (
            f"Coach {self.career.coach_name} ({self.career.coach_style}) - "
            f"{self.career.team_name} | Season {self.career.season}"
        )
        ttk.Label(self.main_frame, text=header_text, style="Header.TLabel").pack(anchor="w", pady=(0, 10))

        self.status_label = ttk.Label(self.main_frame, style="Subheader.TLabel")
        self.status_label.pack(anchor="w", pady=(0, 8))

        controls = ttk.Frame(self.main_frame)
        controls.pack(anchor="w", fill=tk.X, pady=(0, 10))
        ttk.Button(controls, text="Play Next Game", command=self.play_next_game).pack(side=tk.LEFT)
        ttk.Button(controls, text="Start New Season", command=self.start_new_season).pack(side=tk.LEFT, padx=8)
        ttk.Button(controls, text="Back to Setup", command=self._build_start_screen).pack(side=tk.LEFT)

        schedule_frame = ttk.LabelFrame(self.main_frame, text="Schedule")
        schedule_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        self.schedule_list = tk.Listbox(schedule_frame, height=12)
        self.schedule_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        log_frame = ttk.LabelFrame(self.main_frame, text="Game Output")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(log_frame, height=14, wrap="word")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.refresh_career_view()

    def refresh_career_view(self) -> None:
        if self.career is None:
            return

        next_game = self.career_manager.get_next_game(self.career)
        if next_game:
            next_line = (
                f"Next: Week {next_game.week} vs {next_game.opponent_name} "
                f"({'Home' if next_game.is_home else 'Away'})"
            )
        else:
            next_line = "Season complete. Start a new season to continue."

        self.status_label.config(text=f"Record: {self.career.wins}-{self.career.losses} | {next_line}")

        self.schedule_list.delete(0, tk.END)
        for game in self.career.schedule:
            location = "Home" if game.is_home else "Away"
            if game.played:
                text = f"Week {game.week:>2} | {location:<4} | {game.result_summary}"
            else:
                text = f"Week {game.week:>2} | {location:<4} | vs {game.opponent_name}"
            self.schedule_list.insert(tk.END, text)

    def play_next_game(self) -> None:
        if self.career is None:
            return
        if self.career_manager.get_next_game(self.career) is None:
            messagebox.showinfo("Season Finished", "No games left this season. Start a new season.")
            return

        self.career, result, played_game = self.career_manager.play_next_game(self.career)

        output = [played_game.result_summary, "", format_scoreboard(result)]
        if result.drives_log:
            output.extend(["", "Scoring Drives:"])
            output.extend(result.drives_log)

        self.log_text.insert(tk.END, "\n".join(output) + "\n" + ("-" * 70) + "\n")
        self.log_text.see(tk.END)
        self.refresh_career_view()

    def start_new_season(self) -> None:
        if self.career is None:
            return
        self.career = self.career_manager.reset_for_new_season(self.career)
        self.log_text.insert(tk.END, f"Started Season {self.career.season}.\n{'-' * 70}\n")
        self.refresh_career_view()


def launch_gui() -> None:
    root = tk.Tk()
    app = CFBGameGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
