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
from gui_units import create_demo, find_truck_at
from board.game_engine import GameEngine
from board.pathfinding import find_path
from board import rules

SCREEN_W = 900
SCREEN_H = 520
BG = (18, 18, 26)


def hex_at_pos(board_map, pos):
    x, y = pos
    for (q, r), h in board_map._hexes.items():
        cx, cy = axial_to_pixel(q, r)
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
                cx, cy = axial_to_pixel(q, r)
                corners = hex_corners(cx, cy)
                color = (150, 150, 150) if h.road_upgraded else (70, 70, 80)
                pygame.draw.polygon(screen, color, corners)
                pygame.draw.polygon(screen, (30, 30, 40), corners, 2)

            # draw trucks
            from gui_units import draw_trucks
            draw_trucks(screen, players, selected_id=None)

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
                if ev.key == pygame.K_r:
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
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    # click: first try truck
                    tid = find_truck_at(players, ev.pos)
                    if tid:
                        # prevent selecting a truck that already moved this round
                        if tid in engine.moved_this_round:
                            print(f"Truck {tid} already moved this round; cannot select")
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
                                    print(f"No path found from {start} to {hx}; move not queued")
                                else:
                                    cost = res["cost"]
                                    if cost > rules.MP_PER_TURN:
                                        print(f"Path cost {cost} exceeds MP ({rules.MP_PER_TURN}); move not queued")
                                    else:
                                        ok = engine.queue_move(owner, selected_truck, [hx])
                                        if ok:
                                            # move succeeded — clear selection so user can't reissue on same truck
                                            selected_truck = None
                                        else:
                                            print(f"Move failed for {selected_truck}")
            elif ev.type == pygame.MOUSEMOTION:
                hover_hex = hex_at_pos(board_map, ev.pos)

        screen.fill(BG)
        # draw map
        for (q, r), h in board_map._hexes.items():
            cx, cy = axial_to_pixel(q, r)
            corners = hex_corners(cx, cy)
            color = (150, 150, 150) if h.road_upgraded else (70, 70, 80)
            pygame.draw.polygon(screen, color, corners)
            pygame.draw.polygon(screen, (30, 30, 40), corners, 2)

        # highlight hover hex
        if hover_hex:
            hx, hy = hover_hex
            cx, cy = axial_to_pixel(hx, hy)
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
                            nx, ny = axial_to_pixel(node[0], node[1])
                            pygame.draw.circle(screen, (160, 220, 160), (nx, ny), 6)
                        # color cost based on MP available
                        mp = rules.MP_PER_TURN
                        color = (100, 220, 100) if cost <= mp else (220, 100, 100)
                        font = pygame.font.SysFont(None, 18)
                        txt = font.render(f"cost: {cost}", True, color)
                        screen.blit(txt, (cx + 12, cy - 8))

        # draw trucks
        from gui_units import draw_trucks
        draw_trucks(screen, players, selected_id=selected_truck)

        # draw queued moves list
        draw_queued_moves(screen, board_map, engine)

        # popup display
        if popup and pygame.time.get_ticks() < popup_until:
            font = pygame.font.SysFont(None, 22)
            surf = font.render(popup, True, (255, 220, 120))
            screen.blit(surf, (200, 8))
        elif popup and pygame.time.get_ticks() >= popup_until:
            popup = None

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
