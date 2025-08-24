"""Interaction demo (G4): select truck, click hex to queue move, run round.

Run: python gui_interaction.py
Controls:
 - Click a truck to select
 - Click a hex to queue a move for the selected truck
 - R: run one round
 - Esc: quit
"""
import pygame
from gui_map import axial_to_pixel, hex_corners
from gui_units import create_demo, find_truck_at, OWNER_COLORS
from board.game_engine import GameEngine
from board.pathfinding import find_path
from board import rules

SCREEN_W = 1200
SCREEN_H = 800
BG = (18, 18, 26)
# map origin (shifted left to avoid side panel overlap)
MAP_ORIGIN = (SCREEN_W // 2 - 10, SCREEN_H // 2 - 20)


def hex_at_pos(board_map, pos):
    x, y = pos
    for (q, r), h in board_map._hexes.items():
        cx, cy = axial_to_pixel(q, r, origin=MAP_ORIGIN)
        # use radius approx
        if (x - cx) ** 2 + (y - cy) ** 2 <= (24) ** 2:
            return (q, r)
    return None


def draw_queued_moves(surface, board_map, engine):
    font = pygame.font.SysFont(None, 16)
    y = 8
    for i, m in enumerate(engine.movement_queue):
        player_id, truck_id, path = m
        text = f"Q{i}: {player_id}.{truck_id} -> {path}"
        surf = font.render(text, True, (220, 220, 220))
        surface.blit(surf, (8, y))
        y += 18


def animate_moves(screen, clock, board_map, players, engine):
    """Simple animation: step each queued movement one hex at a time at fixed interval."""
    if not engine.movement_queue:
        return

    # copy queue to process
    queue = list(engine.movement_queue)
    step_delay = 120  # ms per step

    for player_id, truck_id, path in queue:
        # animate along path
        if not path:
            continue
        # locate truck object
        player = players[player_id]
        truck = player.trucks.get(truck_id)
        if truck is None:
            continue

        for node in path:
            # move truck visually to node
            truck.position = f"{node[0]},{node[1]}"
            # redraw
            screen.fill(BG)
            # draw map
            for (q, r), h in board_map._hexes.items():
                cx, cy = axial_to_pixel(q, r, origin=MAP_ORIGIN)
                corners = hex_corners(cx, cy)
                if (q, r) == (0, 0):
                    color = (60, 110, 200)
                else:
                    color = (150, 150, 150) if h.road_upgraded else (70, 70, 80)
                pygame.draw.polygon(screen, color, corners)
                pygame.draw.polygon(screen, (30, 30, 40), corners, 2)

            # draw trucks
            from gui_units import draw_trucks
            draw_trucks(screen, players, selected_id=None, origin=MAP_ORIGIN)

            pygame.display.flip()
            # wait small delay
            pygame.time.delay(step_delay)

    # after animating, clear movement queue as moves will be processed by engine
    # (do not actually call engine.process_movement here)
    return


def demo():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("G4: Interaction Demo")
    clock = pygame.time.Clock()

    board_map, players = create_demo()
    engine = GameEngine(board_map, players, rng=lambda: 0.1)

    selected_truck = None
    hover_hex = None
    # phase state: 'A_move' -> 'B_move' -> 'attack'
    phase = 'A_move'
    # map phase to player id for movement phases
    phase_player = {'A_move': 'p1', 'B_move': 'p2'}
    # start of round: clear moved trackers
    engine.moved_this_round.clear()

    popup = None
    popup_until = 0
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_r:
                    # run one round with simple animation and show attack results
                    # animate queued moves first
                    animate_moves(screen, clock, board_map, players, engine)
                    res = engine.run_round()
                    # display attack results briefly
                    ars = res.get("attack_results", [])
                    if ars:
                        # create a combined popup text
                        lines = []
                        for a in ars:
                            lines.append(f"{a['attacker']}->{a['defender']}: dmg={a['damage']} lost={a['attacker_loss']}")
                        popup = " | ".join(lines)
                        popup_until = pygame.time.get_ticks() + 2500
                    else:
                        popup = "No attacks"
                        popup_until = pygame.time.get_ticks() + 1200
                # quick load/unload shortcuts when a truck is selected
                elif ev.key == pygame.K_l and selected_truck:
                    # load 1 soldier from player into truck
                    # find owner
                    owner = None
                    for pid, p in players.items():
                        if selected_truck in p.trucks:
                            owner = p
                            break
                    # only allow loading from warehouse if truck is adjacent to one of owner's warehouses
                    if owner and owner.warehouses:
                        # find any warehouse adjacent to truck
                        t = owner.trucks[selected_truck]
                        tq, tr = map(int, t.position.split(","))
                        adj = False
                        # check adjacency to frontline first
                        if hasattr(board_map, 'frontline') and board_map.frontline:
                            # frontend position should be (0,0)
                            fl_q, fl_r = 0, 0
                            # check if truck is neighbor of frontline
                            neighs = board_map.neighbors(fl_q, fl_r)
                            for n in neighs:
                                if (n.q, n.r) == (tq, tr):
                                    adj = True
                                    # perform load from frontline if available
                                    if sum(t.cargo.values()) < t.capacity and board_map.frontline.stock.get("soldiers", 0) > 0:
                                        board_map.frontline.stock["soldiers"] -= 1
                                        t.cargo["soldiers"] += 1
                                    break
                        # fallback: check owner's warehouses adjacency
                        if not adj:
                            for wid, wh in owner.warehouses.items():
                                wq, wr = map(int, wh.position.split(","))
                                hex_obj = board_map.get_hex(wq, wr)
                                if hex_obj:
                                    neighs = board_map.neighbors(wq, wr)
                                    for n in neighs:
                                        if (n.q, n.r) == (tq, tr):
                                            adj = True
                                            break
                                if adj:
                                    break
                            if adj and sum(t.cargo.values()) < t.capacity and owner.warehouses:
                                # transfer 1 soldier from warehouse stock if available
                                for wid, wh in owner.warehouses.items():
                                    if wh.stock.get("soldiers", 0) > 0:
                                        wh.stock["soldiers"] -= 1
                                        t.cargo["soldiers"] += 1
                                        break
                elif ev.key == pygame.K_u and selected_truck:
                    # unload 1 soldier from truck to player pool
                    owner = None
                    for pid, p in players.items():
                        if selected_truck in p.trucks:
                            owner = p
                            break
                    if owner:
                        t = owner.trucks[selected_truck]
                        # if adjacent to frontline, unload to frontline stock; else unload to owner pool
                        tq, tr = map(int, t.position.split(","))
                        unloaded = False
                        if hasattr(board_map, 'frontline') and board_map.frontline:
                            neighs = board_map.neighbors(0, 0)
                            for n in neighs:
                                if (n.q, n.r) == (tq, tr):
                                    # unload to frontline if truck has soldiers
                                    if t.cargo.get("soldiers", 0) > 0:
                                        t.cargo["soldiers"] -= 1
                                        board_map.frontline.stock["soldiers"] = board_map.frontline.stock.get("soldiers", 0) + 1
                                        unloaded = True
                                    break
                        if not unloaded:
                            if t.cargo.get("soldiers", 0) > 0:
                                t.cargo["soldiers"] -= 1
                                owner.soldiers += 1
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    # check if End Phase button clicked (top-right)
                    mx, my = ev.pos
                    btn_rect = pygame.Rect(SCREEN_W - 140, 8, 128, 28)
                    if btn_rect.collidepoint(mx, my):
                        # End phase pressed
                        if phase == 'A_move':
                            phase = 'B_move'
                        elif phase == 'B_move':
                            # proceed to attack phase: resolve attacks and food
                            ars = engine.process_attack_phase()
                            engine.process_food_phase()
                            # show attack summary popup
                            if ars:
                                lines = []
                                for a in ars:
                                    lines.append(f"{a['attacker']}->{a['defender']}: dmg={a['damage']} lost={a['attacker_loss']}")
                                popup = " | ".join(lines)
                                popup_until = pygame.time.get_ticks() + 2500
                            else:
                                popup = "No attacks"
                                popup_until = pygame.time.get_ticks() + 1200
                            # start next round
                            engine.moved_this_round.clear()
                            phase = 'A_move'
                        else:
                            # other phases fallback
                            phase = 'A_move'
                        # clear selection on phase change
                        selected_truck = None
                        continue

                    # check clicks inside right-side detail panel for load/unload buttons (G7)
                    panel_x = SCREEN_W - 220
                    panel_y = 60
                    panel_w = 208
                    panel_h = 400
                    # button positions relative to panel
                    load_rect = pygame.Rect(panel_x + 12, panel_y + panel_h - 56, 88, 28)
                    unload_rect = pygame.Rect(panel_x + 108, panel_y + panel_h - 56, 88, 28)
                    if load_rect.collidepoint(mx, my) and selected_truck:
                        # perform load 1 soldier (same as keyboard L): from adjacent warehouse to truck
                        owner = None
                        for pid, p in players.items():
                            if selected_truck in p.trucks:
                                owner = p
                                break
                        if owner:
                            t = owner.trucks[selected_truck]
                            tq, tr = map(int, t.position.split(","))
                            done = False
                            # attempt frontline load first
                            if hasattr(board_map, 'frontline') and board_map.frontline:
                                neighs = board_map.neighbors(0, 0)
                                for n in neighs:
                                    if (n.q, n.r) == (tq, tr):
                                        if sum(t.cargo.values()) < t.capacity and board_map.frontline.stock.get("soldiers", 0) > 0:
                                            board_map.frontline.stock["soldiers"] -= 1
                                            t.cargo["soldiers"] += 1
                                            popup = "Loaded 1 soldier from frontline"
                                            popup_until = pygame.time.get_ticks() + 1200
                                            done = True
                                        break
                            # fallback: warehouses
                            if not done and owner.warehouses:
                                adj = False
                                for wid, wh in owner.warehouses.items():
                                    wq, wr = map(int, wh.position.split(","))
                                    hex_obj = board_map.get_hex(wq, wr)
                                    if hex_obj:
                                        neighs = board_map.neighbors(wq, wr)
                                        for n in neighs:
                                            if (n.q, n.r) == (tq, tr):
                                                adj = True
                                                break
                                    if adj:
                                        break
                                if adj and sum(t.cargo.values()) < t.capacity:
                                    for wid, wh in owner.warehouses.items():
                                        if wh.stock.get("soldiers", 0) > 0:
                                            wh.stock["soldiers"] -= 1
                                            t.cargo["soldiers"] += 1
                                            popup = "Loaded 1 soldier from warehouse"
                                            popup_until = pygame.time.get_ticks() + 1200
                                            break
                        continue
                    if unload_rect.collidepoint(mx, my) and selected_truck:
                        # perform unload 1 soldier (same as keyboard U): truck -> frontline if adjacent, else owner pool
                        owner = None
                        for pid, p in players.items():
                            if selected_truck in p.trucks:
                                owner = p
                                break
                        if owner:
                            t = owner.trucks[selected_truck]
                            tq, tr = map(int, t.position.split(","))
                            done = False
                            if hasattr(board_map, 'frontline') and board_map.frontline:
                                neighs = board_map.neighbors(0, 0)
                                for n in neighs:
                                    if (n.q, n.r) == (tq, tr):
                                        if t.cargo.get("soldiers", 0) > 0:
                                            t.cargo["soldiers"] -= 1
                                            board_map.frontline.stock["soldiers"] = board_map.frontline.stock.get("soldiers", 0) + 1
                                            popup = "Unloaded 1 soldier to frontline"
                                            popup_until = pygame.time.get_ticks() + 1200
                                            done = True
                                        break
                            if not done:
                                if t.cargo.get("soldiers", 0) > 0:
                                    t.cargo["soldiers"] -= 1
                                    owner.soldiers += 1
                                    popup = "Unloaded 1 soldier"
                                    popup_until = pygame.time.get_ticks() + 1200
                        continue

                    # click: first try truck
                    tid = find_truck_at(players, ev.pos, origin=MAP_ORIGIN)
                    if tid:
                        # determine owner
                        owner = None
                        for pid, p in players.items():
                            if tid in p.trucks:
                                owner = pid
                                break
                        # allow selection only during movement phases for current player
                        if phase in phase_player and owner != phase_player[phase]:
                            # not this player's movement phase -> show popup
                            popup = f"Not {owner}'s movement phase"
                            popup_until = pygame.time.get_ticks() + 1200
                        elif tid in engine.moved_this_round:
                            popup = f"Truck {tid} already moved this round"
                            popup_until = pygame.time.get_ticks() + 1200
                        else:
                            selected_truck = tid
                    else:
                        hx = hex_at_pos(board_map, ev.pos)
                        if hx and selected_truck:
                            # find owner of selected truck
                            owner = None
                            truck_pos = None
                            for pid, p in players.items():
                                if selected_truck in p.trucks:
                                    owner = pid
                                    truck_pos = p.trucks[selected_truck].position
                                    break
                            if owner and truck_pos:
                                # validate path cost before queuing
                                start = tuple(map(int, truck_pos.split(",")))
                                res = find_path(board_map, start, hx)
                                if res is None:
                                    popup = f"No path found from {start} to {hx}"
                                    popup_until = pygame.time.get_ticks() + 1200
                                else:
                                    cost = res["cost"]
                                    if cost > rules.MP_PER_TURN:
                                        popup = f"Path cost {cost} exceeds MP ({rules.MP_PER_TURN})"
                                        popup_until = pygame.time.get_ticks() + 1200
                                    else:
                                        ok = engine.queue_move(owner, selected_truck, [hx])
                                        if ok:
                                            # move succeeded — clear selection so user can't reissue on same truck
                                            selected_truck = None
                                        else:
                                            popup = f"Move failed for {selected_truck}"
                                            popup_until = pygame.time.get_ticks() + 1200
            elif ev.type == pygame.MOUSEMOTION:
                hover_hex = hex_at_pos(board_map, ev.pos)

        screen.fill(BG)
        # draw map (highlight central hex as frontline)
        for (q, r), h in board_map._hexes.items():
            cx, cy = axial_to_pixel(q, r, origin=MAP_ORIGIN)
            corners = hex_corners(cx, cy)
            # central frontline tile
            if (q, r) == (0, 0):
                color = (60, 110, 200)  # blue frontline
            else:
                color = (150, 150, 150) if h.road_upgraded else (70, 70, 80)
            pygame.draw.polygon(screen, color, corners)
            pygame.draw.polygon(screen, (30, 30, 40), corners, 2)

        # draw warehouses (marker) on top of map but below units
        for pid, p in players.items():
            for wid, wh in p.warehouses.items():
                try:
                    wq, wr = map(int, wh.position.split(","))
                except Exception:
                    continue
                wx, wy = axial_to_pixel(wq, wr, origin=MAP_ORIGIN)
                col = OWNER_COLORS.get(pid, (180, 180, 180))
                # small house marker
                pygame.draw.rect(screen, col, (wx - 10, wy - 10, 20, 20))
                inner = (min(255, col[0] + 40), min(255, col[1] + 40), min(255, col[2] + 40))
                pygame.draw.rect(screen, inner, (wx - 6, wy - 6, 12, 12))
                font = pygame.font.SysFont(None, 14)
                txt = font.render("WH", True, (0, 0, 0))
                screen.blit(txt, (wx - txt.get_width() // 2, wy - txt.get_height() // 2))

        # highlight hover hex
        if hover_hex:
            hx, hy = hover_hex
            cx, cy = axial_to_pixel(hx, hy, origin=MAP_ORIGIN)
            pygame.draw.circle(screen, (200, 200, 100), (cx, cy), 6)

            # if a truck is selected, show path preview and cost
            if selected_truck:
                # find truck owner and position
                owner = None
                truck_pos = None
                for pid, p in players.items():
                    if selected_truck in p.trucks:
                        owner = pid
                        truck_pos = p.trucks[selected_truck].position
                        break
                if truck_pos:
                    sq = tuple(map(int, truck_pos.split(",")))
                    res = find_path(board_map, sq, (hx, hy))
                    if res:
                        path = res["path"]
                        cost = res["cost"]
                        # draw path
                        for node in path:
                            nx, ny = axial_to_pixel(node[0], node[1], origin=MAP_ORIGIN)
                            pygame.draw.circle(screen, (160, 220, 160), (nx, ny), 6)
                        # color cost based on MP available
                        mp = rules.MP_PER_TURN
                        color = (100, 220, 100) if cost <= mp else (220, 100, 100)
                        font = pygame.font.SysFont(None, 18)
                        txt = font.render(f"cost: {cost}", True, color)
                        screen.blit(txt, (cx + 12, cy - 8))

        # draw trucks
        from gui_units import draw_trucks
        draw_trucks(screen, players, selected_id=selected_truck, origin=MAP_ORIGIN)

        # Right-side detail panel for selected unit (G7)
        panel_x = SCREEN_W - 220
        panel_y = 60
        panel_w = 208
        panel_h = 400
        pygame.draw.rect(screen, (22, 22, 30), (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(screen, (60, 60, 70), (panel_x, panel_y, panel_w, panel_h), 2)
        font = pygame.font.SysFont(None, 18)
        if selected_truck:
            # find owner and truck
            owner = None
            truck_obj = None
            for pid, p in players.items():
                if selected_truck in p.trucks:
                    owner = p
                    truck_obj = p.trucks[selected_truck]
                    break
            if truck_obj:
                lines = [f"Truck: {truck_obj.id}", f"Owner: {owner.id}", f"Pos: {truck_obj.position}", f"MP: {truck_obj.remaining_mp}", "cargo:"]
                y = panel_y + 8
                for ln in lines:
                    surf = font.render(ln, True, (220, 220, 220))
                    screen.blit(surf, (panel_x + 8, y))
                    y += 20
                # cargo lines
                for k, v in truck_obj.cargo.items():
                    surf = font.render(f"{k}: {v}", True, (200, 200, 200))
                    screen.blit(surf, (panel_x + 12, y))
                    y += 18
                # show warehouses stocks
                y += 6
                ws = []
                for wid, wh in owner.warehouses.items():
                    ws.append(f"WH {wid} @ {wh.position}")
                    for kk, vv in wh.stock.items():
                        ws.append(f"  {kk}: {vv}")
                for ln in ws:
                    surf = font.render(ln, True, (170, 170, 170))
                    screen.blit(surf, (panel_x + 8, y))
                    y += 16
                # instructions for load/unload
                y += 6
                instr = ["L: load 1 soldier", "U: unload 1 soldier"]
                for ln in instr:
                    surf = font.render(ln, True, (180, 180, 180))
                    screen.blit(surf, (panel_x + 8, y))
                    y += 18
        else:
            surf = font.render("No unit selected", True, (180, 180, 180))
            screen.blit(surf, (panel_x + 8, panel_y + 8))

        # draw queued moves list
        draw_queued_moves(screen, board_map, engine)

        # draw Load/Unload buttons in right-side panel (G7)
        load_btn = pygame.Rect(panel_x + 12, panel_y + panel_h - 56, 88, 28)
        unload_btn = pygame.Rect(panel_x + 108, panel_y + panel_h - 56, 88, 28)
        pygame.draw.rect(screen, (70, 110, 70), load_btn)
        pygame.draw.rect(screen, (110, 70, 70), unload_btn)
        bfont = pygame.font.SysFont(None, 16)
        ltxt = bfont.render("Load 1", True, (240, 240, 240))
        utxt = bfont.render("Unload 1", True, (240, 240, 240))
        screen.blit(ltxt, (load_btn.x + 10, load_btn.y + 6))
        screen.blit(utxt, (unload_btn.x + 6, unload_btn.y + 6))

        # popup display
        if popup and pygame.time.get_ticks() < popup_until:
            font = pygame.font.SysFont(None, 22)
            surf = font.render(popup, True, (255, 220, 120))
            screen.blit(surf, (200, 8))
        elif popup and pygame.time.get_ticks() >= popup_until:
            popup = None

        # draw phase label and End Phase button
        font = pygame.font.SysFont(None, 20)
        phase_text = f"Phase: {phase}"
        p_surf = font.render(phase_text, True, (220, 220, 220))
        screen.blit(p_surf, (SCREEN_W - 260, 12))

        # End Phase button
        btn_rect = pygame.Rect(SCREEN_W - 140, 8, 128, 28)
        pygame.draw.rect(screen, (100, 100, 140), btn_rect)
        btn_txt = font.render("End Phase", True, (240, 240, 240))
        screen.blit(btn_txt, (SCREEN_W - 120, 12))

        # instructions
        font = pygame.font.SysFont(None, 18)
        ins = "Click truck -> click hex to queue move. Press R to run round. Esc to quit."
        surf = font.render(ins, True, (200, 200, 200))
        screen.blit(surf, (8, SCREEN_H - 28))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    demo()
