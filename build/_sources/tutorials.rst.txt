.. _tutorials:

Tutorials
=========

Launch with **Rviz2**
---------------------

This launch file starts Rviz2 for visualizing the robot model and its state.

**Usage:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py [arguments]

**Arguments:**

*   ``name``: Robot namespace (Default: ``dsr01``)
*   ``host``: IP Address of Doosan Robotics Controller (Default: ``127.0.0.1``)
*   ``port``: Port of Doosan Robotics Controller (Default: ``12345``)
*   ``mode``: Operation mode (``virtual`` or ``real``)
*   ``model``: Robot model name (e.g., ``m1013``)
*   ``color``: Robot color (``white`` or ``blue``)
*   ``rt_host``: Real-time host IP (Default: ``192.168.137.50``)

**Examples:**

**Real Mode:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py mode:=real host:=192.168.137.100 port:=12345 model:=m1013

**Virtual Mode:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py mode:=virtual host:=127.0.0.1 port:=12345 model:=m1013

Launch with **Gazebo Simulation**
---------------------------------

This launch file starts Gazebo simulation with the robot model and Rviz2.

**Usage:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_gazebo.launch.py [arguments]

**Arguments:**

*   ``name``: Robot namespace (Default: ``dsr01``)
*   ``host``: IP Address of Doosan Robotics Controller (Default: ``127.0.0.1``)
*   ``port``: Port of Doosan Robotics Controller (Default: ``12345``)
*   ``mode``: Operation mode (``virtual`` or ``real``)
*   ``model``: Robot model name (e.g., ``m1013``)
*   ``color``: Robot color (``white`` or ``blue``)
*   ``gui``: Start RViz2 (``true`` or ``false``)
*   ``gz``: Use Gazebo simulation (``true`` or ``false``)
*   ``x``, ``y``, ``z``, ``R``, ``P``, ``Y``: Robot location and orientation in Gazebo
*   ``rt_host``: Real-time host IP (Default: ``192.168.137.50``)
*   ``use_sim_time``: Use simulation time (Default: ``true``)

**Examples:**

**Real Mode:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_gazebo.launch.py mode:=real host:=192.168.137.100 model:=m1013

**Virtual Mode:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_gazebo.launch.py mode:=virtual host:=127.0.0.1 port:=12346 name:=dsr01 x:=0 y:=0

To add additional arms for multi-control:

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_spawn_on_gazebo.launch.py mode:=virtual host:=127.0.0.1 port:=12347 name:=dsr02 x:=2 y:=2

**Note:** Ensure each additional arm has a unique ``port``, ``name``, and location (``x``, ``y``) to avoid collisions in Gazebo.

Launch with **MuJoCo Simulation**
---------------------------------

This launch file starts MuJoCo simulation with the robot model and Rviz2.

**Usage:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_mujoco.launch.py [arguments]

**Arguments:**

*   ``name``: Robot namespace (Default: ``dsr01``)
*   ``host``: IP Address of Doosan Robotics Controller (Default: ``127.0.0.1``)
*   ``port``: Port of Doosan Robotics Controller (Default: ``12345``)
*   ``mode``: Operation mode (``virtual`` or ``real``)
*   ``model``: Robot model name (e.g., ``m1013``)
*   ``color``: Robot color (``white`` or ``blue``)
*   ``gui``: Start RViz2 (Default: ``true``)
*   ``mj``: Use MuJoCo simulation (Default: ``true``)
*   ``rt_host``: Real-time host IP (Default: ``192.168.137.50``)
*   ``use_sim_time``: Use simulation time (Default: ``true``)
*   ``gripper``: Use gripper (Default: ``none``)
*   ``scene_path``: Relative path to MuJoCo scene XML file (e.g., ``demo/slope_demo_scene.xml``)

**Examples:**

**Virtual Mode:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_mujoco.launch.py mode:=virtual model:=m1013

Launch with **MoveIt2**
-----------------------

⚠ **Caution:** MoveIt2 requires Controller Version **2.12 or higher**.

**Real Mode:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_moveit.launch.py mode:=real model:=m1013 host:=192.168.137.100

**Virtual Mode:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_moveit.launch.py mode:=virtual model:=m1013 host:=127.0.0.1
