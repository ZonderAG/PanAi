import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_panai_sim = get_package_share_directory('panai_sim')
    pkg_panai_desc = get_package_share_directory('panai_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': '-r empty.sdf'}.items()
    )

    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_panai_desc, 'launch', 'rsp.launch.py')),
        launch_arguments={'use_sim_time': 'true'}.items()
    )

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'panai_robot', '-z', '0.1'],
        output='screen'
    )
    
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'
        ],
        output='screen'
    )

    return LaunchDescription([
        gz_sim, rsp, spawn, bridge
    ])
