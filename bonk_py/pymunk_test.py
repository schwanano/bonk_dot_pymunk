import pygame as pyg
import pymunk
import pymunk.pygame_util as pgut
import math
import glob, os, random

from pygame.math import Vector2     #pygame.math.Vector2() is too long

pyg.init()

#getting display size to set the position of window when creating a screen surface
display_info = pyg.display.Info()
display_size = Vector2(display_info.current_w, display_info.current_h)
def set_window_pos(surf):
    global display_info, display_size
    surf_size = Vector2(surf.get_size())
    display_pos = tuple((display_size - surf_size)/2)
    pyg.display.set_window_position(display_pos)


#the menu of the game, currently only has title and start button to start the simulation of pymunk
def menu():
    pyg.font.init()
    #title
    title_font_name = pyg.font.match_font('comic sans')     #i like comic sans
    title_font = pyg.font.Font(title_font_name, size = 50)  #big font
    title_text = "BONK.PYGM"    #bonk.py 'g'ame+'m'unk      #kinda looks like just pygame in short lol
    title = title_font.render(title_text, False, "black")

    #button rect
    start_button_rect = pyg.Rect(0, 0, 100, 30)
    #button text
    start_button_font = pyg.font.Font(title_font_name, size = 30)
    start_button = start_button_font.render(" start ", False, "black")
    start_button_rect = start_button.get_rect(center = start_button_rect.center)
 
    screen = pyg.display.set_mode((640, 480))   #the screen res for all
    set_window_pos(screen)  #moving window to the middle of the monitor
    run = 1     #RUN
    scr_size = Vector2(screen.get_size())   #too lazy to type screen.get_width() and screen.get_height() every time

    while run:      #actual loop
        mouse_pos = pyg.mouse.get_pos()
        click = False   #getting mouse click

        for event in pyg.event.get():
            if event.type == pyg.QUIT:
                run = 0
                return "quit"
            '''
            if event.type == pyg.VIDEORESIZE:
                w, h = event.dict['size'][0], event.dict['size'][1]
                if w/4 <= h/3:
                    w, h = w, w/4 * 3
                else:
                    w, h = h/3 * 4, h
                    screen = pyg.display.set_mode(
                        (w, h), flags = pyg.RESIZABLE
                        )
                scr_size = Vector2(screen.get_size())
                '''     #this is for the game window
            if event.type == pyg.MOUSEBUTTONDOWN and event.button == 1:
                click = True


        screen.fill("grey")

        #title and buttons
        title_pos = ((scr_size.x - title.get_width())/2, 125)
        screen.blit(title, title_pos)

        if start_button_rect.collidepoint(mouse_pos):
            pyg.draw.rect(screen, (220, 220, 220), start_button_rect)
            if click:
                game()
                break

        else:
            pyg.draw.rect(screen, (170, 170, 170), start_button_rect)
           

        start_button_rect.center = scr_size/2
        screen.blit(start_button, start_button_rect)
        
        pyg.display.flip()


def game():
    screen = pyg.display.set_mode((1280, 720))  #the superior scren res
    set_window_pos(screen)  #centering window

    pyg.font.init()
    font_name = pyg.font.match_font("MathJax_Typewriter")
    font = pyg.font.Font(font_name, 74)

    clock = pyg.time.Clock()
    dt = 0

    pgut.positive_y_is_up = True
    space = pymunk.Space()
    space.gravity = (0, -200)
    space.collision_bias = 0

    global round_over, pending_reset, reset_timer, global_movement
    global_movement = Vector2()

    #player and map
    Player.score = {}
    pos_reset(space)

    #used for post-round calls; points rendering, pos_reset, etc.
    round_over = False
    pending_reset = False
    reset_timer = 0

    run = 1     #run, b*tch, RUUUUN
    while run:
        for event in pyg.event.get():
            if event.type == pyg.QUIT:
                run = 0
            if event.type == pyg.VIDEORESIZE:
                w, h = event.dict['size'][0], event.dict['size'][1]
                if w/16 <= h/9:
                    w, h = w, w/16 * 9
                else:
                    w, h = h/9 * 16, h
                    screen = pyg.display.set_mode(
                        (w, h), flags = pyg.RESIZABLE
                        )

        if round_over:
            # Draw all player scores dynamically
            y_offset = 200
            for idx, p in enumerate(Player.group, start=1):
                pid = p.pid
                score = Player.score[pid]
                text_surface = font.render(f"{pid.upper()} : {score}", True, p.col, "grey")
                screen.blit(text_surface, (600, y_offset))
                y_offset += 60  # move down for the next player

            for p in Player.group:
                if Player.score[p.pid] >= 7:
                    win_surface = font.render(f"{p.pid.upper()} win!", True, "white", "black")
                    screen.blit(win_surface, (550, 600))
                    pyg.display.flip()

                    end_time = pyg.time.get_ticks() + 3000
                    while pyg.time.get_ticks() < end_time:
                        for event in pyg.event.get():
                            if event.type == pyg.QUIT:
                                pyg.quit()
                                run = 0
                        clock.tick(60)

                    run = 0

            if pending_reset and pyg.time.get_ticks() >= reset_timer:
                pending_reset = False
                round_over = False
                global_movement = Vector2()
                pos_reset(space)
            
        else:
            global map_display_name, map_display_timer
            current_time = pyg.time.get_ticks()

            screen.fill("white")


            if current_time < map_display_timer:
                for rect in Rect.group:
                    rect.render(screen)
                for player in Player.group:
                    player.render(screen)

                map_surface = font.render(map_display_name.upper(), True, "black", 'grey')
                map_rect = map_surface.get_rect(center=(640, 360))
                screen.blit(map_surface, map_rect)

            else:
                dt = clock.tick(60) / 1000
                
                if dt < 0.1:
                    Rect.cycle(screen, dt)
                    Player.cycle(screen, space, dt)

                    if global_movement:
                        for rect in Rect.group:
                            rect.body.position += global_movement * dt
                            if rect.moving:
                                rect.min_pos += global_movement * dt
                                rect.max_pos += global_movement * dt
                            if rect.rotating:
                                rect.orb_center += global_movement * dt
                        for player in Player.group:
                            player.body.position += global_movement * dt
                    
                    space.step(dt)
                    win_lose()
                    #fps
                    fps(screen, dt)

        pyg.display.flip()

#map loading; shutil is innocent!
def pos_reset(space):
    import shutil
    global players, rects, map_display_name, map_display_timer
    import pygame

    dir_path = os.path.dirname(os.path.realpath(__file__))
    

    for p in Player.group:
        try:
            space.remove(p.shape, p.body)
        except AssertionError:
            pass
    for r in Rect.group:
        try:
            space.remove(r.shape, r.body)
        except AssertionError:
            pass

    players = {}
    rects = {}
    Player.group.clear()
    Rect.group.clear()

    #map loading
    if not glob.glob(f"{dir_path}/maps/*.txt"):
        if glob.glob(f"{dir_path}/maps/Used/*.txt"):
            for map_file in glob.glob(f"{dir_path}/maps/Used/*.txt"):
                shutil.move(map_file, f"{dir_path}/maps")
        else:
            raise FileNotFoundError("no map or folder existing")

    map_files = glob.glob(f"{dir_path}/maps/*.txt")
    map_c = random.choice(map_files)

    # Extract the map name and set up the 2-second display timer
    map_display_name = os.path.splitext(os.path.basename(map_c))[0]
    map_display_timer = pyg.time.get_ticks() + 2000

    bonk_map = []
    with open(map_c, "r", encoding="utf-8") as f:
        for line in f:
            if "\\" in line:
                break
            bonk_map.append(line)

    exec("".join(bonk_map))

    Player.count = len(Player.group)
    for p in Player.group:
        space.add(p.shape, p.body)
    for r in Rect.group:
        space.add(r.shape, r.body)

    shutil.move(map_c, f"{dir_path}/maps/Used")

def win_lose():
    global pending_reset, reset_timer, round_over
    
    if Player.count <= 1 and not pending_reset:  # avoid multiple calls
        for p in Player.group:
            if p.alive:
                Player.score[p.pid] += 1

        pending_reset = True
        reset_timer = pyg.time.get_ticks() + 3000
        round_over = True    

    
def fps(surf, dt):
    font = pyg.font.Font(None, 30)
    framepersec = round((1/dt), 2)
    if framepersec >= 50:
        color = "green"
    elif framepersec >= 30:
        color = "yellow"
    else:
        color = "red" 
    fps_surf = font.render(f"FPS:{framepersec}", False, color)
    surf.blit(fps_surf)


class Player:
    group = []
    score = {}
    count = len(group)

    def __init__(self, pid, pos_x, pos_y, col,
                 kleft, kright, kjump, kfall, kheavy=pyg.K_ESCAPE, karrow=pyg.K_ESCAPE,
                 radius = 20):
        
        self.pid = pid
        self.col = col

        self.body = pymunk.Body(radius, 1)
        self.body.position = (pos_x, pos_y)
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.parent_object = self
        self.shape.friction = 0
        self.shape.collision_type = 2    #COLLTYPE_BALL
        self.shape.elasticity = 0.7
        self.shape.data = self
        self.pos = self.body.position

        self.kleft = kleft
        self.kright = kright
        self.kjump = kjump
        self.kfall = kfall
        self.kheavy = kheavy
        self.karrow = karrow

        self.onground = 0
        self.coyote_time = 5   #frames
        self.alive = 1
        self.arrow_angle = 0
        self.arrow_power = 0

        Player.group.append(self)
        if pid not in Player.score:
            Player.score[pid] = 0

    def render(self, surf):
        y_condition = self.body.position.y < surf.get_height() + self.shape.radius
        x_condition = -self.shape.radius < self.body.position.x < self.shape.radius + surf.get_width()
        if y_condition and x_condition:
            render_pos = pgut.to_pygame(self.shape.body.position, surf)
            pyg.draw.circle(surf, self.col, render_pos, self.shape.radius)
        else:
            shadow_pos = (
                max(15, min(self.body.position.x, surf.get_width()- 15)),
                max(15, min(self.body.position.y, surf.get_height() - 15))
            )
            bar_vector = Vector2(Vector2(shadow_pos)- self.body.position).normalize()
            render_pos = pgut.to_pygame(shadow_pos, surf)
            pyg.draw.circle(surf, "black", render_pos, 10, 2)
            bar_render_pos_1 = pgut.to_pygame(shadow_pos, surf)
            bar_render_pos_2 = pgut.to_pygame(shadow_pos - bar_vector * 8, surf)
            pyg.draw.line(surf, self.col, bar_render_pos_1, bar_render_pos_2, 2)

    def move(self, space, dt):
        keys = pyg.key.get_pressed()
        if keys[self.kjump]:
            if self.onground > 0:
                self.body.apply_impulse_at_local_point((0, 3000 - self.body.velocity.y * self.body.mass))
                self.onground = 0
            if self.onground <= 0:
                self.body.velocity_func = Player.lower_gravity
        elif keys[self.kfall]:
            self.body.velocity_func = Player.higher_gravity
        else:
            self.body.velocity_func = Player.normal_gravity

        if keys[self.karrow]:
            self.arrow_power += dt
            if keys[self.kleft]:
                self.arrow_angle -= dt
            if keys[self.kright]:
                self.arrow_angle += dt
        else:
            if self.arrow_power:
                arrow = self.Arrows(self, self.arrow_angle, self.arrow_power)
                arrow.shoot(space)
            if keys[self.kleft]:
                self.body.apply_impulse_at_local_point((-90, 0))
            if keys[self.kright]:
                self.body.apply_impulse_at_local_point((90, 0))
            
        if 0 < self.onground < self.coyote_time:
            self.onground -= dt * 60

    def cycle(surf, space, dt):
        Player.collision_handler(space, dt)
        for player in Player.group:
            if player.alive:
                player.move(space, dt)
                player.render(surf)
                player.are_you_alive(space)

    def collision_handler(space, dt):
        def pre_solve(arbiter, space, data):
            for shape in arbiter.shapes:
                if type(shape) == pymunk.Circle:
                    player = shape.data
                else:
                    rect = shape.data
            test_points = arbiter.contact_point_set.points[0]

            if rect.death:
                player.are_you_alive(space, death=True)
            elif not rect.bouncy:
                pos = player.body.position
                point = test_points.point_a
                if pos.y > point.y and abs(pos.x - point.x) < player.shape.radius / 3 * 2:
                    player.onground = player.coyote_time
            return True
        
        def separate(arbiter, space, data):
            for shape in arbiter.shapes:
                if type(shape) == pymunk.Circle:
                    player = shape.data
                else:
                    rect = shape.data
            player.onground -= dt * 60
            return True
        
        space.on_collision(0, 2, pre_solve=pre_solve, separate=separate)

    def normal_gravity(body, gravity, damping, dt):
        jump_gravity = (0, -250)
        pymunk.Body.update_velocity(body, jump_gravity, damping, dt)

    def lower_gravity(body, gravity, damping, dt):
        jump_gravity = (0, -110)
        pymunk.Body.update_velocity(body, jump_gravity, damping, dt)

    def higher_gravity(body, gravity, damping, dt):
        jump_gravity = (0, -350)
        pymunk.Body.update_velocity(body, jump_gravity, damping, dt)
    
    def are_you_alive(self, space, death=False):
        if not self.alive:
            pass
        elif not (-100 < self.body.position[1] < 6000) or death:
            if self.alive:
                Player.count -= 1
            self.alive = False
            space.remove(self.shape, self.body)

    class Arrows:
        def __init__(self, parent, direction, angle):
            pass
        def shoot(self, space):
            pass


class Rect:
    group = []
    def __init__(self, col, center, width, height,
                 facing = 0, bouncy = False, rotation = False, movement = False, death = False):
        self.width = width
        self.height = height
        self.facing = facing
        self.color = pyg.Color(col)
        self.bouncy = bouncy
        if type(self.bouncy) == int:
            self.bouncy *= 0.7     #faithful to original game
        self.do_update = rotation or movement
        self.rotating = rotation    #rotation = (orb_center, orb_vel, rot_vel)
        self.moving = movement    #movement = ((x, y)'min', (x, y)'max', (x,y)'vector')
        self.death = death

        self.body = pymunk.Body(body_type = pymunk.Body.KINEMATIC)
        self.shape = pymunk.Poly.create_box(self.body, (self.width, self.height))
        self.shape.data = self
        self.shape.collision_type = 0
        self.shape.body.position = tuple(center)
        self.shape.body.angle = -math.radians(facing)
        self.shape.friction = 1
        if self.bouncy:
            self.shape.elasticity = self.bouncy

        if self.do_update:
            if self.rotating:
                if not self.rotating[0]:
                    self.orb_center = self.shape.body.position
                else:
                    self.orb_center = self.rotating[0]
                self.orb_speed = self.rotating[1]
                self.rot_speed = self.rotating[2]
                self.vel = Vector2(0,0) #orb_vel
                self.defalut_vector_length = Vector2(
                    center - self.orb_center
                    ).length()

            if self.moving:
                self.min_pos = Vector2(self.moving[0])
                self.max_pos = Vector2(self.moving[1])
                self.speed = Vector2(self.moving[2])    #move_vel
                
        Rect.group.append(self)

    def render(self, surf):
        self.position = pgut.to_pygame(self.shape.body.position, surf)
        points = self.shape.get_vertices()
        world_points = []
        for point in points:
            world_point = self.shape.body.local_to_world(point)
            world_points.append(pgut.to_pygame(world_point, surf))
        pyg.draw.polygon(surf, self.color, world_points)
        if self.bouncy:
            pyg.draw.aalines(surf, "black", 1, world_points)
        if self.death:
            pyg.draw.aalines(surf, "red", 1, world_points)

    def cycle(surf, dt):
        for rect in Rect.group:
            rect.update(dt)
            rect.render(surf)

    def rotation(self, dt):
        #orbiting
        if self.rotating[0] and self.rotating[1]:
            direction = Vector2(
                self.shape.body.position - self.orb_center
                ).normalize()
            length = Vector2(self.shape.body.position - self.orb_center
                ).length()
            
            interpolation = (length - self.defalut_vector_length) / self.defalut_vector_length
            if self.orb_speed < 0:
                direction.rotate_ip(90 + interpolation * 360)
                self.body.velocity = tuple(direction * length * -self.orb_speed)
            else:
                direction.rotate_ip(-90 - interpolation * 360)
                self.body.velocity = tuple(direction * length * self.orb_speed)
        #rotating
        self.body.angular_velocity = self.rot_speed

    def movement(self, dt):
        #movement
        if self.min_pos.x > self.shape.body.position.x:
            self.speed.x = abs(self.speed.x)
        elif self.max_pos.x < self.shape.body.position.x:
            self.speed.x = -abs(self.speed.x)
        if self.min_pos.y > self.shape.body.position.y:
            self.speed.y = abs(self.speed.y)
        elif self.max_pos.y < self.shape.body.position.y:
            self.speed.y = -abs(self.speed.y)
        
        #apply speed!
        def speed_set(body, gravity, damping, dt):
            self.body.velocity = tuple(self.speed)
        self.body.velocity_func = speed_set
        
    def update(self, dt):
        if self.do_update:
            if self.rotating:
                self.rotation(dt)
            if self.moving:
                self.movement(dt)


class Line:
    def __init__(self, col, pos1, pos2, width=10,
                 bouncy = False, rotation = False, movement = False, death = False):
        self.center = (pos1+pos2) / 2
        self.width = (pos2-pos1).length()
        self.height = width
        self.facing = (Vector2(pos2)-Vector2(pos1)).angle
        self.color = pyg.Color(col)
        self.bouncy = bouncy
        if type(self.bouncy) == int:
            self.bouncy *= 0.7     #faithful to original game
        self.do_update = rotation or movement
        self.rotating = rotation    #rotation = (orb_center, orb_vel, rot_vel)
        self.moving = movement    #movement = ((x, y)'min', (x, y)'max', (x,y)'vector')
        self.death = death

        self.body = pymunk.Body(body_type = pymunk.Body.KINEMATIC)
        self.shape = pymunk.Poly.create_box(self.body, (self.width, self.height))
        self.shape.data = self
        self.shape.collision_type = 0
        self.shape.body.position = tuple(self.center)
        self.shape.body.angle = math.radians(self.facing)
        self.shape.friction = 1
        if self.bouncy:
            self.shape.elasticity = self.bouncy

        if self.do_update:
            if self.rotating:
                if not self.rotating[0]:
                    self.orb_center = self.shape.body.position
                else:
                    self.orb_center = self.rotating[0]
                self.orb_speed = self.rotating[1]
                self.rot_speed = self.rotating[2]
                self.vel = Vector2(0,0) #orb_vel

            if self.moving:
                self.min_pos = Vector2(self.moving[0])
                self.max_pos = Vector2(self.moving[1])
                self.speed = Vector2(self.moving[2])    #move_vel
                
        Rect.group.append(self)

    def render(self, surf):
        self.position = pgut.to_pygame(self.shape.body.position, surf)
        points = self.shape.get_vertices()
        world_points = []
        for point in points:
            world_point = self.shape.body.local_to_world(point)
            world_points.append(pgut.to_pygame(world_point, surf))
        pyg.draw.polygon(surf, self.color, world_points)
        if self.bouncy:
            pyg.draw.aalines(surf, "black", 1, world_points)
        if self.death:
            pyg.draw.aalines(surf, "red", 1, world_points)

    def cycle(self, surf, dt):
        self.update(dt)
        self.render(surf)

    def rotation(self, dt):
        #orbiting
        if self.rotating[0] and self.rotating[1]:
            direction = Vector2(
                self.shape.body.position - self.orb_center
                ).normalize()
            length = Vector2(self.shape.body.position - self.orb_center
                ).length()
            
            interpolation = (length - self.defalut_vector_length) / self.defalut_vector_length
            if self.orb_speed < 0:
                direction.rotate_ip(90 + interpolation * 360)
                self.body.velocity = tuple(direction * length * -self.orb_speed)
            else:
                direction.rotate_ip(-90 - interpolation * 360)
                self.body.velocity = tuple(direction * length * self.orb_speed)
        #rotating
        self.body.angular_velocity = self.rot_speed

    def movement(self, dt):
        #movement
        if self.min_pos.x > self.shape.body.position.x:
            self.speed.x = abs(self.speed.x)
        elif self.max_pos.x < self.shape.body.position.x:
            self.speed.x = -abs(self.speed.x)
        if self.min_pos.y > self.shape.body.position.y:
            self.speed.y = abs(self.speed.y)
        elif self.max_pos.y < self.shape.body.position.y:
            self.speed.y = -abs(self.speed.y)
        
        #apply speed!
        def speed_set(body, gravity, damping, dt):
            self.body.velocity = tuple(self.speed)
        self.body.velocity_func = speed_set
        
    def update(self, dt):
        if self.do_update:
            if self.rotating:
                self.rotation(dt)
            if self.moving:
                self.movement(dt)



while menu() != 'quit':
    pass

pyg.quit()