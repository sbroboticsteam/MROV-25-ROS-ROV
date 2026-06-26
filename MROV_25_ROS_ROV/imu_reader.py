import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import json
import numpy as np
import threading


class IMUPublisher(Node):
    def __init__(self):
        super().__init__('onboard_imu_publisher')
        self.task = threading.Thread(target=self.poll, args = (self,), daemon=True)
        t.start()

    def poll(self):
        data = None
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                self.get_logger().info(f"[INIT-SERIAL]{line}")
                if line == "IMU-BEGIN":
                    data = ser.read(36)
                    break

        while True:
            data = ser.read(36)  # 9 ints * 4 bytes each
            if len(data) == 36:
                values = struct.unpack("<9i", data)  # 9 little-endian ints
                print(values)

def main(args=None):
    rclpy.init(args=args)
    node = IMUPublisher()
    node.destroy_node()
    rclpy.shutdown()
    

if __name__ == "__main__":
    main()