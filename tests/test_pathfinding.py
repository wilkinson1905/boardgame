from board.map import Map
from board.pathfinding import find_path


def test_find_path_basic():
    m = Map()
    for q in range(0, 4):
        for r in range(0, 3):
            m.add_hex(q, r)

    res = find_path(m, (0, 0), (3, 0))
    assert res is not None
    assert res["path"][0] == (0, 0)
    assert res["path"][-1] == (3, 0)
