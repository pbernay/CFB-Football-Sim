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
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cfbSimulation.data.repository import DatabaseRepository
from cfbSimulation.logic.career import CareerManager, CoachCareer, DecisionScenario
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
        self.career_manager = CareerManager(repository=self.repository, simulator=self.simulator)
        self.season_manager = SeasonManager(repository=self.repository, simulator=self.simulator)

        self.career: CoachCareer | None = None
        self.season_state: SeasonState | None = None

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
        top.addLayout(left)
        left.addWidget(QLabel("Coach Name:"))
        self.coach_name_input = QLineEdit()
        left.addWidget(self.coach_name_input)

        left.addWidget(QLabel("Coach Style:"))
        self.coach_style_combo = QComboBox()
        self.coach_style_combo.addItems(["Balanced", "Run Heavy", "Pass Heavy", "Defensive Minded"])
        left.addWidget(self.coach_style_combo)

        actions = QHBoxLayout()
        for label, handler in [
            ("Start Career", self.start_career_mode),
            ("Load Career", self.load_career_mode),
            ("Play Next Week", self.play_career_week),
            ("Set Game Plan", self.open_strategy_dialog),
            ("Roster", self.open_roster_manager),
            ("Make Decision", self.make_career_decision),
            ("New Season", self.new_career_season),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            actions.addWidget(btn)
        left.addLayout(actions)

        self.career_team = TeamSelectorPreview("Career Team", self.teams, self.simulator)
        top.addWidget(self.career_team)
        layout.addLayout(top)

        self.career_status = QLabel("Create or load a coach career.")
        self.career_status.setWordWrap(True)
        layout.addWidget(self.career_status)

        splitter = QSplitter(Qt.Horizontal)
        self.career_schedule = QListWidget()
        self.career_log = QTextEdit()
        self.career_log.setReadOnly(True)
        splitter.addWidget(self.career_schedule)
        splitter.addWidget(self.career_log)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

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
            f"Record {self.career.wins}-{self.career.losses} | Next: {upcoming}"
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
            starter = "Yes" if player.player_id in starters.values() else "No"
            values = [
                player.player_id,
                f"{player.first_name} {player.last_name}",
                player.position,
                str(player.overall),
                str(player_impact(player.position, player.overall)),
                starter,
            ]
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(value))
        layout.addWidget(table)
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

    def new_career_season(self) -> None:
        if self.career is None:
            QMessageBox.information(self, "No Career", "Create or load a career first.")
            return
        self.career = self.career_manager.reset_for_new_season(self.career)
        self.career_log.append(f"Started Season {self.career.season}.\n{'-' * 70}")
        self.refresh_career_view()


def launch_gui() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = CFBGameGUI()
    window.show()
    app.exec()


if __name__ == "__main__":
    launch_gui()
