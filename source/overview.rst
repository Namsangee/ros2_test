.. _overview:

Overview
========

.. toctree::
   :maxdepth: 1
   :caption: Overview Contents

   
   overview/architecture
   overview/package

Purpose
-------
This package provides control functionality for all Doosan robot models in the **ROS 2 Jazzy** environment.

Features
--------
- Supports all Doosan robot models (A/M/H/E/P series)
- Virtual emulator mode for development and testing without hardware
- Integrated DRFL (Doosan Robot Framework Library) for direct command-level access
- Optional real-time control interface for low-latency communication

   
- Pre-configured launch files for RViz2, Gazebo, and MoveIt 2
- MoveIt 2 integration for motion planning and manipulation tasks
- Gazebo Harmonic simulation support for dynamic testing and validation
- RViz2-based robot state visualization and planning preview


- Includes sample applications and demo scripts for quick setup and usage

Environment
-----------
- OS: Ubuntu 24.04 LTS
- ROS 2: Jazzy Jalisco
- MoveIt: MoveIt 2 (Jazzy release)
- Gazebo: Harmonic
- Language: Python ≥ 3.10, C++17

License
-------
All packages are distributed under the **Apache License 2.0**.  
See the LICENSE file for details.

Architecture
------------
.. .. toctree::
..    :maxdepth: 1

..    overview/architecture

:ref:`Architecture page <architecture>`

Package
--------
.. .. toctree::
..    :maxdepth: 1

..    overview/package


:ref:`Package page <package>`
