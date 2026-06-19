import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Int32, Float64

# takes existing inputs and maps them to the ROS-GZ bridge
class SimMap(Node):

    def __init__(self):
        super().__init__('thruster_splitter')
        self.thruster_topics = [
            '/rov/frt',
            '/rov/frtz',
            '/rov/brt',
            '/rov/brtz',
            '/rov/blt',
            '/rov/bltz',
            '/rov/flt',
            '/rov/fltz'
        ]
        
        # first 5 values are servo values
        # last 3 values are stepper values
        #[prox, dist, clasp, zed, extra]
        self.arm_topics = [
            '/rov/arm1',
            '/rov/arm2',
            None,
            None,
            None,
            '/rov/arm0',
            '/rov/bevelleft',
            '/rov/bevelright'
        ]

        # Create publishers for each channel (NOW Int32)
        self.thruster_pubs = []
        for name in self.thruster_topics:
            pub = self.create_publisher(Int32, name, 10)
            self.thruster_pubs.append(pub)

        # Subscriber (still Float32MultiArray)
        self.thruster_subs = self.create_subscription(
            Float32MultiArray,
            '/thruster_commands',
            self.thruster_callback,
            10
        )
        
        self.arm_pubs = []
        for name in self.arm_topics:
            if name:
                pub = self.create_publisher(Float64, name, 10)
                self.arm_pubs.append(pub)
        
        self.arm_sub = self.create_subscription(
            Float32MultiArray,
            '/arm_commands',
            self.arm_callback,
            10
        )

        self.get_logger().info("Simulation Mapping Node Ready")

    # ==========================
    # Callbacks
    # ==========================

    def thruster_callback(self, msg: Float32MultiArray):
        data = msg.data

        # Safety check
        if len(data) != len(self.thruster_topics):
            self.get_logger().warn(
                f"Expected {len(self.thruster_topics)} values, got {len(data)}"
            )
            return

        outs = []
        for i, value in enumerate(data):
            out = Int32()

            # Scale from [-1, 1] → [0, 255]
            scaled = int(round((value + 1.0) * 127.5))

            # Clamp just in case
            scaled = max(0, min(255, scaled))
            if self.thruster_topics[i] not in ['/rov/frt', '/rov/flt']:
                scaled = 255 - scaled
            if self.thruster_topics[i] in ['/rov/flt', '/rov/frt', '/rov/blt', '/rov/brt']:
                scaled = 255 - scaled
            out.data = scaled
            outs.append(scaled)
            self.thruster_pubs[i].publish(out)

        # Debug
        self.get_logger().info(
            "Thursters: " + " | ".join(
                f"{self.thruster_topics[i]}={outs[i]}"
                for i in range(len(data))
            )
        )
        
    def arm_callback(self, msg: Float32MultiArray):
        data = msg.data
        
        outs = []
        for i, value in enumerate(data):
            out = Float64()
            
            if not self.arm_topics[i]:
                continue
                # scaled = 127
            out.data = value
            outs.append(value)
            self.arm_pubs[i].publish(out)

        # self.get_logger().info(
        #     "Arm: " + " | ".join(
        #         f"{self.arm_topics[i]}={outs[i]}"
        #         for i in range(len(data))
        #     )
        # )

def main(args=None):
    rclpy.init(args=args)
    node = SimMap()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()