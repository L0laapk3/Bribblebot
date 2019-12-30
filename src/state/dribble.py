from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from util.orientation import Orientation
from util.vec import Vec3
import util.const

from state.state import State
import math


normalSpeed = 1409
boostSpeed = 2299

#for zombie tournament

class Dribble(State):
    def __init__(self, agent: BaseAgent):
        super().__init__(agent)
        self.balanceTime = 0
        self.carToTargetIntegral = Vec3()
        self.steerBiasLimit = 0.5


    def tick(self, packet: GameTickPacket) -> bool:

        kickoff = packet.game_info.is_round_active and packet.game_info.is_kickoff_pause


        # car info
        myCar = packet.game_cars[self.agent.index]
        carLocation = Vec3(myCar.physics.location)
        carVelocity = Vec3(myCar.physics.velocity)
        carSpeed = carVelocity.length()

        # ball info
        ballLocation = Vec3(packet.game_ball.physics.location)
        ballVelocity = Vec3(packet.game_ball.physics.velocity)
        if ballLocation.z < 100:
            self.balanceTime = 0
            #return False
        action_display = f"Air time: {self.balanceTime}" 
        self.balanceTime += 1

        # unstuck goal hack
        if abs(carLocation.y) > 5100:
            ballLocation.x = 0

        # target ball info
        #targetBallLocation, targetBallVelocity, targetAngle = getTargetBall(self.agent, packet, carLocation)
        
        teamDirection = 1 if packet.game_cars[self.agent.index].team == 0 else -1
        sidewaysDiff = abs(carLocation.x)-893+100
        if sidewaysDiff > 0:
            sidewaysDiff = max(0, sidewaysDiff + 0.4*(carLocation.y * teamDirection - (5120-100)))
            inTriangleAmount = max(0, min(1, sidewaysDiff / 4500))
            scale = 0.55
        else:
            scale = 2
            inTriangleAmount = 0
        targetBallLocation = Vec3(0, (5120+100 - sidewaysDiff * scale) * teamDirection, 0)

        action_display = f"{round(inTriangleAmount, 1)}"

        ## calculate angles
        ballDirection = math.atan2(ballVelocity.y, -ballVelocity.x)
        carDirection = -myCar.physics.rotation.yaw
        ballToCarAbsoluteLocation = (ballLocation - carLocation).flat()
        carToBallAngle = math.atan2(ballToCarAbsoluteLocation.y, -ballToCarAbsoluteLocation.x) - carDirection
        if abs(carToBallAngle) > math.pi:
            if carToBallAngle > 0:
                carToBallAngle -= 2*math.pi
            else:
                carToBallAngle += 2*math.pi
        ballToTargetAbsoluteLocation = (ballLocation - targetBallLocation).flat()
        carToTargetAngle = math.atan2(ballToTargetAbsoluteLocation.y, -ballToTargetAbsoluteLocation.x) - carDirection
        if abs(carToTargetAngle) > math.pi:
            if carToTargetAngle > 0:
                carToTargetAngle -= 2*math.pi
            else:
                carToTargetAngle += 2*math.pi
        carToTargetAbsoluteLocation = (carLocation - targetBallLocation).flat()

        ## separate into steering and throttle components
        ballToCarLocation = ballToCarAbsoluteLocation.rotate_2D(carDirection)
        ballToTargetLocation = ballToTargetAbsoluteLocation.rotate_2D(carDirection)
        carToTargetLocation = carToTargetAbsoluteLocation.rotate_2D(carDirection)

        ballToCarVelocity = (ballVelocity - carVelocity).flat().rotate_2D(carDirection)
        #carToTargetVelocity = (carVelocity - targetBallVelocity).flat().rotate_2D(carDirection)

        maxSpeed = max(1410, min(2300, 1410 + (2300-1410)/33*myCar.boost))
        carToMaxSpeed = carVelocity.flat().length() - maxSpeed
        desiredSpeed = 1200

        if ballToTargetLocation.y < 500:
            self.carToTargetIntegral += ballToTargetLocation
        else:
            self.carToTargetIntegral = Vec3()

        ## STEERING
        steer = 0
        steerBias = 0
        # ball to car proportional
        #print(f"{round(min(15, max(-15, 0.02 * ballToCarLocation.y)), 2)}\t{round(0.003 * ballToCarVelocity.y, 2)}")
        steer += min(15, max(-15, 0.02 * ballToCarLocation.y))
        # ball to car derivative
        steer += 0.005 * ballToCarVelocity.y
        #print(f"pos: {round(min(15, max(-15, 0.02 * ballToCarLocation.y)), 2)}\tvel: {round(0.009 * ballToCarVelocity.y,2)}")
        # ball to target proportional
        targetSteer = ballToTargetLocation.y
        action_display = f"{round(carToTargetLocation.x)}"
        if carToTargetLocation.x > 300:
            targetSteer = math.copysign(100000, targetSteer)
        steerBias += 0.005 * targetSteer
        # ball to target derivative
        #steerBias += 0.002 * carToTargetVelocity.y
        # ball to target integral
        #steerBias += 0.000001 * self.carToTargetIntegral.y
        #print(f"{round(steerBias, 1)}\t{round(0.008 * carToTargetVelocity.y, 1)}")
        
        if kickoff:
            self.steerBiasLimit = 0
        elif abs(carLocation.x) < 930 and abs(carLocation.y) < 5120-550:
            self.steerBiasLimit = 2.5
        if ballLocation.z > 160 or ballToCarLocation.length() > 800:
            self.steerBiasLimit = max(0.5, self.steerBiasLimit - 0.1)
        elif ballLocation.z < 100:
            self.steerBiasLimit = max(0.5, self.steerBiasLimit - 0.1)
        else:
            self.steerBiasLimit = min(2.5, 1 + 1 * max(0, carSpeed - 600) / 1800, self.steerBiasLimit + 0.065)

        if ballToCarLocation.length() < 180:
            print((1400 - carVelocity.flat().length()) / 350)
            self.steerBiasLimit = min(self.steerBiasLimit, 1.3 + (1400 - carVelocity.flat().length()) / 800)

        steer += min(self.steerBiasLimit, max(-self.steerBiasLimit, steerBias))
        action_display = f"SBL {round(self.steerBiasLimit, 1)} SB: {round(min(self.steerBiasLimit, max(-self.steerBiasLimit, steerBias)), 1)}" 
        #action_display = f"{round(ballToTargetLocation.x)}"

        ## THROTTLE
        throttle = 0
        # ball to car proportional
        throttle += 0.04 * ballToCarLocation.x
        # ball to car derivative
        throttle += 0.01 * ballToCarVelocity.x

        #print(ballVelocity.length())
        if ballToCarLocation.length() < 300 and not (abs(ballToCarLocation.y) > 100 and ballVelocity.length() < 500): # if the ball is too far from the car, use speed to drive car to ball


            throttleBias = 0
            ## NORMAL TARGET BIAS
            #ball to target proportional
            #throttleBias += 0.004 * ballToTargetLocation.x
            # ball to target derivative
            if ballLocation.z > 100:
                #action_display = f"triangle: {round((1 - inTriangleAmount), 1)}\ttargetangle: {round(0.8*math.cos(carToTargetAngle/2), 1)}" 
                carToDesiredSpeed = carVelocity.flat().length() - desiredSpeed * max(0.2, (1 - inTriangleAmount))
                throttleBias += 0.005 * carToDesiredSpeed
            # ball to target integral
            #throttleBias += 0.00001 * self.carToTargetIntegral.x

            ## STEERING HELP BIAS WHEN FAR AWAY
            #targetSteeringSpeed = 400 + 3000 * math.pow(math.cos(carToTargetAngle/2), 16)
            #throttleSteeringBias = max(-1, 3 * (carSpeed - targetSteeringSpeed) / 1400)

        
            # alpha = max(0, min(1, (ballToTargetLocation.length() - 1000) / 3000))

            # throttleBias = throttleSteeringBias * alpha + throttleBias * (1 - alpha)

            throttle += min(2, max(-0.9, throttleBias))
            #action_display = f"TB: {round(throttleBias, 1)}\tT: {round(throttle, 1)}" 
        else:
            throttle = 1-0.8*math.cos(carToBallAngle)

        #print(action_display)

        

        ## set controller state
        self.controllerState.steer = min(1, max(-1, steer))
        self.controllerState.throttle = min(1, max(-1, throttle))
        self.controllerState.boost = False
        if throttle > 1.4 and carLocation.z < 100:
            self.controllerState.boost = carSpeed < 2299.5






        # print(self.ballToTargetIntegral)
        # action_display = f"steer: {round(ballToTargetLocation.y)}"
        # action_display = f"distance: {round(ballToTargetLocation.x)}" 



        # # Find the direction of our car using the Orientation class
        #car_orientation = Orientation(myCar.physics.rotation).forward
        #car_direction = car_orientation.forward


        # steer_correction_radians = find_correction(car_direction, ballToCarLocation)

        # turnProportional = max(-1, min(1, steer_correction_radians * 4))
        # #action_display = f"turn {round(turn, 2)}" 
        # self.controllerState.steer = turnProportional



        # throttleProportional = 10
        # speed = Vec3.length(myCar.physics.velocity)
        # targetSpeed = min(boostSpeed, Vec3.dist(ballLocation, carLocation) * 5 * math.cos(steer_correction_radians))

        # self.controllerState.throttle = max(-1, min(1, (targetSpeed - speed) * 1000))
        # self.controllerState.steer = turnProportional
        # self.controllerState.boost = speed < targetSpeed if self.controllerState.boost or (abs(turnProportional) < 1 and targetSpeed > normalSpeed) else (abs(turnProportional) < 1 and speed < targetSpeed - 400)



        
        targetBallLocation.z = 150
        draw_debug(self.agent, myCar, packet.game_ball, action_display, targetBallLocation)

        return True







def getTargetBall(agent, packet: GameTickPacket, carLocation: Vec3) -> (Vec3, Vec3, float):
    # RADIUS = 1200
    # SPEED = 0.8
    # VELOCITY = SPEED
    # try:
    #     angle = SPEED * packet.game_info.seconds_elapsed 
    #     return  Vec3(RADIUS * math.sin(angle),
    #                  RADIUS * math.cos(angle),
    #                  0), \
    #             Vec3(RADIUS * math.cos(angle),
    #                  RADIUS * -math.sin(angle),
    #                  0) * VELOCITY, \
    #             angle
    # except Exception:
    #     return Vec3()

    teamDirection = 1 if packet.game_cars[agent.index].team == 0 else -1
    sidewaysDiff = abs(carLocation.x)-893+100
    if sidewaysDiff > 0:
        sidewaysDiff = max(0, sidewaysDiff + 0.4*(carLocation.y * teamDirection - (5120-100)))
        scale = 0.6
    else:
        scale = 2
    return Vec3(0, (5120+100 - sidewaysDiff * scale) * teamDirection, 0), Vec3(0, 0 * teamDirection, 0), 0









        
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


def draw_debug(agent, car, ball, action_display, targetBallLocation):
    renderer = agent.renderer
    renderer.begin_rendering()
    ballPrediction = agent.get_ball_prediction_struct()
    
    predictionLine = []
    if ballPrediction is not None:
        for i in range(0, ballPrediction.num_slices):
            predictionLine.append(Vec3(ballPrediction.slices[i].physics.location))

    agent.renderer.begin_rendering()
    red = agent.renderer.create_color(255, 255, 30, 30)
    agent.renderer.draw_polyline_3d(predictionLine, red)
    # draw a line from the car to the ball
    renderer.draw_line_3d(car.physics.location, ball.physics.location, renderer.white())
    renderer.draw_line_3d(targetBallLocation, ball.physics.location, renderer.white())
    # print the action that the bot is taking
    renderer.draw_string_3d(car.physics.location, 2, 2, action_display, renderer.white())

    
    draw_point(renderer, targetBallLocation, renderer.yellow())
    renderer.end_rendering()



def draw_point(renderer, location, color):
    for axis in (Vec3(0, 0, 1), Vec3(0, 1, 0), Vec3(1, 0, 0)):
        renderer.draw_line_3d(location + 100 * axis, location - 100 * axis, color)
