import naoqi as nq
import math

# BALL_RADIUS = 0.09  # meters (big ball)
BALL_RADIUS = 0.06  # meters (small ball)

MOVE_SPEED = 0.5  # fraction of max speed

class BallTracker():
    def __init__(self, ip, port):
        self.proxy = nq.ALProxy("ALTracker", ip, port)
        
        self.proxy.registerTarget("RedBall", BALL_RADIUS)
        
        moveConfig = [["Frequency", MOVE_SPEED]]
        self.proxy.setMoveConfig(moveConfig)
        
        self.proxy.track("RedBall")
        self.setMode("Head")
        
    def setMode(self, mode):
        self.proxy.setMode(mode)
        
    def stop(self):
        self.proxy.stopTracker()
        self.proxy.unregisterAllTargets()
        
    def getPosition(self):
        try:
            position = self.proxy.getTargetPosition(0)
            if len(position) == 0:
                return None
            else:
                return (position[0], position[1])
        except:
            return None
        
    def getDistance(self):
        position = self.getPosition()
        if position is None:
            return None
        else:
            return math.sqrt(position[0] * position[0] + position[1] * position[1])
        
    def getAngle(self):
        position = self.getPosition()
        if position is None:
            return None
        else:
            return math.atan2(position[1], position[0])