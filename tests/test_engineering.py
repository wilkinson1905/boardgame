from board.map import Map
from board.entities import Engineer
from board.engineering import start_upgrade, advance_upgrades


def test_start_and_complete_upgrade():
    m = Map()
    m.add_hex(0, 0)
    eng = Engineer(id="e1", owner_id="p1", position="0,0")
    start_upgrade(m, eng, 0, 0)
    h = m.get_hex(0, 0)
    assert h.upgrade_in_progress is True
    assert h.upgrade_turns_left == 1
    # advance one turn
    advance_upgrades(m)
    assert h.upgrade_in_progress is False
    assert h.road_upgraded is True
