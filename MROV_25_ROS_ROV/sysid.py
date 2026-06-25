import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.action.server import ServerGoalHandle
from rclpy.node import Node

from interface.action import SysID

import sys
import time
import numpy as np
import psutil
import os
import pyzed.sl as sl
import gi
import subprocess

class SysIDAction(Node):
    def __init__(self):
        super().__init__('sysid_action_server')

        self._action_server = ActionServer(
            self,
            Streaming,
            'streaming',
            goal_callback=self.goal_callback,
            execute_callback=self.execute_callback,
            cancel_callback=self.cancel_callback,
        )

        self.running = False
        self.pipe = None

    # ------------------------------------------------------------------ #
    # Goal / cancel callbacks                                              #
    # ------------------------------------------------------------------ #

    def goal_callback(self, goal_request):
        pass

    def cancel_callback(self, goal_handle):
        pass

    # ------------------------------------------------------------------ #
    # Execute                                                              #
    # ------------------------------------------------------------------ #

    def execute_callback(self, goal_handle: ServerGoalHandle):
        pass

        # --- Main loop ---


# ------------------------------------------------------------------ #
# Entry point                                                          #
# ------------------------------------------------------------------ #

def main(args=None):
    rclpy.init(args=args)
    node = SysIDAction()
    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    rclpy.shutdown()


if __name__ == '__main__':
    main()