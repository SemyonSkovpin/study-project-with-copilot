print("hello")

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random

from sim_core import Canvas, advance_canvas, add_persistent_source

print("hello")
# Simulation parameters
WIDTH = 100
HEIGHT = 100
TIMESTEPS = 1000

# Initialize canvas
canvas = Canvas(WIDTH, HEIGHT)

# Place two persistent sources at random locations
source_coords = []
for _ in range(2):
    x = random.randint(0, WIDTH - 1)
    y = random.randint(0, HEIGHT - 1)
    add_persistent_source(canvas, x, y)
    source_coords.append((x, y))

# Prepare to collect frames for animation
frames = []

for t in range(TIMESTEPS):
    print (t)
    advance_canvas(canvas, time=t)
    frames.append(canvas.pressure.T.copy())  # transpose for imshow

# Set up animation with matplotlib
fig, ax = plt.subplots()
im = ax.imshow(frames[0], cmap='RdBu', vmin=-5, vmax=5, animated=True)
ax.set_title("2D Sound Simulation\nSources: {}".format(source_coords))

def update(frame):
    im.set_data(frame)
    return [im]

ani = animation.FuncAnimation(
    fig, update, frames=frames, interval=30, blit=True, repeat=False
)

# Save animation as mp4 (requires ffmpeg) and gif (requires imagemagick)
ani.save('sound_sim.mp4', writer='ffmpeg')
ani.save('sound_sim.gif', writer='imagemagick')

print("done")
#plt.show()