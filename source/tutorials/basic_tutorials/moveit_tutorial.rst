.. _moveit_tutorial:

MoveIt 2 Integration
====================

MoveIt 2 enables motion planning, collision checking, and interactive manipulation for Doosan robots using the ROS 2 control stack.

.. note::

   MoveIt 2 integration requires **Doosan Controller firmware version 2.12 or higher**.

To launch the MoveIt 2 interface, use the following command:

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_moveit.launch.py [arguments]

Launch Arguments
----------------

- ``mode``: Robot operation mode. Choose between:
  
  - ``real``: Connect to physical Doosan robot.
  - ``virtual``: Run in simulator/emulator mode.
  
- ``model``: Robot model name (e.g., ``m1013``, ``a0509``, etc.)
- ``host``: IP address of the robot controller (real mode) or emulator (virtual mode)

Usage Examples
--------------

**Real Mode (Physical Robot)**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_moveit.launch.py mode:=real model:=m1013 host:=192.168.137.100

**Virtual Mode (Simulation)**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_moveit.launch.py mode:=virtual model:=m1013 host:=127.0.0.1

This will launch:

- RViz 2 with the robot model and planning scene
- Move Group (Motion planning backend)
- Joint trajectory controller
- Robot state publisher and static transforms

.. raw:: html

   <br><br>

.. image:: moveit_tutorial1.png
   :alt: MoveIt RViz2 Launch Screenshot
   :width: 100%
   :align: center

.. raw:: html

   <br><br>

Motion Execution Demo
-----------------------

The following animation demonstrates a typical pick-and-place motion planned and executed using MoveIt 2:

.. image:: moveit.gif
   :alt: MoveIt Motion Execution
   :width: 100%
   :align: center

.. raw:: html

   <br><br>

For further customization or troubleshooting, see the corresponding launch files in the ``dsr_bringup2`` and ``dsr_moveit_config_{model}`` packages.
