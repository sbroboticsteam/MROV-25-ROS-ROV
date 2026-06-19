from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        Node(
            package='MROV_25_ROS_ROV',
            executable='serial_map',
            name='serial_map',
            output='screen'
        ),
        Node(
            package='MROV_25_ROS_ROV',
            executable='rov_input_subscriber',
            name='rov_input_subscriber',
            output='screen'
        ),
        Node(
            package='MROV_25_ROS_ROV',
            executable='arm_input_subscriber',
            name='arm_input_subscriber',
            output='screen'
        ),
        Node(
            package='MROV_25_ROS_ROV',
            executable='streaming_server',
            name='streaming_server',
            output='screen'
        )
    ])