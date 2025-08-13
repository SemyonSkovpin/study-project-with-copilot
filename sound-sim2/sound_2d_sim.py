import pygame
import numpy as np
import sys

# Config
WIDTH, HEIGHT = 320, 480    # Canvas size (fits most phones)
GRID_SIZE = 80              # Simulation grid (smaller = faster, larger = higher res)
CELL_SIZE_X = WIDTH // GRID_SIZE
CELL_SIZE_Y = (HEIGHT-36) // GRID_SIZE  # Leave space for buttons
FPS = 30                    # Target framerate
DAMPING = 0.998             # Damping factor for the wave
SOUND_SPEED = 1.7           # Controls wave speed; ~1.7 is visually reasonable

# Colors
BG_COLOR = (20, 20, 30)
PRESSURE_COLOR = (0, 180, 255)
NEG_PRESSURE_COLOR = (255, 0, 80)
BUTTON_COLOR = (60, 60, 70)
BUTTON_ACTIVE = (100, 180, 100)
TEXT_COLOR = (255, 255, 255)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Sound Simulation")
font = pygame.font.SysFont("arial", 18)

# Simulation state
pressure = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
prev_pressure = np.zeros_like(pressure)
sources = []  # Persistent sources: (gx, gy)
mode = 0      # 0 = clap, 1 = add source, 2 = remove source

# Button areas
BTN_W, BTN_H = WIDTH // 3, 36
buttons = [
    pygame.Rect(0, 0, BTN_W, BTN_H),
    pygame.Rect(BTN_W, 0, BTN_W, BTN_H),
    pygame.Rect(2*BTN_W, 0, BTN_W, BTN_H)
]
btn_labels = ["Clap", "Add Source", "Remove Source"]

def draw_buttons():
    for i, rect in enumerate(buttons):
        color = BUTTON_ACTIVE if i == mode else BUTTON_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=8)
        label = font.render(btn_labels[i], True, TEXT_COLOR)
        lw, lh = label.get_size()
        screen.blit(label, (rect.x + (rect.width-lw)//2, rect.y + (rect.height-lh)//2))

def grid_from_xy(x, y):
    gx = int(np.clip(x//CELL_SIZE_X, 0, GRID_SIZE-1))
    gy = int(np.clip((y-BTN_H)//CELL_SIZE_Y, 0, GRID_SIZE-1))
    return gx, gy

def update_wave():
    global pressure, prev_pressure
    # 2D wave equation, simple finite difference, fixed edges
    laplacian = (
        np.roll(pressure, 1, axis=0) + np.roll(pressure, -1, axis=0) +
        np.roll(pressure, 1, axis=1) + np.roll(pressure, -1, axis=1)
        - 4 * pressure
    )
    next_pressure = (
        2 * pressure - prev_pressure + (SOUND_SPEED ** 2) * laplacian
    ) * DAMPING
    # Zero at boundaries
    next_pressure[0,:]=0; next_pressure[-1,:]=0
    next_pressure[:,0]=0; next_pressure[:,-1]=0

    # Add persistent sources
    for gx, gy in sources:
        next_pressure[gx, gy] += 1.2 * np.sin(pygame.time.get_ticks()/200.0)

    prev_pressure, pressure = pressure, next_pressure

def draw_canvas():
    arr = np.zeros((GRID_SIZE, GRID_SIZE, 3), dtype=np.uint8)
    norm = np.clip(pressure, -1.0, 1.0)
    arr[...,0] = (NEG_PRESSURE_COLOR[0]*(norm<0) + PRESSURE_COLOR[0]*(norm>0)) * np.abs(norm)
    arr[...,1] = (NEG_PRESSURE_COLOR[1]*(norm<0) + PRESSURE_COLOR[1]*(norm>0)) * np.abs(norm)
    arr[...,2] = (NEG_PRESSURE_COLOR[2]*(norm<0) + PRESSURE_COLOR[2]*(norm>0)) * np.abs(norm)

    surf = pygame.surfarray.make_surface(np.flipud(np.transpose(arr, (1,0,2))))
    surf = pygame.transform.scale(surf, (WIDTH, HEIGHT-BTN_H))
    screen.blit(surf, (0, BTN_H))

    # Draw source markers
    for gx, gy in sources:
        x = gx*CELL_SIZE_X + CELL_SIZE_X//2
        y = gy*CELL_SIZE_Y + BTN_H + CELL_SIZE_Y//2
        pygame.draw.circle(screen, (255,255,0), (x, y), max(CELL_SIZE_X//2,4), 2)

def handle_tap(x, y):
    global mode, pressure
    # Check if tap on button
    for i, rect in enumerate(buttons):
        if rect.collidepoint(x, y):
            set_mode(i)
            return

    # Otherwise, handle tap in canvas
    if y < BTN_H: return
    gx, gy = grid_from_xy(x, y)
    if mode == 0:
        # CLAP: Add high pressure impulse
        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            pressure[gx, gy] += 5.0
    elif mode == 1:
        # ADD: Place persistent source if not too close to another
        if all(np.hypot(gx-sx, gy-sy) > 2 for sx, sy in sources):
            sources.append((gx, gy))
    elif mode == 2:
        # REMOVE: Remove nearest source if close
        if sources:
            dists = [np.hypot(gx-sx, gy-sy) for sx, sy in sources]
            imin = int(np.argmin(dists))
            if dists[imin] < 4:
                sources.pop(imin)

def set_mode(new_mode):
    global mode
    mode = new_mode

def main():
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                handle_tap(mx, my)

        update_wave()
        screen.fill(BG_COLOR)
        draw_canvas()
        draw_buttons()
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()