from typing import Dict, List, Optional, Tuple
import heapq
from .map import Map
from . import rules


Coord = Tuple[int, int]


def hex_distance(a: Coord, b: Coord) -> int:
    aq, ar = a
    bq, br = b
    dx = aq - bq
    dy = ar - br
    return (abs(dx) + abs(dy) + abs(dx + dy)) // 2


def neighbors(coord: Coord) -> List[Coord]:
    q, r = coord
    directions = [(+1, 0), (+1, -1), (0, -1), (-1, 0), (-1, +1), (0, +1)]
    return [(q + dq, r + dr) for dq, dr in directions]


def cost_for_tile(board_map: Map, coord: Coord) -> int:
    h = board_map.get_hex(coord[0], coord[1])
    if h is None:
        return 9999
    return rules.UPGRADED_ROAD_COST if h.road_upgraded else rules.UNUPGRADED_ROAD_COST


def find_path(board_map: Map, start: Coord, goal: Coord) -> Optional[Dict]:
    """A* search on axial hex grid. Returns dict with 'path' (list of coords from start->goal) and 'cost'.
    Returns None if no path found."""
    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from: Dict[Coord, Optional[Coord]] = {start: None}
    cost_so_far: Dict[Coord, int] = {start: 0}

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            break

        for n in neighbors(current):
            new_cost = cost_so_far[current] + cost_for_tile(board_map, n)
            if n not in cost_so_far or new_cost < cost_so_far[n]:
                cost_so_far[n] = new_cost
                priority = new_cost + hex_distance(n, goal)
                heapq.heappush(frontier, (priority, n))
                came_from[n] = current

    if goal not in came_from:
        return None

    # reconstruct path
    path: List[Coord] = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = came_from.get(cur)
    path.reverse()
    return {"path": path, "cost": cost_so_far[goal]}
