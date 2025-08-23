#!/usr/bin/env python
"""Simple CLI prototype for the boardgame demo.

Usage:
  - Demo: python cli.py --demo
  - Interactive: python cli.py
Commands (interactive): status, move <player> <truck> q,r [q,r ...], attack <attacker> <defender> <num>, run, quit
"""
import argparse
from board.map import Map
from board.entities import PlayerState, Truck, Warehouse, Engineer
from board import rules
from board.game_engine import GameEngine


def create_demo_game() -> (Map, dict):
    m = Map()
    # create a simple line map from -3..3
    for q in range(-3, 4):
        m.add_hex(q, 0)

    # players
    p1 = PlayerState(id="p1", soldiers=rules.INITIAL_SOLDIERS, ammo=rules.INITIAL_AMMO, food=rules.INITIAL_FOOD, engineers=rules.INITIAL_ENGINEERS)
    p2 = PlayerState(id="p2", soldiers=rules.INITIAL_SOLDIERS, ammo=rules.INITIAL_AMMO, food=rules.INITIAL_FOOD, engineers=rules.INITIAL_ENGINEERS)

    # warehouses at ends
    w1 = Warehouse(id="w1", owner_id="p1", stock={"soldiers": rules.INITIAL_SOLDIERS, "ammo": rules.INITIAL_AMMO, "food": rules.INITIAL_FOOD})
    w2 = Warehouse(id="w2", owner_id="p2", stock={"soldiers": rules.INITIAL_SOLDIERS, "ammo": rules.INITIAL_AMMO, "food": rules.INITIAL_FOOD})
    p1.warehouses[w1.id] = w1
    p2.warehouses[w2.id] = w2

    # trucks: place p1 at -3, p2 at 3
    for i in range(rules.TRUCK_COUNT):
        t1 = Truck(id=f"p1_t{i}", owner_id="p1", position=f"{-3},{0}", capacity=rules.TRUCK_CAPACITY, remaining_mp=rules.MP_PER_TURN)
        t2 = Truck(id=f"p2_t{i}", owner_id="p2", position=f"3,{0}", capacity=rules.TRUCK_CAPACITY, remaining_mp=rules.MP_PER_TURN)
        p1.trucks[t1.id] = t1
        p2.trucks[t2.id] = t2

    return m, {"p1": p1, "p2": p2}


def print_status(players):
    for pid, p in players.items():
        print(f"Player {pid}: soldiers={p.soldiers}, ammo={p.ammo}, food={p.food}")
        for tid, t in p.trucks.items():
            print(f"  Truck {tid}: pos={t.position} MP={t.remaining_mp} cargo={t.cargo}")


def parse_coord(s: str):
    q, r = s.split(",")
    return int(q), int(r)


def interactive_loop(engine: GameEngine, players):
    print("Enter commands (status, move, attack, run, quit). Type 'help' for details.")
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break
        if not line:
            continue
        parts = line.split()
        cmd = parts[0]
        if cmd == "quit":
            break
        if cmd == "help":
            print("Commands:\n status\n move <player> <truck> q,r [q,r ...]\n attack <attacker> <defender> <num>\n run\n quit")
            continue
        if cmd == "status":
            print_status(players)
            continue
        if cmd == "move":
            if len(parts) < 4:
                print("usage: move <player> <truck> q,r [q,r ...]")
                continue
            player_id = parts[1]
            truck_id = parts[2]
            coords = [parse_coord(c) for c in parts[3:]]
            engine.queue_move(player_id, truck_id, coords)
            print(f"queued move {truck_id} for {player_id}")
            continue
        if cmd == "attack":
            if len(parts) != 4:
                print("usage: attack <attacker> <defender> <num>")
                continue
            engine.queue_attack(parts[1], parts[2], int(parts[3]))
            print("queued attack")
            continue
        if cmd == "run":
            engine.run_round()
            print("round executed")
            print_status(players)
            w = engine.check_victory()
            if w:
                print(f"Victory: {w}")
                break
            continue
        print("unknown command")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="run demo sequence")
    args = ap.parse_args()

    m, players = create_demo_game()
    engine = GameEngine(m, players, rng=lambda: 0.1)

    if args.demo:
        print("Demo start")
        print_status(players)
        # demo: move first truck and attack
        first_truck = next(iter(players["p1"].trucks.values())).id
        engine.queue_move("p1", first_truck, [( -2, 0 ), ( -1, 0 ), (0,0)])
        engine.queue_attack("p1", "p2", 3)
        engine.run_round()
        print("After demo round:")
        print_status(players)
        v = engine.check_victory()
        if v:
            print(f"Victory: {v}")
        return

    # interactive
    interactive_loop(engine, players)


if __name__ == "__main__":
    main()
