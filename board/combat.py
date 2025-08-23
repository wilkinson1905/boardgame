import math
import random
from typing import Callable, Dict


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def success_probability(attacking: int, defending: int) -> float:
    """Compute success probability P based on attacking and defending soldiers.

    Uses the formula from the spec:
      P = clamp(0.5 + 0.15 * (A/D - 1), 0.05, 0.95)
    If D == 0, returns 1.0 (auto-success).
    """
    if defending <= 0:
        return 1.0
    ratio = attacking / defending
    p = 0.5 + 0.15 * (ratio - 1)
    return clamp(p, 0.05, 0.95)


def resolve_attack(attacking_soldiers: int, defending_soldiers: int, ammo_available: int, *,
                   damage_ratio: float = 0.4, rng: Callable[[], float] = None) -> Dict:
    """Resolve an attack.

    Rules implemented:
    - Number of participating attackers is limited by available ammo (1 ammo per attacker).
    - Ammo used equals participating attackers.
    - Success probability computed by `success_probability` using participating attackers and defenders.
    - On success: damage = max(1, floor(participating * damage_ratio)). Damage is applied to defenders.
    - On failure: attacker suffers a small loss = floor(participating * 0.1).

    Returns a dict with keys:
      participating, ammo_used, success (bool), damage (int), attacker_loss (int), prob (float)
    """
    if rng is None:
        rng = random.random

    participating = min(attacking_soldiers, ammo_available)
    if participating <= 0:
        return {"participating": 0, "ammo_used": 0, "success": False, "damage": 0, "attacker_loss": 0, "prob": 0.0}

    ammo_used = participating
    prob = success_probability(participating, defending_soldiers)
    roll = rng()
    success = roll < prob

    if success:
        damage = max(1, math.floor(participating * damage_ratio))
        attacker_loss = 0
    else:
        damage = 0
        attacker_loss = math.floor(participating * 0.1)

    return {
        "participating": participating,
        "ammo_used": ammo_used,
        "success": success,
        "damage": damage,
        "attacker_loss": attacker_loss,
        "prob": prob,
        "roll": roll,
    }
