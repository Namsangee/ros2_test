.. _drl_services:

drl Services
============

.. contents::
   :depth: 1
   :local:

.. _DrlPause:

DrlPause
--------

This service is used to stop the currently executing DRL program from the robot controller.

**Request:**

.. code-block::

   (None)

**Response:**

.. code-block::

   bool success

.. _DrlResume:

DrlResume
---------

It is a service to resume the currently paused DRL program in the robot controller.

**Request:**

.. code-block::

   (None)

**Response:**

.. code-block::

   bool success

.. _DrlStart:

DrlStart
--------

This is a service to execute a program configured in the DRL language in the robot controller.

**Request:**

.. code-block::

   int8    robot_system       # Robot System Mode: 0 = Real, 1 = Virtual
   string  code               # DRL code to execute

**Response:**

.. code-block::

   bool success

.. _DrlStop:

DrlStop
-------

**Request:**

.. code-block::

   int8    stop_mode          # <STOP_TYPE> stop_mode

**Response:**

.. code-block::

   bool success

.. _GetDrlState:

GetDrlState
-----------

Get DRL Program State.

**Request:**

.. code-block::

   (None)

**Response:**

.. code-block::

   int8 drl_state             # <DRL_PROGRAM_STATE>
   bool success

