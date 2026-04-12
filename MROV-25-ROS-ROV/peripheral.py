import rclpy
from rclpy.node import Node

from std_msgs.msg import String
import json
import sys

import serial

# class for exposing peripherals from STM
class PeripheralPublisher(Node):
    def __init__(self):
        pass

def main(args=None):

    rclpy.init(args=args)

    periph_pub = PeripheralPublisher()

    rclpy.spin(periph_pub)

    periph_pub.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()