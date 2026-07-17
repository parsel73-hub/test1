from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import math
import random

Color = Tuple[int, int, int]
Vec2 = Tuple[float, float]

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

INVENTORY_RADIUS = 24.0
BALL_RADIUS = 16.0
BALL_SPEED = 180.0

DELETE_ZONE_WIDTH = 140
DELETE_ZONE_HEIGHT = 140


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def mix_colors(c1: Color, c2: Color) -> Color:
    r = (c1[0] + c2[0]) // 2
    g = (c1[1] + c2[1]) // 2
    b = (c1[2] + c2[2]) // 2
    mixed = (r, g, b)

    if mixed == c1 or mixed == c2:
        mixed = (
            int(lerp(mixed[0], random.randint(0, 255), 0.15)),
            int(lerp(mixed[1], random.randint(0, 255), 0.15)),
            int(lerp(mixed[2], random.randint(0, 255), 0.15)),
        )

    return tuple(clamp(x, 0, 255) for x in mixed)  # type: ignore


def color_quality(c: Color) -> float:
    return (max(c) - min(c)) / 255.0


@dataclass
class Ball:
    x: float
    y: float
    vx: float
    vy: float
    color: Color
    radius: float = BALL_RADIUS
    held: bool = False
    in_inventory: bool = False
    removed: bool = False
    id: int = field(default_factory=lambda: random.randint(1, 1_000_000_000))

    @property
    def pos(self) -> Vec2:
        return self.x, self.y

    @pos.setter
    def pos(self, value: Vec2) -> None:
        self.x, self.y = value


class BallLogic:
    def __init__(self, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.balls: List[Ball] = []
        self.inventory: List[Ball] = []
        self.mouse_ball: Optional[Ball] = None
        self.mouse_pos: Vec2 = (width / 2, height / 2)
        self.delete_zone = (0, 0, DELETE_ZONE_WIDTH, DELETE_ZONE_HEIGHT)

    def spawn_ball(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        color: Optional[Color] = None
    ) -> Ball:
        x = self.width / 2 if x is None else x
        y = self.height / 2 if y is None else y
        angle = random.random() * math.tau
        speed = BALL_SPEED * (0.6 + random.random() * 0.8)
        ball = Ball(
            x=x,
            y=y,
            vx=math.cos(angle) * speed,
            vy=math.sin(angle) * speed,
            color=color or self.random_color(),
        )
        self.balls.append(ball)
        return ball

    def random_color(self) -> Color:
        palette = [
            (255, 80, 80),
            (80, 180, 255),
            (110, 255, 140),
            (255, 190, 70),
            (200, 90, 255),
        ]
        return random.choice(palette)

    def set_mouse_pos(self, x: float, y: float) -> None:
        self.mouse_pos = (x, y)
        if self.mouse_ball and self.mouse_ball.held:
            self.mouse_ball.pos = (x, y)

    def grab_ball(self) -> Optional[Ball]:
        if self.mouse_ball is not None:
            return self.mouse_ball

        x, y = self.mouse_pos
        candidate = self._nearest_ball(x, y, INVENTORY_RADIUS)
        if candidate:
            candidate.held = True
            candidate.in_inventory = True
            candidate.vx = 0.0
            candidate.vy = 0.0
            self.mouse_ball = candidate
            return candidate
        return None

    def release_ball(self, x: Optional[float] = None, y: Optional[float] = None) -> Optional[Ball]:
        if self.mouse_ball is None:
            return None

        ball = self.mouse_ball
        self.mouse_ball = None
        ball.held = False
        if x is not None and y is not None:
            ball.pos = (x, y)
        ball.in_inventory = False
        ball.vx = random.uniform(-1, 1) * BALL_SPEED
        ball.vy = random.uniform(-1, 1) * BALL_SPEED
        return ball

    def send_to_inventory(self, ball: Ball) -> None:
        if ball not in self.inventory:
            self.inventory.append(ball)
        ball.in_inventory = True
        ball.held = False
        ball.vx = 0.0
        ball.vy = 0.0

    def spit_from_inventory(
        self,
        count: int = 1,
        x: Optional[float] = None,
        y: Optional[float] = None
    ) -> List[Ball]:
        released: List[Ball] = []
        x = self.width / 2 if x is None else x
        y = self.height / 2 if y is None else y

        for _ in range(min(count, len(self.inventory))):
            ball = self.inventory.pop(0)
            ball.in_inventory = False
            ball.pos = (x + random.uniform(-20, 20), y + random.uniform(-20, 20))
            angle = random.random() * math.tau
            ball.vx = math.cos(angle) * BALL_SPEED
            ball.vy = math.sin(angle) * BALL_SPEED
            released.append(ball)

        return released

    def remove_in_delete_zone(self) -> List[Ball]:
        x, y, w, h = self.delete_zone
        removed: List[Ball] = []

        for ball in list(self.balls):
            if x <= ball.x <= x + w and y <= ball.y <= y + h:
                ball.removed = True
                self.balls.remove(ball)
                if ball in self.inventory:
                    self.inventory.remove(ball)
                if ball is self.mouse_ball:
                    self.mouse_ball = None
                removed.append(ball)

        return removed

    def update(self, dt: float) -> None:
        for ball in self.balls:
            if ball.removed or ball.held or ball.in_inventory:
                continue

            ball.x += ball.vx * dt
            ball.y += ball.vy * dt

            if ball.x - ball.radius < 0:
                ball.x = ball.radius
                ball.vx *= -1
            if ball.x + ball.radius > self.width:
                ball.x = self.width - ball.radius
                ball.vx *= -1
            if ball.y - ball.radius < 0:
                ball.y = ball.radius
                ball.vy *= -1
            if ball.y + ball.radius > self.height:
                ball.y = self.height - ball.radius
                ball.vy *= -1

        self._handle_collisions()
        self.remove_in_delete_zone()

        if self.mouse_ball and self.mouse_ball.held:
            self.mouse_ball.pos = self.mouse_pos

    def _handle_collisions(self) -> None:
        active = [b for b in self.balls if not b.removed and not b.in_inventory and not b.held]

        for i in range(len(active)):
            a = active[i]
            for j in range(i + 1, len(active)):
                b = active[j]
                dx = b.x - a.x
                dy = b.y - a.y
                dist = math.hypot(dx, dy)
                min_dist = a.radius + b.radius

                if 0 < dist <= min_dist:
                    t = 1.0 - clamp(dist / min_dist, 0.0, 1.0)
                    if dist == 0:
                        nx, ny = 1.0, 0.0
                    else:
                        nx, ny = dx / dist, dy / dist

                    mix_strength = 0.18 + 0.52 * t
                    new_color = mix_colors(a.color, b.color)
                    a.color = self._blend_toward(a.color, new_color, mix_strength)
                    b.color = self._blend_toward(b.color, new_color, mix_strength)

                    overlap = min_dist - dist
                    shift = overlap / 2
                    a.x -= nx * shift
                    a.y -= ny * shift
                    b.x += nx * shift
                    b.y += ny * shift

    def _blend_toward(self, src: Color, dst: Color, t: float) -> Color:
        return (
            int(lerp(src[0], dst[0], t)),
            int(lerp(src[1], dst[1], t)),
            int(lerp(src[2], dst[2], t)),
        )

    def _nearest_ball(self, x: float, y: float, max_distance: float) -> Optional[Ball]:
        best = None
        best_dist = max_distance

        for ball in self.balls:
            if ball.removed or ball.in_inventory or ball.held:
                continue
            d = math.hypot(ball.x - x, ball.y - y)
            if d <= best_dist:
                best = ball
                best_dist = d

        return best

    def score_ball(self, ball: Ball) -> float:
        return color_quality(ball.color)

    def clear(self) -> None:
        self.balls.clear()
        self.inventory.clear()
        self.mouse_ball = None

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import math
import random

Color = Tuple[int, int, int]
Vec2 = Tuple[float, float]

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

INVENTORY_RADIUS = 24.0
BALL_RADIUS = 16.0
BALL_SPEED = 180.0

DELETE_ZONE_WIDTH = 140
DELETE_ZONE_HEIGHT = 140


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def mix_colors(c1: Color, c2: Color) -> Color:
    r = (c1[0] + c2[0]) // 2
    g = (c1[1] + c2[1]) // 2
    b = (c1[2] + c2[2]) // 2
    mixed = (r, g, b)

    if mixed == c1 or mixed == c2:
        mixed = (
            int(lerp(mixed[0], random.randint(0, 255), 0.15)),
            int(lerp(mixed[1], random.randint(0, 255), 0.15)),
            int(lerp(mixed[2], random.randint(0, 255), 0.15)),
        )

    return tuple(clamp(x, 0, 255) for x in mixed)  # type: ignore


def color_quality(c: Color) -> float:
    return (max(c) - min(c)) / 255.0


@dataclass
class Ball:
    x: float
    y: float
    vx: float
    vy: float
    color: Color
    radius: float = BALL_RADIUS
    held: bool = False
    in_inventory: bool = False
    removed: bool = False
    id: int = field(default_factory=lambda: random.randint(1, 1_000_000_000))

    @property
    def pos(self) -> Vec2:
        return self.x, self.y

    @pos.setter
    def pos(self, value: Vec2) -> None:
        self.x, self.y = value


class BallLogic:
    def __init__(self, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.balls: List[Ball] = []
        self.inventory: List[Ball] = []
        self.mouse_ball: Optional[Ball] = None
        self.mouse_pos: Vec2 = (width / 2, height / 2)
        self.delete_zone = (0, 0, DELETE_ZONE_WIDTH, DELETE_ZONE_HEIGHT)

    def spawn_ball(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        color: Optional[Color] = None
    ) -> Ball:
        x = self.width / 2 if x is None else x
        y = self.height / 2 if y is None else y
        angle = random.random() * math.tau
        speed = BALL_SPEED * (0.6 + random.random() * 0.8)
        ball = Ball(
            x=x,
            y=y,
            vx=math.cos(angle) * speed,
            vy=math.sin(angle) * speed,
            color=color or self.random_color(),
        )
        self.balls.append(ball)
        return ball

    def random_color(self) -> Color:
        palette = [
            (255, 80, 80),
            (80, 180, 255),
            (110, 255, 140),
            (255, 190, 70),
            (200, 90, 255),
        ]
        return random.choice(palette)

    def set_mouse_pos(self, x: float, y: float) -> None:
        self.mouse_pos = (x, y)
        if self.mouse_ball and self.mouse_ball.held:
            self.mouse_ball.pos = (x, y)

    def grab_ball(self) -> Optional[Ball]:
        if self.mouse_ball is not None:
            return self.mouse_ball

        x, y = self.mouse_pos
        candidate = self._nearest_ball(x, y, INVENTORY_RADIUS)
        if candidate:
            candidate.held = True
            candidate.in_inventory = True
            candidate.vx = 0.0
            candidate.vy = 0.0
            self.mouse_ball = candidate
            return candidate
        return None

    def release_ball(self, x: Optional[float] = None, y: Optional[float] = None) -> Optional[Ball]:
        if self.mouse_ball is None:
            return None

        ball = self.mouse_ball
        self.mouse_ball = None
        ball.held = False
        if x is not None and y is not None:
            ball.pos = (x, y)
        ball.in_inventory = False
        ball.vx = random.uniform(-1, 1) * BALL_SPEED
        ball.vy = random.uniform(-1, 1) * BALL_SPEED
        return ball

    def send_to_inventory(self, ball: Ball) -> None:
        if ball not in self.inventory:
            self.inventory.append(ball)
        ball.in_inventory = True
        ball.held = False
        ball.vx = 0.0
        ball.vy = 0.0

    def spit_from_inventory(
        self,
        count: int = 1,
        x: Optional[float] = None,
        y: Optional[float] = None
    ) -> List[Ball]:
        released: List[Ball] = []
        x = self.width / 2 if x is None else x
        y = self.height / 2 if y is None else y

        for _ in range(min(count, len(self.inventory))):
            ball = self.inventory.pop(0)
            ball.in_inventory = False
            ball.pos = (x + random.uniform(-20, 20), y + random.uniform(-20, 20))
            angle = random.random() * math.tau
            ball.vx = math.cos(angle) * BALL_SPEED
            ball.vy = math.sin(angle) * BALL_SPEED
            released.append(ball)

        return released

    def remove_in_delete_zone(self) -> List[Ball]:
        x, y, w, h = self.delete_zone
        removed: List[Ball] = []

        for ball in list(self.balls):
            if x <= ball.x <= x + w and y <= ball.y <= y + h:
                ball.removed = True
                self.balls.remove(ball)
                if ball in self.inventory:
                    self.inventory.remove(ball)
                if ball is self.mouse_ball:
                    self.mouse_ball = None
                removed.append(ball)

        return removed

    def update(self, dt: float) -> None:
        for ball in self.balls:
            if ball.removed or ball.held or ball.in_inventory:
                continue

            ball.x += ball.vx * dt
            ball.y += ball.vy * dt

            if ball.x - ball.radius < 0:
                ball.x = ball.radius
                ball.vx *= -1
            if ball.x + ball.radius > self.width:
                ball.x = self.width - ball.radius
                ball.vx *= -1
            if ball.y - ball.radius < 0:
                ball.y = ball.radius
                ball.vy *= -1
            if ball.y + ball.radius > self.height:
                ball.y = self.height - ball.radius
                ball.vy *= -1

        self._handle_collisions()
        self.remove_in_delete_zone()

        if self.mouse_ball and self.mouse_ball.held:
            self.mouse_ball.pos = self.mouse_pos

    def _handle_collisions(self) -> None:
        active = [b for b in self.balls if not b.removed and not b.in_inventory and not b.held]

        for i in range(len(active)):
            a = active[i]
            for j in range(i + 1, len(active)):
                b = active[j]
                dx = b.x - a.x
                dy = b.y - a.y
                dist = math.hypot(dx, dy)
                min_dist = a.radius + b.radius

                if 0 < dist <= min_dist:
                    t = 1.0 - clamp(dist / min_dist, 0.0, 1.0)
                    if dist == 0:
                        nx, ny = 1.0, 0.0
                    else:
                        nx, ny = dx / dist, dy / dist

                    mix_strength = 0.18 + 0.52 * t
                    new_color = mix_colors(a.color, b.color)
                    a.color = self._blend_toward(a.color, new_color, mix_strength)
                    b.color = self._blend_toward(b.color, new_color, mix_strength)

                    overlap = min_dist - dist
                    shift = overlap / 2
                    a.x -= nx * shift
                    a.y -= ny * shift
                    b.x += nx * shift
                    b.y += ny * shift

    def _blend_toward(self, src: Color, dst: Color, t: float) -> Color:
        return (
            int(lerp(src[0], dst[0], t)),
            int(lerp(src[1], dst[1], t)),
            int(lerp(src[2], dst[2], t)),
        )

    def _nearest_ball(self, x: float, y: float, max_distance: float) -> Optional[Ball]:
        best = None
        best_dist = max_distance

        for ball in self.balls:
            if ball.removed or ball.in_inventory or ball.held:
                continue
            d = math.hypot(ball.x - x, ball.y - y)
            if d <= best_dist:
                best = ball
                best_dist = d

        return best

    def score_ball(self, ball: Ball) -> float:
        return color_quality(ball.color)

    def clear(self) -> None:
        self.balls.clear()
        self.inventory.clear()
        self.mouse_ball = None