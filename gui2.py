import math
import pygame

from logic import BallLogic, BALL_RADIUS, DELETE_ZONE_WIDTH, DELETE_ZONE_HEIGHT

WIDTH = 1280
HEIGHT = 720
FPS = 60
START_BALLS = 18

WHITE = (255, 255, 255)
BLACK = (25, 25, 25)
DELETE_BG = (255, 235, 235)
DELETE_BORDER = (220, 90, 90)
DELETE_TEXT = (140, 40, 40)
INVENTORY_PANEL = (245, 245, 245)
INVENTORY_BORDER = (210, 210, 210)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball Logic Playground")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 18)
small_font = pygame.font.SysFont("arial", 14)

logic = BallLogic(WIDTH, HEIGHT)
for _ in range(START_BALLS):
    logic.spawn_ball(
        x=WIDTH * 0.2 + (_ % 6) * 120,
        y=HEIGHT * 0.25 + (_ // 6) * 120
    )

dragging = False
spit_cooldown = 0.0


def draw_ball(surface, ball):
    radius = int(ball.radius)
    pygame.draw.circle(surface, ball.color, (int(ball.x), int(ball.y)), radius)
    outline = tuple(max(0, c - 40) for c in ball.color)
    pygame.draw.circle(surface, outline, (int(ball.x), int(ball.y)), radius, 2)


def draw_hud(surface):
    inv_rect = pygame.Rect(12, HEIGHT - 62, 280, 48)
    pygame.draw.rect(surface, INVENTORY_PANEL, inv_rect, border_radius=12)
    pygame.draw.rect(surface, INVENTORY_BORDER, inv_rect, 1, border_radius=12)

    inv_text = font.render(f"Инвентарь: {len(logic.inventory)}", True, BLACK)
    balls_text = font.render(f"Шариков на поле: {len(logic.balls)}", True, BLACK)
    surface.blit(inv_text, (24, HEIGHT - 52))
    surface.blit(balls_text, (150, HEIGHT - 52))

    hint = small_font.render("ЛКМ: взять / отпустить   ПКМ: вернуть в инвентарь   Колесо: выплюнуть 1", True, (80, 80, 80))
    surface.blit(hint, (320, HEIGHT - 48))


running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    spit_cooldown = max(0.0, spit_cooldown - dt)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEMOTION:
            logic.set_mouse_pos(*event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            logic.set_mouse_pos(*event.pos)
            if event.button == 1:
                if logic.mouse_ball is None:
                    grabbed = logic.grab_ball()
                    if grabbed is not None:
                        dragging = True
                else:
                    dragging = True

            elif event.button == 3:
                if logic.mouse_ball is not None:
                    logic.send_to_inventory(logic.mouse_ball)
                    logic.mouse_ball = None
                    dragging = False
                else:
                    grabbed = logic.grab_ball()
                    if grabbed is not None:
                        logic.send_to_inventory(grabbed)
                        logic.mouse_ball = None

            elif event.button in (4, 5):
                if spit_cooldown <= 0.0 and logic.inventory:
                    logic.spit_from_inventory(count=1, x=event.pos[0], y=event.pos[1])
                    spit_cooldown = 0.12

        elif event.type == pygame.MOUSEBUTTONUP:
            logic.set_mouse_pos(*event.pos)
            if event.button == 1 and dragging:
                logic.release_ball(*event.pos)
                dragging = False

    logic.update(dt)

    screen.fill(WHITE)

    x, y, w, h = logic.delete_zone
    delete_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, DELETE_BG, delete_rect)
    pygame.draw.rect(screen, DELETE_BORDER, delete_rect, 3)
    pygame.draw.line(screen, DELETE_BORDER, (10, 10), (x + w - 10, y + h - 10), 4)
    pygame.draw.line(screen, DELETE_BORDER, (x + w - 10, 10), (10, y + h - 10), 4)

    label = font.render("ЗОНА УДАЛЕНИЯ", True, DELETE_TEXT)
    screen.blit(label, (14, 16))

    for ball in logic.balls:
        if not ball.removed:
            draw_ball(screen, ball)

    if logic.mouse_ball is not None and logic.mouse_ball.held:
        mx, my = logic.mouse_pos
        pulse_r = int(logic.mouse_ball.radius + 8 + 2 * math.sin(pygame.time.get_ticks() * 0.01))
        pygame.draw.circle(screen, (30, 30, 30), (int(mx), int(my)), pulse_r, 1)

    draw_hud(screen)
    pygame.display.flip()

pygame.quit()