"""Basic desper usage example: a console based bouncing ball.

Inspired by the infamous bouncing DVD logo screensaver.

Only requirement is desper.
"""
import os
import time

import desper

WIDTH = 20
HEIGHT = 10


class DVD:
    """DVD component, specifies which character shall be rendered.

    By default, DVDs are 'O' characters.
    """

    def __init__(self, character='O'):
        self.character = character


class Velocity:
    """Velocity component, contains a simple 2D vector.

    For simplicity, populate its value by default with a 45 degrees
    vector.
    """
    value = desper.math.Vec2(1, 1)


class VelocityProcessor(desper.Processor):
    """Update positional components with velocity."""

    def process(self, dt):
        # Query velocity components
        for entity, velocity in self.world.get(Velocity):
            # Extract positional component from the same entity
            transform = self.world.get_component(entity, desper.Transform2D)

            # Actually update position
            transform.position += velocity.value


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def render_screen(screen):
    """Given a screen matrix, print on terminal."""
    print('\n'.join([''.join(row) for row in screen]))


class ConsoleRenderProcessor(desper.Processor):
    """Render the DVD on screen through the terminal.

    The full pipeline is: clear the terminal, render the DVDs, sleep
    for a fixed amount of time.
    """

    def __init__(self, width, height, wait_time=0.5):
        self.width = width
        self.height = height
        self.wait_time = wait_time

    def build_screen(self):
        """Build an empty screen of the correct width and height.

        The screen is a list of lists of spaces.
        """
        return [[' '] * self.width for _ in range(self.height)]

    def process(self, dt):
        # Clear terminal before printing anything else
        clear_screen()

        # Build an empty "screen" of the given width and height
        screen = self.build_screen()

        # Query velocity components
        for entity, dvd in self.world.get(DVD):
            # Extract positional component from the same entity
            transform = self.world.get_component(entity, desper.Transform2D)

            # Set screen character to the right position
            screen[transform.position.y][transform.position.x] = dvd.character

        # Render screen
        render_screen(screen)

        # Wait
        time.sleep(self.wait_time)


class BounceProcessor(desper.Processor):
    """Bounce DVDs when they are colliding with a wall."""

    def process(self, dt):
        # Query DVD components
        for entity, dvd, in self.world.get(DVD):
            # Extract positional and velocity components from the same entity
            transform = self.world.get_component(entity, desper.Transform2D)
            velocity = self.world.get_component(entity, Velocity)

            # DVD is colliding with a wall if either its x or y are 0
            # or are equal to WIDTH - 1 (x) or HEIGHT - 1 (y)
            # The result of the collision should be a bounce
            # that is, a change in velocity.
            # This can be easily obtained by reflecting the interested
            # velocity component
            if transform.position.x == 0 or transform.position.x == WIDTH - 1:
                velocity.value = desper.math.Vec2(-velocity.value.x,
                                                  velocity.value.y)

            if transform.position.y == 0 or transform.position.y == HEIGHT - 1:
                velocity.value = desper.math.Vec2(velocity.value.x,
                                                  -velocity.value.y)


def world_transformer(handle: desper.WorldHandle, world: desper.World):
    """Setup main components and processors for the DVD scene."""
    # Add processors for per-frame calculations we're interested in.
    # In particular: Updating velocities, rendering.
    world.add_processor(VelocityProcessor())
    world.add_processor(BounceProcessor())
    world.add_processor(ConsoleRenderProcessor(WIDTH, HEIGHT))

    # Create the DVD entity. A DVD needs a position (Transform2D) and
    # a Velocity.
    world.create_entity(desper.Transform2D(), Velocity(), DVD())


def main():
    """Setup the experiment."""
    # Create a World through a WorldHandle and populate it with a
    # transform function
    handle = desper.WorldHandle()
    handle.transform_functions.append(world_transformer)

    # Set the newly created handle as the current scene and start the loop
    desper.default_loop.switch(handle)
    desper.default_loop.start()


if __name__ == '__main__':
    main()
