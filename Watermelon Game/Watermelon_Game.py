import pymunk
import pygame
import sys
import numpy as np

from object import Object

BLACK = (0,0,0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)


BALL_COLLISION = 0
GROUND_COLLISION = 2
LIMIT_COLLISION = 100
LIMIT_HEIGHT = 160
DROP_HEIGHT = 100
EVENT_LIMIT = pygame.USEREVENT + 1

# Collision handler for balls
def post_solve_arbiter(arbiter, space, data):
    for contact in arbiter.contact_point_set.points:
        impulse = arbiter.total_impulse * 0.5
        body1, body2 = arbiter.shapes
        body1.body.apply_impulse_at_world_point(impulse, contact.point_a)
        body2.body.apply_impulse_at_world_point(-impulse, contact.point_b)

def post_solve_arbiter2(arbiter, space, data):
    for contact in arbiter.contact_point_set.points:
        impulse = arbiter.total_impulse * 0.5
        body1, body2 = arbiter.shapes
        body1.body.apply_impulse_at_world_point(impulse, contact.point_a)

def add_object(radius, x, y):
    object = Object(radius, x, y)
    circle = pymunk.Circle(object, object.radius)
    circle.elasticity = 0.2
    object.circle = circle
    return object, circle

def object_color(radius):
        return np.abs(np.cos(radius/60)) * np.array([255,0,0]) + np.abs(np.sin(radius/60)) * np.array([0,255,0])

class Game():
    def __init__(self, width, height):
        # Constants
        self.SCREEN_WIDTH = width
        self.SCREEN_HEIGHT = height
        self.FRUIT_SIZE = 12
        self.FRAME_RATE = 60

        self.running = True
        self.ending = True

        self.objects = []
        self.next_radius = np.random.randint(1,4)*self.FRUIT_SIZE

        self.drop_x = self.SCREEN_WIDTH // 2
        
        self.score = 0
        self.object_timer = 0
        self.limit_timer = 0

        self.space = pymunk.Space()
        self.gravity = (0, 1000)
        self.space.gravity = self.gravity
        self.space.add_collision_handler(BALL_COLLISION, BALL_COLLISION).post_solve = post_solve_arbiter
        self.space.add_collision_handler(BALL_COLLISION, GROUND_COLLISION).post_solve = post_solve_arbiter2

        ground = pymunk.Segment(self.space.static_body, (0, self.SCREEN_HEIGHT), (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), 10)
        ground.friction = 1.0
        ground.collision_type = GROUND_COLLISION
        self.space.add(ground)

        left_wall = pymunk.Segment(self.space.static_body, (0, self.SCREEN_HEIGHT), (0, 0), 10)
        left_wall.friction = 1.0
        left_wall.collision_type = GROUND_COLLISION
        self.space.add(left_wall)

        right_wall = pymunk.Segment(self.space.static_body, (self.SCREEN_WIDTH, 0), (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), 10)
        right_wall.friction = 1.0
        right_wall.collision_type = GROUND_COLLISION
        self.space.add(right_wall)

        self.state = dict()

    def update(self, action):
        if action[0]:
            self.drop_x = self.drop_x - 200 / self.FRAME_RATE
            if self.drop_x < self.next_radius:
                self.drop_x = self.next_radius
        if action[1]:
            self.drop_x = self.drop_x + 200 / self.FRAME_RATE
            if self.drop_x > self.SCREEN_WIDTH-self.next_radius:
                self.drop_x = self.SCREEN_WIDTH-self.next_radius
        if action[2] and self.object_timer == 0:
            object, circle = add_object(self.next_radius, self.drop_x, DROP_HEIGHT)
            self.space.add(object, circle)
            self.objects.append(object)
            self.next_radius = np.random.randint(1,4)*self.FRUIT_SIZE
            self.object_timer = self.FRAME_RATE // 2
        if self.object_timer > 0:
            self.object_timer = self.object_timer - 1
                
        delete_queue = []
        for i in range(len(self.objects)-1):
            for other in self.objects[i+1:]:
                if self.objects[i].check_collision(other) == 1:
                    if self.objects[i].radius <= self.FRUIT_SIZE * 10:            
                        delete_queue.append(self.objects[i])
                        delete_queue.append(other)
                        object, circle = add_object(self.objects[i].radius + self.FRUIT_SIZE, 0.5 * (self.objects[i].position[0] + other.position[0]), 0.5 * (self.objects[i].position[1] + other.position[1]))
                        self.space.add(object, circle)
                        self.objects.append(object)
                        def calc_score(radius):
                            n = radius // self.FRUIT_SIZE
                            return n * (n + 1) // 2
                        self.score = self.score + calc_score(object.radius)
        for obj in delete_queue:
            self.space.remove(obj, obj.circle)
            self.objects.remove(obj)
            del obj
        limit_violated = False
        for obj in self.objects:
            if obj.position.y - obj.radius < LIMIT_HEIGHT:
                limit_violated = True
        if limit_violated:
            self.limit_timer = self.limit_timer + 1
            if self.limit_timer > self.FRAME_RATE * 2:
                self.running = False
        else:
            self.limit_timer = 0
        self.space.step(1 / self.FRAME_RATE)
        self.state['FRUIT'] = [{'x':obj.position[0], 'y':obj.position[1], 'r':obj.radius} for obj in self.objects] + [{'x':self.drop_x, 'y': DROP_HEIGHT, 'r':self.next_radius}]
        self.state['score'] = self.score
        self.state['drop_x'] = self.drop_x
    
    def setting(self):
        self.font_arial = pygame.font.SysFont("arial", 20, True, False)
        # Create the game window
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        icon = pygame.image.load("icon.png")
        pygame.display.set_icon(icon)
        pygame.display.set_caption("Watermelon Game")
        # Create a clock object to control the frame rate
        self.clock = pygame.time.Clock()

    def draw(self):
        self.screen.fill(WHITE)
        for obj in self.objects:
            pygame.draw.circle(self.screen, object_color(obj.radius), obj.position, obj.radius)
        pygame.draw.circle(self.screen, object_color(self.next_radius), (self.drop_x, DROP_HEIGHT), self.next_radius)
        pygame.draw.line(self.screen, BLACK, (0, self.SCREEN_HEIGHT), (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), 20)
        pygame.draw.line(self.screen, BLACK, (0, self.SCREEN_HEIGHT), (0, 0), 20)
        pygame.draw.line(self.screen, BLACK, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), (self.SCREEN_WIDTH, 0), 20)
        pygame.draw.line(self.screen, RED, (10, LIMIT_HEIGHT), (self.SCREEN_WIDTH-10, LIMIT_HEIGHT), 4)
        score_text = self.font_arial.render(f"score: {self.score}", True, BLACK)
        self.screen.blit(score_text, (20, 20))
        # Update the screen
        pygame.display.update()
        self.clock.tick(self.FRAME_RATE)

    def quit(self):
        pygame.quit()

    def run(self, mode='VISUALIZE'):
        if mode == 'VISUALIZE':
            pygame.init()
            self.setting()

        if mode == 'TRAIN':
            self.state = {'gravity': np.array(self.gravity), 'walls':np.array([self.SCREEN_WIDTH, self.SCREEN_HEIGHT])}
            self.state['FRUIT'] = np.array([])
            self.state['score'] = 0
        # Game loop
        if mode == 'VISUALIZE':
            action = [False, False, False]
            action_list = []
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        self.ending = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        action[2] = True
                    elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                        action[2] = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                        action[0] = True
                    elif event.type == pygame.KEYUP and event.key == pygame.K_LEFT:
                        action[0] = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                        action[1] = True
                    elif event.type == pygame.KEYUP and event.key == pygame.K_RIGHT:
                        action[1] = False

                action_list.append("%i%i%i\n" % (action[0], action[1], action[2]))
                self.update(action)
                self.draw()

            with open('data.txt', 'w') as fp:
                fp.write("%i\n" % seed)
                for action_text in action_list:
                    fp.write(action_text)
                print("Write Done")

            while self.ending:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.ending = False
            # Quit Pygame
            self.quit()

seed = np.random.randint(1000,9000)+1000
np.random.seed(seed)
if __name__ == "__main__":    
    game=Game(400,600)
    game.run('VISUALIZE')
    sys.exit()