import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray


class ROVInputSubscriber(Node):
    def __init__(self):
        super().__init__('rov_input_subscriber')

        self.subscription = self.create_subscription(
            Float64MultiArray,
            '/arm_controller/commands',
            self.command_callback,
            10
        )

        self.get_logger().info('ROV input subscriber started')

    def command_callback(self, msg: Float64MultiArray):
        if len(msg.data) != 4:
            self.get_logger().warn(
                f'Expected 4 values, got {len(msg.data)}'
            )
            return

        left_x, left_y, right_x, right_y = msg.data

        self.get_logger().info(
            f'Received commands | '
            f'LX: {left_x:.2f}, LY: {left_y:.2f}, '
            f'RX: {right_x:.2f}, RY: {right_y:.2f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = ROVInputSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
