import naoqi as nq
import math
import almath

LANDMARK_SIZE = 0.2  # meters

class GoalTracker():
    def __init__(self, ip, port):
        self.proxy = nq.ALProxy("ALLandMarkDetection", ip, port)
        self.memory = nq.ALProxy("ALMemory", ip, port)
        
        self.proxy.subscribe("goal")
        
    def setMode(self, mode):
        pass
        
    def stop(self):
        pass
        
    def getPosition(self, motionProxy):
        try:
            markData = self.memory.getData("LandmarkDetected")
            
            wzCamera = markData[1][0][0][1]
            wyCamera = markData[1][0][0][2]
            
            angularSize = markData[1][0][0][3]
            
            distanceFromCameraToLandmark = LANDMARK_SIZE / (2 * math.tan(angularSize / 2))
            
            transform = motionProxy.getTransform("CameraTop", 2, True)
            transformList = almath.vectorFloat(transform)
            robotToCamera = almath.Transform(transformList)
            
            cameraToLandmarkRotationTransform = almath.Transform_from3DRotation(0, wyCamera, wzCamera)
            cameraToLandmarkTranslationTransform = almath.Transform(distanceFromCameraToLandmark, 0, 0)
            
            robotToLandmark = robotToCamera * cameraToLandmarkRotationTransform * cameraToLandmarkTranslationTransform
            
            x = robotToLandmark.r1_c4
            y = robotToLandmark.r2_c4
            
            return (x, y)
        except:
            return None
        
    def getDistance(self):
        position = self.getPosition()
        if position is None:
            return None
        else:
            return (position[0]**2 + position[1]**2)**0.5
        
    def getAngle(self):
        position = self.getPosition()
        if position is None:
            return None
        else:
            return math.atan2(position[1], position[0])