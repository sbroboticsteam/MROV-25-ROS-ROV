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
        self.speed = 1.0

        self.sub = self.create_subscription(
            String,
            '/controller2/full_state',
            self.cb,
            10
        )

        self.thruster_pub = self.create_publisher(
            Float32MultiArray,
            '/arm_commands',
            10
        )

        self.get_logger().info("Arm Controller subscriber + arm publisher ready")


    def cb(self, msg: String):
        data = json.loads(msg.data)
                
        data['right_y'] *= -1
        data['left_y'] *= -1

        k = 0.25
        deadzone = 0.2
        
        prox = k * (0) # ignoring for now
        prox = (1 if data["left_y"] > deadzone else data["left_y"]) 
        prox *= k
        
        dist = (1 if data["right_y"] > deadzone else data["right_y"]) 
        dist = -1 if dist < -deadzone else 0 
        dist *= k
        # wrist = k
        
        clasp = k * data["LB"] # should act like a toggle 

        out_msg = Float32MultiArray()
        joints = np.array([prox, dist, clasp]) #TODO: include stepper values for base, wristL, wristR
        out_msg.data = joints.astype(float).tolist()
        self.thruster_pub.publish(out_msg)
        per_pow = k * 100

        self.get_logger().info(
            "Arm -> " +
            " | ".join(f"T{i}:{float(v):+.3f}" for i, v in enumerate(joints)) +
            f" | Flow Rate={per_pow:.0f}% "
        )

def main(args=None):
    rclpy.init(args=args)
    node = ArmControllerSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
