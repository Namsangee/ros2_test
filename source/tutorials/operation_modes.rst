.. _operation_modes:

Operation Modes
===============

This section describes the operation modes available for the Doosan robot system.

**Virtual Mode**
----------------

Use virtual mode when operating without a physical robot. (**Docker is required**)

If you omit the ``mode`` argument, it defaults to ``virtual``.

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_gazebo.launch.py mode:=virtual

When launched in virtual mode, the **emulator (DRCF)** will automatically start and stop during the launch lifecycle.

.. note::
   - Emulator location: ``dsr_common2/bin/``
   - One emulator instance will be launched for each robot.
   - The system automatically assigns different ports for multiple robots.

To check if the emulator is running correctly:

.. code-block:: bash

   ps -ef | grep drcf
   docker ps   # If emulator runs in Docker container

**Real Mode**
-------------

Use real mode when controlling an actual robot.

In real mode, the system communicates with the physical robot controller over TCP/IP.

- Default IP: ``192.168.137.100`` |br| 
- Default Port: ``12345``

Pass the following arguments to launch in real mode:

.. code-block:: bash

   ros2 launch dsr_bringup2 dsr_bringup2_gazebo.launch.py mode:=real host:=192.168.137.100 port:=12345

.. note::
  Make sure your PC is connected to the **same subnet** as the robot controller. |br|
  (e.g., PC IP: ``192.168.137.X``)

**Connect with the Real Robot Controller**

- Turn on the robot and check the **Teach Pendant** screen.

.. image:: images/etc/teach_pendant_screen.png
   :alt: Teach Pendant Main Screen
   :width: 800px
   :align: center

.. raw:: html

   <br><br>

- Navigate to ``Settings → Network`` and confirm the controller IP.

.. image:: images/etc/network_of_tp_screen.png
   :alt: Network Settings on TP
   :width: 800px
   :align: center

.. raw:: html

   <br><br>

- Use this IP address as the ``host`` argument in your launch command. |br|

- If the ROS 2 control node is running successfully, the control will transfer from the TP to ROS 2.

- A pop-up will appear on the TP confirming the transfer of control to ROS 2.


.. image:: images/etc/transfer_control_pop_up.png
   :alt: Control Transfer Pop-up
   :width: 800px
   :align: center

.. raw:: html

   <br>
   <br>

