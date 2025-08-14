import numpy as np
from typing import List, Tuple, Optional

class Canvas:
    """
    Holds the state of the simulation: pressure fields and persistent sound sources.
    Arrays are shaped (width, height) for consistency with existing code.
    """
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.pressure = np.zeros((width, height), dtype=np.float32)
        self.prev_pressure = np.zeros((width, height), dtype=np.float32)
        # List of (x, y) tuples of persistent sources
        self.persistent_sources: List[Tuple[int, int]] = []

def add_pulse(canvas: Canvas, x: int, y: int, amplitude: float = 5.0):
    """Apply a single pressure impulse at (x, y)."""
    if 0 <= x < canvas.width and 0 <= y < canvas.height:
        canvas.pressure[x, y] += amplitude

def add_persistent_source(canvas: Canvas, x: int, y: int):
    """Add a persistent sound source at (x, y) if not already present."""
    if (x, y) not in canvas.persistent_sources:
        canvas.persistent_sources.append((x, y))

def remove_persistent_source(canvas: Canvas, x: int, y: int, radius: int = 2):
    """Remove the nearest persistent source to (x, y) within a given radius."""
    if not canvas.persistent_sources:
        return
    dists = [np.hypot(x - sx, y - sy) for (sx, sy) in canvas.persistent_sources]
    imin = int(np.argmin(dists))
    if dists[imin] <= radius:
        canvas.persistent_sources.pop(imin)

def handle_input(canvas: Canvas, x: int, y: int, mode: str):
    """
    Handle a user tap on (x, y) with a given mode:
    - "pulse": instant pressure
    - "consistent": add persistent source
    - "remove": remove persistent source
    """
    if mode == "pulse":
        add_pulse(canvas, x, y)
    elif mode == "consistent":
        add_persistent_source(canvas, x, y)
    elif mode == "remove":
        remove_persistent_source(canvas, x, y)
    else:
        raise ValueError(f"Unknown mode: {mode}")

def advance_canvas(
    canvas: Canvas,
    sound_speed: float = 0.5,          # Lower default for stability
    damping: float = 0.998,
    time: float = 0.0,                 # Simulation step index or time units
    dt: float = 0.2,                   # Time step size
    dx: float = 1.0,                   # Grid spacing x
    dy: float = 1.0,                   # Grid spacing y
    source_amp: float = 1.0,           # Amplitude of sinusoidal sources
    source_freq: float = 0.05,         # Frequency (cycles per unit time)
    clip: Optional[float] = 100.0,     # Clip magnitude to avoid overflow; set None to disable
    boundary: str = "reflective",      # "reflective" (default), "periodic", or "fixed"
):
    """
    Advance the simulation by one timestep using a stable 2D wave equation scheme.

    Discretization (leapfrog):

      P_next = 2P - P_prev + (c^2 * dt^2) * Laplacian(P)
      P_next *= damping

    Stability (CFL) condition for 2D with dx=dy:
      (c * dt / dx) <= 1 / sqrt(2)
    Defaults chosen to satisfy this.

    boundary:
      - "periodic": wrap with np.roll (torus)
      - "fixed": zero Dirichlet boundary after update (absorbing-ish)
      - "reflective": Neumann/mirrored boundary after update (reflective wall, default)
    """
    P = canvas.pressure
    P_prev = canvas.prev_pressure

    # 8-neighbor Laplacian (9-point stencil, Moore neighborhood)
    # Weights: adjacent: 1, diagonals: 1, center: -8
    # Normalization: 1/3 for isotropy

    lap = (
        np.roll(P,  1, axis=0) + np.roll(P, -1, axis=0) +  # up, down
        np.roll(P,  1, axis=1) + np.roll(P, -1, axis=1) +  # left, right
        np.roll(np.roll(P,  1, axis=0),  1, axis=1) +      # up-left
        np.roll(np.roll(P,  1, axis=0), -1, axis=1) +      # up-right
        np.roll(np.roll(P, -1, axis=0),  1, axis=1) +      # down-left
        np.roll(np.roll(P, -1, axis=0), -1, axis=1)        # down-right
        - 8.0 * P
    ) / (3.0 * dx * dx)

    laplacian = lap

    coeff = (sound_speed * dt) ** 2  # c^2 * dt^2

    # Leapfrog update
    P_next = (2.0 * P - P_prev) + coeff * laplacian

    # Add persistent sources (sinusoidal, using continuous time t = time * dt)
    t_cont = time * dt
    if canvas.persistent_sources and source_amp != 0.0:
        s_val = source_amp * np.sin(2.0 * np.pi * source_freq * t_cont)
        for (sx, sy) in canvas.persistent_sources:
            if 0 <= sx < canvas.width and 0 <= sy < canvas.height:
                P_next[sx, sy] += s_val

    # Damping
    if damping != 1.0:
        P_next *= damping

    # Boundary conditions
    if boundary == "fixed":
        P_next[0, :] = 0.0
        P_next[-1, :] = 0.0
        P_next[:, 0] = 0.0
        P_next[:, -1] = 0.0
    elif boundary == "reflective":
        # Neumann: mirror the edge values
        # Top and bottom
        P_next[0, :] = P_next[1, :]
        P_next[-1, :] = P_next[-2, :]
        # Left and right
        P_next[:, 0] = P_next[:, 1]
        P_next[:, -1] = P_next[:, -2]
    # else: "periodic" already applied via np.roll

    # Numerical safety: replace NaN/Inf and clip
    if clip is not None:
        # Use nan_to_num with bounds; if clip is small, this also bounds infs.
        np.nan_to_num(P_next, copy=False, nan=0.0, posinf=clip, neginf=-clip)
        np.clip(P_next, -clip, clip, out=P_next)
    else:
        np.nan_to_num(P_next, copy=False, nan=0.0)

    # Rotate buffers
    canvas.prev_pressure[:, :] = P
    canvas.pressure[:, :] = P_next