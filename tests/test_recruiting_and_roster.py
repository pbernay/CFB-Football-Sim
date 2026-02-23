from pathlib import Path

from cfbSimulation.logic.career import CareerManager


def test_scouting_generates_reports_and_consumes_points(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=33)
    career = manager.create_new_career("Scout Coach", "Balanced", "tID1", weeks=2)

    prior_points = career.scouting_points
    career = manager.invest_in_scouting(career, 20)

    assert career.scouting_points == prior_points - 20
    assert career.scouting_reports
    assert all("scout_note" in report for report in career.scouting_reports)


def test_recruit_offer_acceptance_adds_signed_recruit(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=7)
    career = manager.create_new_career("Recruit Coach", "Balanced", "tID1", weeks=2)
    career = manager.invest_in_scouting(career, 40)
    recruit_id = str(career.scouting_reports[0]["recruit_id"])

    career, accepted, _ = manager.offer_recruit(career, recruit_id, salary_offer=1700)

    assert accepted is True
    assert any(r["recruit_id"] == recruit_id for r in career.signed_recruits)


def test_offseason_applies_roster_changes(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=5)
    career = manager.create_new_career("Offseason Coach", "Balanced", "tID1", weeks=1)
    career = manager.invest_in_scouting(career, 35)
    recruit_id = str(career.scouting_reports[0]["recruit_id"])
    career, _, _ = manager.offer_recruit(career, recruit_id, salary_offer=1700)

    roster_before = len(career.roster)
    career = manager.reset_for_new_season(career, weeks=2)

    assert career.season == 2
    assert career.offseason_summary
    assert len(career.roster) >= 35


def test_recruit_budget_and_progress_tracking(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=9)
    career = manager.create_new_career("Budget Coach", "Balanced", "tID1", weeks=2)
    career = manager.invest_in_scouting(career, 25)
    recruit_id = str(career.scouting_reports[0]["recruit_id"])

    assert career.recruiting_budget_remaining == 1800

    career, _, _ = manager.offer_recruit(career, recruit_id, salary_offer=500)

    tracked = career.recruiting_board.get(recruit_id)
    if tracked:
        assert "last_offer_progress" in tracked
        assert 0 <= int(tracked["last_offer_progress"]) <= 100
    assert career.recruiting_budget_remaining == 1300


def test_new_season_budget_uses_last_record(tmp_path: Path):
    manager = CareerManager(save_path=tmp_path / "career.json", seed=11)
    career = manager.create_new_career("Record Coach", "Balanced", "tID1", weeks=2)
    career.wins = 10
    career.losses = 2

    career = manager.reset_for_new_season(career, weeks=2)

    assert career.last_season_wins == 10
    assert career.last_season_losses == 2
    assert career.recruiting_budget == manager.calculate_recruiting_budget(10, 2)
    assert career.recruiting_budget_remaining == career.recruiting_budget
