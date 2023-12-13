# coding=utf-8
# !venv/pin/python

import naoqi as nq
import time
import math
import almath

from ball_tracker import BallTracker
from goal_tracker import GoalTracker

IP_ADDRESS = "10.160.64.12"  # PABLO
# IP_ADDRESS = "10.160.64.33" # KUSHKA
# IP_ADDRESS = "10.160.64.38" # BORIN
# IP_ADDRESS = "10.160.64.19" # LYRA
# IP_ADDRESS = "10.160.64.18" # DIABLO
PROXY_PORT = 9559

# BALL_SIZE = 0.06  # meters (small ball)
BALL_SIZE = 0.09  # meters (big ball)
LANDMARK_SIZE = 0.2  # meters

MOVEMENT_SPEED = 0.2  # fraction of max speed
SHOOTING_DISTANCE = 0.5  # meters

possible_states = [
    "searching",
    "positioning",
    "moving",
    "shooting"
]

search_positions = [ # headPitch, headYaw
    (0.3, 0.5),
    (0.3, 0.375),
    (0.3, 0.25),
    (0.3, 0.125),
    (0.3, 0),
    (0.3, -0.125),
    (0.3, -0.25),
    (0.3, -0.375),
    (0.3, -0.5),
]

def start_talker():
    global talker

    talker = nq.ALProxy("ALTextToSpeech", IP_ADDRESS, PROXY_PORT)
    talker.setVolume(1.0)

    talker.say("Hello")

def start_motion():
    global motion, posture

    motion = nq.ALProxy("ALMotion", IP_ADDRESS, PROXY_PORT)
    posture = nq.ALProxy("ALRobotPosture", IP_ADDRESS, PROXY_PORT)

    motion.wakeUp()
    posture.goToPosture("Stand", 0.5)

def stop():
    global tracker, motion, posture

    

    print("Tracking stopped")

    posture.goToPosture("Crouch", 0.5)
    motion.rest()
    motion.setStiffnesses("Body", 0)

    print("Motion and posture stopped")
    
def find_collinear_point(B, G):
    print("Ball position: " + str(B))
    print("Goal position: " + str(G))
    # Extract the x and y coordinates of B and G
    x_b, y_b = B
    x_g, y_g = G
    
    # Since PB is equally distant to BG, k is 1
    # If PB is closer to B, k < 1
    # k = 0.5 / (math.sqrt(x_g*2 + y_g*2) - math.sqrt(x_b*2 + y_b*2))
    # k = 1
    distance_goal_to_ball = math.sqrt((x_g - x_b)**2 + (y_g - y_b)**2)
    k = SHOOTING_DISTANCE / distance_goal_to_ball
    
    # Calculate the Cartesian coordinates of P
    x_p = x_b * (1 + k) - k * x_g
    y_p = y_b * (1 + k) - k * y_g
    
    # # Convert Cartesian coordinates of P to polar coordinates
    # r = math.sqrt(x_p*2 + y_p*2)
    # theta = math.atan2(y_p, x_p)
    
    # Return the polar coordinates of P
    return (x_p, y_p)

def get_magic_angle(target_postion, ball_position, theta):
    distance_x = target_postion[0] - ball_position[0]
    
    return theta + math.asin(distance_x / SHOOTING_DISTANCE)

def main():
    
    start_talker()
    start_motion()
    
    bt = BallTracker(IP_ADDRESS, PROXY_PORT)
    gt = GoalTracker(IP_ADDRESS, PROXY_PORT)
    
    current_state = "searching"
    registered_ball_positions = []
    registered_goal_positions = []

    try:
        while True:
            if current_state == "searching":
                print("Searching...")
                # Go through all search positions and if any of the goal or ball is found, add them to the registered positions
                for position in search_positions:
                    motion.setAngles(["HeadPitch", "HeadYaw"], position, 0.1)
                    time.sleep(1)
                        
                    goal_position = gt.getPosition(motion)
                    print("Goal position: " + str(goal_position))
                    if goal_position is not None:
                        registered_goal_positions.append(goal_position)
                        
                    ball_position = bt.getPosition()
                    print("Ball position: " + str(ball_position))
                    if ball_position is not None:
                        registered_ball_positions.append(ball_position)
                
                if len(registered_ball_positions) > 0 and len(registered_goal_positions) > 0:
                    print("Saw the goal " + str(len(registered_goal_positions)) + " times and the ball " + str(len(registered_ball_positions)) + " times")
                    # talker.say("Saw the goal " + str(len(registered_goal_positions)) + " times and the ball " + str(len(registered_ball_positions)) + " times")
                    bt.setMode("Head")
                    current_state = "positioning"
                else:
                    print("Didn't see the goal or the ball")
                    talker.say("Didn't see the goal or the ball")
                    current_state = "searching"

            elif current_state == "positioning":
                print("Positioning...")
                # Get averages of all registered positions
                ball_position = (sum([position[0] for position in registered_ball_positions]) / len(registered_ball_positions), sum([position[1] for position in registered_ball_positions]) / len(registered_ball_positions))
                goal_position = (sum([position[0] for position in registered_goal_positions]) / len(registered_goal_positions), sum([position[1] for position in registered_goal_positions]) / len(registered_goal_positions))
                
                # Find the collinear point
                collinear_point = find_collinear_point(ball_position, goal_position)
                print("Collinear point: " + str(collinear_point))
                
                # current_state = None
                # break
                if math.sqrt(collinear_point[0]**2 + collinear_point[1]**2) < 0.2:
                    print("Collinear point is close enough")
                else:
                    # Calculate the distance and angle to the collinear point
                    angle = math.atan2(collinear_point[1], collinear_point[0])
                    distance = math.sqrt(collinear_point[0]**2 + collinear_point[1]**2)
                    
                    # Move to the collinear point
                    motion.moveTo(0, 0, angle, [["MaxStepFrequency", MOVEMENT_SPEED]])
                    motion.waitUntilMoveIsFinished()
                    motion.moveTo(distance, 0, 0, [["MaxStepFrequency", MOVEMENT_SPEED]])
                    motion.waitUntilMoveIsFinished()
                    # motion.moveTo(collinear_point[0], collinear_point[1], 0, [["MaxStepFrequency", MOVEMENT_SPEED]])
                    
                    # Calculate the angle to the goal
                    magic_angle = get_magic_angle(collinear_point, ball_position, angle)
                    magic_angle = abs(magic_angle) if angle < 0 else -abs(magic_angle)
                    
                    # Turn to the goal
                    motion.moveTo(0, 0, magic_angle, [["MaxStepFrequency", MOVEMENT_SPEED]])
                    motion.waitUntilMoveIsFinished()
                
                current_state = "moving"
                print("Moving...")
                
            elif current_state == "moving":
                # Track ball until it is close enough to shoot
                distance = bt.getDistance()
                if distance < 0.3:
                    bt.stop()
                    current_state = "shooting"
                elif distance == None:
                    print("Lost ball")
                    current_state = None
                else:
                    bt.setMode("Move")
                    print("Distance to ball: " + str(distance))
                time.sleep(0.5)
                
            elif current_state == "shooting":
                print("Shooting...")
                talker.say("Shooting ball")
                motion.moveTo(0.15, 0.0, 0, [["MaxStepFrequency", MOVEMENT_SPEED]])
                current_state = None
                
            else:
                break
                

    except KeyboardInterrupt:
        print("Interrupted by user, shutting down...")
        
    bt.stop()
    gt.stop()
    stop()

if __name__ == "__main__":
    main()
