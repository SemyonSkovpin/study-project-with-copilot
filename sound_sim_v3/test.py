import pygame
import random
import numpy as np
from sim_core import Canvas, advance_canvas, add_persistent_source

import imageio

# Simulation parameters
WIDTH = 100
HEIGHT = 100
TIMESTEPS = 1000
SCALE = 5  # Each simulation cell will be SCALE x SCALE pixels
FPS = 60

def pressure_to_color(p, vmin=-5, vmax=5):
    """Map pressure value to RGB color."""
    norm = (p - vmin) / (vmax - vmin)
    norm = np.clip(norm, 0, 1)
    # Blue (low) -> White (mid) -> Red (high)
    return (
        int(255 * norm),                       # R
        int(255 * (1 - abs(norm - 0.5) * 2)),  # G (white at center)
        int(255 * (1 - norm))                  # B
    )

def draw_canvas(surface, pressure):
    arr_min, arr_max = pressure.min(), pressure.max()
    if arr_max - arr_min < 1e-5:
        arr_max = arr_min + 1e-5
    for x in range(WIDTH):
        for y in range(HEIGHT):
            color = pressure_to_color(pressure[x, y], vmin=-5, vmax=5)
            rect = pygame.Rect(x * SCALE, y * SCALE, SCALE, SCALE)
            surface.fill(color, rect)

def run_and_capture_simulation():
    canvas = Canvas(WIDTH, HEIGHT)

    # Place two persistent sources at random locations
    source_coords = []
    for _ in range(2):
        x = random.randint(0, WIDTH - 1)
        y = random.randint(0, HEIGHT - 1)
        add_persistent_source(canvas, x, y)
        source_coords.append((x, y))
    print("Sound sources at:", source_coords)

    # Prepare to capture frames as numpy arrays for GIF
    frames = []
    for timestep in range(TIMESTEPS):
        advance_canvas(canvas, time=timestep)
        # Convert pressure to RGB image (H x W x 3, uint8)
        arr_min, arr_max = canvas.pressure.min(), canvas.pressure.max()
        if arr_max - arr_min < 1e-5:
            arr_max = arr_min + 1e-5
        norm = (canvas.pressure - arr_min) / (arr_max - arr_min)
        image = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        for x in range(WIDTH):
            for y in range(HEIGHT):
                image[y, x] = pressure_to_color(canvas.pressure[x, y], vmin=-5, vmax=5)
        # Upscale for visibility
        if SCALE > 1:
            image = np.kron(image, np.ones((SCALE, SCALE, 1), dtype=np.uint8))
        frames.append(image)
    return frames

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
    pygame.display.set_caption("Sound Simulation (Pygame)")
    clock = pygame.time.Clock()

    # --- Run simulation and capture all frames ---
    print("Running simulation and capturing frames...")
    frames = run_and_capture_simulation()
    print("Simulation done. Starting animation.")

    # --- Play animation in pygame ---
    running = True
    frame_idx = 0
    total_frames = len(frames)
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        # Display current frame
        surf = pygame.surfarray.make_surface(np.transpose(frames[frame_idx], (1, 0, 2)))
        screen.blit(surf, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)
        frame_idx += 1
        if frame_idx >= total_frames:
            frame_idx = 0  # Loop the animation

    # --- Save last frame as PNG ---
    pygame.image.save(screen, "sound_sim_final.png")
    print("Last frame saved as sound_sim_final.png.")

    # --- Save GIF animation ---
    print("Saving animation to sound_sim.gif ...")
    imageio.mimsave("sound_sim.gif", frames, duration=1/FPS)
    print("Animation saved as sound_sim.gif.")

    pygame.quit()

if __name__ == "__main__":
    main()