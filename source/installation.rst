.. _installation:

Installation
============

Prerequisites
-------------

To utilize the new emulator in virtual mode, **Docker** is required. Install Docker by following the official guide: `Docker Installation for Ubuntu <https://docs.docker.com/engine/install/ubuntu/>`_

Required Dependencies
---------------------

Before installing the package, ensure that the necessary dependencies are installed:

.. code-block:: bash

   sudo apt update
   sudo apt install ros-jazzy-ros-gz \
                     ros-jazzy-gz-ros2-control


Install Gazebo Simulation
-------------------------

.. code-block:: bash

   sudo sh -c 'echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable `lsb_release -cs` main" > /etc/apt/sources.list.d/gazebo-stable.list'
   wget http://packages.osrfoundation.org/gazebo.key -O - | sudo apt-key add -
   sudo apt-get update
   sudo apt-get install -y libignition-gazebo6-dev ros-humble-gazebo-ros-pkgs ros-humble-ros-gz-sim ros-humble-ros-gz

Package Installation
--------------------

Ensure that you have installed **ros-humble-desktop** using `apt-get`. We recommend placing the package inside:

.. code-block:: bash

   mkdir -p ~/ros2_ws/src
   cd ~/ros2_ws/src

Clone the required repositories:

.. code-block:: bash

   git clone -b humble https://github.com/doosan-robotics/doosan-robot2.git

Install dependencies:

.. code-block:: bash

   rosdep install -r --from-paths . --ignore-src --rosdistro $ROS_DISTRO -y

Run the emulator installation script:

.. code-block:: bash

   cd ~/ros2_ws/src/doosan-robot2
   chmod +x ./install_emulator.sh
   sudo ./install_emulator.sh

Build the package:

.. code-block:: bash

   cd ~/ros2_ws
   colcon build
   . install/setup.bash

To use **ROS2 with Version 3.x Controller**, specify the build option:

.. code-block:: bash

   colcon build --cmake-args -DDRCF_VER=3
