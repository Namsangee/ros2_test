.. _motion_services:

motion Services
===============

.. contents::
   :depth: 1
   :local:

AlterMotion
-----------

**Request:**

.. code-block::

   float64[6] pos               # position  

**Response:**

.. code-block::

   bool success

ChangeOperationSpeed
--------------------

**Request:**

.. code-block::

   int8 speed              # operation speed: (1~100)

**Response:**

.. code-block::

   bool success

CheckMotion
-----------

Return status of the currently active motion.
Homing is performed by moving to the joint motion to the mechanical or user defined home position.
According to the input parameter [target], it moves to the mechanical home defined in the system or the home set by the user.

**Request:**

(None)

**Response:**

.. code-block::

   int8       status          # DR_STATE_IDLE(0) : no motion in action
                           # DR_STATE_INIT(1) : motion being calculated
                           # DR_STATE_BUSY(2) : motion in operation
   bool       success 

DisableAlterMotion
------------------

Deactivates alter motion.

**Request:**

(None)

**Response:**

.. code-block::

   bool success

EnableAlterMotion
-----------------

**Request:**

.. code-block::

   int32      n                 # Cycle time number 
   int8       mode              # DR_DPOS(0) : accumulation amount, DR_DVEL(1) : increment amount 
   int8       ref               # DR_BASE(0), DR_TOOL(1), DR_WORLD(2), user coord(101~200) 
                             # <ref is only available in M2.40 or later> 
   float64[2] limit_dpos        # First value : limitation of position[mm], Second value : limitation of orientation[deg]
   float64[2] limit_dpos_per    # First value : limitation of position[mm], Second value : limitation of orientation[deg]

**Response:**

.. code-block::

   bool success

Fkin
----

**Request:**

.. code-block::

   float64[6] pos               # joint pos(posj)  
   int8       ref     #= 0      # DR_BASE(0), DR_WORLD(2)
                             # <ref is only available in M2.40 or later> 

**Response:**

.. code-block::

   float64[6] conv_posx         # task pos(posx)
   bool       success 

Ikin
----

**Request:**

.. code-block::

   float64[6] pos               # task pos(posx)  
   int8       sol_space         # solution space : 0 ~ 7
   int8       ref     #= 0      # DR_BASE(0), DR_WORLD(2)
                             # <ref is only available in M2.40 or later> 

**Response:**

.. code-block::

   float64[6] conv_posj         # joint pos(posj)  
   bool       success

Jog
---

Single jog

**Request:**

.. code-block::

   int8 jog_axis          # 0 ~ 5 : JOINT 1 ~ 6 
                       # 6 ~ 11: TASK 1 ~ 6 (X,Y,Z,rx,ry,rz)
   int8 move_reference    # 0 : MOVE_REFERENCE_BASE, 1 : MOVE_REFERENCE_TOOL
   float64 speed          # jog speed [%] : + forward , 0=stop, - backward  

**Response:**

.. code-block::

   bool success

JogMulti
--------

Multi jog speed = (250mm/s x 1.73) x unit vecter x speed [%]

**Request:**

.. code-block::

   float64[6] jog_axis    # unit vecter of Task space [Tx, Ty, Tz, Rx, Ry, Rz] : -1.0 ~ +1.0 
   int8 move_reference    # 0 : MOVE_REFERENCE_BASE, 1 : MOVE_REFERENCE_TOOL, 2 : MOVE_REFERENCE_WORLD
   float64 speed          # jog speed [%]  

**Response:**

.. code-block::

   bool success

MoveBlending
------------

**Request:**

.. code-block::

   std_msgs/Float64MultiArray[] segment #50 x (pos1[6]:pos2[6]:type[1]:radius[1])        
   int8           pos_cnt               # target cnt 
   float64[2]     vel                  # set velocity: [mm/sec], [deg/sec]
   float64[2]     acc                  # set acceleration: [mm/sec2], [deg/sec2]
   float64        time #= 0.0          # Time [sec] 
   int8           ref                  # DR_BASE(0), DR_TOOL(1), DR_WORLD(2)
                                    # <DR_WORLD is only available in M2.40 or later 
   int8           mode #= 0            # MOVE_MODE_ABSOLUTE=0, MOVE_MODE_RELATIVE=1 
   int8           sync_type #=0         # SYNC = 0, ASYNC = 1

**Response:**

.. code-block::

   bool success

MoveCircle
----------

**Request:**

.. code-block::

   std_msgs/Float64MultiArray[] pos  # target[2][6]  
   float64[2]      vel               # set velocity: [mm/sec], [deg/sec]
   float64[2]      acc               # set acceleration: [mm/sec2], [deg/sec2]
   float64         time #= 0.0       # Time [sec] 
   float64         radius #=0.0      # Radius under blending mode [mm] 
   int8            ref               # DR_BASE(0), DR_TOOL(1), DR_WORLD(2)
                                  # <DR_WORLD is only available in M2.40 or later> 
   int8            mode #= 0         # MOVE_MODE_ABSOLUTE=0, MOVE_MODE_RELATIVE=1 
   float64         angle1 #= 0.0     # angle1 [degree]
   float64         angle2 #= 0.0     # angle2 [degree]
   int8            blend_type #= 0    # BLENDING_SPEED_TYPE_DUPLICATE=0, BLENDING_SPEED_TYPE_OVERRIDE=1
   int8            sync_type #=0      # SYNC = 0, ASYNC = 1

**Response:**

.. code-block::

   bool success

MoveHome
--------

Homing is performed by moving to the joint motion to the mechanical or user defined home position.
According to the input parameter [target], it moves to the mechanical home defined in the system or the home set by the user.

**Request:**

.. code-block::

   int8       target           # DR_HOME_TARGET_MECHANIC(0) : Mechanical home, joint angle (0,0,0,0,0,0)
                            # DR_HOME_TARGET_USER(1)     : user home

**Response:**

.. code-block::

   int8       res              # 0=success, otherwise fail 
   bool       success

MoveJoint
---------

The robot moves to the target joint position (pos) from the current joint position.

**Request:**

.. code-block::

   float64[6] pos               # target joint angle list [degree] 
   float64    vel               # set velocity: [deg/sec]
   float64    acc               # set acceleration: [deg/sec2]
   float64    time #= 0.0       # Time [sec] 
   float64    radius #=0.0      # Radius under blending mode [mm] 
   int8       mode #= 0         # MOVE_MODE_ABSOLUTE=0, MOVE_MODE_RELATIVE=1 
   int8       blend_type #= 0    # BLENDING_SPEED_TYPE_DUPLICATE=0, BLENDING_SPEED_TYPE_OVERRIDE=1
   int8       sync_type #=0      # SYNC = 0, ASYNC = 1

**Response:**

.. code-block::

   bool success

MoveJointx
----------

**Request:**

.. code-block::

   float64[6] pos              # target  
   float64    vel              # set velocity: [deg/sec]
   float64    acc              # set acceleration: [deg/sec2] 
   float64    time #= 0.0      # Time [sec] 
   float64    radius #=0.0     # Radius under blending mode [mm]   
   int8       ref              # DR_BASE(0), DR_TOOL(1), DR_WORLD(2)
                            # <DR_WORLD is only available in M2.40 or later> 
   int8       mode #= 0        # MOVE_MODE_ABSOLUTE=0, MOVE_MODE_RELATIVE=1 
   int8       blend_type #= 0   # BLENDING_SPEED_TYPE_DUPLICATE=0, BLENDING_SPEED_TYPE_OVERRIDE=1
   int8       sol              # SolutionSpace : 0~7
   int8       sync_type #=0     # SYNC = 0, ASYNC = 1

**Response:**

.. code-block::

   bool success

MoveLine
--------

**Request:**

.. code-block::

   float64[6] pos               # target  
   float64[2] vel               # set velocity: [mm/sec], [deg/sec]
   float64[2] acc               # set acceleration: [mm/sec2], [deg/sec2]
   float64    time #= 0.0       # Time [sec] 
   float64    radius #=0.0      # Radius under blending mode [mm] 
   int8       ref               # DR_BASE(0), DR_TOOL(1), DR_WORLD(2)
                             # <DR_WORLD is only available in M2.40 or later> 
   int8       mode #= 0         # DR_MV_MOD_ABS(0), DR_MV_MOD_REL(1) 
   int8       blend_type #= 0    # BLENDING_SPEED_TYPE_DUPLICATE=0, BLENDING_SPEED_TYPE_OVERRIDE=1
   int8       sync_type #=0      # SYNC = 0, ASYNC = 1

**Response:**

.. code-block::

   bool success

MovePause
---------

Motion pause.

**Request:**

(None)

**Response:**

.. code-block::

   bool success

MovePeriodic
------------

**Request:**

.. code-block::

   float64[6] amp              # Amplitude (motion between -amp and +amp) [mm] or [deg]   
   float64[6] periodic         # Period (time for 1 cycle) [sec]
   float64    acc              # Acc-, dec- time [sec] 
   int8       repeat           # Repetition count 
   int8       ref  #= 1        # DR_BASE(0), DR_TOOL(1), DR_WORLD(2)
                            # <DR_WORLD is only available in M2.40 or later 

   int8       sync_type #=0     # SYNC = 0, ASYNC = 1

**Response:**

.. code-block::

   bool success

MoveResume
----------

Motion pause.

**Request:**

(None)

**Response:**

.. code-block::

   bool success

MoveSpiral
----------

**Request:**

.. code-block::

   float64    revolution       # Total number of revolutions 
   float64    max_radius        # Final spiral radius [mm]
   float64    max_length        # Distance moved in the axis direction [mm]
   float64[2] vel              # set velocity: [mm/sec], [deg/sec]
   float64[2] acc              # set acceleration: [mm/sec2], [deg/sec2]
   float64    time #= 0.0      # Total execution time <sec> 
   int8       task_axis         # TASK_AXIS_X = 0, TASK_AXIS_Y = 1, TASK_AXIS_Z = 2   
   int8       ref  #= 1        # DR_BASE(0), DR_TOOL(1), DR_WORLD(2)
                            # <DR_WORLD is only available in M2.40 or later 
   int8       sync_type #=0     # SYNC = 0, ASYNC = 1 

**Response:**

.. code-block::

   bool success

MoveSplineJoint
---------------

**Request:**

.. code-block::

   std_msgs/Float64MultiArray[] pos         # target [100][6] pos
   int8       pos_cnt                       # target cnt 
   float64[6]    vel                        # set joint velocity: [deg/sec]
   float64[6]    acc                        # set joint acceleration: [deg/sec2] 
   float64    time #= 0.0                   # Time [sec] 
   int8       mode #= 0                     # MOVE_MODE_ABSOLUTE=0, MOVE_MODE_RELATIVE=1 
   int8       sync_type #=0                 # SYNC = 0, ASYNC = 1

**Response:**

.. code-block::

   bool success

MoveSplineTask
--------------

**Request:**

.. code-block::

   std_msgs/Float64MultiArray[] pos  # target 
   int8            pos_cnt            # target cnt 
   float64[2]      vel               # set velocity: [mm/sec], [deg/sec]
   float64[2]      acc               # set acceleration: [mm/sec2], [deg/sec2]
   float64         time #= 0.0       # Time [sec] 
   int8            ref               # DR_BASE(0), DR_TOOL(1), DR_WORLD(2)
                                  # <DR_WORLD is only available in M2.40 or later 
   int8            mode #= 0         # MOVE_MODE_ABSOLUTE=0, MOVE_MODE_RELATIVE=1 
   int8            opt  #= 0         # SPLINE_VELOCITY_OPTION_DEFAULT=0, SPLINE_VELOCITY_OPTION_CONST=1 
   int8            sync_type #=0      # SYNC = 0, ASYNC = 1

**Response:**

.. code-block::

   bool success

MoveStop
--------

**Request:**

.. code-block::

   int32 stop_mode         # DR_QSTOP_STO(0) : Quick stop (Stop Category 1 without STO(Safe Torque Off)
                        # DR_QSTOP(1)     : Quick stop (Stop Category 2)
                        # DR_SSTO(2)      : Soft Stop
                        # DR_HOLD(3)      : HOLD stop

**Response:**

.. code-block::

   bool success

MoveWait
--------

This Service sets the waiting time between the previous motion command 
and the motion command in the next line.

**Request:**

(None)

**Response:**

.. code-block::

   bool success

SetRefCoord
-----------

**Request:**

.. code-block::

   int8       coord            # DR_BASE(0), DR_TOOL(1), DR_WORLD(2), user coord(101~200)
                            # <DR_WORLD is only available in M2.40 or later> 

**Response:**

.. code-block::

   bool success

SetSingularityHandling
----------------------

**Request:**

.. code-block::

   int8       mode         # DR_AVOID(0)     : Automatic avoidance mode
                        # DR_TASK_STOP(1) : Deceleration/ Warning/ Task termination
                        # DR_VAR_VEL(2)   : Variable velocity mode

**Response:**

.. code-block::

   bool success

Trans
-----

**Request:**

.. code-block::

   float64[6] pos               # task pos(posx)  
   float64[6] delta             # delta (posx)  
   int8       ref     #= 0      # DR_BASE(0), DR_TOOL(1), DR_WORLD(2)
                             # <DR_WORLD is only available in M2.40 or later> 
   int8       ref_out #= 0      # DR_BASE(0), DR_WORLD(2)
                             # <ref_out is only available in M2.40 or later>

**Response:**

.. code-block::

   float64[6] trans_pos         # trans pos(posx) 
   bool       success
