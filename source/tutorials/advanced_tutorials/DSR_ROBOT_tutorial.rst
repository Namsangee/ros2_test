.. _DSR_ROBOT_tutorial:

DSR_ROBOT2 Library Tutorial
==================

This tutorial provides an overview of the ``DSR_ROBOT2`` library and instructions on how to use it for robot control.

The ``DSR_ROBOT2`` library offers a high-level Python interface for controlling the DSR robot within the ROS 2 ecosystem. It is designed to simplify robot manipulation by providing a user friendly API.

Architecture
----------


The ``DSR_ROBOT2`` package acts as a ROS 2 wrapper, enabling robot control through Python scripting. The architecture is composed of the following layers:

.. image:: ../../_static/tutorial/ros2_interface.png
     :alt: Robot Model Preview
     :width: 800px
     :align: center

*   ``DSR_ROBOT2`` (Python Interface): The primary Python library that functions as a ROS 2 client. It publishes command messages via topics and interacts with the controller node through services.
*   ``dsr_controller2``: A ROS 2 node that serves as the bridge between the ROS 2 ecosystem and the robot's native control library. It subscribes to command topics and exposes services, which are then translated into calls to the ``DRFL``.
*   ``DRFL`` (Doosan Robot Framework Library): A C++ API that handles direct communication with the robot's core controller software (``DRCF``).
*   ``DRCF`` (Doosan Robot Control Framework): The low-level controller software running on the robot hardware or in the emulator.


Usage
----------

.. note::
   For practical examples, please refer to the ``dsr_example2`` package.

This section provides a step-by-step walkthrough of the essential components for controlling the robot using the ``DSR_ROBOT2`` library.

**1. Initializing the Robot Configuration**

Before any operation, you must specify the robot's ID and model name. The ``DR_init`` module is used to store this configuration, which will be used by the library to connect to the correct robot controller.

.. code-block:: python

    import DR_init
    ROBOT_ID   = "dsr01"
    ROBOT_MODEL= "m1013"
    DR_init.__dsr__id   = ROBOT_ID
    DR_init.__dsr__model = ROBOT_MODEL

**2. Setting up the ROS 2 Node**

Communication in ROS 2 is handled through nodes. You must initialize the `rclpy` library and create a node. This node is then assigned to the `DR_init` module, enabling the library to communicate over the ROS 2 network.

.. code-block:: python

    import rclpy

    rclpy.init(args=args)
    node = rclpy.create_node('single_robot_simple_py', namespace=ROBOT_ID)
    DR_init.__dsr__node = node

**3. Importing Robot Control Functions Needed**

The core functionalities for robot control, such as movement commands and position definitions, are imported from the ``DSR_ROBOT2`` library.

.. code-block:: python

    from DSR_ROBOT2 import movej, movejx, movesj, movesx, movel, movec
    from DSR_ROBOT2 import posj, posx
    from DSR_ROBOT2 import ROBOT_MODE_AUTONOMOUS

**4. Setting the Robot's Operational Mode and Speed**

Before sending motion commands or settings, the robot must be set to the correct mode.

- ``ROBOT_MODE_AUTONOMOUS`` allows the robot to be actually controlled and moved. 
- ``ROBOT_MODE_MANUAL`` allows for robot settings, such as adding tools at the end-effector.

You can also set default global velocities and accelerations if you want.

.. code-block:: python

    set_robot_mode(ROBOT_MODE_AUTONOMOUS)

    set_velx(30, 20)    # Set global task speed: 30(mm/sec), 20(deg/sec)
    set_accx(60, 40)    # Set global task acceleration: 60(mm/sec2), 40(deg/sec2)

**5. Defining Positions**

You can define target positions mainly in two primary coordinate systems:

-   **Joint Space** (``posj``): Defines the angular position of each of the robot's six joints.
-   **Task Space** (``posx``): Defines the position (X, Y, Z) and orientation (Roll, Pitch, Yaw) of the robot's end-effector (or tool).

.. code-block:: python

    # Joint space position: (j1, j2, j3, j4, j5, j6)
    p1 = posj(0, 0, 90.0, 0, 90.0, 0)

    # Task space position: (x, y, z, r, p, y)
    x1 = posx(400, 500, 800.0, 0.0, 180.0, 0.0)

**6. Executing a Motion Command**

With a target position defined, you can command the robot to move. The ``movej`` function, for example, moves the robot to a specified joint position. 
You can override the global speed and acceleration for specific movements.

.. code-block:: python

    # Move to joint position p1 with a velocity of 100 deg/s and acceleration of 100 deg/s^2
    movej(p1, vel=100, acc=100)

**7. Launch and Execute**

Setup and build the node. Now you can move the robot as you want.

.. code-block:: bash

  ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py 
  # Run in a new terminal the node you created
  ros2 run <pkg_name> <new_node_name>
  # ex> ros2 run dsr_example single_robot_simple

**8. Additional Motion Commands**

The library provides various other motion commands (e.g., ``movel`` for linear motion, ``movec`` for circular motion) to accommodate different application needs.

Refer to the following link for more informations :

- `ROS2 manual (old version) <https://manual.doosanrobotics.com/en/ros/>`_
- `DRFL manual <https://manual.doosanrobotics.com/en/api/>`_
- `DRL manual <https://manual.doosanrobotics.com/en/programming-manual/>`_

Or the current function list below:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Category
     - Functions
   * - **System Operations**
     - * set_robot_mode(robot_mode)
       * get_robot_mode()
       * set_robot_system(robot_system)
       * get_robot_system()
       * get_robot_state()
       * set_robot_speed_mode(speed_mode)
       * get_robot_speed_mode()
       * set_safe_stop_reset_type(reset_type)
       * get_last_alarm()
       * get_current_pose(space_type)
   * - **Standard Motion (Service-based)**
     - * movej(...)
       * movel(...)
       * movejx(...)
       * movec(...)
       * movesj(...)
       * movesx(...)
       * moveb(...)
       * move_spiral(...)
       * move_periodic(...)
       * move_wait()
       * jog(...)
       * jog_multi(...)
       * trans(...)
       * fkin(...)
       * ikin(...)
       * set_ref_coord(...)
       * move_home()
       * check_motion()
       * change_operation_speed(...)
       * enable_alter_motion(...)
       * alter_motion(...)
       * disable_alter_motion(...)
       * set_singularity_handling(...)
   * - **Real-time & Streaming Motion (Topic-based)**
     - * servoj(...)
       * servol(...)
       * speedj(...)
       * speedl(...)
       * servoj_rt(...)
       * servol_rt(...)
       * speedj_rt(...)
       * speedl_rt(...)
       * torque_rt(...)
       * alter_motion_stream(...)
   * - **Auxiliary Control Operations**
     - * get_control_mode()
       * get_control_space()
       * get_current_posj()
       * get_current_velj()
       * get_desired_posj()
       * get_desired_velj()
       * get_current_posx(...)
       * get_current_velx(...)
       * get_desired_posx(...)
       * get_desired_velx(...)
       * get_current_tool_flange_posx(...)
       * get_current_solution_space()
       * get_current_rotm(...)
       * get_joint_torque()
       * get_external_torque()
       * get_tool_force(...)
       * get_solution_space(...)
       * get_orientation_error(...)
   * - **Force/Stiffness Control**
     - * get_workpiece_weight()
       * reset_workpiece_weight()
       * parallel_axis1(...)
       * parallel_axis2(...)
       * align_axis1(...)
       * align_axis2(...)
       * is_done_bolt_tightening(...)
       * release_compliance_ctrl()
       * task_compliance_ctrl(...)
       * set_stiffnessx(...)
       * calc_coord(...)
       * set_user_cart_coord1(...)
       * set_user_cart_coord2(...)
       * set_user_cart_coord3(...)
       * overwrite_user_cart_coord(...)
       * get_user_cart_coord(...)
       * set_desired_force(...)
       * release_force()
       * check_position_condition(...)
       * check_force_condition(...)
       * check_orientation_condition1(...)
       * check_orientation_condition2(...)
       * coord_transform(...)
   * - **GPIO**
     - * set_digital_output(...)
       * get_digital_input(...)
       * set_tool_digital_output(...)
       * get_tool_digital_input(...)
       * set_analog_output(...)
       * get_analog_input(...)
       * set_mode_analog_output(...)
       * set_mode_analog_input(...)
       * get_digital_output(...)
       * get_tool_digital_output(...)
   * - **Modbus**
     - * set_modbus_output(...)
       * get_modbus_input(...)
       * add_modbus_signal(...)
       * del_modbus_signal(...)
   * - **TCP (Tool Center Point) Operations**
     - * set_current_tcp(...)
       * get_current_tcp()
       * config_create_tcp(...)
       * config_delete_tcp(...)
   * - **Tool Operations**
     - * set_current_tool(...)
       * get_current_tool()
       * config_create_tool(...)
       * config_delete_tool(...)
       * set_tool_shape(...)
   * - **DRL (Doosan Robot Language) Operations**
     - * drl_pause()
       * drl_resume()
       * drl_start(...)
       * drl_stop(...)
       * get_drl_state()
   * - **Real-time (RT) Control**
     - * connect_rt_control()
       * disconnect_rt_control()
       * get_rt_control_output_version_list()
       * get_rt_control_input_version_list()
       * get_rt_control_input_data_list()
       * get_rt_control_output_data_list()
       * start_rt_control()
       * stop_rt_control()
       * set_rt_control_input(...)
       * set_rt_control_output(...)
       * set_velj_rt(...)
       * set_accj_rt(...)
       * set_velx_rt(...)
       * set_accx_rt(...)
       * read_data_rt(...)
       * write_data_rt(...)