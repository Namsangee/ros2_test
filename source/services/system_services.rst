.. _system_services:

system Services
===============

.. contents::
   :depth: 1
   :local:

ChangeCollisionSensitivity
--------------------------

**Request:**

.. code-block::

   int8 sensitivity   # 0 ~ 100 

**Response:**

.. code-block::

   bool success

GetCurrentPose
--------------

**Request:**

.. code-block::

   int8 space_type # 0=ROBOT_SPACE_JOINT, 1=ROBOT_SPACE_TASK

**Response:**

.. code-block::

   float64[6] pos
   bool       success

GetLastAlarm
------------

**Request:**

(None)

**Response:**

.. code-block::

   LogAlarm log_alarm
   bool        success

GetRobotMode
------------

Return to current robot-mode

**Request:**

(None)

**Response:**

.. code-block::

   int8 robot_mode
   bool        success

GetRobotSpeedMode
-----------------

**Request:**

(None)

**Response:**

.. code-block::

   int8 speed_mode # 0 : SPEED_NORMAL_MODE
                # 1 : SPEED_REDUCED_MODE
   bool        success   

GetRobotState
-------------

**Request:**

(None)

**Response:**

.. code-block::

   int8 robot_state    # 0 : STATE_INITIALIZING
                    # 1 : STATE_STANDBY
                    # 2 : STATE_MOVING
                    # 3 : STATE_SAFE_OFF
                    # 4 : STATE_TEACHING
                    # 5 : STATE_SAFE_STOP
                    # 6 : STATE_EMERGENCY_STOP:
                    # 7 : STATE_HOMMING
                    # 8 : STATE_RECOVERY
                    # 9 : eSTATE_SAFE_STOP2
                    # 10: STATE_SAFE_OFF2
                    # 11: STATE_RESERVED1
                    # 12: STATE_RESERVED2
                    # 13: STATE_RESERVED3
                    # 14: STATE_RESERVED4
                    # 15: STATE_NOT_READY
   bool        success                    

GetRobotSystem
--------------

**Request:**

(None)

**Response:**

.. code-block::

   int8 robot_system   # 0 : ROBOT_SYSTEM_REAL
                    # 1 : ROBOT_SYSTEM_VIRTUAL
   bool        success

ServoOff
--------

**Request:**

.. code-block::

   int8 STOP_TYPE_QUICK_STO = 0
   int8 STOP_TYPE_QUICK = 1
   int8 STOP_TYPE_SLOW = 2
   int8 STOP_TYPE_HOLD = 3
   int8 STOP_TYPE_EMERGENCY = 3

   int8 stop_type     

**Response:**

.. code-block::

   bool success

SetRobotControl
---------------

**Request:**

.. code-block::

   int8 robot_control 

**Response:**

.. code-block::

   bool success

SetRobotMode
------------

Change the robot-mode

**Request:**

.. code-block::

   int8 robot_mode # <Robot_Mode>

**Response:**

.. code-block::

   bool success

SetRobotSpeedMode
-----------------

**Request:**

.. code-block::

   int8 speed_mode # 0 : SPEED_NORMAL_MODE, 1 : SPEED_REDUCED_MODE

**Response:**

.. code-block::

   bool success    
                   

SetRobotSystem
--------------

**Request:**

.. code-block::

   int8 robot_system   # 0 : ROBOT_SYSTEM_REAL, 1 : ROBOT_SYSTEM_VIRTUAL

**Response:**

.. code-block::

   bool success

SetSafeStopResetType
--------------------

**Request:**

.. code-block::

   int8 reset_type     # 0=SAFE_STOP_RESET_TYPE_DEFAULT = SAFE_STOP_RESET_TYPE_PROGRAM_STOP , 1= SAFE_STOP_RESET_TYPE_PROGRAM_RESUME 

**Response:**

.. code-block::

   bool success

SetSafetyMode
-------------

**Request:**

.. code-block::

   int8 safety_mode
   int8 safety_event

**Response:**

.. code-block::

   bool success
