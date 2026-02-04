#!/usr/bin/env python3
"""
Launch file for testing DeviceState message reception in Unity.

This launch file starts:
1. Force Dimension node with low-latency DeviceState publishing
2. ROS-TCP-Endpoint for Unity communication

Prerequisites:
- Unity project must be running with DeviceStateSubscriber script attached
- Force Dimension hardware must be connected (or use disable_hardware:=true)

Usage:
    ros2 launch ros_spheres_environment device_state_test.launch.py
    ros2 launch ros_spheres_environment device_state_test.launch.py disable_hardware:=true
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    # Declare arguments
    disable_hardware_arg = DeclareLaunchArgument(
        'disable_hardware',
        default_value='false',
        description='Set to true to run without hardware (simulation mode)'
    )

    # Config paths
    config_dir = os.path.join(
        get_package_share_directory('ros_spheres_environment'),
        'config'
    )

    unity_config = os.path.join(config_dir, 'device_state_test.yaml')

    # Get launch configuration
    disable_hardware = LaunchConfiguration('disable_hardware')

    # 1. Force Dimension Node with low-latency DeviceState
    force_dimension_node = Node(
        package='force_dimension',
        executable='node',
        name='force_dimension',
        namespace='robot',
        output='screen',
        parameters=[{
            # Hardware settings
            'disable_hardware': disable_hardware,

            # Sampling rate
            'sample_interval_s': 0.001,  # 1 kHz internal sampling

            # DeviceState decimation for 100 Hz publishing
            'feedback_sample_decimation.state': 10,  # 1000/10 = 100 Hz

            # Enable all metrics for testing
            'device_state_metrics.include_position': True,
            'device_state_metrics.include_velocity': True,
            'device_state_metrics.include_orientation': True,
            'device_state_metrics.include_gripper': True,
            'device_state_metrics.include_buttons': True,

            # Force feedback settings
            'enable_force': True,
            'gravity_compensation': True,
            'effector_mass_kg': 0.19,
        }],
        remappings=[
            ('feedback/state', '/robot/feedback/state'),
        ]
    )

    # 2. ROS-TCP-Endpoint for Unity
    unity_endpoint_node = Node(
        package='ros_tcp_endpoint',
        executable='default_server_endpoint',
        name='unity_endpoint',
        output='screen',
        parameters=[unity_config]
    )

    return LaunchDescription([
        disable_hardware_arg,
        force_dimension_node,
        unity_endpoint_node,
    ])
