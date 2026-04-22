import rclpy
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle
from rclpy.node import Node

from interface.action import Streaming


class StreamingActionClient(Node):
    def __init__(self):
        super().__init__('streaming_action_client')
        self._client = ActionClient(self, Streaming, 'streaming')
        self._goal_handle: ClientGoalHandle = None

    def start_stream(self):
        self.get_logger().info('Waiting for streaming action server...')
        self._client.wait_for_server()

        goal = Streaming.Goal()
        goal.width = 1280
        goal.height = 720
        goal.framerate = 30
        goal.encoding = 'BGRA'

        self.get_logger().info('Sending stream goal...')
        send_future = self._client.send_goal_async(
            goal,
            feedback_callback=self._feedback_callback,
        )
        send_future.add_done_callback(self._goal_response_callback)

    def stop_stream(self):
        if self._goal_handle is None:
            self.get_logger().warn('No active stream to stop.')
            return

        self.get_logger().info('Sending cancel request...')
        cancel_future = self._goal_handle.cancel_goal_async()
        cancel_future.add_done_callback(self._cancel_callback)

    def _goal_response_callback(self, future):
        self._goal_handle = future.result()

        if not self._goal_handle.accepted:
            self.get_logger().warn('Goal rejected — a stream may already be running.')
            self._goal_handle = None
            return

        self.get_logger().info('Goal accepted — stream is starting.')
        result_future = self._goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

    def _feedback_callback(self, feedback_msg):
        fb = feedback_msg.feedback
        self.get_logger().info(
            f'[{fb.pipeline_status}] '
            f'frames={fb.frames_sent} | '
            f'fps={fb.current_fps:.1f} | '
            f'cpu={fb.cpu_percent:.1f}% | '
            f'mem={fb.memory_mb:.1f}MB'
        )

    def _result_callback(self, future):
        result = future.result().result
        self._goal_handle = None

        if result.success:
            self.get_logger().info(
                f'Stream ended cleanly. '
                f'Frames sent: {result.total_frames_sent} | '
                f'{result.message}'
            )
        else:
            self.get_logger().error(
                f'Stream failed: {result.message} '
                f'(frames sent before failure: {result.total_frames_sent})'
            )

    def _cancel_callback(self, future):
        cancel_response = future.result()
        if len(cancel_response.goals_canceling) > 0:
            self.get_logger().info('Cancel accepted — stream is stopping.')
        else:
            self.get_logger().warn('Cancel was rejected — stream may have already stopped.')


def main(args=None):
    rclpy.init(args=args)
    client = StreamingActionClient()
    client.start_stream()

    try:
        rclpy.spin(client)
    except KeyboardInterrupt:
        client.get_logger().info('Keyboard interrupt — stopping stream.')
        client.stop_stream()
        import time
        time.sleep(1.0)
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()