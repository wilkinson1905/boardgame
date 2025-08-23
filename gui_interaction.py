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


def demo():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("G4: Interaction Demo")
    clock = pygame.time.Clock()

    board_map, players = create_demo()
    engine = GameEngine(board_map, players, rng=lambda: 0.1)

    selected_truck = None
    hover_hex = None

    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                if ev.key == pygame.K_r:
                    # run one round
                    engine.run_round()
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    # click: first try truck
                    tid = find_truck_at(players, ev.pos)
                    if tid:
                        selected_truck = tid
                    else:
                        hx = hex_at_pos(board_map, ev.pos)
                        if hx and selected_truck:
                            # find owner of selected truck
                            owner = None
                            for pid, p in players.items():
                                if selected_truck in p.trucks:
                                    owner = pid
                                    break
                            if owner:
                                engine.queue_move(owner, selected_truck, [hx])
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

        # draw trucks
        from gui_units import draw_trucks
        draw_trucks(screen, players, selected_id=selected_truck)

        # draw queued moves list
        draw_queued_moves(screen, board_map, engine)

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
