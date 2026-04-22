import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

# from action_tutorials_interfaces.action import Fibonacci
from interface.action import Mapping


class MappingActionClient(Node):

    def __init__(self):
        super().__init__('mapping_action_client')
        self._action_client = ActionClient(self, Mapping, 'mapping')

    def send_goal(self, order):
        goal_msg = Mapping.Goal()
        goal_msg.order = order

        self._action_client.wait_for_server()

        return self._action_client.send_goal_async(goal_msg)


def main(args=None):
    rclpy.init(args=args)

    action_client = MappingActionClient()

    future = action_client.send_goal(10)

    rclpy.spin_until_future_complete(action_client, future)


if __name__ == '__main__':
    main()