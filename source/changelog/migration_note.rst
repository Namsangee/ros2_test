.. _migration_note:

Migration fr9m Humble to Jazzy
===============================

This document summarizes the changes applied during the migration from **ROS 2 Humble** to **ROS 2 Jazzy**.  
For detailed code-level differences, please refer to each component section below.

Bringup
-------

**MoveItConfigsBuilder Updates**

- Use `.planning_pipelines()` to explicitly define `planning_plugins`, `default_planning_pipeline`, and `load_all`.
- `default_planning_pipeline` is now **mandatory**; if omitted, runtime errors may occur.
- After `.to_moveit_configs()`, apply `.to_dict()` to consistently pass parameters to both `MoveGroup` and `RViz` nodes.

**Dynamic YAML Configuration**

- New `dynamic_yaml` launch argument enables runtime generation of controller YAML from the robot model.
- The system parses `robot_description` to extract active/passive joints and creates controller YAML dynamically.
- If a specific controller YAML (e.g., `dsr_controller2_<model>.yaml`) is missing, it falls back to `dsr_controller2.yaml`.

**Launch Flow Refactoring**

- Replaced parallel launch with sequential execution using `OnProcessExit`.
- Full node execution sequence:

  ``set_config_node → ros2_control_node → joint_state_broadcaster → dsr_controller2 → dsr_moveit_controller → move_group + RViz2``

- `set_config_node` sets hardware params and triggers `ros2_control_node`.
- `joint_state_broadcaster` is started early to provide `/joint_states` to subscribers.

Hardware Interface (dsr_hw_interface2)
--------------------------------------

**Hardware-Centric Architecture**

- Migrated from `ControllerInterface` (Humble) to `SystemInterface` (Jazzy).
- Initialization steps (DRFL init, callbacks, param parsing) are now handled in hardware layer.
- Lifecycle hooks `on_init()`, `on_configure()`, `on_activate()` are fully respected.

**Callback Refactoring**

- Moved all callbacks (`OnMonitoringState`, `OnMonitoringDataEx`, `OnDisconnected`, `OnLogAlarm`) into the hardware layer.
- Now registered collectively inside `DRHWInterface::on_init()` or `on_activate()` for consistency.

**Flexible DOF & Parameter Parsing**

- Robot metadata (model, dof, gripper) are parsed from `HardwareInfo`.
- Arrays such as `joint_position_`, `joint_velocity_`, `command_` are resized dynamically based on joint count.

**Hardware Index Mapping**

- Introduced `hw_mapping_` to map URDF/SRDF joint names to DRFL internal indices.
- Improves clarity and enables multi-model reuse.

**RT Control Enhancements**

- Conditional use of `rt_host` vs `host` based on DRCF version (e.g., ≥ 3.0 uses `rt_host`).
- Functions like `set_rt_control_output()` and `start_rt_control()` run only in robot mode and non-emulator cases.

**Monitoring Extensions**

- Replaced `OnMonitoringDataCB` with `OnMonitoringDataExCB` and `OnMonitoringCtrlIOExCB`.
- Enables access to force/torque/position data in tool/world/user frames for advanced compliance control.

**Additional Improvements**

- Added real-time error monitoring via `/error` topic using `LogAlarm` callback.
- Emulator mode is auto-detected by checking for loopback IP (`127.0.0.1`).

Xacro Fixes
-----------

- Add `pi`-related expressions as `xacro:property` at the top:

  .. code-block:: xml

     <xacro:property name="double_pi" value="${2.0 * pi}"/>
     <xacro:property name="neg_double_pi" value="${-2.0 * pi}"/>
     <xacro:property name="neg_pi" value="${-1.0 * pi}"/>

- Jazzy's `ros2_control` cannot parse raw expressions like `{2*pi}`.
- Always wrap expressions with `${...}` using `xacro:property`.

SRDF Fixes
----------

- Ensure `<robot name="...">` matches URDF:

  .. code-block:: xml

     <!-- Before -->
     <robot name="dsr">

     <!-- After -->
     <robot name="m1013">

- Jazzy strictly requires that URDF and SRDF use the same robot name.
- Mismatches will trigger: `Semantic description is not specified for the same robot as the URDF`.

_planning.yaml Fixes
---------------------

- Replace `planning_plugin` (string) with `planning_plugins` (string_array).
- Split all adapters into `request_adapters` and `response_adapters`.

  .. code-block:: yaml

     planning_plugins:
       - ompl_interface/OMPLPlanner

     request_adapters:
       - default_planning_request_adapters/ResolveConstraintFrames
       - default_planning_request_adapters/ValidateWorkspaceBounds
       - default_planning_request_adapters/CheckStartStateBounds
       - default_planning_request_adapters/CheckStartStateCollision

     response_adapters:
       - default_planning_response_adapters/AddTimeOptimalParameterization
       - default_planning_response_adapters/ValidateSolution
       - default_planning_response_adapters/DisplayMotionPath

- YAML values must now be written in hyphen-prefixed list format for `string_array`.

QoS Changes
-----------

- Deprecated: ``rmw_qos_profile_*``
- New: Use `rclcpp::QoS` for all publishers/subscribers.

  .. code-block:: cpp

     auto qos = rclcpp::QoS(10).best_effort();
     node->create_subscription<MsgType>("topic", qos, callback);

- Default policy updates (some topics):

  - `reliable` → `best_effort`
  - `transient_local` → `volatile`

