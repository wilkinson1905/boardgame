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
from board.entities import PlayerState, Truck, Warehouse
from board import rules


SCREEN_W = 900
SCREEN_H = 480
BG = (24, 24, 34)
OWNER_COLORS = {"p1": (200, 80, 80), "p2": (80, 120, 200)}


def create_demo():
    m = Map()
    # create a rectangular axial grid (cols x rows), centered around (0,0)
    cols = 13
    rows = 15
    half_cols = cols // 2
    half_rows = rows // 2
    for row in range(rows):
        for col in range(cols):
            # convert even-r offset (col,row) to axial (q,r) for pointy-top layout
            q = col - half_cols - (row // 2)
            r = row - half_rows
            m.add_hex(q, r)

    p1 = PlayerState(id="p1", soldiers=rules.INITIAL_SOLDIERS, ammo=rules.INITIAL_AMMO, food=rules.INITIAL_FOOD)
    p2 = PlayerState(id="p2", soldiers=rules.INITIAL_SOLDIERS, ammo=rules.INITIAL_AMMO, food=rules.INITIAL_FOOD)

    # create warehouses at top and bottom edges (one tile inward), centered horizontally
    qs = [q for (q, r) in m._hexes.keys()]
    rs = [r for (q, r) in m._hexes.keys()]
    min_q = min(qs)
    max_q = max(qs)
    min_r = min(rs)
    max_r = max(rs)

    # target rows: one tile inward from top and bottom
    top_r = min_r + 1
    bot_r = max_r - 1

    # find candidate q values at those rows and pick the q closest to center (0)
    top_candidates = [q for (q, r) in m._hexes.keys() if r == top_r]
    bot_candidates = [q for (q, r) in m._hexes.keys() if r == bot_r]
    print(top_candidates)
    print(bot_candidates)
    if top_candidates:
        w1_q = top_candidates[int(len(top_candidates)/2)]
        w1_r = top_r
    else:
        # fallback to leftmost top-most
        w1_q = min_q
        # pick r for that q closest to min_r
        col = [h for (q, r), h in m._hexes.items() if q == w1_q]
        w1_r = min(col, key=lambda h: abs(h.r - min_r)).r if col else min_r

    if bot_candidates:
        w2_q = bot_candidates[int(len(bot_candidates)/2)]
        w2_r = bot_r
    else:
        w2_q = max_q
        col = [h for (q, r), h in m._hexes.items() if q == w2_q]
        w2_r = min(col, key=lambda h: abs(h.r - max_r)).r if col else max_r

    w1 = Warehouse(id="p1_wh", owner_id="p1", position=f"{w1_q},{w1_r}", stock={"soldiers": rules.INITIAL_SOLDIERS, "ammo": rules.INITIAL_AMMO, "food": rules.INITIAL_FOOD})
    w2 = Warehouse(id="p2_wh", owner_id="p2", position=f"{w2_q},{w2_r}", stock={"soldiers": rules.INITIAL_SOLDIERS, "ammo": rules.INITIAL_AMMO, "food": rules.INITIAL_FOOD})
    p1.warehouses[w1.id] = w1
    p2.warehouses[w2.id] = w2

    # mark warehouse hex occupants for map-based checks
    h1 = m.get_hex(w1_q, w1_r)
    if h1:
        h1.occupants.append('warehouse')
    h2 = m.get_hex(w2_q, w2_r)
    if h2:
        h2.occupants.append('warehouse')

    # helper: choose spawn neighbor toward map center
    center_q = (min_q + max_q) / 2
    center_r = sum(rs) / len(rs) if rs else 0
    def spawn_neighbor_toward_center(h):
        neighs = m.neighbors(h.q, h.r)
        if not neighs:
            return None
        # pick neighbor whose (q,r) is closest to map center
        best = min(neighs, key=lambda nh: (nh.q - center_q) ** 2 + (nh.r - center_r) ** 2)
        return best

    # create trucks with some cargo values for display
    # for each warehouse pick the neighbor toward center and spawn trucks along that inward direction
    # place trucks: for p1 (top) place on the row one inward from top, centered;
    # for p2 (bottom) place on the row one inward from bottom, centered.
    for owner_id, wh in [("p1", w1), ("p2", w2)]:
        wq, wr = map(int, wh.position.split(","))
        wh_hex = m.get_hex(wq, wr)
        # target rows for trucks (one inward from warehouse rows)
        top_truck_r = top_r - 1
        bot_truck_r = bot_r + 1

        target_r = top_truck_r if owner_id == "p1" else bot_truck_r

        # gather available q values on that target row
        q_on_row = sorted([q for (q, r) in m._hexes.keys() if r == target_r])
        chosen_positions = []
        if len(q_on_row) >= rules.TRUCK_COUNT:
            mid = len(q_on_row) // 2
            start = mid - (rules.TRUCK_COUNT // 2)
            if start < 0:
                start = 0
            chosen_qs = q_on_row[start:start + rules.TRUCK_COUNT]
            # if slice shorter, pad from left
            if len(chosen_qs) < rules.TRUCK_COUNT:
                # extend with nearby qs
                need = rules.TRUCK_COUNT - len(chosen_qs)
                extra = q_on_row[:need]
                chosen_qs += extra
            for qv in chosen_qs:
                chosen_positions.append((qv, target_r))
        else:
            # fallback: try neighbor-based spawn as before
            spawn_hex = None
            if wh_hex:
                neighs = m.neighbors(wh_hex.q, wh_hex.r)
                if neighs:
                    spawn_hex = min(neighs, key=lambda nh: (nh.q - center_q) ** 2 + (nh.r - center_r) ** 2)
            if spawn_hex:
                base_q, base_r = spawn_hex.q, spawn_hex.r
            else:
                base_q, base_r = (wq + (1 if owner_id == "p1" else -1), wr)
            for i in range(rules.TRUCK_COUNT):
                chosen_positions.append((base_q + i, base_r))

        # create trucks at chosen positions
        for i, (pos_q, pos_r) in enumerate(chosen_positions):
            if owner_id == "p1":
                t = Truck(id=f"p1_t{i}", owner_id="p1", position=f"{pos_q},{pos_r}", capacity=rules.TRUCK_CAPACITY, remaining_mp=rules.MP_PER_TURN)
                t.cargo["soldiers"] = 2 + i
                t.cargo["ammo"] = 3
                p1.trucks[t.id] = t
            else:
                t = Truck(id=f"p2_t{i}", owner_id="p2", position=f"{pos_q},{pos_r}", capacity=rules.TRUCK_CAPACITY, remaining_mp=rules.MP_PER_TURN)
                t.cargo["soldiers"] = 1 + i
                t.cargo["ammo"] = 2
                p2.trucks[t.id] = t

    return m, {"p1": p1, "p2": p2}


def draw_trucks(surface, players, selected_id=None, origin=(400, 200)):
    font = pygame.font.SysFont(None, 16)
    for pid, p in players.items():
        color = OWNER_COLORS.get(pid, (190, 190, 190))
        for tid, t in p.trucks.items():
            q, r = map(int, t.position.split(","))
            x, y = axial_to_pixel(q, r, origin=origin)
            # draw truck body
            rect = pygame.Rect(x - 10, y - 10, 20, 20)
            pygame.draw.rect(surface, color, rect)
            # highlight selection
            if tid == selected_id:
                pygame.draw.rect(surface, (255, 255, 0), rect, 3)
            # draw cargo soldiers count
            txt = font.render(str(t.cargo.get("soldiers", 0)), True, (0, 0, 0))
            surface.blit(txt, (x - txt.get_width() // 2, y - txt.get_height() // 2))


def find_truck_at(players, pos, origin=(400, 200)):
    x, y = pos
    for pid, p in players.items():
        for tid, t in p.trucks.items():
            tq, tr = map(int, t.position.split(","))
            tx, ty = axial_to_pixel(tq, tr, origin=origin)
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
