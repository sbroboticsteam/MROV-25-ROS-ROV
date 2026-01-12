import rclpy
import json
from rclpy.node import Node
from std_msgs.msg import String


class ControllerSubscriber(Node):

    def __init__(self):
        super().__init__('controller_sub')
        self.subscription = self.create_subscription(
            String,
            'controller_input',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info('I heard: "%s"' % msg.data)
        controller_dict = json.loads(msg.data)
        #Do wtv with it here


def main(args=None):
    rclpy.init(args=args)

    controller_subscriber = ControllerSubscriber()

    rclpy.spin(controller_subscriber)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    controller_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()