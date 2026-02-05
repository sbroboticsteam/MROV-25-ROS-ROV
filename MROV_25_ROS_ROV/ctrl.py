import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import numpy as np



def thruster_mix(FWB, LR, UD, ROLL, PITCH, YAW):
   V_FL = UD + PITCH + ROLL
   V_FR = UD + PITCH - ROLL
   V_BR = UD - PITCH - ROLL
   V_BL = UD - PITCH + ROLL
   D_FL = FWB - LR + YAW
   D_FR = FWB + LR - YAW
   D_BR = FWB + LR + YAW
   D_BL = FWB - LR - YAW
   thrusters = np.array([
       V_FL, V_FR, V_BR, V_BL,
       D_FL, D_FR, D_BR, D_BL
   ])
   max_mag = np.max(np.abs(thrusters))
   if max_mag > 1.0:
       thrusters /= max_mag
   return thrusters

def speed_ctrl(thrusters, speed):
   return thrusters*speed

class ControllerSubscriber(Node):

    def __init__(self):
        super().__init__('controller_subscriber')
        self.mode = True
        self.speed = 1
        self.sub = self.create_subscription(
            String,
            '/controller/full_state',
            self.cb,
            10
        )

        self.get_logger().info("Controller subscriber ready")

    def cb(self, msg: String):
        data = json.loads(msg.data)
        data['right_x'] *= -1
        data['left_x'] *= -1

        if data['LB']:
            self.mode = False
        if data['RB']:
            self.mode = True

        if data['dpad_up']:
            self.speed = 1
        elif data['dpad_right']:
            self.speed = 0.75
        elif data['dpad_left']:
            self.speed = 0.5
        elif data['dpad_down']:
            self.speed = 0.25
        
        if self.mode:
            thrusters = thruster_mix(data['left_y'],data['left_x'],data['lt']-data['rt'],data['right_x'],data['right_y'],0)
        else:
            thrusters = thruster_mix(data['left_y'],data['left_x'],data['lt']-data['rt'],0,0, data['right_x'])
        
        thrusters = speed_ctrl(thrusters,self.speed)
        disp_mode = "Pitch/Roll" if self.mode else "Yaw"
        per_pow = self.speed * 100
        self.get_logger().info("Thrusters: " + ", ".join(f"{x:.3f}" if isinstance(x, float) else str(x) for x in thrusters) + f" Speed={per_pow}% Power, Mode={disp_mode}")



def main(args=None):
    rclpy.init(args=args)
    node = ControllerSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
