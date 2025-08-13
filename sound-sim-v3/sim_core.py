import numpy as np
from typing import List, Tuple

class Canvas:
    """
    Holds the state of the simulation: pressure fields and persistent sound sources.
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


def advance_canvas(canvas: Canvas, sound_speed: float = 1.7, damping: float = 0.998, time: float = 0.0):
    """
    Advance the simulation by one timestep using the 2D wave equation.
    - sound_speed: Controls how fast waves propagate.
    - damping: <1.0 damps the wave energy over time.
    - time: Simulation time, used for persistent source phase.
    """
    P = canvas.pressure
    P_prev = canvas.prev_pressure

    # Compute Laplacian with np.roll for periodic neighbors (set boundary below)
    laplacian = (
        np.roll(P, 1, axis=0) + np.roll(P, -1, axis=0) +
        np.roll(P, 1, axis=1) + np.roll(P, -1, axis=1) -
        4 * P
    )

    # Leapfrog update for wave equation
    P_next = (2 * P - P_prev + (sound_speed ** 2) * laplacian) * damping

    # Add persistent sources (sinusoidal)
    freq = 0.05  # Tweak as desired
    for (sx, sy) in canvas.persistent_sources:
        if 0 <= sx < canvas.width and 0 <= sy < canvas.height:
            P_next[sx, sy] += 1.2 * np.sin(time * freq)

    # Zero Dirichlet boundary conditions
    P_next[0, :] = 0
    P_next[-1, :] = 0
    P_next[:, 0] = 0
    P_next[:, -1] = 0

    # Swap for next step
    canvas.prev_pressure = P.copy()
    canvas.pressure = P_next
