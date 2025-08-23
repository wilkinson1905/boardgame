"""Map renderer for pygame (G2).

Run: python gui_map.py
Shows a simple hex map rendered using axial coordinates.
"""
import math
import sys
try:
    import pygame
except Exception:
    print("pygame is required. Install with: pip install pygame")
    raise

from board.map import Map


HEX_SIZE = 30  # radius in pixels
HEX_COLOR = (70, 70, 90)
HEX_BORDER = (120, 120, 140)
UPGRADED_COLOR = (160, 120, 60)


def axial_to_pixel(q: int, r: int, size: int = HEX_SIZE, origin=(400, 200)):
    """Convert axial coords (q,r) to pixel (x,y) for pointy-top hexes."""
    x = size * math.sqrt(3) * (q + r / 2) + origin[0]
    y = size * 1.5 * r + origin[1]
    return int(x), int(y)


def hex_corners(center_x: int, center_y: int, size: int = HEX_SIZE):
    corners = []
    for i in range(6):
        angle = math.pi / 180 * (60 * i - 30)  # pointy-top
        x = center_x + size * math.cos(angle)
        y = center_y + size * math.sin(angle)
        corners.append((int(x), int(y)))
    return corners


def draw_map(surface: 'pygame.Surface', board_map: Map):
    # iterate hexes and draw
    for (q, r), h in board_map._hexes.items():
        cx, cy = axial_to_pixel(q, r)
        corners = hex_corners(cx, cy)
        # fill based on upgraded
        color = UPGRADED_COLOR if h.road_upgraded else HEX_COLOR
        pygame.draw.polygon(surface, color, corners)
        pygame.draw.polygon(surface, HEX_BORDER, corners, 2)
        # draw id
        font = pygame.font.SysFont(None, 16)
        txt = font.render(h.id, True, (220, 220, 220))
        surface.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))


def demo():
    pygame.init()
    screen = pygame.display.set_mode((800, 480))
    pygame.display.set_caption("G2: Map Renderer Demo")
    clock = pygame.time.Clock()

    # create a demo map
    m = Map()
    for q in range(-5, 6):
        for r in range(-2, 3):
            m.add_hex(q, r)

    # mark a couple upgraded
    h = m.get_hex(0, 0)
    if h:
        h.road_upgraded = True
    h2 = m.get_hex(2, 0)
    if h2:
        h2.road_upgraded = True

    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False

        screen.fill((30, 30, 40))
        draw_map(screen, m)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    demo()
