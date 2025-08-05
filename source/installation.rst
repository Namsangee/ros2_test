.. _installation:

Installation
============

Prerequisites
-------------

This package is developed for ROS 2 Jazzy. Please ensure you have a working ROS 2 Jazzy installation by following the `official installation guide <https://docs.ros.org/en/jazzy/Installation.html>`_.

To utilize the new emulator in virtual mode, **Docker** is required. Install Docker by following the `Docker official installation guide for Ubuntu <https://docs.docker.com/engine/install/ubuntu/>`_.

Required Dependencies
---------------------

Before installing the package, ensure that the necessary dependencies are installed:

.. code-block:: bash

   sudo apt update
   sudo apt-get install -y libpoco-dev libyaml-cpp-dev wget \
      ros-jazzy-control-msgs ros-jazzy-realtime-tools ros-jazzy-xacro \
      ros-jazzy-joint-state-publisher-gui ros-jazzy-ros2-control \
      ros-jazzy-ros2-controllers ros-jazzy-gazebo-msgs ros-jazzy-moveit-msgs \
      dbus-x11 ros-jazzy-moveit-configs-utils ros-jazzy-moveit-ros-move-group \


Install Gazebo Simulation:

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install -y ros-jazzy-ros-gz ros-jazzy-gz-ros2-control

Package Installation
--------------------

Ensure that you have installed **ros-jazzy-desktop** using `apt-get`. 
We recommend placing the package inside:

.. code-block:: bash

   mkdir -p ~/ros2_ws/src
   cd ~/ros2_ws/src

Clone the required repositories:

.. code-block:: bash

   git clone -b jazzy https://github.com/doosan-robotics/doosan-robot2.git

Install dependencies:

.. code-block:: bash

   rosdep install -r --from-paths . --ignore-src --rosdistro $ROS_DISTRO -y

Run the emulator installation script:

.. code-block:: bash

   cd ~/ros2_ws/src/doosan-robot2
   chmod +x ./install_emulator.sh
   sudo ./install_emulator.sh

Build & Settings
--------------------

.. code-block:: bash

   cd ~/ros2_ws
   colcon build
   . install/setup.bash

.. note::
   To use **ROS2 with Version 3.x Controller**, specify the build option:

   .. code-block:: bash

      colcon build --cmake-args -DDRCF_VER=3


Need to add the ``PYTHONPATH`` of the repo to your ``.bashrc``:

   .. code-block:: bash

      echo 'export PYTHONPATH=$PYTHONPATH:~/ros2_ws/install/dsr_common2/lib/dsr_common2/imp' >> ~/.bashrc && source ~/.bashrc


Try to test the installation by running the following command:

   .. code-block:: bash

      ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py