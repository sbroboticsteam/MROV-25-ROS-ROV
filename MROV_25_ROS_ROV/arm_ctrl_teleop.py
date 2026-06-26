import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32MultiArray
import json
import numpy as np

import PID

# def wrist_differential()

class TeleopArmControllerSubscriber(Node):
    def __init__(self):
        super().__init__('teleop_arm_controller_subscriber')
        self.controller = PID(np.array([0.5, 0.5, 0.5, 0.5, 0.5]))
        self.latest_physical = None
        # self.sevo_controller = PID(0.5)
        # i might need multiple PID controllers. 
        # actually, each joint might need its own controller
        # i can just make each term a vector and implement element wise multiplication
        self.physical_sub = self.create_subscription(
            Float32MultiArray,
            "/physical_encoders",
            self.
        )
        
        self.controller_sub = self.create_subscription(
            Float32MultiArray,
            "teleop_arm_controller"
            self.cb,
            10
        )

        self.arm_pub = self.create_publisher(
            Float32MultiArray,
            '/arm_commands',
            10
        )

        self.get_logger().info("Teleop Arm Controller Ready")

    def update_physical(self, msg: Float32MultiArray):
        self.latest_physical = np.array(msg.data)


    def cb(self, msg: Float32MultiArray):
        state = np.array(self.latest_physical.data)
        
        setpoint = np.array(msg.data)
        self.controller.setSetpoint(setpoint) # use the teleop arm input array as the set point
        joint_inputs = self.controller.evaluate(state, setpoint)
        
        #publish these inputs appropriately
        
                
def main(args=None):
    rclpy.init(args=args)
    node = TeleopArmControllerSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()