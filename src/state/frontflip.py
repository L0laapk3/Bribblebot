from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from util.orientation import Orientation
from util.vec import Vec3
import util.const

from state.state import State
import math



class Frontflip(State):
    def __init__(self, agent: BaseAgent): 
        super().__init__(agent)
        self.startTick = 0
        self.state = 0


    def tick(self, packet: GameTickPacket) -> bool:


        if self.state == 3:
            return False





        if self.startTick == 0:
            self.startTick = self.agent.tick
        ticksElapsed = self.agent.tick - self.startTick
            

        jumpTick = 7
        if self.state == 0:
            if ticksElapsed >= jumpTick:
                self.state = 1
            else:
                self.controllerState.jump = True
        
        if self.state == 1:
                if self.controllerState.jump: # set it to false for one input frame
                    self.controllerState.jump = False
                else:
                    self.state = 2
        if self.state == 2:
                self.state = 3
                self.controllerState.jump = True

        self.controllerState.pitch = -1
        self.controllerState.throttle = 1
        self.controllerState.throttle = 1

        #print(f"{ticksElapsed}\t{self.controllerState.jump}")
        return True
