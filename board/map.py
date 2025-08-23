from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Hex:
    id: str
    q: int
    r: int
    terrain: str = "plain"
    road_upgraded: bool = False
    occupants: List[str] = field(default_factory=list)
    # engineering/upgrade state
    upgrade_in_progress: bool = False
    upgrade_turns_left: int = 0


class Map:
    """Simple axial-coordinate hex map"""

    def __init__(self):
        # store hexes by (q,r) tuple
        self._hexes: Dict[Tuple[int, int], Hex] = {}

    def add_hex(self, q: int, r: int, terrain: str = "plain") -> Hex:
        h = Hex(id=f"{q},{r}", q=q, r=r, terrain=terrain)
        self._hexes[(q, r)] = h
        return h

    def get_hex(self, q: int, r: int) -> Hex:
        return self._hexes.get((q, r))

    def neighbors(self, q: int, r: int) -> List[Hex]:
        # axial hex neighbors
        directions = [(+1, 0), (+1, -1), (0, -1), (-1, 0), (-1, +1), (0, +1)]
        res = []
        for dq, dr in directions:
            h = self._hexes.get((q + dq, r + dr))
            if h:
                res.append(h)
        return res
