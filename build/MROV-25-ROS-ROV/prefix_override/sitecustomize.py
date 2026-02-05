import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/germangiraffe/Documents/tester/ros2_ws/src/MROV-25-ROS-ROV/install/MROV-25-ROS-ROV'
