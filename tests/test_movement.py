from board.map import Map
from board.entities import Truck
from board.movement import path_cost, move_truck
from board import rules


def test_path_cost_unupgraded():
    m = Map()
    m.add_hex(0, 0)
    m.add_hex(1, 0)
    # default road_upgraded False -> cost should be UNUPGRADED_ROAD_COST per tile
    cost = path_cost(m, [(0, 0), (1, 0)])
    assert cost == rules.UNUPGRADED_ROAD_COST * 2


def test_move_truck_success_and_mp_deduction():
    m = Map()
    m.add_hex(0, 0)
    m.add_hex(1, 0)
    t = Truck(id="t1", owner_id="p1", position="0,0", capacity=rules.TRUCK_CAPACITY)
    t.remaining_mp = 6
    ok = move_truck(m, t, [(1, 0)])
    assert ok is True
    assert t.position == "1,0"
    assert t.remaining_mp == 6 - rules.UNUPGRADED_ROAD_COST


def test_move_truck_insufficient_mp():
    m = Map()
    m.add_hex(0, 0)
    m.add_hex(1, 0)
    m.add_hex(2, 0)
    t = Truck(id="t2", owner_id="p1", position="0,0", capacity=rules.TRUCK_CAPACITY)
    t.remaining_mp = 2
    # path of two tiles costs 4 -> should fail
    ok = move_truck(m, t, [(1, 0), (2, 0)])
    assert ok is False
