
import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.action.server import ServerGoalHandle
from rclpy.node import Node

from interface.actions import Mapping
# import pyzed.sl as sl
# import gi
# gi.require_version('Gst', '1.0')
# gi.require_version('GLib', '2.0')
# from gi.repository import Gst, GLib
# import threading

import sys
import numpy as np
import pyzed.sl as sl
import gi

import subprocess

gi.require_version('Gst', '1.0')
from gi.repository import Gst

DEST_IP   = "192.168.1.196"
DEST_PORT = 5600
WIDTH     = 1280
HEIGHT    = 720
FPS       = 15
BITRATE   = 4000
# ───────────────────────


class MappingActionServer(Node):
    def __init__(self):
        super().__init__('mapping_action_server')
        self._action_server = ActionServer(
            self,
            Mapping,
            'mapping',
            goal_callback=self.goal_callback,
            execute_callback=self.execute_callback,
            cancel_callback=self.cancel_callback)
        
        self.running = False
        
    def goal_callback(self, goal_request):
        if self.running:
            return GoalResponse.REJECT
        else:
            return GoalResponse.ACCEPT

    def execute_callback(self, goal_handle):
        goal = goal_handle.request
        feedback = Mapping.Feedback()
        
        self.running = True
        zed = self.open_zed()
        mesh = sl.Mesh()
        # i = 0
        try:
            while self.running:
                if (zed.grab() == sl.ERROR_CODE.SUCCESS) :
                    # In background, spatial mapping will use new images, depth and pose to create and update the mesh. No specific functions are required here
                    mapping_state = zed.get_spatial_mapping_state()

                    # Print spatial mapping state
                    # print("\rImages captured: {0} / 60 || {1}".format(i, mapping_state))
                    # i = i+1
            # print('\n')
            
            zed.extract_whole_spatial_map(mesh) # Extract the whole mesh
            mesh.filter(sl.MESH_FILTER.LOW) # Filter the mesh (remove unnecessary vertices and faces)
            # mesh.save("mesh.obj") # Save the mesh in an obj file
            print("mesh wouldve been built, discarding")
            
            # Disable tracking and mapping and close the camera
            zed.disable_spatial_mapping()
            zed.disable_positional_tracking()
            zed.close()
            return 0

        except KeyboardInterrupt:
            print("\nStopping...")

        finally:
            # pipeline.set_state(Gst.State.NULL)
            zed.close()
    
    def cancel_callback(self):
        self.running = False
        #scp the results back to operator through ip
        result = subprocess.run(["scp",""])
        return CancelResponse.ACCEPT
    
    def open_zed(self):
        zed = sl.Camera()
        init = sl.InitParameters()
        init.camera_resolution = sl.RESOLUTION.HD720
        init.camera_fps = FPS
        init.depth_mode = sl.DEPTH_MODE.PERFORMANCE
        init.coordinate_units = sl.UNIT.METER

        err = zed.open(init)
        if err != sl.ERROR_CODE.SUCCESS:
            print(f"ZED open failed: {err}")
            sys.exit(1)

        print("ZED camera opened")
        
        
        tracking_parameters = sl.PositionalTrackingParameters()
        err = zed.enable_positional_tracking(tracking_parameters)
        if (err != sl.ERROR_CODE.SUCCESS):
            print("ERROR HERE")
            exit(-1)
            
        mapping_parameters = sl.SpatialMappingParameters()
        err = zed.enable_spatial_mapping(mapping_parameters)
        if (err != sl.ERROR_CODE.SUCCESS):
            exit(-1)

        return zed
    
    # def make_pipeline(self):
    #     Gst.init(None)

    #     desc = (
    #         f"appsrc name=src is-live=true block=true format=time "
    #         f"caps=video/x-raw,format=RGB,width={WIDTH},height={HEIGHT},framerate={FPS}/1 ! "
    #         "videoconvert ! "
    #         "video/x-raw,format=I420 ! "
    #         f"x264enc bitrate={BITRATE} speed-preset=ultrafast tune=zerolatency key-int-max=30 ! "
    #         "rtph264pay pt=96 config-interval=1 ! "
    #         f"udpsink host={DEST_IP} port={DEST_PORT}"
    #     )

    #     pipeline = Gst.parse_launch(desc)
    #     appsrc = pipeline.get_by_name("src")

    #     appsrc.set_property("is-live", True)
    #     appsrc.set_property("format", Gst.Format.TIME)

    #     return pipeline, appsrc


def main(args=None):
    rclpy.init(args=args)

    mapping_action_server = MappingActionServer()

    rclpy.spin(mapping_action_server)


if __name__ == '__main__':
    main()