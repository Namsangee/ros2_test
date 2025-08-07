.. _io_services:

io Services
===========

.. contents::
   :depth: 1
   :local:

.. _GetCtrlBoxAnalogInput:

GetCtrlBoxAnalogInput
---------------------

**Request:**

.. code-block::

   int8        channel    # 1 = ch1, 2= ch2

**Response:**

.. code-block::

   float64     value
   bool        success

.. _GetCtrlBoxDigitalInput:

GetCtrlBoxDigitalInput
----------------------

This service reads the I/O signals from digital contact points of the controller and reads the digital input contact value.

**Request:**

.. code-block::

   int8        index    # Digital Input in Control Box (1 ~ 16)

**Response:**

.. code-block::

   int8        value    # 0 = OFF, 1 = ON
   bool        success

.. _GetCtrlBoxDigitalOutput:

GetCtrlBoxDigitalOutput
-----------------------

**Request:**

.. code-block::

   int8       index    # Control box digital output port (1 ~ 16)

**Response:**

.. code-block::

   int8       value    # Current output status (0 = ON, 1 = OFF)
   bool       success

.. _GetToolDigitalInput:

GetToolDigitalInput
-------------------

This service gets the current control box IO input status.

**Request:**

.. code-block::

   int8        index    # Digital Input in Flange (1 ~ 6)

**Response:**

.. code-block::

   int8        value    # 0 = OFF, 1 = ON
   bool        success

.. _GetToolDigitalOutput:

GetToolDigitalOutput
--------------------

This service gets the current tool IO output status.

**Request:**

.. code-block::

   int8       index    # Flange digital output port (1 ~ 6)

**Response:**

.. code-block::

   int8       value    # Current output status (0 = ON, 1 = OFF)
   bool       success

.. _SetCtrlBoxAnalogInputType:

SetCtrlBoxAnalogInputType
-------------------------

**Request:**

.. code-block::

   int8        channel  # 1 = ch1, 2 = ch2 
   int8        mode     # 0 = current, 1 = voltage

**Response:**

.. code-block::

   bool        success

.. _SetCtrlBoxAnalogOutput:

SetCtrlBoxAnalogOutput
----------------------

**Request:**

.. code-block::

   int8        channel  # 1 = ch1, 2 = ch2 
   float64     value

**Response:**

.. code-block::

   bool        success

.. _SetCtrlBoxAnalogOutputType:

SetCtrlBoxAnalogOutputType
--------------------------

**Request:**

.. code-block::

   int8        channel  # 1 = ch1, 2 = ch2 
   int8        mode     # 0 = current, 1 = voltage

**Response:**

.. code-block::

   bool        success

.. _SetCtrlBoxDigitalOutput:

SetCtrlBoxDigitalOutput
---------------------
