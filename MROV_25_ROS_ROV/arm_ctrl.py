import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32MultiArray
import json
import numpy as np

# def wrist_differential()

class ArmControllerSubscriber(Node):
    def __init__(self):
        super().__init__('arm_controller_subscriber')

        self.mode = True
        self.rate = 1.0

        self.sub = self.create_subscription(
            String,
            '/controller2/full_state',
            self.cb,
            10
        )

        self.arm_pub = self.create_publisher(
            Float32MultiArray,
            '/arm_commands',
            10
        )

        self.get_logger().info("Arm Controller subscriber + arm publisher ready")


    def cb(self, msg: String):
        data = json.loads(msg.data)
                
        data['right_y'] *= -1
        data['left_y'] *= -1

        if data['dpad_up']:
            self.rate = 1.0
        elif data['dpad_right']:
            self.rate = 0.75
        elif data['dpad_left']:
            self.rate = 0.5
        elif data['dpad_down']:
            self.rate = 0.25

        deadzone = 0.2
        
        prox = data["left_y"]
        prox = self.rate * np.sign(data["left_y"]) if abs(data["left_y"]) > deadzone else 0
        # prox = 0

        dist = self.rate * np.sign(data["right_y"]) if abs(data["right_y"]) > deadzone else 0
        # wrist = self.rate
        
        clasp = self.rate * (2 * data["LB"] - 1) # should act like a toggle, but 1 or -1

        out_msg = Float32MultiArray()
        joints = np.array([prox, dist, clasp, 0]) #TODO: include stepper values for base, wristL, wristR
        out_msg.data = joints.astype(float).tolist()
        self.arm_pub.publish(out_msg)
        per_pow = self.rate * 100

        # self.get_logger().info(
        #     "Arm -> " +
        #     " | ".join(f"T{i}:{float(v):+.3f}" for i, v in enumerate(joints)) +
        #     f" | Flow Rate={per_pow:.0f}% "
        # )

def main(args=None):
    rclpy.init(args=args)
    node = ArmControllerSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()