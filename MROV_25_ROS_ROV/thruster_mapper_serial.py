import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import serial
import time
import struct


class ThrusterMapperSerial(Node):

    def __init__(self):
        super().__init__('thruster_mapper_serial')

        # ==========================
        # CONSTANTS
        # ==========================
        self.LOW = 1100
        self.HIGH = 1900
        self.MID = (self.LOW + self.HIGH) / 2.0

        # State for latest commands
        self.esc_values = [1500] * 8
        self.servo_values = [1500] * 4

        # ==========================
        # SERIAL SETUP
        # ==========================
        self.port = '/dev/ttyACM0'   # CHANGE if needed
        self.baudrate = 115200

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # allow device reset
            self.get_logger().info(f"Serial connected on {self.port}")
        except Exception as e:
            self.get_logger().error(f"Serial connection failed: {e}")
            self.ser = None

        # ==========================
        # ROS SUBSCRIBERS
        # ==========================
        self.sub_thrusters = self.create_subscription(
            Float32MultiArray,
            '/thruster_commands',
            self.thruster_callback,
            10
        )

        self.sub_arm = self.create_subscription(
            Float32MultiArray,
            '/arm_commands',
            self.arm_callback,
            10
        )

        self.get_logger().info("Unified STM Mapper Serial Node Ready")

    # ==========================
    # Mapping Function
    # ==========================
    def map_value(self, x, is_arm=False):
        if is_arm:
            # map arm values from float to 1000-2000
            mid = 1500
            high = 2000
            return int(mid + x * (high - mid))
        else:
            return int(self.MID + x * (self.HIGH - self.MID))

    # ==========================
    # Callbacks
    # ==========================
    def thruster_callback(self, msg: Float32MultiArray):
        data = msg.data
        esc_mapped = [self.map_value(x) for x in data]
        while len(esc_mapped) < 8:
            esc_mapped.append(1500)
        self.esc_values = esc_mapped[:8]
        self.send_serial()

    def arm_callback(self, msg: Float32MultiArray):
        data = msg.data
        arm_mapped = [self.map_value(x, is_arm=True) for x in data]
        while len(arm_mapped) < 4:
            arm_mapped.append(1500)
        self.servo_values = arm_mapped[:4]
        self.send_serial()

    def send_serial(self):
        if self.ser is None:
            return

        all_values = self.esc_values + self.servo_values
        packet = b''
        for value in all_values:
            packet += struct.pack('<i', value)

        try:
            self.ser.write(packet)
        except Exception as e:
            self.get_logger().error(f"Serial write failed: {e}")

        # Debug
        self.get_logger().info(
            "Sent STM: " + ", ".join(str(v) for v in all_values)
        )


def main(args=None):
    rclpy.init(args=args)
    node = ThrusterMapperSerial()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()