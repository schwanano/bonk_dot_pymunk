import pygame
import pygame as pyg
import pymunk
import pymunk.pygame_util as pgut
import math
import glob
import os
import sys
from pygame.math import Vector2

pyg.init()
pyg.font.init()

# Global variables for script execution context
global_movement = Vector2()

# Display Setup
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
screen = pyg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pyg.display.set_caption("BONK.PYGM - Map Viewer")

display_info = pyg.display.Info()
display_size = Vector2(display_info.current_w, display_info.current_h)
surf_size = Vector2(screen.get_size())
pyg.display.set_window_position(tuple((display_size - surf_size) / 2))


class Player:
    group = []
    score = {}
    count = 0

    def __init__(self, pid, pos_x, pos_y, col, *args, radius=20, **kwargs):
        self.pid = pid
        self.col = col
        self.radius = radius

        self.body = pymunk.Body(radius, 1)
        self.body.position = (pos_x, pos_y)
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.data = self
        Player.group.append(self)

    def render(self, surf, cam_offset):
        view_pos = self.body.position - cam_offset
        render_pos = pgut.to_pygame(view_pos, surf)
        
        # Draw player spawn body
        pyg.draw.circle(surf, self.col, render_pos, self.radius)
        pyg.draw.circle(surf, "black", render_pos, self.radius, 2)

        # Draw Player ID label
        font = pyg.font.SysFont("Comic Sans MS", 16, bold=True)
        text = font.render(self.pid, True, "white")
        text_rect = text.get_rect(center=render_pos)
        surf.blit(text, text_rect)


class Rect:
    group = []

    def __init__(self, col, center, width, height,
                 facing=0, bouncy=False, rotation=False, movement=False, death=False):
        self.width = width
        self.height = height
        self.facing = facing
        self.color = pyg.Color(col)
        self.bouncy = bouncy
        if isinstance(self.bouncy, (int, float)):
            self.bouncy *= 0.7

        self.do_update = bool(rotation or movement)
        self.rotating = rotation
        self.moving = movement
        self.death = death

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.shape = pymunk.Poly.create_box(self.body, (self.width, self.height))
        self.shape.data = self
        self.shape.body.position = tuple(center)
        self.shape.body.angle = -math.radians(facing)

        if self.do_update:
            if self.rotating:
                if not self.rotating[0]:
                    self.orb_center = self.shape.body.position
                else:
                    self.orb_center = Vector2(self.rotating[0])
                self.orb_speed = self.rotating[1]
                self.rot_speed = self.rotating[2]
                self.defalut_vector_length = Vector2(center - self.orb_center).length()

            if self.moving:
                self.min_pos = Vector2(self.moving[0])
                self.max_pos = Vector2(self.moving[1])
                self.speed = Vector2(self.moving[2])

        Rect.group.append(self)

    def render(self, surf, cam_offset):
        points = self.shape.get_vertices()
        world_points = []
        for point in points:
            world_point = self.shape.body.local_to_world(point)
            view_point = world_point - cam_offset
            world_points.append(pgut.to_pygame(view_point, surf))

        pyg.draw.polygon(surf, self.color, world_points)
        if self.bouncy:
            pyg.draw.aalines(surf, "black", True, world_points)
        if self.death:
            pyg.draw.aalines(surf, "red", True, world_points)

    def rotation(self, dt):
        if self.rotating[0] and self.rotating[1]:
            direction = Vector2(self.shape.body.position - self.orb_center)
            length = direction.length()
            if length > 0:
                direction = direction.normalize()
                interpolation = (length - self.defalut_vector_length) / self.defalut_vector_length if self.defalut_vector_length else 0
                if self.orb_speed < 0:
                    direction.rotate_ip(90 + interpolation * 360)
                    self.body.velocity = tuple(direction * length * -self.orb_speed)
                else:
                    direction.rotate_ip(-90 - interpolation * 360)
                    self.body.velocity = tuple(direction * length * self.orb_speed)
        self.body.angular_velocity = self.rot_speed

    def movement(self, dt):
        if self.min_pos.x > self.shape.body.position.x:
            self.speed.x = abs(self.speed.x)
        elif self.max_pos.x < self.shape.body.position.x:
            self.speed.x = -abs(self.speed.x)
        if self.min_pos.y > self.shape.body.position.y:
            self.speed.y = abs(self.speed.y)
        elif self.max_pos.y < self.shape.body.position.y:
            self.speed.y = -abs(self.speed.y)

        self.body.velocity = tuple(self.speed)

    def update(self, dt):
        if self.do_update:
            if self.rotating:
                self.rotation(dt)
            if self.moving:
                self.movement(dt)


class Line:
    def __init__(self, col, pos1, pos2, width=10,
                 bouncy=False, rotation=False, movement=False, death=False):
        pos1, pos2 = Vector2(pos1), Vector2(pos2)
        self.center = (pos1 + pos2) / 2
        self.width = (pos2 - pos1).length()
        self.height = width
        self.facing = (pos2 - pos1).angle
        self.color = pyg.Color(col)
        self.bouncy = bouncy
        if isinstance(self.bouncy, (int, float)):
            self.bouncy *= 0.7

        self.do_update = bool(rotation or movement)
        self.rotating = rotation
        self.moving = movement
        self.death = death

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.shape = pymunk.Poly.create_box(self.body, (self.width, self.height))
        self.shape.data = self
        self.shape.body.position = tuple(self.center)
        self.shape.body.angle = math.radians(self.facing)

        if self.do_update:
            if self.rotating:
                if not self.rotating[0]:
                    self.orb_center = self.shape.body.position
                else:
                    self.orb_center = Vector2(self.rotating[0])
                self.orb_speed = self.rotating[1]
                self.rot_speed = self.rotating[2]

            if self.moving:
                self.min_pos = Vector2(self.moving[0])
                self.max_pos = Vector2(self.moving[1])
                self.speed = Vector2(self.moving[2])

        Rect.group.append(self)

    def render(self, surf, cam_offset):
        points = self.shape.get_vertices()
        world_points = []
        for point in points:
            world_point = self.shape.body.local_to_world(point)
            view_point = world_point - cam_offset
            world_points.append(pgut.to_pygame(view_point, surf))

        pyg.draw.polygon(surf, self.color, world_points)
        if self.bouncy:
            pyg.draw.aalines(surf, "black", True, world_points)
        if self.death:
            pyg.draw.aalines(surf, "red", True, world_points)

    def rotation(self, dt):
        if self.rotating[0] and self.rotating[1]:
            direction = Vector2(self.shape.body.position - self.orb_center)
            length = direction.length()
            if length > 0:
                direction = direction.normalize()
                interpolation = (length - self.defalut_vector_length) / self.defalut_vector_length if self.defalut_vector_length else 0
                if self.orb_speed < 0:
                    direction.rotate_ip(90 + interpolation * 360)
                    self.body.velocity = tuple(direction * length * -self.orb_speed)
                else:
                    direction.rotate_ip(-90 - interpolation * 360)
                    self.body.velocity = tuple(direction * length * self.orb_speed)
        self.body.angular_velocity = self.rot_speed

    def movement(self, dt):
        if self.min_pos.x > self.shape.body.position.x:
            self.speed.x = abs(self.speed.x)
        elif self.max_pos.x < self.shape.body.position.x:
            self.speed.x = -abs(self.speed.x)
        if self.min_pos.y > self.shape.body.position.y:
            self.speed.y = abs(self.speed.y)
        elif self.max_pos.y < self.shape.body.position.y:
            self.speed.y = -abs(self.speed.y)

        self.body.velocity = tuple(self.speed)

    def update(self, dt):
        if self.do_update:
            if self.rotating:
                self.rotation(dt)
            if self.moving:
                self.movement(dt)


def find_map_files():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    maps = glob.glob(f"{dir_path}/maps/*.txt") + glob.glob(f"{dir_path}/maps/Used/*.txt")
    if not maps:
        maps = glob.glob(f"{dir_path}/*.txt")
    return sorted(list(set(maps)))


def load_map(file_path, space):
    global global_movement
    global_movement = Vector2()

    Player.group.clear()
    Rect.group.clear()

    # Reset space
    for shape in list(space.shapes):
        space.remove(shape)
    for body in list(space.bodies):
        space.remove(body)

    players = {}
    rects = {}

    bonk_map = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if "\\" in line:
                break
            bonk_map.append(line)

    exec_env = {
        "players": players,
        "rects": rects,
        "Player": Player,
        "Rect": Rect,
        "Line": Line,
        "pygame": pyg,
        "pyg": pyg,
        "Vector2": Vector2,
        "math": math,
        "global_movement": global_movement,
    }

    exec("".join(bonk_map), exec_env)

    for p in Player.group:
        space.add(p.shape, p.body)
    for r in Rect.group:
        space.add(r.shape, r.body)


def main():
    pgut.positive_y_is_up = True
    space = pymunk.Space()

    map_files = find_map_files()
    if not map_files:
        print("No map files found!")
        pyg.quit()
        return

    current_map_idx = 0
    load_map(map_files[current_map_idx], space)

    camera_pos = Vector2(640, 360)
    camera_speed = 500
    is_paused = False

    clock = pyg.time.Clock()
    font = pyg.font.SysFont("Consolas", 18, bold=True)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pyg.event.get():
            if event.type == pyg.QUIT:
                running = False

            elif event.type == pyg.KEYDOWN:
                if event.key == pyg.K_ESCAPE:
                    running = False
                elif event.key in (pyg.K_RIGHTBRACKET, pyg.K_n):
                    current_map_idx = (current_map_idx + 1) % len(map_files)
                    load_map(map_files[current_map_idx], space)
                    camera_pos = Vector2(640, 360)
                elif event.key in (pyg.K_LEFTBRACKET, pyg.K_p):
                    current_map_idx = (current_map_idx - 1) % len(map_files)
                    load_map(map_files[current_map_idx], space)
                    camera_pos = Vector2(640, 360)
                elif event.key == pyg.K_r:
                    camera_pos = Vector2(640, 360)
                elif event.key == pyg.K_SPACE:
                    is_paused = not is_paused

        # Camera Movement Logic
        keys = pyg.key.get_pressed()
        speed = camera_speed * (2.5 if keys[pyg.K_LSHIFT] or keys[pyg.K_RSHIFT] else 1.0)

        if keys[pyg.K_LEFT]:
            camera_pos.x -= speed * dt
        if keys[pyg.K_RIGHT]:
            camera_pos.x += speed * dt
        if keys[pyg.K_UP]:
            camera_pos.y += speed * dt
        if keys[pyg.K_DOWN]:
            camera_pos.y -= speed * dt

        # Physics/Animation Step
        if not is_paused and dt < 0.1:
            for rect in Rect.group:
                if rect.do_update:
                    rect.update(dt)
            space.step(dt)

        cam_offset = camera_pos - Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

        screen.fill((230, 230, 230))

        # Render Game Geometry
        for rect in Rect.group:
            rect.render(screen, cam_offset)
        for player in Player.group:
            player.render(screen, cam_offset)

        # Render HUD Overlay
        map_name = os.path.basename(map_files[current_map_idx])
        hud_lines = [
            f"Map [{current_map_idx + 1}/{len(map_files)}]: {map_name}",
            f"Camera Center: ({int(camera_pos.x)}, {int(camera_pos.y)})",
            "---------------------------------------",
            "Arrow Keys: Pan Camera (Hold SHIFT: Fast)",
            "N / ] : Next Map | P / [ : Prev Map",
            "SPACE: Toggle Animation Pause | R: Reset Cam",
        ]

        overlay = pyg.Surface((440, 130), pyg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (10, 10))

        for idx, line in enumerate(hud_lines):
            color = (255, 255, 0) if idx == 0 else (255, 255, 255)
            text_surface = font.render(line, True, color)
            screen.blit(text_surface, (20, 15 + idx * 18))

        pyg.display.flip()

    pyg.quit()


if __name__ == "__main__":
    main()