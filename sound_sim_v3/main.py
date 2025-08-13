import pygame
import numpy as np
import random
from sim_core import Canvas, advance_canvas, add_persistent_source, handle_input

# Simulation parameters
WIDTH = 100
HEIGHT = 100
FPS = 60
VMIN, VMAX = -5.0, 5.0  # Color mapping range

# Modes for simulation
MODES = [
    ("pulse", "Pulse"),
    ("consistent", "Consistent"),
    ("remove", "Remove"),
]
BUTTON_WIDTH = 140
BUTTON_HEIGHT = 40
BUTTON_MARGIN = 10

# Screen parameters (set these to your device resolution or let Pygame detect)
SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0

def pressure_to_image(pressure: np.ndarray, scale: int) -> pygame.Surface:
    """
    Convert pressure array (WIDTH, HEIGHT) to a Pygame Surface with correct color mapping and scaling.
    """
    denom = (VMAX - VMIN) if (VMAX - VMIN) != 0 else 1e-6
    norm = (pressure - VMIN) / denom
    norm = np.clip(norm, 0.0, 1.0)

    R = (255.0 * norm).astype(np.uint8)
    G = (255.0 * (1.0 - np.abs(norm - 0.5) * 2.0)).astype(np.uint8)
    B = (255.0 * (1.0 - norm)).astype(np.uint8)
    img = np.stack([R, G, B], axis=-1)      # (WIDTH, HEIGHT, 3)
    img = np.transpose(img, (1, 0, 2))      # (HEIGHT, WIDTH, 3) for Pygame

    surf = pygame.surfarray.make_surface(img)
    if scale != 1:
        surf = pygame.transform.scale(surf, (pressure.shape[0]*scale, pressure.shape[1]*scale))
    return surf

def draw_mode_buttons(screen, font, current_mode):
    buttons = []
    for idx, (mode_key, mode_text) in enumerate(MODES):
        x = BUTTON_MARGIN
        y = BUTTON_MARGIN + idx * (BUTTON_HEIGHT + BUTTON_MARGIN)
        rect = pygame.Rect(x, y, BUTTON_WIDTH, BUTTON_HEIGHT)
        color = (180, 120, 40) if current_mode == mode_key else (100, 80, 20)
        pygame.draw.rect(screen, color, rect, border_radius=8)
        text_surf = font.render(mode_text, True, (255,255,255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
        buttons.append((rect, mode_key))
    return buttons

def main():
    global SCREEN_WIDTH, SCREEN_HEIGHT

    pygame.init()
    pygame.display.set_caption("Sound Simulation")

    # Font for buttons
    font = pygame.font.SysFont("arial", 24)

    # Get display size and scale
    info = pygame.display.Info()
    SCREEN_WIDTH = info.current_w
    SCREEN_HEIGHT = info.current_h

    # Calculate scale so canvas fills width
    scale = SCREEN_WIDTH // WIDTH
    canvas_pix_width = WIDTH * scale
    canvas_pix_height = HEIGHT * scale
    offset_x = (SCREEN_WIDTH - canvas_pix_width) // 2
    offset_y = (SCREEN_HEIGHT - canvas_pix_height) // 2

    # Set up screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Simulation setup
    canvas = Canvas(WIDTH, HEIGHT)
    rng = np.random.default_rng()
    for _ in range(2):
        x = int(rng.integers(0, WIDTH))
        y = int(rng.integers(0, HEIGHT))
        add_persistent_source(canvas, x, y)

    running = True
    clock = pygame.time.Clock()
    timestep = 0
    mode = "pulse"

    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Check if mode button was clicked
                for rect, mkey in draw_mode_buttons(screen, font, mode):
                    if rect.collidepoint(mx, my):
                        mode = mkey
                        break
                else:
                    # Map to canvas grid coordinates (x, y)
                    gx = (mx - offset_x) // scale
                    gy = (my - offset_y) // scale
                    if 0 <= gx < WIDTH and 0 <= gy < HEIGHT:
                        # FIX: DO NOT swap gx, gy; pass as-is for natural mapping
                        handle_input(canvas, gx, gy, mode)

        # Step simulation
        advance_canvas(
            canvas,
            sound_speed=0.5,
            damping=0.998,
            time=timestep,
            dt=0.2,
            dx=1.0,
            dy=1.0,
            source_amp=1.0,
            source_freq=0.05,
            clip=50.0,
            boundary="periodic",
        )
        timestep += 1

        # Draw background
        screen.fill((30, 15, 0))
        # Convert simulation to surface and blit centered
        surf = pressure_to_image(canvas.pressure, scale)
        screen.blit(surf, (offset_x, offset_y))

        # Draw buttons (on top)
        draw_mode_buttons(screen, font, mode)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()