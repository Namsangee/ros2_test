.. _launch_parameters:

Launch Parameters
=================

**mode**
--------

- ``mode:=real`` → Drive a robot in reality (default IP: ``192.168.127.100``, port: ``12345``)
- ``mode:=virtual`` → Drive a robot virtually (default IP: ``127.0.0.1``, port: ``12345``)
  - Emulator starts and terminates automatically with launch lifetime.

**name**
-------

- Robot namespace (Default: ``dsr01``)

**host**
-------

- IP Address of **Doosan Robotics Controller**
  - Default: ``192.168.137.100``
  - Virtual mode: ``127.0.0.1``

**port**
-------

- Port of **Doosan Robotics Controller** (Default: ``12345``)

**model**
--------

- Doosan robot model name

**color**
--------

- Select ``white`` or ``blue`` (Only ``white`` for E0609)

**gui**
------

- Activate/Deactivate GUI (``true``/``false``)

**gz**
-----

- Activate/Deactivate Gazebo Simulation (``true``/``false``)
