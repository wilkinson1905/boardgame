"""Minimal pygame frontend for the boardgame prototype.

Run: python gui.py

Controls:
 - Space: run one round
 - Esc or window close: quit
"""
import sys
import pygame
from board.map import Map
from board.game_engine import GameEngine
from board.entities import PlayerState, Truck, Warehouse
from board import rules


SCREEN_W = 800
SCREEN_H = 400
BG = (30, 30, 30)
COLORS = {"p1": (200, 80, 80), "p2": (80, 80, 200)}


def create_demo():
    m = Map()
    for q in range(-6, 7):
        m.add_hex(q, 0)

    p1 = PlayerState(id="p1", soldiers=rules.INITIAL_SOLDIERS, ammo=rules.INITIAL_AMMO, food=rules.INITIAL_FOOD)
    p2 = PlayerState(id="p2", soldiers=rules.INITIAL_SOLDIERS, ammo=rules.INITIAL_AMMO, food=rules.INITIAL_FOOD)
    for i in range(rules.TRUCK_COUNT):
        t1 = Truck(id=f"p1_t{i}", owner_id="p1", position=f"{-6},{0}", capacity=rules.TRUCK_CAPACITY, remaining_mp=rules.MP_PER_TURN)
        t2 = Truck(id=f"p2_t{i}", owner_id="p2", position=f"6,{0}", capacity=rules.TRUCK_CAPACITY, remaining_mp=rules.MP_PER_TURN)
        p1.trucks[t1.id] = t1
        p2.trucks[t2.id] = t2

    return m, {"p1": p1, "p2": p2}


def world_to_screen(q: int, r: int) -> (int, int):
    # place along horizontal line
    x = int((q + 6) * (SCREEN_W / 14))
    y = SCREEN_H // 2 + r * 30
    return x, y


def draw(screen, board_map: Map, players):
    screen.fill(BG)
    # draw hex placeholders
    for (q, r), h in board_map._hexes.items():
        x, y = world_to_screen(q, r)
        pygame.draw.circle(screen, (60, 60, 60), (x, y), 20)
        if h.road_upgraded:
            pygame.draw.circle(screen, (120, 120, 120), (x, y), 10)

    # draw trucks
    for pid, p in players.items():
        for tid, t in p.trucks.items():
            q, r = map(int, t.position.split(","))
            x, y = world_to_screen(q, r)
            pygame.draw.rect(screen, COLORS.get(pid, (200, 200, 200)), (x - 8, y - 8, 16, 16))

    # draw status
    font = pygame.font.SysFont(None, 20)
    x = 10
    y = 10
    for pid, p in players.items():
        txt = f"{pid}: soldiers={p.soldiers} ammo={p.ammo} food={p.food}"
        surf = font.render(txt, True, (220, 220, 220))
        screen.blit(surf, (x, y))
        y += 22


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Boardgame Prototype")
    clock = pygame.time.Clock()

    board_map, players = create_demo()
    engine = GameEngine(board_map, players, rng=lambda: 0.1)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    # demo: queue a simple attack and run one round
                    engine.queue_attack("p1", "p2", 3)
                    engine.run_round()

        draw(screen, board_map, players)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
