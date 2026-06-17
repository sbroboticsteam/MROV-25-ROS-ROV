import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32MultiArray
import json
import numpy as np

# def wrist_differential()

class ArmControllerSubscriber(Node):
    def __init__(self):
        super().__init__('arm_controller_subscriber')
        # changes from entire arm control to differential wrist control
        self.wrist_mode = False
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
                
        data['right_x'] *= -1
        data['right_y'] *= -1
        data['left_x'] *= -1
        data['left_y'] *= -1

        if data['dpad_up']:
            self.rate = 1.0
        elif data['dpad_right']:
            self.rate = 0.75
        elif data['dpad_left']:
            self.rate = 0.5
        elif data['dpad_down']:
            self.rate = 0.25
            
        # if data["RB"]:
        #     self.wrist_mode = not self.wrist_mode # toggles wrist mode
        
        # hold for wrist mode
        self.wrist_mode = False
        if data["RB"]:
            self.wrist_mode = True

        deadzone = 0.2
        
        # prox controls up and down movement
        prox = data["left_y"]
        prox = self.rate * np.sign(data["left_y"]) if abs(data["left_y"]) > deadzone else 0

        #distal controls the 2nd joint from the wirst - elbow movement
        dist = self.rate * np.sign(data["right_y"]) if abs(data["right_y"]) > deadzone else 0
        # wrist = self.rate
        
        #clasp is the claw actuation
        clasp = self.rate * (2 * data["LB"] - 1) # should act like a toggle, but 1 or -1

        #zed, no calculation, followed by an extra servo
        
        #stepper calculations
        #shoulder joint, this is side to side motion of the arm
        shoulder = data["left_x"]
        
        #wrist calculations, split into two
        # wrist = data['rt'] - data["lt"]
        wristL = 0
        wristR = 0
        if self.wrist_mode:
            # lock other joints
            prox = 0
            dist = 0
            
            wrist_pitch = data['right_y']
            wrist_roll = data['right_x']
            
            wristL = wrist_pitch + wrist_roll
            wristR = wrist_roll - wrist_pitch
            
            
        out_msg = Float32MultiArray()
        joints = np.array([prox, dist, clasp, 0, 0, shoulder, wristL, wristR]) 
        out_msg.data = joints.astype(float).tolist()
        self.arm_pub.publish(out_msg)


        # per_pow = self.rate * 100
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