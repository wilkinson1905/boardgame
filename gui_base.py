"""Minimal pygame startup template for G1.

Run: python gui_base.py
This opens a window and exits on ESC or window close.
"""
try:
    import pygame
except Exception:
    raise ImportError("pygame not installed. Install with: pip install pygame")


def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 360))
    pygame.display.set_caption("GUI Base - Boardgame")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 24)

    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False

        screen.fill((40, 40, 50))
        txt = font.render("G1: minimal GUI loop. Press ESC to quit.", True, (220, 220, 220))
        screen.blit(txt, (20, 20))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
