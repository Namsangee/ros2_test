.. _realtime_services:

realtime Services
=================

.. contents::
   :depth: 1
   :local:
   
ConnectRtControl
----------------

**Request:**

.. code-block::

   string     ip_address
   uint32     port

**Response:**

.. code-block::

   bool       success

DisconnectRtControl
-------------------

**Request:**

(None)

**Response:**

.. code-block::

   bool       success

GetRtControlInputDataList
-------------------------

**Request:**

.. code-block::

   string     version

**Response:**

.. code-block::

   bool       success
   string     data

GetRtControlInputVersionList
----------------------------

**Request:**

(None)

**Response:**

.. code-block::

   bool       success
   string     version

GetRtControlOutputDataList
--------------------------

**Request:**

.. code-block::

   string     version

**Response:**

.. code-block::

   bool       success
   string     data

GetRtControlOutputVersionList
-----------------------------

**Request:**

(None)

**Response:**

.. code-block::

   bool       success
   string     version

ReadDataRt
----------

**Request:**

(None)

**Response:**

.. code-block::

   RobotStateRt       data

SetAccjRt
---------

**Request:**

.. code-block::

   float64[6] acc

**Response:**

.. code-block::

   bool       success

SetAccxRt
---------

**Request:**

.. code-block::

   float64    trans
   float64    rotation

**Response:**

.. code-block::

   bool       success

SetRtControlInput
-----------------

**Request:**

.. code-block::

   string     version
   float64    period
   int32      loss

**Response:**

.. code-block::

   bool       success

SetRtControlOutput
------------------

**Request:**

.. code-block::

   string     version
   float64    period
   int32      loss

**Response:**

.. code-block::

   bool       success

SetVeljRt
---------

**Request:**

.. code-block::

   float64[6] vel

**Response:**

.. code-block::

   bool       success

SetVelxRt
---------

**Request:**

.. code-block::

   float64    trans
   float64    rotation

**Response:**

.. code-block::

   bool       success

StartRtControl
--------------

**Request:**

(None)

**Response:**

.. code-block::

   bool       success

StopRtControl
-------------

**Request:**

(None)

**Response:**

.. code-block::

   bool       success

WriteDataRt
-----------

**Request:**

.. code-block::

   float64[6] external_force_torque
   int32      external_digital_input
   int32      external_digital_output
   float64[6] external_analog_input
   float64[6] external_analog_output

**Response:**

.. code-block::

   bool       success