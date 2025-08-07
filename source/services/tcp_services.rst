.. _tcp_services:

tcp Services
============

.. contents::
   :depth: 1
   :local:

ConfigCreateTcp
---------------

It is a service for registering and using robot TCP information in advance for safety.

**Request:**

.. code-block::

   string          name         # tcp name 
   float64[6]      pos          # coordinates of the TCP 

**Response:**

.. code-block::

   bool success

ConfigDeleteTcp
---------------

It is a service for deleting the TCP information registered in advance in the robot controller.

**Request:**

.. code-block::

   string          name             # tcp name 

**Response:**

.. code-block::

   bool success

GetCurrentTcp
-------------

It is the service to get the currently set TCP information from the robot controller.

**Request:**

(None)

**Response:**

.. code-block::

   string         info # tcp name
   bool        success

SetCurrentTcp
-------------

It is a service that sets the information about the currently installed TCP.

**Request:**

.. code-block::

   string         name # tcp name

**Response:**

.. code-block::

   bool           success
