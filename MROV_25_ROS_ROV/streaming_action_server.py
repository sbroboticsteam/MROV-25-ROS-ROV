import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.action.server import ServerGoalHandle
from rclpy.node import Node

from interface.action import Streaming

import sys
import time
import numpy as np
import psutil
import os
import pyzed.sl as sl
import gi
import subprocess

gi.require_version('Gst', '1.0')
from gi.repository import Gst

DEST_IP = "192.168.1.196"
DEST_PORT = 5600
WIDTH = 1280
HEIGHT = 720
FPS = 30
BITRATE = 8000
SBS_W = WIDTH * 2


class StreamingActionServer(Node):
    def __init__(self):
        super().__init__('streaming_action_server')

        # Init GStreamer once at node startup, not per goal
        Gst.init(None)

        # Track process for CPU/memory feedback
        self._proc = psutil.Process(os.getpid())
        self._proc.cpu_percent(interval=None)  # throw away dummy first reading

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
        if self.running:
            self.get_logger().warn('Stream already active — rejecting goal.')
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        # Only signal the execute loop — let it handle cleanup
        self.get_logger().info('Cancel request received.')
        self.running = False
        return CancelResponse.ACCEPT

    # ------------------------------------------------------------------ #
    # Execute                                                              #
    # ------------------------------------------------------------------ #

    def execute_callback(self, goal_handle: ServerGoalHandle):
        self.running = True  # set here, not in goal_callback
        self.get_logger().info(f'Starting stream → {DEST_IP}:{DEST_PORT}')

        result = Streaming.Result()

        # --- Open ZED and pipeline ---
        zed = self.open_zed()
        if zed is None:
            self.get_logger().error('Failed to open ZED camera.')
            self.running = False
            result.success = False
            result.message = 'ZED camera failed to open'
            goal_handle.abort()
            return result

        pipeline, appsrc = self.make_pipeline()
        self.pipe = pipeline
        pipeline.set_state(Gst.State.PLAYING)

        mat_l = sl.Mat()
        mat_r = sl.Mat()
        runtime = sl.RuntimeParameters()

        pts = 0
        duration = int(1e9 / FPS)
        frames_sent = 0
        feedback = Streaming.Feedback()

        self.get_logger().info(f'Streaming {SBS_W}x{HEIGHT} @ {FPS}fps')

        # --- Main loop ---
        while self.running:
            if zed.grab(runtime) != sl.ERROR_CODE.SUCCESS:
                continue

            zed.retrieve_image(mat_l, sl.VIEW.LEFT)
            zed.retrieve_image(mat_r, sl.VIEW.RIGHT)

            sbs = np.concatenate(
                [mat_l.get_data(), mat_r.get_data()],
                axis=1
            )

            buf = Gst.Buffer.new_wrapped(sbs.tobytes())
            buf.pts = pts
            buf.duration = duration
            pts += duration
            frames_sent += 1

            ret = appsrc.emit("push-buffer", buf)
            if ret != Gst.FlowReturn.OK:
                self.get_logger().error(f'push-buffer error: {ret}')
                break

            # Publish feedback every 30 frames (~1 second at 30fps)
            if frames_sent % FPS == 0:
                feedback.frames_sent = frames_sent
                feedback.current_fps = float(FPS)
                feedback.pipeline_status = 'RUNNING'
                feedback.cpu_percent = self._proc.cpu_percent(interval=None)
                feedback.memory_mb = self._proc.memory_info().rss / 1024 / 1024
                goal_handle.publish_feedback(feedback)

        # --- Cleanup ---
        pipeline.set_state(Gst.State.NULL)
        self.pipe = None
        zed.close()
        self.running = False

        result.total_frames_sent = frames_sent

        if goal_handle.is_cancel_requested:
            result.success = True
            result.message = 'Stream stopped by client'
            goal_handle.canceled()
            self.get_logger().info(f'Stream canceled after {frames_sent} frames.')
        else:
            # Loop exited due to push-buffer error or other internal failure
            result.success = False
            result.message = 'Stream stopped due to pipeline error'
            goal_handle.abort()
            self.get_logger().error('Stream aborted due to pipeline error.')

        return result

    # ------------------------------------------------------------------ #
    # ZED setup                                                            #
    # ------------------------------------------------------------------ #

    def open_zed(self):
        zed = sl.Camera()
        init = sl.InitParameters()
        init.camera_resolution = sl.RESOLUTION.HD720
        init.camera_fps = FPS
        init.depth_mode = sl.DEPTH_MODE.PERFORMANCE
        init.coordinate_units = sl.UNIT.METER

        err = zed.open(init)
        if err != sl.ERROR_CODE.SUCCESS:
            self.get_logger().error(f'ZED open failed: {err}')
            return None

        self.get_logger().info('ZED camera opened.')

        tracking_parameters = sl.PositionalTrackingParameters()
        err = zed.enable_positional_tracking(tracking_parameters)
        if err != sl.ERROR_CODE.SUCCESS:
            self.get_logger().error(f'Positional tracking failed: {err}')
            zed.close()
            return None

        mapping_parameters = sl.SpatialMappingParameters()
        err = zed.enable_spatial_mapping(mapping_parameters)
        if err != sl.ERROR_CODE.SUCCESS:
            self.get_logger().error(f'Spatial mapping failed: {err}')
            zed.close()
            return None

        return zed

    # ------------------------------------------------------------------ #
    # GStreamer pipeline                                                    #
    # ------------------------------------------------------------------ #

    def make_pipeline(self):
        desc = (
            f"appsrc name=src is-live=true block=true format=time "
            f"caps=video/x-raw,format=BGRA,width={SBS_W},height={HEIGHT},framerate={FPS}/1 ! "
            "videoconvert ! "
            "video/x-raw,format=I420 ! "
            f"x264enc bitrate={BITRATE} speed-preset=ultrafast tune=zerolatency key-int-max=30 ! "
            "rtph264pay pt=96 config-interval=1 ! "
            f"udpsink host={DEST_IP} port={DEST_PORT}"
        )

        pipeline = Gst.parse_launch(desc)
        appsrc = pipeline.get_by_name("src")
        appsrc.set_property("is-live", True)
        appsrc.set_property("format", Gst.Format.TIME)

        return pipeline, appsrc


# ------------------------------------------------------------------ #
# Entry point                                                          #
# ------------------------------------------------------------------ #

def main(args=None):
    rclpy.init(args=args)
    node = StreamingActionServer()
    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    rclpy.shutdown()


if __name__ == '__main__':
    main()