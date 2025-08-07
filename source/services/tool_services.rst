.. _tool_services:

tool Services
=============

.. contents::
   :depth: 1
   :local:

ConfigCreateTool
----------------

It is a service for registering and using robot Tool information in advance for safety.

**Request:**

.. code-block::

   string          name        # tool name 
   float64         weight      # tool weight 
   float64[3]      cog         # Center of gravity
   float64[6]      inertia     # tool inertia 

**Response:**

.. code-block::

   bool success

ConfigDeleteTool
----------------

It is a service to delete tool information registered in advance in the robot controller.

**Request:**

.. code-block::

   string          name        # tool name 

**Response:**

.. code-block::

   bool success

GetCurrentTool
--------------

It is a service to fetch the currently set tool information from the robot controller.

**Request:**

(None)

**Response:**

.. code-block::

   string         info # tool name
   bool        success

SetCurrentTool
--------------

It is a service to set information about currently installed tool.

**Request:**

.. code-block::

   string          name        # tool name

**Response:**

.. code-block::

   bool            success

SetToolShape
------------

It is a service to set information about currently installed tool.  
Activates the tool shape information of the entered name among the tool shape information registered in the Teach Pendant.

**Request:**

.. code-block::

   string          name        # Tool name registered in the Teach Pendant

**Response:**

.. code-block::

   bool            success