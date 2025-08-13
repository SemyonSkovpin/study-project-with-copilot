import numpy as np
import random
import imageio

from sound_sim_v3.sim_core import Canvas, advance_canvas, add_persistent_source

# Simulation parameters
WIDTH = 100
HEIGHT = 100
TIMESTEPS = 1000
SCALE = 5               # Each simulation cell will be SCALE x SCALE pixels
FPS = 30                # Playback speed for GIF
VMIN, VMAX = -5.0, 5.0  # Color mapping range

def pressure_to_image(pressure: np.ndarray) -> np.ndarray:
    """
    Convert pressure array (shape [W, H]) to an RGB image (H, W, 3) uint8.
    Vectorized (no Python loops) and upscaled by SCALE.
    """
    # pressure is shaped (W, H); convert to normalized [0,1] safely
    denom = (VMAX - VMIN) if (VMAX - VMIN) != 0 else 1e-6
    norm = (pressure - VMIN) / denom
    norm = np.clip(norm, 0.0, 1.0)

    # Build color channels: Blue(low) -> White(mid) -> Red(high)
    R = (255.0 * norm).astype(np.uint8)
    G = (255.0 * (1.0 - np.abs(norm - 0.5) * 2.0)).astype(np.uint8)
    B = (255.0 * (1.0 - norm)).astype(np.uint8)

    img = np.stack([R, G, B], axis=-1)            # (W, H, 3)
    img = np.transpose(img, (1, 0, 2))            # (H, W, 3)

    if SCALE > 1:
        img = np.repeat(np.repeat(img, SCALE, axis=0), SCALE, axis=1)
    return img

def main():
    # Initialize canvas
    canvas = Canvas(WIDTH, HEIGHT)

    # Place two persistent sources at random locations
    rng = np.random.default_rng()
    sources = []
    for _ in range(2):
        x = int(rng.integers(0, WIDTH))
        y = int(rng.integers(0, HEIGHT))
        add_persistent_source(canvas, x, y)
        sources.append((x, y))
    print("Sources at:", sources)

    # Stream frames directly to GIF to avoid high RAM usage
    with imageio.get_writer("sound_sim.gif", mode="I", duration=1.0 / FPS) as writer:
        for t in range(TIMESTEPS):
            # Use stable parameters; you can tweak sound_speed/dt/damping
            advance_canvas(
                canvas,
                sound_speed=0.5,   # must satisfy c*dt/dx <= 1/sqrt(2) with defaults dt=0.2, dx=1
                damping=0.998,
                time=t,
                dt=0.2,
                dx=1.0,
                dy=1.0,
                source_amp=1.0,
                source_freq=0.05,
                clip=50.0,
                boundary="periodic",
            )

            frame = pressure_to_image(canvas.pressure)
            writer.append_data(frame)

    print("GIF saved as sound_sim.gif")

if __name__ == "__main__":
    main()