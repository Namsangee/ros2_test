.. _timeline_note:

Update Timeline
===============

This page documents major updates, bug fixes, and structural changes made to the Jazzy version of the codebase.

Update Format
-------------

Each entry should include:

- **Date** of change
- **Type** of update (Feature / Fix / Refactor / Docs / etc.)
- **Module or Component** affected
- **Description** of what was changed
- **Related commit or issue (optional)**

Timeline
--------

**2025-07-28**

- **Type**: Feature  
- **Component**: `dsr_bringup2/launch/start.launch.py`  
- **Description**:  
  Added `OnProcessExit` event chaining to ensure `move_group` is launched after `dsr_moveit_controller`. Improved launch stability and reproducibility across Gazebo and real robot modes.  
- **Commit**: `a1b2c3d`


**2025-07-29**

- **Type**: Refactor  
- **Component**: `dsr_hardware2/src/dsr_hardware2.cpp`  
- **Description**:  
  Refactored `read()` and `write()` to support dynamic DOF configuration via `dof_` parameter in URDF. Removed hardcoded `NUM_JOINT` references.  
- **Commit**: `fe234bc`




**2025-08-04**

- **Type**: Fix  
- **Component**: `dsr_msgs2/srv/GetToolForce.srv`  
- **Description**:  
  Fixed `ref` parameter being ignored. Now correctly transforms force/torque values to `DR_BASE`, `DR_WORLD`, or `DR_TOOL` frame.  
- **Issue**: `#235`  




