from typing import Dict, List, Tuple, Callable, Optional
from .map import Map
from .entities import PlayerState, Truck
from . import movement, combat, rules


class GameEngine:
    def __init__(self, board_map: Map, players: Dict[str, PlayerState], rng: Optional[Callable[[], float]] = None):
        self.map = board_map
        self.players = players
        self.movement_queue: List[Tuple[str, str, List[Tuple[int, int]]]] = []  # (player_id, truck_id, path)
        self.attack_queue: List[Dict] = []  # dicts with attacker_id, defender_id, attacking_soldiers
        self.rng = rng

    # ----- queueing API -----
    def queue_move(self, player_id: str, truck_id: str, path: List[Tuple[int, int]]):
        self.movement_queue.append((player_id, truck_id, path))

    def queue_attack(self, attacker_id: str, defender_id: str, attacking_soldiers: int):
        self.attack_queue.append({"attacker": attacker_id, "defender": defender_id, "attacking": attacking_soldiers})

    # ----- phases -----
    def process_movement_phase(self):
        for player_id, truck_id, path in list(self.movement_queue):
            player = self.players[player_id]
            truck = player.trucks.get(truck_id)
            if truck is None:
                continue
            movement.move_truck(self.map, truck, path)
        self.movement_queue.clear()

    def process_attack_phase(self):
        for action in list(self.attack_queue):
            attacker_id = action["attacker"]
            defender_id = action["defender"]
            attack_num = action["attacking"]
            att = self.players[attacker_id]
            defp = self.players[defender_id]

            # determine available soldiers and ammo
            participating = min(attack_num, att.soldiers, att.ammo)
            # call combat resolver
            res = combat.resolve_attack(participating, defp.soldiers, att.ammo, rng=self.rng)

            # apply results
            att.ammo -= res["ammo_used"]
            att.soldiers -= res["attacker_loss"]
            defp.soldiers -= res["damage"]
            if defp.soldiers < 0:
                defp.soldiers = 0

        self.attack_queue.clear()

    def process_food_phase(self):
        # Each player consumes food equal to soldiers. If food insufficient, apply penalty.
        for p in self.players.values():
            if p.food >= p.soldiers:
                p.food -= p.soldiers
            else:
                # consume what remains
                p.food = 0
                # apply starvation penalty: lose 10% of current soldiers, min 1 if soldiers>0
                if p.soldiers > 0:
                    loss = max(1, p.soldiers // 10)
                    p.soldiers -= loss
                    if p.soldiers < 0:
                        p.soldiers = 0

    def check_victory(self) -> Optional[str]:
        # return player_id of winner if any, else None
        alive = [pid for pid, p in self.players.items() if p.soldiers > 0]
        if len(alive) == 1:
            return alive[0]
        return None

    def run_round(self):
        self.process_movement_phase()
        self.process_attack_phase()
        self.process_food_phase()
