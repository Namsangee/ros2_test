.. _moveit_tutorial:

MoveIt2 Integration
===================

⚠ **Note:** MoveIt2 requires Doosan Controller version **2.12 or higher**.

Use this launch file to perform motion planning and manipulation tasks with MoveIt2.

**Command:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_moveit.launch.py [arguments]

**Arguments:**

- ``mode``: Launch mode (``real`` or ``virtual``)
- ``model``: Robot model (e.g., ``m1013``)
- ``host``: IP address of the Doosan Controller

**Examples:**

- Real Mode:

  .. code-block:: bash

     ros2 launch dsr_bringup2 dsr_bringup2_moveit.launch.py mode:=real model:=m1013 host:=192.168.137.100

- Virtual Mode:

  .. code-block:: bash

     ros2 launch dsr_bringup2 dsr_bringup2_moveit.launch.py mode:=virtual model:=m1013 host:=127.0.0.1