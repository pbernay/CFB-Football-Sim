"""PySide6 GUI for single game, season mode, and coach career mode."""

from __future__ import annotations

import sys
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QRadioButton,
    QSplitter,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cfbSimulation.data.repository import DatabaseRepository
from cfbSimulation.logic.career import CareerManager, CoachCareer, DecisionScenario
from cfbSimulation.logic.player_stats import PlayerStatsManager
from cfbSimulation.logic.season import SeasonManager, SeasonPhase, SeasonState
from cfbSimulation.logic.simulator import GameSimulator, TeamSnapshot, format_scoreboard


class HelmetPreview(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.team_id = ""
        self.team_name = ""
        self.setFixedSize(180, 105)

    def set_team(self, snapshot: TeamSnapshot) -> None:
        self.team_id = snapshot.team_id
        self.team_name = snapshot.name
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#f6f8fb"))

        value = sum(ord(ch) for ch in self.team_id)
        color = QColor(f"#{(value * 123457) % 0xFFFFFF:06x}")
        painter.setBrush(color)
        painter.setPen(QPen(QColor("#1f2937"), 2))
        painter.drawEllipse(20, 14, 112, 68)

        painter.setBrush(QColor("#d4d4d8"))
        painter.drawRect(96, 40, 66, 24)
        for y in (43, 50, 57):
            painter.drawLine(98, y, 160, y)

        initials = "".join(word[0] for word in self.team_name.split()[:2]).upper()[:3]
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(47, 56, initials)


class TeamSelectorPreview(QWidget):
    def __init__(self, title: str, teams: list, simulator: GameSimulator, on_change: Callable | None = None) -> None:
        super().__init__()
        self.simulator = simulator
        self.on_change = on_change
        self.team_options = {f"{team.team_id} - {team.name}": team.team_id for team in teams}

        layout = QVBoxLayout(self)
        box = QGroupBox(title)
        layout.addWidget(box)
        inner = QVBoxLayout(box)

        self.combo = QComboBox()
        self.combo.addItems(list(self.team_options.keys()))
        self.combo.currentIndexChanged.connect(self.refresh_preview)
        inner.addWidget(self.combo)

        self.helmet = HelmetPreview()
        inner.addWidget(self.helmet)

        self.ratings_label = QLabel("Ratings: -")
        inner.addWidget(self.ratings_label)

        inner.addWidget(QLabel("Top Players:"))
        self.players = QListWidget()
        self.players.setMaximumHeight(130)
        inner.addWidget(self.players)

        self.refresh_preview()

    def get_selected_team_id(self) -> str | None:
        return self.team_options.get(self.combo.currentText())

    def refresh_preview(self) -> None:
        team_id = self.get_selected_team_id()
        if not team_id:
            return
        snapshot = self.simulator.build_team_snapshot(team_id)
        self.helmet.set_team(snapshot)
        self.ratings_label.setText(
            f"OVR {snapshot.overall_rating} | OFF {snapshot.offensive_rating} | "
            f"DEF {snapshot.defensive_rating} | ST {snapshot.special_teams_rating}"
        )
        self.players.clear()
        for player in snapshot.players[:5]:
            self.players.addItem(f"{player.first_name} {player.last_name} ({player.position}) - {player.overall}")
        if self.on_change:
            self.on_change()


class CFBGameGUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CFB Football Sim")
        self.resize(1300, 820)

        self.repository = DatabaseRepository()
        self.simulator = GameSimulator(repository=self.repository)
        self.stats_manager = PlayerStatsManager(repository=self.repository)
        self.career_manager = CareerManager(repository=self.repository, simulator=self.simulator, stats_manager=self.stats_manager)
        self.season_manager = SeasonManager(repository=self.repository, simulator=self.simulator, stats_manager=self.stats_manager)

        self.career: CoachCareer | None = None
        self.season_state: SeasonState | None = None
        self.scouting_dialog: QDialog | None = None

        self.teams = self.repository.list_teams(limit=None)
        self.strategy_options = self.simulator.predefined_strategies()
        self.single_home_starters: dict[str, str] = {}
        self.single_away_starters: dict[str, str] = {}

        self._build_layout()

    def _build_layout(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)

        nav = QFrame()
        nav.setFrameShape(QFrame.StyledPanel)
        nav.setMaximumWidth(260)
        nav_layout = QVBoxLayout(nav)
        title = QLabel("CFB Football Sim")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        nav_layout.addWidget(title)
        nav_layout.addWidget(QLabel("Main Navigation"))

        self.stack = QStackedWidget()

        self.main_menu_btn = QPushButton("Main Menu")
        self.single_btn = QPushButton("Single Game")
        self.season_btn = QPushButton("Season Mode")
        self.career_btn = QPushButton("Career Mode")

        for idx, button in enumerate((self.main_menu_btn, self.single_btn, self.season_btn, self.career_btn)):
            nav_layout.addWidget(button)
            button.clicked.connect(lambda _=False, page_index=idx: self.stack.setCurrentIndex(page_index))

        nav_layout.addStretch()
        nav_layout.addWidget(QLabel("Tip: Start from Main Menu for quick actions."))

        self._build_main_menu_page()
        self._build_single_game_page()
        self._build_season_page()
        self._build_career_page()

        splitter = QSplitter()
        splitter.addWidget(nav)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(1, 5)
        outer.addWidget(splitter)

    def _create_menu_card(self, heading: str, body: str, button_text: str, target_index: int) -> QGroupBox:
        card = QGroupBox(heading)
        layout = QVBoxLayout(card)
        text = QLabel(body)
        text.setWordWrap(True)
        layout.addWidget(text)
        btn = QPushButton(button_text)
        btn.clicked.connect(lambda: self.stack.setCurrentIndex(target_index))
        layout.addWidget(btn)
        return card

    def _build_main_menu_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)

        hero = QLabel("Welcome to CFB Football Sim")
        hero.setFont(QFont("Arial", 24, QFont.Bold))
        sub = QLabel("Choose a mode to jump into quick matchups, full seasons, or coach career progression.")
        sub.setWordWrap(True)
        layout.addWidget(hero)
        layout.addWidget(sub)

        cards = QGridLayout()
        cards.addWidget(
            self._create_menu_card(
                "Single Game",
                "Pick home and away teams, customize strategy and starters, then run an instant simulation.",
                "Open Single Game",
                1,
            ),
            0,
            0,
        )
        cards.addWidget(
            self._create_menu_card(
                "Season Mode",
                "Guide one team through regular season and playoff rounds with week-by-week outcomes.",
                "Open Season Mode",
                2,
            ),
            0,
            1,
        )
        cards.addWidget(
            self._create_menu_card(
                "Career Mode",
                "Create or load a coach profile with strategy planning, decisions, and progression systems.",
                "Open Career Mode",
                1 + 2,
            ),
            1,
            0,
            1,
            2,
        )
        layout.addLayout(cards)
        layout.addStretch()
        self.stack.addWidget(page)

    def _build_single_game_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)

        selectors = QHBoxLayout()
        self.single_home = TeamSelectorPreview("Home Team", self.teams, self.simulator)
        self.single_away = TeamSelectorPreview("Away Team", self.teams, self.simulator)
        selectors.addWidget(self.single_home)
        selectors.addWidget(self.single_away)
        layout.addLayout(selectors)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Home Strategy:"))
        self.single_home_strategy = QComboBox()
        self.single_home_strategy.addItems(list(self.strategy_options.keys()))
        controls.addWidget(self.single_home_strategy)

        controls.addWidget(QLabel("Away Strategy:"))
        self.single_away_strategy = QComboBox()
        self.single_away_strategy.addItems(list(self.strategy_options.keys()))
        controls.addWidget(self.single_away_strategy)

        home_lineup_btn = QPushButton("Edit Home Starters")
        home_lineup_btn.clicked.connect(lambda: self.open_lineup_dialog(self.single_home, "home"))
        away_lineup_btn = QPushButton("Edit Away Starters")
        away_lineup_btn.clicked.connect(lambda: self.open_lineup_dialog(self.single_away, "away"))
        sim_btn = QPushButton("Simulate Single Game")
        sim_btn.clicked.connect(self.play_single_game)
        controls.addWidget(home_lineup_btn)
        controls.addWidget(away_lineup_btn)
        controls.addWidget(sim_btn)
        layout.addLayout(controls)

        self.single_output = QTextEdit()
        self.single_output.setReadOnly(True)
        layout.addWidget(self.single_output)

        self.stack.addWidget(page)

    def play_single_game(self) -> None:
        home_id = self.single_home.get_selected_team_id()
        away_id = self.single_away.get_selected_team_id()
        if not home_id or not away_id:
            QMessageBox.warning(self, "Missing Team", "Choose both home and away teams.")
            return
        if home_id == away_id:
            QMessageBox.warning(self, "Invalid Matchup", "Home and away teams must be different.")
            return

        result = self.simulator.simulate_single_game(
            home_id,
            away_id,
            home_strategy=self.strategy_options[self.single_home_strategy.currentText()],
            away_strategy=self.strategy_options[self.single_away_strategy.currentText()],
            home_starters=self.single_home_starters,
            away_starters=self.single_away_starters,
        )
        lines = [format_scoreboard(result)]
        if result.drives_log:
            lines.extend(["", "Scoring Summary:"])
            lines.extend([f"- {line}" for line in result.drives_log])
        self.single_output.setPlainText("\n".join(lines))

    def open_lineup_dialog(self, selector: TeamSelectorPreview, side: str) -> None:
        team_id = selector.get_selected_team_id()
        if not team_id:
            QMessageBox.information(self, "No Team", "Select a team first.")
            return

        if self.career and self.career.team_id == team_id and self.career.roster:
            players = self.career.roster
        else:
            players = self.repository.get_players_for_team(team_id)
        positions = ["QB", "RB", "WR", "TE", "LB", "CB", "S", "K"]
        current = self.single_home_starters if side == "home" else self.single_away_starters

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Set Starters - {team_id}")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Choose one starter per position for bonus impact."))

        combos: dict[str, QComboBox] = {}
        for pos in positions:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{pos}:"))
            combo = QComboBox()
            options = [f"{p.player_id} | {p.first_name} {p.last_name} ({p.overall})" for p in players if p.position == pos][:8]
            combo.addItems(options)
            if pos in current and options:
                for index, option in enumerate(options):
                    if option.startswith(current[pos]):
                        combo.setCurrentIndex(index)
                        break
            combos[pos] = combo
            row.addWidget(combo)
            layout.addLayout(row)

        buttons = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        cancel_btn = QPushButton("Cancel")
        buttons.addWidget(apply_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        def apply_lineup() -> None:
            plan = {}
            for pos, combo in combos.items():
                raw = combo.currentText().strip()
                if raw:
                    plan[pos] = raw.split("|", 1)[0].strip()
            if side == "home":
                self.single_home_starters = plan
            else:
                self.single_away_starters = plan
            dialog.accept()

        apply_btn.clicked.connect(apply_lineup)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def _build_season_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)

        top = QHBoxLayout()
        self.season_team = TeamSelectorPreview("Your Team", self.teams, self.simulator)
        top.addWidget(self.season_team)
        layout.addLayout(top)

        controls = QHBoxLayout()
        start_btn = QPushButton("Start Season")
        start_btn.clicked.connect(self.start_season_mode)
        play_btn = QPushButton("Play Next Week")
        play_btn.clicked.connect(self.play_season_week)
        controls.addWidget(start_btn)
        controls.addWidget(play_btn)
        controls.addStretch()
        layout.addLayout(controls)

        self.season_status = QLabel("Start a season to begin.")
        self.season_status.setWordWrap(True)
        layout.addWidget(self.season_status)

        splitter = QSplitter(Qt.Horizontal)
        self.season_schedule = QListWidget()
        self.season_log = QTextEdit()
        self.season_log.setReadOnly(True)
        splitter.addWidget(self.season_schedule)
        splitter.addWidget(self.season_log)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        self.stack.addWidget(page)

    def start_season_mode(self) -> None:
        team_id = self.season_team.get_selected_team_id()
        if not team_id:
            QMessageBox.warning(self, "Missing Team", "Please choose a team.")
            return
        next_year = 1 if self.season_state is None else self.season_state.season + 1
        self.season_state = self.season_manager.start_season(team_id=team_id, season_number=next_year)
        self.season_log.clear()
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

        self.season_status.setText(
            f"Season {self.season_state.season} | {self.season_state.team_name} "
            f"Record: {self.season_state.wins}-{self.season_state.losses} | "
            f"Playoffs: {self.season_state.playoff_wins}-{self.season_state.playoff_losses} | "
            f"Phase: {self.season_state.phase.value.title()} | Next: {upcoming}"
        )
        self.season_schedule.clear()
        for game in self.season_state.schedule:
            marker = game.result_summary if game.played else f"vs {game.opponent_name}"
            site = "Home" if game.is_home else "Away"
            self.season_schedule.addItem(f"Week {game.week:>2} | {site:<4} | {marker}")
        for game in self.season_state.playoff_schedule:
            marker = game.result_summary if game.played else f"vs {game.opponent_name}"
            self.season_schedule.addItem(f"Playoff {game.week:>2} | Away | {marker}")

    def play_season_week(self) -> None:
        if self.season_state is None:
            QMessageBox.information(self, "No Season", "Start a season first.")
            return
        if self.season_state.phase == SeasonPhase.COMPLETE:
            QMessageBox.information(self, "Season Complete", "Start a new season to continue.")
            return
        self.season_state, result, played_game = self.season_manager.play_next_game(self.season_state)
        self.season_log.append(f"{played_game.result_summary}\n\n{format_scoreboard(result)}\n{'-' * 70}")
        self.refresh_season_view()

    def _build_career_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)

        top = QHBoxLayout()
        left = QVBoxLayout()
        top.addLayout(left, 3)
        left.addWidget(QLabel("Coach Name:"))
        self.coach_name_input = QLineEdit()
        left.addWidget(self.coach_name_input)

        left.addWidget(QLabel("Coach Style:"))
        self.coach_style_combo = QComboBox()
        self.coach_style_combo.addItems(["Balanced", "Run Heavy", "Pass Heavy", "Defensive Minded"])
        left.addWidget(self.coach_style_combo)

        left.addWidget(QLabel("AI Difficulty:"))
        self.ai_difficulty_combo = QComboBox()
        self.ai_difficulty_combo.addItems(list(self.career_manager.ai_difficulty_profiles().keys()))
        left.addWidget(self.ai_difficulty_combo)

        actions = QHBoxLayout()
        for label, handler in [
            ("Start Career", self.start_career_mode),
            ("Load Career", self.load_career_mode),
            ("Play Next Week", self.play_career_week),
            ("Set Game Plan", self.open_strategy_dialog),
            ("Roster", self.open_roster_manager),
            ("Player Stats", self.open_player_stats_dialog),
            ("Scout Recruits", self.open_scouting_dialog),
            ("Make Offer", self.open_recruiting_dialog),
            ("Make Decision", self.make_career_decision),
            ("New Season", self.new_career_season),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            actions.addWidget(btn)
        left.addLayout(actions)

        left.addWidget(QLabel("Career Console:"))
        self.career_log = QTextEdit()
        self.career_log.setReadOnly(True)
        self.career_log.setMinimumHeight(180)
        left.addWidget(self.career_log)

        self.career_team = TeamSelectorPreview("Career Team", self.teams, self.simulator)
        top.addWidget(self.career_team, 1)
        layout.addLayout(top)

        self.career_status = QLabel("Create or load a coach career.")
        self.career_status.setWordWrap(True)
        layout.addWidget(self.career_status)

        self.career_schedule = QListWidget()
        layout.addWidget(self.career_schedule)

        self.stack.addWidget(page)

    def start_career_mode(self) -> None:
        team_id = self.career_team.get_selected_team_id()
        if not team_id:
            QMessageBox.warning(self, "Missing Team", "Please choose a team.")
            return
        try:
            self.career = self.career_manager.create_new_career(
                coach_name=self.coach_name_input.text().strip(),
                coach_style=self.coach_style_combo.currentText(),
                team_id=team_id,
                ai_difficulty=self.ai_difficulty_combo.currentText(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Career", str(exc))
            return
        self.career_log.clear()
        self.refresh_career_view()

    def load_career_mode(self) -> None:
        loaded = self.career_manager.load()
        if loaded is None:
            QMessageBox.information(self, "No Save", "No saved career found.")
            return
        self.career = loaded
        self.coach_name_input.setText(loaded.coach_name)
        self.refresh_career_view()
        self.career_log.append("Loaded saved career.\n" + "-" * 70)

    def refresh_career_view(self) -> None:
        if self.career is None:
            return
        next_game = self.career_manager.get_next_game(self.career)
        if next_game:
            planned = self.career.strategy_plan.get(next_game.week, "Balanced")
            upcoming = f"Week {next_game.week} vs {next_game.opponent_name} ({'Home' if next_game.is_home else 'Away'}) [{planned}]"
        else:
            upcoming = "Season complete."

        self.career_status.setText(
            f"Coach {self.career.coach_name} ({self.career.coach_style}) | "
            f"Lvl {self.career.coach_level} Prestige {self.career.prestige} Morale {self.career.morale} | "
            f"{self.career.team_name} | Season {self.career.season} | "
            f"AI {self.career.ai_difficulty} | Record {self.career.wins}-{self.career.losses} | "
            f"Budget ${self.career.recruiting_budget_remaining}/${self.career.recruiting_budget} | "
            f"ScoutPts {self.career.scouting_points} | Signed {len(self.career.signed_recruits)} | Next: {upcoming}"
        )
        self.career_schedule.clear()
        for game in self.career.schedule:
            marker = game.result_summary if game.played else f"vs {game.opponent_name}"
            site = "Home" if game.is_home else "Away"
            self.career_schedule.addItem(f"Week {game.week:>2} | {site:<4} | {marker}")

    def play_career_week(self) -> None:
        if self.career is None:
            QMessageBox.information(self, "No Career", "Create or load a career first.")
            return
        if self.career_manager.get_next_game(self.career) is None:
            QMessageBox.information(self, "Season Complete", "Start a new season.")
            return
        self.career, result, played_game = self.career_manager.play_next_game(self.career)
        self.career_log.append(f"{played_game.result_summary}\n\n{format_scoreboard(result)}\n{'-' * 70}")
        self.refresh_career_view()

    def open_strategy_dialog(self) -> None:
        if self.career is None:
            QMessageBox.information(self, "No Career", "Create or load a career first.")
            return
        next_game = self.career_manager.get_next_game(self.career)
        if next_game is None:
            QMessageBox.information(self, "No Games", "Season is complete. Start a new season.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Game Plan - Week {next_game.week}")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Opponent: {next_game.opponent_name}"))

        strategy_combo = QComboBox()
        strategy_combo.addItems(list(self.strategy_options.keys()))
        strategy_combo.setCurrentText(self.career.strategy_plan.get(next_game.week, "Balanced"))
        layout.addWidget(strategy_combo)

        positions = ["QB", "RB", "WR", "TE", "LB", "CB", "S", "K"]
        players = self.repository.get_players_for_team(self.career.team_id)
        existing = self.career.starter_plan.get(next_game.week, {})
        starter_choices: dict[str, QComboBox] = {}

        for pos in positions:
            row = QHBoxLayout()
            row.addWidget(QLabel(pos))
            combo = QComboBox()
            options = ["(No change)"] + [
                f"{p.player_id} | {p.first_name} {p.last_name} ({p.overall})" for p in players if p.position == pos
            ][:8]
            combo.addItems(options)
            if pos in existing:
                for idx, option in enumerate(options):
                    if option.startswith(existing[pos]):
                        combo.setCurrentIndex(idx)
                        break
            starter_choices[pos] = combo
            row.addWidget(combo)
            layout.addLayout(row)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Save Plan")
        cancel_btn = QPushButton("Cancel")
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        def save_plan() -> None:
            self.career_manager.set_week_strategy(self.career, next_game.week, strategy_combo.currentText())
            starters = {}
            for pos, combo in starter_choices.items():
                if combo.currentText() != "(No change)":
                    starters[pos] = combo.currentText().split("|", 1)[0].strip()
            self.career_manager.set_week_starters(self.career, next_game.week, starters)
            self.career_log.append(f"Game plan set for Week {next_game.week}: {strategy_combo.currentText()}\n{'-' * 70}")
            self.refresh_career_view()
            dialog.accept()

        save_btn.clicked.connect(save_plan)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def open_roster_manager(self) -> None:
        team_id = self.career.team_id if self.career else self.career_team.get_selected_team_id()
        if not team_id:
            QMessageBox.information(self, "No Team", "Select a team first.")
            return

        if self.career and self.career.team_id == team_id and self.career.roster:
            players = self.career.roster
        else:
            players = self.repository.get_players_for_team(team_id)
        if not players:
            QMessageBox.information(self, "No Players", "No roster found for selected team.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Team Roster")
        dialog.resize(860, 520)
        layout = QVBoxLayout(dialog)

        table = QTableWidget(len(players), 6)
        table.setHorizontalHeaderLabels(["Player ID", "Name", "Pos", "OVR", "Impact", "Starter"])
        current_week = self.career.current_week if self.career else 1
        starters = self.career.starter_plan.get(current_week, {}) if self.career else {}

        def player_impact(position: str, overall: int) -> int:
            weight = {"QB": 1.2, "RB": 1.05, "WR": 1.0, "TE": 0.95, "LB": 1.0, "CB": 1.0, "S": 0.95, "K": 0.9}.get(position, 0.92)
            return int(round(overall * weight))

        for row, player in enumerate(players):
            if isinstance(player, dict):
                player_id = str(player.get("player_id", player.get("recruit_id", "")))
                first_name = str(player.get("first_name", ""))
                last_name = str(player.get("last_name", ""))
                position = str(player.get("position", ""))
                overall = int(player.get("overall", 0))
            else:
                player_id = player.player_id
                first_name = player.first_name
                last_name = player.last_name
                position = player.position
                overall = player.overall
            starter = "Yes" if player_id in starters.values() else "No"
            values = [
                player_id,
                f"{first_name} {last_name}",
                position,
                str(overall),
                str(player_impact(position, overall)),
                starter,
            ]
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(value))
        layout.addWidget(table)
        dialog.exec()

    def open_player_stats_dialog(self) -> None:
        top = self.stats_manager.top_players(limit=40)
        if not top:
            QMessageBox.information(self, "No Stats", "Player stats will appear after game simulations.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Player Season Stats")
        dialog.resize(980, 580)
        layout = QVBoxLayout(dialog)

        controls = QHBoxLayout()
        compare_btn = QPushButton("Compare Players")
        controls.addWidget(compare_btn)
        controls.addStretch()
        layout.addLayout(controls)

        table = QTableWidget(len(top), 10)
        table.setHorizontalHeaderLabels(["Player", "Team", "Pos", "GP", "PassYds", "RushYds", "RecYds", "TDs", "Tackles", "INT"])
        for row, stat in enumerate(top):
            tds = stat.pass_tds + stat.rush_tds + stat.receiving_tds
            values = [
                stat.player_name,
                stat.team_id,
                stat.position,
                str(stat.games_played),
                str(stat.pass_yards),
                str(stat.rush_yards),
                str(stat.receiving_yards),
                str(tds),
                str(stat.tackles),
                str(stat.interceptions),
            ]
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(value))
        layout.addWidget(table)

        compare_output = QTextEdit()
        compare_output.setReadOnly(True)
        compare_output.setMaximumHeight(130)
        layout.addWidget(compare_output)

        def compare_players() -> None:
            text, ok = QInputDialog.getText(dialog, "Compare", "Enter Player IDs (comma-separated):")
            if not ok or not text.strip():
                return
            ids = [item.strip() for item in text.split(",") if item.strip()]
            compared = self.stats_manager.compare_players(ids)
            if not compared:
                compare_output.setPlainText("No matching players found in saved stats yet.")
                return
            lines = ["Comparison:"]
            for stat in compared:
                total_tds = stat.pass_tds + stat.rush_tds + stat.receiving_tds
                total_yards = stat.pass_yards + stat.rush_yards + stat.receiving_yards
                lines.append(f"- {stat.player_name} ({stat.team_id}/{stat.position}): {total_yards} yds, {total_tds} TD, {stat.tackles} tackles")
            compare_output.setPlainText("\n".join(lines))

        compare_btn.clicked.connect(compare_players)
        dialog.exec()

    def make_career_decision(self) -> None:
        if self.career is None:
            QMessageBox.information(self, "No Career", "Create or load a career first.")
            return
        scenario = self.career_manager.get_weekly_scenario(self.career)
        choice = self._choose_decision_option(scenario)
        if choice is None:
            return
        self.career_log.append(f"Decision: {scenario.title} -> {choice}\n{'-' * 70}")
        self.refresh_career_view()

    def _choose_decision_option(self, scenario: DecisionScenario) -> str | None:
        dialog = QDialog(self)
        dialog.setWindowTitle(scenario.title)
        layout = QVBoxLayout(dialog)
        description = QLabel(scenario.description)
        description.setWordWrap(True)
        layout.addWidget(description)

        group = QButtonGroup(dialog)
        label_map = {item.key: item.label for item in scenario.options}
        for index, option in enumerate(scenario.options):
            radio = QRadioButton(option.label)
            group.addButton(radio)
            group.setId(radio, index)
            layout.addWidget(radio)
            if index == 0:
                radio.setChecked(True)

        buttons = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        cancel_btn = QPushButton("Cancel")
        buttons.addWidget(apply_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        result: dict[str, str | None] = {"value": None}

        def confirm() -> None:
            chosen = scenario.options[group.checkedId()]
            self.career_manager.apply_decision(self.career, scenario.key, chosen.key)
            result["value"] = label_map[chosen.key]
            dialog.accept()

        apply_btn.clicked.connect(confirm)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()
        return result["value"]

    def open_scouting_dialog(self) -> None:
        if self.career is None:
            QMessageBox.information(self, "No Career", "Create or load a career first.")
            return

        dialog = QDialog(self)
        self.scouting_dialog = dialog
        dialog.setWindowTitle("Scouting")
        dialog.resize(900, 480)
        layout = QVBoxLayout(dialog)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Invest scouting points:"))
        spend = QSpinBox()
        spend.setRange(5, max(5, self.career.scouting_points))
        spend.setSingleStep(5)
        spend.setValue(min(20, max(5, self.career.scouting_points)))
        controls.addWidget(spend)
        scout_btn = QPushButton("Run Scouting")
        controls.addWidget(scout_btn)
        offer_btn = QPushButton("Send Offer To Selected")
        controls.addWidget(offer_btn)
        controls.addStretch()
        layout.addLayout(controls)

        self.scouting_table = QTableWidget(0, 6)
        self.scouting_table.setHorizontalHeaderLabels(["Recruit ID", "Name", "Pos", "OVR", "Scout Outlook", "Offer Progress"])
        layout.addWidget(self.scouting_table)

        def run_scouting() -> None:
            try:
                self.career_manager.invest_in_scouting(self.career, spend.value())
            except ValueError as exc:
                QMessageBox.warning(dialog, "Scouting", str(exc))
                return
            spend.setRange(5, max(5, self.career.scouting_points))
            self._populate_scouting_table()
            self.refresh_career_view()

        scout_btn.clicked.connect(run_scouting)
        offer_btn.clicked.connect(self._offer_selected_recruit_from_scouting)
        self._populate_scouting_table()
        dialog.exec()

    def open_recruiting_dialog(self) -> None:
        if self.career is None:
            QMessageBox.information(self, "No Career", "Create or load a career first.")
            return
        board = list(self.career.recruiting_board.values())
        if not board:
            QMessageBox.information(self, "Recruiting", "No recruits on your board yet. Scout first.")
            return

        options = [f"{r['recruit_id']} | {r['name']} ({r['position']}) OVR {r['overall']}" for r in board]
        selected, ok = QInputDialog.getItem(self, "Recruiting Offer", "Select recruit:", options, editable=False)
        if not ok:
            return
        recruit_id = selected.split("|", 1)[0].strip()
        min_offer = 250
        max_offer = max(min_offer, self.career.recruiting_budget_remaining)
        default_offer = min(650, max_offer)
        offer, ok_offer = QInputDialog.getInt(
            self,
            "Recruiting Offer",
            f"Enter salary offer (remaining budget ${self.career.recruiting_budget_remaining}):",
            default_offer,
            min_offer,
            max_offer,
            25,
        )
        if not ok_offer:
            return
        self._send_recruit_offer(recruit_id, offer)

    def _populate_scouting_table(self) -> None:
        if self.career is None or not hasattr(self, "scouting_table"):
            return
        reports = self.career.scouting_reports
        self.scouting_table.setRowCount(len(reports))
        for row, rep in enumerate(reports):
            recruit_id = str(rep["recruit_id"])
            self.scouting_table.setItem(row, 0, QTableWidgetItem(recruit_id))
            self.scouting_table.setItem(row, 1, QTableWidgetItem(str(rep["name"])))
            self.scouting_table.setItem(row, 2, QTableWidgetItem(str(rep["position"])))
            self.scouting_table.setItem(row, 3, QTableWidgetItem(str(rep["overall"])))
            self.scouting_table.setItem(row, 4, QTableWidgetItem(str(rep["scout_note"])))
            board_item = self.career.recruiting_board.get(recruit_id, {})
            progress = int(board_item.get("last_offer_progress", 0))
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(progress)
            bar.setFormat(f"{progress}%")
            self.scouting_table.setCellWidget(row, 5, bar)

    def _offer_selected_recruit_from_scouting(self) -> None:
        if self.career is None or not hasattr(self, "scouting_table"):
            return
        row = self.scouting_table.currentRow()
        if row < 0:
            QMessageBox.information(self.scouting_dialog or self, "Recruiting", "Select a recruit row first.")
            return
        recruit_id_item = self.scouting_table.item(row, 0)
        if recruit_id_item is None:
            return
        recruit_id = recruit_id_item.text().strip()
        min_offer = 250
        max_offer = max(min_offer, self.career.recruiting_budget_remaining)
        default_offer = min(650, max_offer)
        offer, ok_offer = QInputDialog.getInt(
            self.scouting_dialog or self,
            "Recruiting Offer",
            f"Enter salary offer (remaining budget ${self.career.recruiting_budget_remaining}):",
            default_offer,
            min_offer,
            max_offer,
            25,
        )
        if not ok_offer:
            return
        self._send_recruit_offer(recruit_id, offer)
        self._populate_scouting_table()

    def _send_recruit_offer(self, recruit_id: str, offer: int) -> None:
        if self.career is None:
            return
        try:
            _, accepted, reason = self.career_manager.offer_recruit(self.career, recruit_id, offer)
        except ValueError as exc:
            QMessageBox.warning(self, "Recruiting", str(exc))
            return
        self.career_log.append(f"Recruiting offer {recruit_id}: {'Accepted' if accepted else 'Rejected'} - {reason}")
        self.career_log.append("-" * 70)
        self.refresh_career_view()

    def new_career_season(self) -> None:
        if self.career is None:
            QMessageBox.information(self, "No Career", "Create or load a career first.")
            return
        self.career = self.career_manager.reset_for_new_season(self.career)
        if self.career.offseason_summary:
            self.career_log.append("Offseason Week Summary:")
            for line in self.career.offseason_summary:
                self.career_log.append(f"- {line}")
            self.career_log.append("-" * 70)
        self.career_log.append(f"Started Season {self.career.season}.\n{'-' * 70}")
        self.refresh_career_view()


def launch_gui() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = CFBGameGUI()
    window.show()
    app.exec()


if __name__ == "__main__":
    launch_gui()
