.. _force_services:

force Services
==============

.. contents::
   :depth: 1
   :local:

.. _AlignAxis1:

AlignAxis1
----------

**Request:**

.. code-block::

   float64[6] x1                # task pos(posx)  
   float64[6] x2                # task pos(posx)  
   float64[6] x3                # task pos(posx)
   float64[3] source_vect       # source vector[3]  
   int8       axis              # DR_AXIS_X(0), DR_AXIS_Y(1), DR_AXIS_Z(2) 
   int8       ref               # DR_BASE(0), DR_WORLD(2), user coord(101~200)
                             # <ref is only available in M2.40 or later> 

**Response:**

.. code-block::

   bool       success

.. _AlignAxis2:

AlignAxis2
----------

**Request:**

.. code-block::

   float64[3] target_vect       # target vector[3]  
   float64[3] source_vect       # source vector[3]  
   int8       axis              # DR_AXIS_X(0), DR_AXIS_Y(1), DR_AXIS_Z(2) 
   int8       ref               # DR_BASE(0), DR_WORLD(2), user coord(101~200)
                             # <ref is only available in M2.40 or later> 

**Response:**

.. code-block::

   bool       success 

.. _CalcCoord:

CalcCoord
---------

This service is only available in M2.50 or later

**Request:**

.. code-block::

   int8       input_pos_cnt     # input_pos_cnt
   float64[6] x1                # task pos(posx)  
   float64[6] x2                # task pos(posx)  
   float64[6] x3                # task pos(posx)
   float64[6] x4                # task pos(posx)
   int8       ref               # DR_BASE(0), DR_WORLD(2)
   int8       mod               # input mode(only valid when the number of input poses is 2)
                             # 0: defining z-axis based on the current Tool-z direction
                             # 1: defining z-axis based on the z direction of x1 

**Response:**

.. code-block::

   float64[6] conv_posx         # task pos(posx) 
   bool       success

.. _CheckForceCondition:


CheckForceCondition
-------------------

This service checks the status of the given force. It disregards the force direction and only compares the sizes. 
This condition can be repeated with the while or if statement. Measuring the force, axis is based on the ref coordinate and measuring the moment,
axis is based on the tool coordinate.

**Request:**

.. code-block::

   int8       axis              # DR_AXIS_X(0), DR_AXIS_Y(1), DR_AXIS_Z(2), DR_AXIS_A(10), DR_AXIS_B(11), DR_AXIS_C(12) 
   float64    min               # min >=0.0   
   float64    max               # max >=0.0 
   int8       ref     #= 0      # DR_BASE(0), DR_TOOL(1), DR_WORLD(2), user coord(101~200)
                             # <DR_WORLD is only available in M2.40 or later> 

**Response:**

.. code-block::

   bool       success                 # True or False

.. _CheckOrientationCondition1:


CheckOrientationCondition1
--------------------------

**Request:**

.. code-block::

   int8       axis              # DR_AXIS_A(10), DR_AXIS_B(11), DR_AXIS_C(12) 
   float64[6] min               # task pos(posx)  
   float64[6] max               # task pos(posx)  
   int8       ref  #= 0         # DR_BASE(0), DR_TOOL(1), DR_WORLD(2), user_coordinate(101~200)
                             # <DR_WORLD is only available in M2.40 or later> 
   int8       mode #= 0         # DR_MV_MOD_ABS(0)

**Response:**

.. code-block::

   bool success                 # True or False

.. _CheckOrientationCondition2:

CheckOrientationCondition2
--------------------------

**Request:**

.. code-block::

   int8       axis              # DR_AXIS_A(10), DR_AXIS_B(11), DR_AXIS_C(12) 
   float64    min               # minimum value  
   float64    max               # maximum value  
   int8       ref  #= 0         # DR_BASE(0), DR_TOOL(1), DR_WORLD(2), user_coordinate(101~200)
                             # <DR_WORLD is only available in M2.40 or later> 
   int8       mode #= 1         # DR_MV_MOD_REL(1)
   float64[6] pos               # task pos(pos)  

**Response:**

.. code-block::

   bool success                 # True or False

.. _CheckPositionCondition:

CheckPositionCondition
----------------------

**Request:**

.. code-block::

   int8       axis              # DR_AXIS_X(0), DR_AXIS_Y(1), DR_AXIS_Z(2) 
   float64    min               # min    
   float64    max               # max  
   int8       ref     #= 0      # DR_BASE(0), DR_TOOL(1), DR_WORLD(2), user_coordinate(101~200)
                             # <DR_WORLD is only available in M2.40 or later> 
   int8       mode #= 0         # DR_MV_MOD_ABS(0), DR_MV_MOD_REL(1) 
   float64[6] pos               # task pos(posx)  

**Response:**

.. code-block::

   bool success                 # True or False


.. _CoordTransform:

CoordTransform
--------------

**Request:**

.. code-block::

   float64[6] pos_in            # task pos(posx)  
   int8       ref_in            # DR_BASE(0), DR_TOOL(1), DR_WORLD(2), user coord(101~200)
                             # <ref is only available in M2.40 or later> 
   int8       ref_out           # DR_BASE(0), DR_TOOL(1), DR_WORLD(2), user coord(101~200) 
                             # <ref is only available in M2.40 or later> 

**Response:**

.. code-block::

   float64[6] conv_posx         # task pos(posx)
   bool       success

.. _GetUserCartCoord:

GetUserCartCoord
----------------

This service is only available in M2.50 or later

**Request:**

.. code-block::

   int8       id                # ID of user coord 

**Response:**

.. code-block::

   float64[6] conv_posx         # task pos(posx)  
   int8       ref               # Reference coordinate of the coordinate to get
   bool       success

.. _GetWorkpieceWeight:

GetWorkpieceWeight
------------------

**Request:**

(None)

**Response:**

.. code-block::

   float32       weight               # Measured weight, Negative value if error
   bool          success

.. _IsDoneBoltTightening:

IsDoneBoltTightening
--------------------

**Request:**

.. code-block::

   float64    m                 # Target torque  
   float64    timeout           # Monitoring duration [sec]  
   int8       axis              # DR_AXIS_X(0), DR_AXIS_Y(1), DR_AXIS_Z(2) 

**Response:**

.. code-block::

   bool       success

.. _OverwriteUserCartCoord:

OverwriteUserCartCoord
----------------------

This service is only available in M2.50 or later

**Request:**

.. code-block::

   int8       id                # ID of user coord 
   float64[6] pos               # task pos(posx)  
   int8       ref        #= 0   # DR_BASE(0), DR_WORLD(2)

**Response:**

.. code-block::

   int8       id                # Successful coordinate setting, Set user coordinate ID (101 - 200)
                             # (-1) Failed coordinate setting
   bool       success                             

.. _ParallelAxis1:

ParallelAxis1
-------------

**Request:**

.. code-block::

   float64[6] x1                # task pos(posx)  
   float64[6] x2                # task pos(posx)  
   float64[6] x3                # task pos(posx)
   int8       axis              # DR_AXIS_X(0), DR_AXIS_Y(1), DR_AXIS_Z(2) 
   int8       ref        #= 0   # DR_BASE(0), DR_WORLD(2), user coord(101~200)
                             # <ref is only available in M2.40 or later> 

**Response:**

.. code-block::

   bool       success 

.. _ParallelAxis2:

ParallelAxis2
-------------

**Request:**

.. code-block::

   float64[3] vect              # vector[3]  
   int8       axis              # DR_AXIS_X(0), DR_AXIS_Y(1), DR_AXIS_Z(2) 
   int8       ref        #= 0   # DR_BASE(0), DR_WORLD(2), user coord(101~200)
                             # <ref is only available in M2.40 or later> 

**Response:**

.. code-block::

   bool       success 

.. _ReleaseComplianceCtrl:

ReleaseComplianceCtrl
---------------------

**Request:**

(None)

**Response:**

.. code-block::

   bool       success 

.. _ReleaseForce:

ReleaseForce
------------

**Request:**

.. code-block::

   float64    time # 0          # Time needed to reduce the force (0 ~ 1.0) 

**Response:**

.. code-block::

   bool       success 

.. _ResetWorkpieceWeight:

ResetWorkpieceWeight
--------------------

Initializes the weight data of the material to initialize the algorithm before measuring the weight of the material.

**Request:**

(None)

**Response:**

.. code-block::

   bool       success 

.. _SetDesiredForce:

SetDesiredForce
---------------

**Request:**

.. code-block::

   float64[6] fd                # Three translational target forces + Three rotational target moments
   int8[6]    dir               # Force control in the corresponding direction if 1, Compliance control in the corresponding direction if 0
   int8       ref               # Reference coordinate of the coordinate to get
   float64    time # 0          # Transition time of target force to take effect (0 ~ 1.0 sec)
   int8       mod               # DR_FC_MOD_ABS(0): force control with absolute value, 
                             # DR_FC_MOD_REL(1): force control with relative value to initial state (the instance when this function is called) 

**Response:**

.. code-block::

   bool       success

.. _SetStiffnessx:

SetStiffnessx
-------------

**Request:**

.. code-block::

   float64[6] stx               # default[500, 500, 500, 100, 100, 100], Three translational stiffnesses + Three rotational stiffnesses
   int8       ref               # the preset reference coordinate system.
   float64    time              # Stiffness varying time(0 ~ 1.0) [sec], Linear transition during the specified time   

**Response:**

.. code-block::

   bool       success 

.. _SetUserCartCoord1:

SetUserCartCoord1
-----------------

**Request:**

.. code-block::

   float64[6] pos                # task pos(posx)  
   int8       ref                # DR_BASE(0), DR_WORLD(2)
                              # <ref is only available in M2.40 or later> 

**Response:**

.. code-block::

   int8        id                # set user coord (101~120) or fail(-1)
   bool        success    

.. _SetUserCartCoord2:

SetUserCartCoord2
-----------------

**Request:**

.. code-block::

   float64[6] x1                 # task pos(posx)  
   float64[6] x2                 # task pos(posx)  
   float64[6] x3                 # task pos(posx)
   float64[6] pos                # pos(posx)
   int8       ref                # DR_BASE(0), DR_WORLD(2)
                              # <ref is only available in M2.40 or later> 

**Response:**

.. code-block::

   int8    id                    # set user coord (101~200) or fail(-1) 
   bool        success   

.. _SetUserCartCoord3:

SetUserCartCoord3
-----------------

**Request:**

.. code-block::

   float64[3] u1                # X-axis unit vector  
   float64[3] v1                # Y-axis unit vector 
   float64[6] pos               # task pos(posx) 
   int8       ref               # DR_BASE(0), DR_WORLD(2)
                             # <ref is only available in M2.40 or later> 

**Response:**

.. code-block::

   int8    id                   # set user coord (101~120) or fail(-1) 
   bool        success   

.. _TaskComplianceCtrl:

TaskComplianceCtrl
------------------

**Request:**

.. code-block::

   float64[6] stx               # Three translational stiffnesses + Three rotational stiffnesses
                             # default  [3000, 3000, 3000, 200, 200, 200]
   int8       ref               # the preset reference coordinate system.
   float64    time              # Stiffness varying time [ 0 ~ 1.0 sec], Linear transition during the specified time 

**Response:**

.. code-block::

   bool       success
