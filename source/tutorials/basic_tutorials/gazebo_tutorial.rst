.. _gazebo_tutorial:

Gazebo Simulation
=================

This launch file starts the robot in the Gazebo Harmonic simulator with optional RViz2.

**Command:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_gazebo.launch.py [arguments]

**Arguments:**

- ``name``: Robot namespace (Default: ``dsr01``)
- ``host``: IP address of the Doosan Controller (Default: ``127.0.0.1``)
- ``port``: Communication port (Default: ``12345``)
- ``mode``: Launch mode (``real`` or ``virtual``)
- ``model``: Robot model name (e.g., ``m1013``)
- ``color``: Robot color (``white`` or ``blue``)
- ``gui``: Launch RViz2 (``true`` or ``false``)
- ``gz``: Enable Gazebo simulation (``true`` or ``false``)
- ``x``, ``y``, ``z``, ``R``, ``P``, ``Y``: Robot pose in simulation
- ``rt_host``: Real-time controller IP (Default: ``192.168.137.50``)
- ``use_sim_time``: Use simulation time (Default: ``true``)

**Examples:**

- Real Mode:

  .. code-block:: bash

     ros2 launch dsr_bringup2 dsr_bringup2_gazebo.launch.py mode:=real host:=192.168.137.100 model:=m1013

- Virtual Mode:

  .. code-block:: bash

     ros2 launch dsr_bringup2 dsr_bringup2_gazebo.launch.py mode:=virtual host:=127.0.0.1 port:=12346 name:=dsr01 x:=0 y:=0

- Multi-arm (Virtual):

  .. code-block:: bash

     ros2 launch dsr_bringup2 dsr_bringup2_spawn_on_gazebo.launch.py mode:=virtual host:=127.0.0.1 port:=12347 name:=dsr02 x:=2 y:=2

.. note::

   For multi-arm setup, each robot must use a unique ``name``, ``port``, and ``x/y`` position to avoid collision in Gazebo.