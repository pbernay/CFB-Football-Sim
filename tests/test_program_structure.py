from cfbSimulation.logic.program_structure import (
    Division,
    ProgramStructureEngine,
    ProgramTier,
)
from cfbSimulation.logic.season import SeasonManager


def test_program_contexts_assign_divisions_and_tiers():
    manager = SeasonManager(seed=13)
    engine = ProgramStructureEngine(
        manager.repository, manager.simulator, seed=13, top_x_fbs=4
    )

    contexts = engine.build_contexts()

    fbs_count = sum(1 for ctx in contexts.values() if ctx.division == Division.FBS)
    assert fbs_count == 4
    assert all(ctx.profile.tier in ProgramTier for ctx in contexts.values())


def test_poll_updates_after_recorded_game():
    manager = SeasonManager(seed=9)
    state = manager.start_season("tID1", weeks=2)
    preseason_ap = [item.points for item in state.ap_poll]
    preseason_fcs = [item.points for item in state.fcs_poll]

    state, result, _ = manager.play_next_game(state)

    assert len(state.ap_poll) > 0
    assert len(state.fcs_poll) > 0
    ap_changed = [item.points for item in state.ap_poll] != preseason_ap
    fcs_changed = [item.points for item in state.fcs_poll] != preseason_fcs
    assert ap_changed or fcs_changed
    assert result.home_team.score >= 0
