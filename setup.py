from setuptools import find_packages, setup

package_name = 'MROV_25_ROS_ROV'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/main_launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='karamat',
    maintainer_email='karamathasan420@gmail.com',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'rov_input_subscriber = MROV_25_ROS_ROV.ctrl:main',
            'thruster_serial_node = MROV_25_ROS_ROV.serial_thruster_node:main',
            'splitter = MROV_25_ROS_ROV.splitter:main',
            'thruster_mapper_serial = MROV_25_ROS_ROV.thruster_mapper_serial:main',
            'streaming_server = MROV_25_ROS_ROV.streaming_action_server:main',
            'streaming_client = MROV_25_ROS_ROV.streaming_action_client:main'
        ],
    },
)
