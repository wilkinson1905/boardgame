from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Truck:
    id: str
    owner_id: str
    position: str  # hex id like 'q,r'
    capacity: int = 10
    cargo: Dict[str, int] = field(default_factory=lambda: {"soldiers": 0, "ammo": 0, "food": 0, "engineers": 0})
    remaining_mp: int = 0


@dataclass
class Warehouse:
    id: str
    owner_id: str
    stock: Dict[str, int] = field(default_factory=lambda: {"soldiers": 0, "ammo": 0, "food": 0})


@dataclass
class PlayerState:
    id: str
    warehouses: Dict[str, Warehouse] = field(default_factory=dict)
    trucks: Dict[str, Truck] = field(default_factory=dict)
    soldiers: int = 0
    ammo: int = 0
    food: int = 0
    engineers: int = 0


@dataclass
class Engineer:
    id: str
    owner_id: str
    position: str
