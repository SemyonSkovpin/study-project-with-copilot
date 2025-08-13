import pygame
import sys
from sound-sim-v3.sim_core import Canvas, advance_canvas, handle_input

CANVAS_WIDTH = 320
CANVAS_HEIGHT = 240

MODES = ["pulse", "consistent", "remove"]
BUTTON_HEIGHT = 60   # Height of the button row

def map_screen_to_canvas(touch_x, touch_y, display_width, display_height, canvas_width, canvas_height):
    scale = min(display_width / canvas_width, (display_height - BUTTON_HEIGHT) / canvas_height)
    scaled_width = int(canvas_width * scale)
    scaled_height = int(canvas_height * scale)
    x_offset = (display_width - scaled_width) // 2
    y_offset = (display_height - BUTTON_HEIGHT - scaled_height) // 2

    if (x_offset <= touch_x < x_offset + scaled_width and
        y_offset <= touch_y < y_offset + scaled_height):
        canvas_x = int((touch_x - x_offset) / scale)
        canvas_y = int((touch_y - y_offset) / scale)
        return (canvas_x, canvas_y)
    else:
        return None

def get_button_rects(display_width, display_height):
    btn_width = display_width // 3
    rects = []
    for i in range(3):
        rect = pygame.Rect(i * btn_width, display_height - BUTTON_HEIGHT, btn_width, BUTTON_HEIGHT)
        rects.append(rect)
    return rects

def render_canvas(surface, canvas):
    array = canvas.pressure
    arr_min, arr_max = array.min(), array.max()
    if arr_max - arr_min < 1e-5:
        arr_max = arr_min + 1e-5
    norm = (array - arr_min) / (arr_max - arr_min)
    img = (norm * 255).astype('uint8')
    rgb_img = pygame.surfarray.make_surface(
        img.repeat(3).reshape((canvas.width, canvas.height, 3)).swapaxes(0, 1)
    )
    surface.blit(rgb_img, (0, 0))

def draw_buttons(screen, mode, font):
    display_width, display_height = screen.get_size()
    rects = get_button_rects(display_width, display_height)
    colors = [(150,200,255), (180,255,180), (255,200,200)]
    active_colors = [(30,90,200), (40,140,40), (180,40,40)]
    for i, rect in enumerate(rects):
        color = active_colors[i] if MODES[i] == mode else colors[i]
        pygame.draw.rect(screen, color, rect)
        label = font.render(MODES[i].capitalize(), True, (0,0,0))
        label_rect = label.get_rect(center=rect.center)
        screen.blit(label, label_rect)
    return rects

def main():
    pygame.init()
    pygame.display.set_caption("Sound Simulation")
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    font = pygame.font.SysFont(None, 36)
    clock = pygame.time.Clock()

    canvas = Canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    sim_time = 0.0
    mode = "pulse"
    canvas_surface = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))

    while True:
        display_width, display_height = screen.get_size()
        scale = min(display_width / CANVAS_WIDTH, (display_height - BUTTON_HEIGHT) / CANVAS_HEIGHT)
        scaled_width = int(CANVAS_WIDTH * scale)
        scaled_height = int(CANVAS_HEIGHT * scale)
        x_offset = (display_width - scaled_width) // 2
        y_offset = (display_height - BUTTON_HEIGHT - scaled_height) // 2

        button_rects = get_button_rects(display_width, display_height)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                if event.type == pygame.FINGERDOWN:
                    tx = int(event.x * display_width)
                    ty = int(event.y * display_height)
                else:
                    tx, ty = event.pos

                # Check if a button was pressed
                for i, rect in enumerate(button_rects):
                    if rect.collidepoint(tx, ty):
                        mode = MODES[i]
                        break
                else:
                    mapped = map_screen_to_canvas(
                        tx, ty,
                        display_width, display_height,
                        CANVAS_WIDTH, CANVAS_HEIGHT
                    )
                    if mapped:
                        x, y = mapped
                        handle_input(canvas, x, y, mode)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    mode = "pulse"
                elif event.key == pygame.K_2:
                    mode = "consistent"
                elif event.key == pygame.K_3:
                    mode = "remove"
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        advance_canvas(canvas, time=sim_time)
        sim_time += 1.0

        render_canvas(canvas_surface, canvas)

        # Draw scaled simulation
        scaled_surf = pygame.transform.smoothscale(canvas_surface, (scaled_width, scaled_height))
        screen.fill((0, 0, 0))
        screen.blit(scaled_surf, (x_offset, y_offset))

        # Draw buttons at the bottom
        draw_buttons(screen, mode, font)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()