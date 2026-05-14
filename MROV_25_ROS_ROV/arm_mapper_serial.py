import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import serial
import time


class ArmMapperSerial(Node):

    def __init__(self):
        super().__init__('arm_mapper_serial')

        # ==========================
        # CONSTANTS
        # ==========================
        self.LOW = 1000
        self.HIGH = 2000
        self.MID = (self.LOW + self.HIGH) / 2.0

        # ==========================
        # SERIAL SETUP
        # ==========================
        self.port = '/dev/ttyUSB0'   # CHANGE if needed
        self.baudrate = 115200

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # allow device reset
            self.get_logger().info(f"Serial connected on {self.port}")
        except Exception as e:
            self.get_logger().error(f"Serial connection failed: {e}")
            self.ser = None

        # ==========================
        # ROS SUBSCRIBER
        # ==========================
        self.sub = self.create_subscription(
            Float32MultiArray,
            '/arm_commands',
            self.callback,
            10
        )

        self.get_logger().info("Arm Mapper Serial Node Ready")

    # ==========================
    # Mapping Function
    # ==========================
    def map_value(self, x):
        return int(self.MID + x * (self.HIGH - self.MID))

    # ==========================
    # Callback
    # ==========================
    def callback(self, msg: Float32MultiArray):
        if self.ser is None:
            return

        data = msg.data

        # Map all values
        mapped = [self.map_value(x) for x in data]

        # Convert to CSV string - assuming 4 servos max for now
        # Add padding to reach exactly 4 servos
        servos = mapped[:4]
        while len(servos) < 4:
            servos.append(1500)

        import struct
        packet = b''
        for value in servos:
            packet += struct.pack('<i', value)

        try:
            self.ser.write(packet)
        except Exception as e:
            self.get_logger().error(f"Serial write failed: {e}")

        # Debug
        self.get_logger().info(
            "Sent Arm: " + ", ".join(str(v) for v in servos)
        )


def main(args=None):
    rclpy.init(args=args)
    node = ArmMapperSerial()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()