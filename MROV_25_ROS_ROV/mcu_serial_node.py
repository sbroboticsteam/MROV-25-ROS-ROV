import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import serial
import time
import struct

class MCU_SerialNode(Node):
    def __init__(self):
        super().__init__('mcu_serial_node')

        self.declare_parameter('port', '/dev/ttyUSB0')
        self.port = self.get_parameter('port').get_parameter_value().string_value
        self.baudrate = 115200

        self.esc_values = [1500] * 8
        self.servo_values = [1500] * 4

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)
            self.get_logger().info(f"Serial connected on {self.port}")
        except Exception as e:
            self.get_logger().error(f"Serial connection failed: {e}")
            self.ser = None

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

        self.timer = self.create_timer(0.05, self.send_packet)

        self.get_logger().info("MCU Serial Node Ready")

    def map_esc(self, val):
        return int(1500 + val * 400)

    def map_servo(self, val):
        return int(1500 + val * 500)

    def thruster_callback(self, msg: Float32MultiArray):
        data = msg.data
        for i in range(min(8, len(data))):
            self.esc_values[i] = self.map_esc(data[i])

    def arm_callback(self, msg: Float32MultiArray):
        data = msg.data
        for i in range(min(4, len(data))):
            self.servo_values[i] = self.map_servo(data[i])

    def send_packet(self):
        if self.ser is None:
            return

        packet = b''
        for value in self.esc_values + self.servo_values:
            packet += struct.pack('<i', value)

        try:
            self.ser.write(packet)
        except Exception as e:
            self.get_logger().error(f"Serial write failed: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = MCU_SerialNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
