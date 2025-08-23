from board.map import Map
from board.entities import Truck, PlayerState, Warehouse
from board import rules


def test_map_neighbors():
    m = Map()
    # make a small cluster
    m.add_hex(0, 0)
    m.add_hex(1, 0)
    m.add_hex(0, 1)
    n = m.neighbors(0, 0)
    # neighbors should include (1,0) and (0,1)
    ids = {h.id for h in n}
    assert "1,0" in ids
    assert "0,1" in ids


def test_truck_and_player_defaults():
    t = Truck(id="t1", owner_id="p1", position="0,0", capacity=rules.TRUCK_CAPACITY)
    assert t.cargo["soldiers"] == 0
    p = PlayerState(id="p1")
    p.trucks[t.id] = t
    assert p.trucks["t1"].capacity == rules.TRUCK_CAPACITY


def test_warehouse_stock():
    w = Warehouse(id="w1", owner_id="p1")
    w.stock["soldiers"] = 5
    assert w.stock["soldiers"] == 5
