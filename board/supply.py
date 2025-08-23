from typing import Dict
from .entities import Truck, Warehouse


def cargo_total(cargo: Dict[str, int]) -> int:
    return sum(cargo.get(k, 0) for k in cargo)


def load_from_warehouse(warehouse: Warehouse, truck: Truck, resource: str, amount: int) -> None:
    """Load `amount` of resource from warehouse onto truck.

    Raises ValueError on insufficient stock or capacity overflow.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")
    if warehouse.stock.get(resource, 0) < amount:
        raise ValueError("warehouse does not have enough resource")

    current_total = cargo_total(truck.cargo)
    if current_total + amount > truck.capacity:
        raise ValueError("loading would exceed truck capacity")

    warehouse.stock[resource] = warehouse.stock.get(resource, 0) - amount
    truck.cargo[resource] = truck.cargo.get(resource, 0) + amount


def unload_to_warehouse(truck: Truck, warehouse: Warehouse, resource: str, amount: int) -> None:
    """Unload `amount` of resource from truck into warehouse.

    Raises ValueError on insufficient cargo.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")
    if truck.cargo.get(resource, 0) < amount:
        raise ValueError("truck does not have enough resource to unload")

    truck.cargo[resource] = truck.cargo.get(resource, 0) - amount
    warehouse.stock[resource] = warehouse.stock.get(resource, 0) + amount
