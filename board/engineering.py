from .map import Map
from .entities import Engineer


UPGRADE_TURNS = 1


def start_upgrade(board_map: Map, engineer: Engineer, q: int, r: int) -> None:
    h = board_map.get_hex(q, r)
    if h is None:
        raise ValueError("hex not found")
    if h.road_upgraded:
        raise ValueError("road already upgraded")
    if h.upgrade_in_progress:
        raise ValueError("upgrade already in progress")

    # place engineer
    engineer.position = f"{q},{r}"
    h.upgrade_in_progress = True
    h.upgrade_turns_left = UPGRADE_TURNS


def advance_upgrades(board_map: Map) -> None:
    # decrement turns left and complete upgrades
    for h in list(board_map._hexes.values()):
        if h.upgrade_in_progress:
            h.upgrade_turns_left -= 1
            if h.upgrade_turns_left <= 0:
                h.upgrade_in_progress = False
                h.road_upgraded = True
                h.upgrade_turns_left = 0
