import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Int32


class ThrusterSplitter(Node):

    def __init__(self):
        super().__init__('thruster_splitter')

        # ==========================
        # HARD-CODED CHANNEL NAMES
        # ==========================
        self.channels = [
            '/rov/bltz',
            '/rov/brtz',
            '/rov/fltz',
            '/rov/frtz',
            '/rov/blt',
            '/rov/brt',
            '/rov/flt',
            '/rov/frt'
        ]

        # Create publishers for each channel (NOW Int32)
        self.pubs = []
        for name in self.channels:
            pub = self.create_publisher(Int32, name, 10)
            self.pubs.append(pub)

        # Subscriber (still Float32MultiArray)
        self.sub = self.create_subscription(
            Float32MultiArray,
            '/thruster_commands',
            self.callback,
            10
        )

        self.get_logger().info("Thruster Splitter Node Ready")

    # ==========================
    # Callback
    # ==========================

    def callback(self, msg: Float32MultiArray):
        data = msg.data

        # Safety check
        if len(data) != len(self.channels):
            self.get_logger().warn(
                f"Expected {len(self.channels)} values, got {len(data)}"
            )
            return

        for i, value in enumerate(data):
            out = Int32()

            # Scale from [-1, 1] → [0, 255]
            scaled = int(round((value + 1.0) * 127.5))

            # Clamp just in case
            scaled = max(0, min(255, scaled))
            if self.channels[i] in ['/rov/frt', '/rov/brt']:
                scaled = 255 - scaled
            out.data = scaled
            self.pubs[i].publish(out)

        # Debug
        self.get_logger().info(
            "Split: " + " | ".join(
                f"{self.channels[i]}={int(max(0, min(255, round((data[i] + 1.0) * 127.5))))}"
                for i in range(len(data))
            )
        )


def main(args=None):
    rclpy.init(args=args)
    node = ThrusterSplitter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()