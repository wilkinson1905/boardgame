from typing import List, Tuple
from .map import Map
from .entities import Truck
from . import rules


def coord_to_tuple(coord: str) -> Tuple[int, int]:
    q, r = coord.split(",")
    return int(q), int(r)


def path_cost(board_map: Map, path: List[Tuple[int, int]]) -> int:
    """Calculate total movement cost for a path given the map.

    path is a list of (q, r) tuples representing successive hexes to enter.
    The cost to enter each hex is determined by road_upgraded flag (1) or unupgraded (2),
    or a default terrain cost of 3 for non-road terrain.
    """
    cost = 0
    for q, r in path:
        h = board_map.get_hex(q, r)
        if h is None:
            # treat unknown hex as high cost (impassable)
            cost += 9999
            continue
        # interpret terrain/road
        if h.road_upgraded:
            cost += rules.UPGRADED_ROAD_COST
        else:
            # assume plain/road distinction not explicitly modeled; use unupgraded cost
            cost += rules.UNUPGRADED_ROAD_COST
    return cost


def move_truck(board_map: Map, truck: Truck, path: List[Tuple[int, int]]) -> bool:
    """Attempt to move truck along path. Returns True on success, False if insufficient MP or invalid path."""
    # initialize MP if zero
    if truck.remaining_mp <= 0:
        truck.remaining_mp = rules.MP_PER_TURN

    total = path_cost(board_map, path)
    if total > truck.remaining_mp:
        return False

    # perform move: set position to last hex and deduct MP
    if path:
        last_q, last_r = path[-1]
        h = board_map.get_hex(last_q, last_r)
        if h and 'warehouse' in getattr(h, 'occupants', []):
            # trucks may not enter warehouse hexes
            return False
        truck.position = f"{last_q},{last_r}"
    truck.remaining_mp -= total
    return True
