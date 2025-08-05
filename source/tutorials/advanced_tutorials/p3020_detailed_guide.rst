.. _p3020_detailed_guide:

P3020 MoveIt2 & ros2_control Integration Guide
==============================================

This document provides detailed configuration instructions for integrating the P3020 model (5 DOF) into the ROS 2 Jazzy + MoveIt 2 + ros2_control framework. It also applies to other Doosan models with different degrees of freedom (DoF), with necessary adjustments.

The P3020 model includes a dummy joint (`joint_4`) which is fixed and excluded from control execution.



1. URDF Configuration
---------------------

**File**: `dsr_description2/urdf/p3020.urdf`

- Use `type="fixed"` for passive or dummy joints.
- Include inertial parameters for all links, including dummy ones.
- Ensure all active joints (`joint_1`, `joint_2`, `joint_3`, `joint_5`, `joint_6`) are defined as `revolute` or `continuous`.

**Example**:

.. code-block:: xml

   <joint name="joint_4" type="fixed">
     <origin xyz="0 -0.89 -0.1731" rpy="1.5708 0 0"/>
     <parent link="link_3"/>
     <child link="link_4"/>
   </joint>



2. Xacro Modifications
----------------------

2.1 **ros2_control.xacro**

**File**: `dsr_description2/config/ros2_control.xacro`

- Declare command and state interfaces only for **controllable joints**.
- Remove or comment out fixed joints from interface declarations.

2.2 **urdf.xacro**

**File**: `dsr_description2/urdf/p3020.urdf.xacro`

- Imports macro files like `macro.p3020.white.xacro`.
- Fixed joints (e.g., `joint_4`) must be defined as `type="fixed"` in those macros.

2.3 **dsr.ros2_control.xacro** (MoveIt mock control)

**File**: `dsr_moveit_config_p3020/config/dsr.ros2_control.xacro`

- Uses `mock_components/GenericSystem`.
- Ensure joint list excludes fixed joints.
- References `initial_positions.yaml` for default values.

2.4 **MoveIt URDF Xacro**

**File**: `dsr_moveit_config_p3020/config/p3020.urdf.xacro`

- Loads `dsr_description2` macros
- Includes `dsr.ros2_control.xacro` for simulated control



3. YAML Configuration
---------------------

3.1 **initial_positions.yaml**

**File**: `dsr_moveit_config_p3020/config/initial_positions.yaml`

- Remove or comment out fixed joints:

.. code-block:: yaml

   initial_positions:
     joint_1: 0.0
     joint_2: 0.0
     joint_3: 0.0
     # joint_4: 0.0
     joint_5: 0.0
     joint_6: 0.0

3.2 **joint_limits.yaml**

**File**: `dsr_moveit_config_p3020/config/joint_limits.yaml`

- Remove `joint_4` and define limits for only movable joints.

3.3 **moveit_controllers.yaml**

**File**: `dsr_moveit_config_p3020/config/moveit_controllers.yaml`

- Define `dsr_moveit_controller` with movable joint names only.

3.4 **ros2_controllers.yaml**

**File**: `dsr_moveit_config_p3020/config/ros2_controllers.yaml`

- Declares the JointTrajectoryController and joint_state_broadcaster
- `joints:` list must exclude fixed joints

3.5 **dsr_controller2.yaml**

**File**: `dsr_controller2/config/dsr_controller2.yaml`

- Generally generated dynamically from launch
- If used manually, ensure fixed joints are commented out

