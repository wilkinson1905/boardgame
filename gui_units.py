"""Unit/Truck renderer for pygame (G3).

Run: python gui_units.py
Displays map (using axial coords) and draws trucks with owner colors and labels. Click a truck to select.
"""
import sys
try:
    import pygame
except Exception:
    print("pygame is required. Install with: pip install pygame")
    raise

from gui_map import axial_to_pixel, hex_corners
from board.map import Map
from board.entities import PlayerState, Truck
from board import rules


SCREEN_W = 900
SCREEN_H = 480
BG = (24, 24, 34)
OWNER_COLORS = {"p1": (200, 80, 80), "p2": (80, 120, 200)}


def create_demo():
    m = Map()
    for q in range(-6, 7):
        for r in range(-2, 3):
            m.add_hex(q, r)

    p1 = PlayerState(id="p1", soldiers=rules.INITIAL_SOLDIERS, ammo=rules.INITIAL_AMMO, food=rules.INITIAL_FOOD)
    p2 = PlayerState(id="p2", soldiers=rules.INITIAL_SOLDIERS, ammo=rules.INITIAL_AMMO, food=rules.INITIAL_FOOD)

    # create trucks with some cargo values for display
    for i in range(rules.TRUCK_COUNT):
        t1 = Truck(id=f"p1_t{i}", owner_id="p1", position=f"{-6 + i},{0}", capacity=rules.TRUCK_CAPACITY, remaining_mp=rules.MP_PER_TURN)
        t1.cargo["soldiers"] = 2 + i
        t1.cargo["ammo"] = 3
        t2 = Truck(id=f"p2_t{i}", owner_id="p2", position=f"{6 - i},{0}", capacity=rules.TRUCK_CAPACITY, remaining_mp=rules.MP_PER_TURN)
        t2.cargo["soldiers"] = 1 + i
        t2.cargo["ammo"] = 2
        p1.trucks[t1.id] = t1
        p2.trucks[t2.id] = t2

    return m, {"p1": p1, "p2": p2}


def draw_trucks(surface, players, selected_id=None):
    font = pygame.font.SysFont(None, 16)
    for pid, p in players.items():
        color = OWNER_COLORS.get(pid, (190, 190, 190))
        for tid, t in p.trucks.items():
            q, r = map(int, t.position.split(","))
            x, y = axial_to_pixel(q, r)
            # draw truck body
            rect = pygame.Rect(x - 10, y - 10, 20, 20)
            pygame.draw.rect(surface, color, rect)
            # highlight selection
            if tid == selected_id:
                pygame.draw.rect(surface, (255, 255, 0), rect, 3)
            # draw cargo soldiers count
            txt = font.render(str(t.cargo.get("soldiers", 0)), True, (0, 0, 0))
            surface.blit(txt, (x - txt.get_width() // 2, y - txt.get_height() // 2))


def find_truck_at(players, pos):
    x, y = pos
    for pid, p in players.items():
        for tid, t in p.trucks.items():
            tq, tr = map(int, t.position.split(","))
            tx, ty = axial_to_pixel(tq, tr)
            if (x - tx) ** 2 + (y - ty) ** 2 <= 16 ** 2:
                return tid
    return None


def demo():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("G3: Units/Trucks Demo")
    clock = pygame.time.Clock()

    board_map, players = create_demo()
    selected = None

    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    tid = find_truck_at(players, ev.pos)
                    selected = tid

        screen.fill(BG)
        # draw map via small copy of draw_map to keep demo self-contained
        for (q, r), h in board_map._hexes.items():
            cx, cy = axial_to_pixel(q, r)
            corners = hex_corners(cx, cy)
            color = (150, 150, 150) if h.road_upgraded else (80, 80, 90)
            pygame.draw.polygon(screen, color, corners)
            pygame.draw.polygon(screen, (40, 40, 50), corners, 2)

        draw_trucks(screen, players, selected_id=selected)

        # HUD
        font = pygame.font.SysFont(None, 20)
        y = 8
        for pid, p in players.items():
            txt = f"{pid}: soldiers={p.soldiers} ammo={p.ammo} food={p.food}"
            surf = font.render(txt, True, (220, 220, 220))
            screen.blit(surf, (8, y))
            y += 22

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    demo()
