"""Unit/Truck renderer for pygame (G3).

Run: python gui_units.py
Displays map (using axial coords) and draws trucks with owner colors and labels. Click a truck to select.
"""
try:
    import pygame
except Exception:
    raise ImportError("pygame is required. Install with: pip install pygame")

from gui_map import axial_to_pixel, hex_corners
from board.map import Map
from board.entities import PlayerState, Truck, Warehouse
from board import rules


SCREEN_W = 900
SCREEN_H = 480
BG = (24, 24, 34)
OWNER_COLORS = {"p1": (200, 80, 80), "p2": (80, 120, 200)}


def create_demo():
    # --- build rectangular map ---
    m = Map()
    cols = 13
    rows = 15
    half_cols = cols // 2
    half_rows = rows // 2
    for row in range(rows):
        for col in range(cols):
            q = col - half_cols - (row // 2)
            r = row - half_rows
            m.add_hex(q, r)

    # --- player state ---
    p1 = PlayerState(id="p1", soldiers=rules.INITIAL_SOLDIERS, ammo=rules.INITIAL_AMMO, food=rules.INITIAL_FOOD)
    p2 = PlayerState(id="p2", soldiers=rules.INITIAL_SOLDIERS, ammo=rules.INITIAL_AMMO, food=rules.INITIAL_FOOD)

    # --- warehouse placement: top/bottom rows, one tile inward, centered horizontally ---
    qs = [q for (q, r) in m._hexes.keys()]
    rs = [r for (q, r) in m._hexes.keys()]
    min_r = min(rs)
    max_r = max(rs)

    top_r = min_r + 1
    bot_r = max_r - 1

    def pick_center_q(row):
        vals = sorted([q for (q, r) in m._hexes.keys() if r == row])
        if not vals:
            return 0
        return vals[len(vals) // 2]

    w1_q = pick_center_q(top_r)
    w1_r = top_r
    w2_q = pick_center_q(bot_r)
    w2_r = bot_r

    w1 = Warehouse(id="p1_wh", owner_id="p1", position=f"{w1_q},{w1_r}", stock={"soldiers": rules.INITIAL_SOLDIERS, "ammo": rules.INITIAL_AMMO, "food": rules.INITIAL_FOOD})
    w2 = Warehouse(id="p2_wh", owner_id="p2", position=f"{w2_q},{w2_r}", stock={"soldiers": rules.INITIAL_SOLDIERS, "ammo": rules.INITIAL_AMMO, "food": rules.INITIAL_FOOD})
    p1.warehouses[w1.id] = w1
    p2.warehouses[w2.id] = w2

    # mark warehouse tiles
    h1 = m.get_hex(w1_q, w1_r)
    if h1:
        h1.occupants.append('warehouse')
    h2 = m.get_hex(w2_q, w2_r)
    if h2:
        h2.occupants.append('warehouse')

    # --- truck placement: put trucks centered on rows just inward from warehouses ---
    center_q = (min(qs) + max(qs)) / 2
    center_r = sum(rs) / len(rs) if rs else 0

    def choose_positions_on_row(target_r, count):
        q_on_row = sorted([q for (q, r) in m._hexes.keys() if r == target_r])
        if len(q_on_row) >= count:
            mid = len(q_on_row) // 2
            start = max(0, mid - (count // 2))
            return [(q_on_row[start + i], target_r) for i in range(count)]
        # fallback: pick neighbors of warehouse toward center
        return None

    # p1 trucks (top): one row further inward from warehouse
    p1_positions = choose_positions_on_row(top_r + 1, rules.TRUCK_COUNT)
    p2_positions = choose_positions_on_row(bot_r - 1, rules.TRUCK_COUNT)

    # fallback neighbor-based placement
    if p1_positions is None:
        wh_hex = m.get_hex(w1_q, w1_r)
        neighs = m.neighbors(wh_hex.q, wh_hex.r) if wh_hex else []
        if neighs:
            base = min(neighs, key=lambda nh: (nh.q - center_q) ** 2 + (nh.r - center_r) ** 2)
            p1_positions = [(base.q + i, base.r) for i in range(rules.TRUCK_COUNT)]
        else:
            p1_positions = [(w1_q + i, w1_r) for i in range(rules.TRUCK_COUNT)]

    if p2_positions is None:
        wh_hex = m.get_hex(w2_q, w2_r)
        neighs = m.neighbors(wh_hex.q, wh_hex.r) if wh_hex else []
        if neighs:
            base = min(neighs, key=lambda nh: (nh.q - center_q) ** 2 + (nh.r - center_r) ** 2)
            p2_positions = [(base.q + i, base.r) for i in range(rules.TRUCK_COUNT)]
        else:
            p2_positions = [(w2_q + i, w2_r) for i in range(rules.TRUCK_COUNT)]

    for i, (pos_q, pos_r) in enumerate(p1_positions):
        t = Truck(id=f"p1_t{i}", owner_id="p1", position=f"{pos_q},{pos_r}", capacity=rules.TRUCK_CAPACITY, remaining_mp=rules.MP_PER_TURN)
        t.cargo["soldiers"] = 2 + i
        t.cargo["ammo"] = 3
        p1.trucks[t.id] = t

    for i, (pos_q, pos_r) in enumerate(p2_positions):
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
