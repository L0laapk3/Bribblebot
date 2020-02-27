import math

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.quick_chats import QuickChats
from util.orientation import Orientation
from util.vec import Vec3
import util.const

import sys
from stateMachine import StateMachine


class BribbleBot(BaseAgent):

    def initialize_agent(self):
        # This runs once before the bot starts up
        self.controllerState = SimpleControllerState()
        self.stateMachine = StateMachine(self)
        
        self.lastTime = 0
        self.realLastTime = 0
        self.doneTicks = 0
        self.skippedTicks = 0
        self.ticksThisPacket = 0
        self.tick = 0
        self.FPS = 120
        self.lastQuickChatTime = 0

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.packet = packet

        self.handleTime()

        ballY = packet.game_ball.physics.location.y

        if abs(ballY) > 5120+60 and packet.game_info.seconds_elapsed - self.lastQuickChatTime > 15:
            teamDirection = 1 if packet.game_ball.latest_touch.team == 0 else -1
            if ballY * teamDirection > 0:
                if packet.game_ball.latest_touch.team == packet.game_cars[self.index].team:
                    self.send_quick_chat(QuickChats.CHAT_EVERYONE, QuickChats.Compliments_NiceShot)
                    self.send_quick_chat(QuickChats.CHAT_EVERYONE, QuickChats.Compliments_Thanks)
                else:
                    self.send_quick_chat(QuickChats.CHAT_EVERYONE, QuickChats.Apologies_Whoops)
                    self.send_quick_chat(QuickChats.CHAT_EVERYONE, QuickChats.Apologies_NoProblem)
            
            else:
                self.send_quick_chat(QuickChats.CHAT_EVERYONE, QuickChats.Reactions_Savage)
                self.send_quick_chat(QuickChats.CHAT_EVERYONE, QuickChats.Compliments_WhatASave)

            self.lastQuickChatTime = packet.game_info.seconds_elapsed


        return self.stateMachine.tick(packet)






    def handleTime(self):
        # this is the most conservative possible approach, but it could lead to having a "backlog" of ticks if seconds_elapsed
        # isnt perfectly accurate.
        if not self.lastTime:
            self.lastTime = self.packet.game_info.seconds_elapsed
        else:
            if self.realLastTime == self.packet.game_info.seconds_elapsed:
                return

            if int(self.lastTime) != int(self.packet.game_info.seconds_elapsed):
                if self.skippedTicks > 0:
                    print(f"dropped {self.skippedTicks} ticks last second!")
                self.skippedTicks = self.doneTicks = 0

            self.ticksThisPacket = round(max(1, (self.packet.game_info.seconds_elapsed - self.lastTime) * self.FPS))
            self.lastTime = min(self.packet.game_info.seconds_elapsed, self.lastTime + self.ticksThisPacket)
            self.realLastTime = self.packet.game_info.seconds_elapsed
            self.tick += self.ticksThisPacket
            if self.ticksThisPacket > 1:
                #print(f"Skipped {ticksPassed - 1} ticks!")
                self.skippedTicks += self.ticksThisPacket - 1
            self.doneTicks += 1