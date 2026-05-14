from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        
        Node(
            package='MROV-25-ROS-ROV',
            executable='mcu_serial_node',
            name='mcu_serial_node',
            output='screen',
            parameters=[{'port': '/dev/ttyUSB0'}]
        ),
        Node(
            package='MROV-25-ROS-ROV',
            executable='rov_input_subscriber',
            name='rov_input_subscriber',
            output='screen'
        ),
        Node(
            package='MROV-25-ROS-ROV',
            executable='arm_input_subscriber',
            name='arm_input_subscriber',
            output='screen'
        ),
       
    ])