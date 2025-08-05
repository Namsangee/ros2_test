.. _rviz_tutorial:

RViz2 Launch
============

This launch file starts Rviz2 for visualizing the robot model and its state.

**Command:**

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py [arguments]

**Arguments:**

- ``name``: Robot namespace (Default: ``dsr01``)
- ``host``: IP address of the Doosan Controller (Default: ``127.0.0.1``)
- ``port``: Communication port (Default: ``12345``)
- ``mode``: Launch mode (``real`` or ``virtual``)
- ``model``: Robot model name (e.g., ``m1013``)
- ``color``: Robot color (``white`` or ``blue``)
- ``rt_host``: Real-time controller IP (Default: ``192.168.137.50``)

**Examples:**

- Real Robot:

  .. code-block:: bash

     ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py mode:=real host:=192.168.137.100 model:=m1013

- Virtual Robot:

  .. code-block:: bash

     ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py mode:=virtual host:=127.0.0.1 model:=m1013

.. image:: ../../_static/tutorial/rviz1.png
   :alt: Robot Model Preview
   :width: 800px
   :align: center