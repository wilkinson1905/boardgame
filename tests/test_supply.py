import pytest
from board.entities import Truck, Warehouse
from board.supply import load_from_warehouse, unload_to_warehouse


def test_load_and_unload():
    w = Warehouse(id="w1", owner_id="p1")
    w.stock["food"] = 10
    t = Truck(id="t1", owner_id="p1", position="0,0", capacity=5)
    # load 3 food
    load_from_warehouse(w, t, "food", 3)
    assert t.cargo["food"] == 3
    assert w.stock["food"] == 7

    # unload 2
    unload_to_warehouse(t, w, "food", 2)
    assert t.cargo["food"] == 1
    assert w.stock["food"] == 9


def test_load_exceeds_capacity():
    w = Warehouse(id="w1", owner_id="p1")
    w.stock["ammo"] = 10
    t = Truck(id="t2", owner_id="p1", position="0,0", capacity=2)
    with pytest.raises(ValueError):
        load_from_warehouse(w, t, "ammo", 3)
