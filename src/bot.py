import math

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from util.orientation import Orientation
from util.vec import Vec3
import util.const

from stateMachine import StateMachine

class L0lbot(BaseAgent):

    def initialize_agent(self):
        # This runs once before the bot starts up
        self.controllerState = SimpleControllerState()
        self.stateMachine = StateMachine(self)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:

        return self.stateMachine.tick(packet)




