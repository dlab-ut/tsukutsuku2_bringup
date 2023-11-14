import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LoadComposableNodes
from launch_ros.actions import Node
from launch_ros.descriptions import ComposableNode
from nav2_common.launch import RewrittenYaml
from launch import substitutions

# revised from https://navigation.ros.org/tutorials/docs/navigation2_with_keepout_filter.html#configure-costmap-filter-info-publisher-server

def generate_launch_description():
    # Get the launch directory
    # costmap_filters_demo_dir = get_package_share_directory('nav2_costmap_filters_demo')

    # Create our own temporary YAML files that include substitutions
    lifecycle_nodes = ['filter_mask_server', 'costmap_filter_info_server']

    # Parameters
    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    mask_yaml_file = LaunchConfiguration('mask')

    # Declare the launch arguments
    declare_namespace_cmd = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Top-level namespace')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true')

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart', default_value='true',
        description='Automatically startup the nav2 stack')

    declare_params_file_cmd = DeclareLaunchArgument(
            'params_file',
            default_value=[substitutions.TextSubstitution(text=os.path.join(
                get_package_share_directory('tsukutsuku2_bringup'), 'config', '')), substitutions.TextSubstitution(text='filter_params.yaml')],
            description='Full path to the ROS 2 parameters file to use')

    declare_mask_yaml_file_cmd = DeclareLaunchArgument(
            'mask',
            default_value="/home/tsukutsuku/maps/campus/ogm/binary_mask.yaml",
            description='Full path to filter mask yaml file to load')

    # Make re-written yaml
    param_substitutions = {
        'use_sim_time': use_sim_time,
        'yaml_filename': mask_yaml_file}

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=namespace,
        param_rewrites=param_substitutions,
        convert_types=True)

    # Nodes launching commands
    start_lifecycle_manager_cmd = Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_costmap_filters',
            namespace=namespace,
            output='screen',
            emulate_tty=True,  # https://github.com/ros2/launch/issues/188
            parameters=[{'use_sim_time': use_sim_time},
                        {'autostart': autostart},
                        {'node_names': lifecycle_nodes}])

    start_map_server_cmd = Node(
            package='nav2_map_server',
            executable='map_server',
            name='filter_mask_server',
            namespace=namespace,
            output='screen',
            emulate_tty=True,  # https://github.com/ros2/launch/issues/188
            parameters=[configured_params])

    start_costmap_filter_info_server_cmd = Node(
            package='nav2_map_server',
            executable='costmap_filter_info_server',
            name='costmap_filter_info_server',
            namespace=namespace,
            output='screen',
            emulate_tty=True,  # https://github.com/ros2/launch/issues/188
            parameters=[configured_params])
    
    load_composable_nodes = LoadComposableNodes(
        target_container="",
        composable_node_descriptions=[
            ComposableNode(
                package='nav2_map_server',
                plugin='nav2_map_server::MapServer',
                name='filter_mask_server',
                parameters=[configured_params]),
            ComposableNode(
                package='nav2_map_server',
                plugin='nav2_map_server::CostmapFilterInfoServer',
                name='costmap_filter_info_server',
                parameters=[configured_params],
            ),
            ComposableNode(
                package='nav2_lifecycle_manager',
                plugin='nav2_lifecycle_manager::LifecycleManager',
                name='lifecycle_manager_filter_server',
                parameters=[{'use_sim_time': use_sim_time,
                             'autostart': autostart,
                             'node_names': lifecycle_nodes}]),
        ]
    )

    ld = LaunchDescription()

    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_autostart_cmd)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(declare_mask_yaml_file_cmd)

    ld.add_action(start_lifecycle_manager_cmd)
    ld.add_action(start_map_server_cmd)
    ld.add_action(start_costmap_filter_info_server_cmd)

    # ld.add_action(load_composable_nodes)

    return ld