import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import serial
import time


class ThrusterSerialNode(Node):

    def __init__(self):
        super().__init__('thruster_serial_node')

        # ===== Serial Setup =====
        self.port = '/dev/ttyUSB0'   # CHANGE if needed
        self.baudrate = 115200

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # allow Arduino reset
            self.get_logger().info(f"Serial connected on {self.port}")
        except Exception as e:
            self.get_logger().error(f"Serial connection failed: {e}")
            self.ser = None

        # ===== ROS Subscriber =====
        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/thruster_commands',
            self.callback,
            10
        )

        self.get_logger().info("Thruster Serial Node Ready")

    # ==========================
    # Callback
    # ==========================

    def callback(self, msg: Float32MultiArray):
        if self.ser is None:
            return

        thrusters = msg.data  # list of 8 floats

        # Convert from [-1,1] to [1100,1900] PWM example
        pwm_values = [
            int(1500 + t * 400) for t in thrusters
        ]

        # Format as CSV line
        serial_string = ",".join(str(v) for v in pwm_values) + "\n"

        try:
            self.ser.write(serial_string.encode())
        except Exception as e:
            self.get_logger().error(f"Serial write failed: {e}")

        # Debug print
        self.get_logger().info(f"Sent PWM: {pwm_values}")


def main(args=None):
    rclpy.init(args=args)
    node = ThrusterSerialNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()