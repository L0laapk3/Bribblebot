from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from util.orientation import Orientation
from util.vec import Vec3
import util.const

from state.state import State
import math


normalSpeed = 1409
boostSpeed = 2299

class Showtime(State):
    def __init__(self, agent: BaseAgent):
        super().__init__(agent)


    def tick(self, packet: GameTickPacket) -> bool:
        

        ball_location = Vec3(packet.game_ball.physics.location)

        my_car = packet.game_cars[self.agent.index]
        car_location = Vec3(my_car.physics.location)

        car_to_ball = ball_location - car_location

        # Find the direction of our car using the Orientation class
        car_orientation = Orientation(my_car.physics.rotation)
        car_direction = car_orientation.forward

        steer_correction_radians = find_correction(car_direction, car_to_ball)

        turn = max(-1, min(1, steer_correction_radians * 50))
        #action_display = f"turn {round(turn, 2)}" 
        self.controllerState.steer = turn




        speed = Vec3.length(my_car.physics.velocity)
        targetSpeed = min(boostSpeed, Vec3.dist(ball_location, car_location) * 3.5)


        action_display = f"speed {round(speed)}/{round(targetSpeed)}" 

        self.controllerState.throttle = max(-1, min(1, (targetSpeed - speed) * 50))
        self.controllerState.steer = turn
        self.controllerState.boost = speed < targetSpeed if self.controllerState.boost or (abs(turn) < 1 and targetSpeed > normalSpeed) else (abs(turn) < 1 and speed < targetSpeed - 200)

        draw_debug(self.agent.renderer, my_car, packet.game_ball, action_display)

        return True










        
def find_correction(current: Vec3, ideal: Vec3) -> float:
    # Finds the angle from current to ideal vector in the xy-plane. Angle will be between -pi and +pi.

    # The in-game axes are left handed, so use -x
    current_in_radians = math.atan2(current.y, -current.x)
    ideal_in_radians = math.atan2(ideal.y, -ideal.x)

    diff = current_in_radians - ideal_in_radians

    # Make sure that diff is between -pi and +pi.
    if abs(diff) > math.pi:
        if diff < 0:
            diff += 2 * math.pi
        else:
            diff -= 2 * math.pi

    return diff


def draw_debug(renderer, car, ball, action_display):
    renderer.begin_rendering()
    # draw a line from the car to the ball
    renderer.draw_line_3d(car.physics.location, ball.physics.location, renderer.white())
    # print the action that the bot is taking
    renderer.draw_string_3d(car.physics.location, 2, 2, action_display, renderer.white())
    renderer.end_rendering()