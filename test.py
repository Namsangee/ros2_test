#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, time
import numpy as np

# -----------------------------------------------------------------------------
# Isaac Sim App Initialization
# -----------------------------------------------------------------------------
try:
    from isaacsim import SimulationApp
except Exception:
    from omni.isaac.kit import SimulationApp

CONFIG = {"renderer": "RayTracedLighting", "headless": False}
simulation_app = SimulationApp(CONFIG)

import carb
import omni.usd
import omni.graph.core as og
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils import extensions, nucleus, prims, rotations, stage, viewports
from omni.isaac.core.utils.prims import set_targets
from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf, UsdPhysics

# -----------------------------------------------------------------------------
# Early safety settings (disable known-crashy paths)
# -----------------------------------------------------------------------------
_settings = carb.settings.get_settings()

def _set(k, v):
    try:
        _settings.set(k, v)
    except Exception:
        pass

_set("/renderer/multiGpu/enabled", False)
_set("/rtx/aa/enabled", True)
_set("/rtx/denoiser/enabled", True)
_set("/rtx/reflections/enabled", True)
_set("/rtx/indirectDiffuse/enabled", True)
_set("/renderer/textureStreaming/enabled", True)

# 여러 버전 키 후보 (존재하면 False로)
for key in [
    "/app/viewport/selection/enableOutline",
    "/app/viewport/selection/enableHighlight",
    "/app/viewport/selection/outline/enabled",
    "/app/viewport/selection/highlight/enabled",
]:
    _set(key, False)

# -----------------------------------------------------------------------------
# Paths / Constants
# -----------------------------------------------------------------------------

# m1013
ROBOT_MOUNT_PRIM      = "/Root"
ROBOT_USD_PATH        = "/ros2_ws/src/curobo/cumotion_pkg/config/usd/m1013_gripper.usd"

# room
BACKGROUND_STAGE_PRIM = "/background"
BACKGROUND_USD_PATH   = "/ros2_ws/src/curobo/cumotion_pkg/config/usd/room.usd"

# machine
MACHINE_MOUNT_PATH = "/Environment/Machine" 
MACHINE_USD_PATH  = "/ros2_ws/src/curobo/cumotion_pkg/config/etc/machine/machine.usd"

# plate
PLATE_MOUNT_PATH = "/Environment/Plate" 
PLATE_USD_PATH  = "/ros2_ws/src/curobo/cumotion_pkg/config/etc/plate/plate3.usdc"

GRAPH_PATH            = "/ActionGraph"
ROS_VIEWPORT_NAME     = "ros_camera_viewport"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
# Wait until USD Stage is ready, return stage
def wait_stage(timeout: float = 10.0):
    # Wait until a valid USD stage is available or until timeout expires
    ctx = omni.usd.get_context()
    t0 = time.time()
    while time.time() - t0 < timeout:
        stg = ctx.get_stage()
        if stg:
            return stg
        simulation_app.update()
        time.sleep(0.05)
    return ctx.get_stage()


def prim_exists(path: str) -> bool:
    # Check if a prim exists and is valid at the given USD stage path
    stg = omni.usd.get_context().get_stage()
    if not stg:
        return False
    p = stg.GetPrimAtPath(path)
    return bool(p and p.IsValid())


def pick_robot_root():
    # Return the first valid robot root prim path, fallback to default if none found
    wait_stage()
    candidates = ["/Root/m1013/m1013", "/Root/m1013", "/m1013/m1013", "/m1013"]
    for p in candidates:
        if prim_exists(p):
            return p
    return "/Root/m1013"


def find_camera_path():
    # Search for a valid camera prim path under the robot root
    stg = wait_stage()
    robot_root = pick_robot_root()
    candidates = [
        "/Root/m1013/d435i_camera/realsense_camera",
        "/Root/m1013/m1013/d435i_camera/realsense_camera",
        f"{robot_root}/d435i_camera/realsense_camera",
        f"{robot_root}/realsense_camera",
    ]
    for c in candidates:
        p = stg.GetPrimAtPath(c)
        if p and p.IsValid() and UsdGeom.Camera.Get(stg, p.GetPath()):
            return str(p.GetPath())
    root_prim = stg.GetPrimAtPath(robot_root)
    if root_prim and root_prim.IsValid():
        for p in Usd.PrimRange(root_prim):
            if UsdGeom.Camera.Get(stg, p.GetPath()):
                return str(p.GetPath())
    return None


def find_grasp_frame_path():
    # Locate the grasp_frame prim path under the robot root
    stg = wait_stage()
    robot_root = pick_robot_root()
    candidates = [
        f"{robot_root}/grasp_frame",
        f"{robot_root}/gripper_frame/grasp_frame",
        "/Root/m1013/m1013/grasp_frame",
        "/Root/m1013/gripper_frame/grasp_frame",
    ]
    for c in candidates:
        p = stg.GetPrimAtPath(c)
        if p and p.IsValid():
            return str(p.GetPath())
    root_prim = stg.GetPrimAtPath(robot_root)
    if root_prim and root_prim.IsValid():
        for p in Usd.PrimRange(root_prim):
            if p.GetName() == "grasp_frame":
                return str(p.GetPath())
    return None

# Add a background USD to the stage, handling Isaac content paths and local files
def add_background(background_path: str, prim_path: str):
    assets_root_path = nucleus.get_assets_root_path()

    if background_path.startswith("/Isaac"):
        if not assets_root_path:
            carb.log_warn("[Background] Isaac content path given but assets_root_path is None; skipping.")
            return
        full = assets_root_path + background_path
        stage.add_reference_to_stage(full, prim_path)
        return

    if os.path.isabs(background_path):
        if not os.path.exists(background_path):
            raise FileNotFoundError(f"[Background] Local USD not found: {background_path}")
        stage.add_reference_to_stage(f"file://{background_path}", prim_path)
        return

    stage.add_reference_to_stage(background_path, prim_path)

def _norm_usd_path(p: str) -> str:
    assets_root = nucleus.get_assets_root_path()
    if p.startswith("/Isaac"):
        if not assets_root:
            raise RuntimeError("No Nucleus assets root for /Isaac path")
        return assets_root + p
    if os.path.isabs(p):
        if not os.path.exists(p):
            raise FileNotFoundError(p)
        return "file://" + p
    return p

def fix_plate(usd_path: str, mount_path: str):
    stg = wait_stage()
    # ensure mount prim
    if not prim_exists(mount_path):
        prims.create_prim(mount_path, "Xform")

    # re-add reference cleanly
    prim = stg.GetPrimAtPath(mount_path)
    try:
        prim.GetReferences().ClearReferences()
    except Exception:
        pass
    stage.add_reference_to_stage(_norm_usd_path(usd_path), mount_path)

    # let the reference load a moment
    for _ in range(3):
        simulation_app.update()

    # patch all meshes under the plate: disable subdivision, enable double-sided
    root = stg.GetPrimAtPath(mount_path)
    for p in Usd.PrimRange(root):
        m = UsdGeom.Mesh(p)
        if not m:
            continue
        try: m.GetSubdivisionSchemeAttr().Set("none")
        except Exception: pass
        try: m.CreateDoubleSidedAttr(True)
        except Exception: pass
# -----------------------------------------------------------------------------
# ROS2 Bridge / Simulation Context
# -----------------------------------------------------------------------------
extensions.enable_extension("omni.isaac.ros2_bridge")
simulation_app.update()
simulation_context = SimulationContext(stage_units_in_meters=1.0)

# -----------------------------------------------------------------------------
# Scene Setup
# -----------------------------------------------------------------------------
assets_root_path = nucleus.get_assets_root_path()
if assets_root_path is None:
    carb.log_warn("No Nucleus assets root found; proceeding with local assets only.")

viewports.set_camera_view(eye=np.array([1.2, 1.2, 0.8]), target=np.array([0, 0, 0.5]))  # Setting viewports
add_background(BACKGROUND_USD_PATH, BACKGROUND_STAGE_PRIM) # Setting background usd

# Setting robot usd
if not os.path.exists(ROBOT_USD_PATH):
    raise FileNotFoundError(f"Robot USD not found: {ROBOT_USD_PATH}")
if not prim_exists("/Root/m1013"):
    prims.create_prim(
        "/Root/m1013",
        "Xform",
        position=np.array([0.0, -0.64, -0.23]),
        orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0, 0, 1), 90)),
    )
stage.add_reference_to_stage(ROBOT_USD_PATH, "/Root/m1013")

# Setting machine usd
if not os.path.exists(MACHINE_USD_PATH):
    raise FileNotFoundError(f"Machine USD not found: {MACHINE_USD_PATH}")
if not prim_exists(MACHINE_MOUNT_PATH):
    prims.create_prim(
        MACHINE_MOUNT_PATH,
        "Xform",
        position=np.array([-1.5, 0.0, 0.0], dtype=float),
        orientation=rotations.gf_rotation_to_np_array(
            Gf.Rotation(Gf.Vec3d(0,0,1), 0.0) *   
            Gf.Rotation(Gf.Vec3d(0,1,0),   -90.0)  *   
            Gf.Rotation(Gf.Vec3d(1,0,0),   90.0)  
        ),
        scale=np.array([1.0, 1.0, 1.0], dtype=float),
    )
stage.add_reference_to_stage(MACHINE_USD_PATH, MACHINE_MOUNT_PATH)

# Setting robot usd
if not os.path.exists(ROBOT_USD_PATH):
    raise FileNotFoundError(f"Robot USD not found: {ROBOT_USD_PATH}")
if not prim_exists("/Root/m1013"):
    prims.create_prim(
        "/Root/m1013",
        "Xform",
        position=np.array([0.0, -0.64, -0.23]),
        orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0, 0, 1), 90)),
    )
stage.add_reference_to_stage(ROBOT_USD_PATH, "/Root/m1013")

# Setting plate usd
fix_plate(PLATE_USD_PATH, PLATE_MOUNT_PATH)
# if not os.path.exists(PLATE_USD_PATH):
#     raise FileNotFoundError(f"Machine USD not found: {PLATE_USD_PATH}")
# if not prim_exists(PLATE_MOUNT_PATH):
#     prims.create_prim(
#         PLATE_MOUNT_PATH,
#         "Xform",
#         position=np.array([0.0, 0.0, 0.0], dtype=float),
#         orientation=rotations.gf_rotation_to_np_array(
#             Gf.Rotation(Gf.Vec3d(0,0,1), 0.0) *   
#             Gf.Rotation(Gf.Vec3d(0,1,0),   0.0)  *   
#             Gf.Rotation(Gf.Vec3d(1,0,0),   0.0)  
#         ),
#         scale=np.array([1.0, 1.0, 1.0], dtype=float),
#     )
# stage.add_reference_to_stage(PLATE_USD_PATH, PLATE_MOUNT_PATH)

for _ in range(10):
    simulation_app.update()
    time.sleep(0.02)

simulation_app.update()

# -----------------------------------------------------------------------------
# ROS_DOMAIN_ID
# -----------------------------------------------------------------------------
try:
    ros_domain_id = int(os.environ["ROS_DOMAIN_ID"])
    print("Using ROS_DOMAIN_ID:", ros_domain_id)
except (ValueError, KeyError):
    ros_domain_id = 0
    print("ROS_DOMAIN_ID not set, using 0")

# -----------------------------------------------------------------------------
# Robot / Camera paths
# -----------------------------------------------------------------------------
robot_root = pick_robot_root()
camera_path = find_camera_path()
grasp_frame_path = find_grasp_frame_path()
if not grasp_frame_path:
    print("[WARN] grasp_frame prim not found under robot root.")
else:
    print("[INFO] grasp_frame prim:", grasp_frame_path)

if not camera_path:
    raise RuntimeError("Camera prim not found under /Root/m1013.")
print("[INFO] Robot root:", robot_root)
print("[INFO] Camera prim:", camera_path)

# -----------------------------------------------------------------------------
# Graph 1: Robot <-> ROS + TF + /clock  (OnTick: per-frame publish)
# -----------------------------------------------------------------------------
target_list = [Sdf.Path(robot_root), Sdf.Path(camera_path)]
if grasp_frame_path:
    target_list.append(Sdf.Path(grasp_frame_path))

try:
    keys = og.Controller.Keys
    og.Controller.edit(
        {"graph_path": f"{GRAPH_PATH}/Robot", "evaluator_name": "execution"},
        {
            keys.CREATE_NODES: [
                ("OnTick", "omni.graph.action.OnTick"),
                ("Context", "omni.isaac.ros2_bridge.ROS2Context"),
                ("ReadSimTime", "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                ("PublishClock", "omni.isaac.ros2_bridge.ROS2PublishClock"),
                ("PublishTransformTree", "omni.isaac.ros2_bridge.ROS2PublishTransformTree"),
                ("PublishJointState", "omni.isaac.ros2_bridge.ROS2PublishJointState"),
                ("SubscribeJointState", "omni.isaac.ros2_bridge.ROS2SubscribeJointState"),
                ("ArticulationController", "omni.isaac.core_nodes.IsaacArticulationController"),
            ],
            keys.CONNECT: [
                # per-frame triggers
                ("OnTick.outputs:tick", "PublishJointState.inputs:execIn"),
                ("OnTick.outputs:tick", "SubscribeJointState.inputs:execIn"),
                ("OnTick.outputs:tick", "ArticulationController.inputs:execIn"),
                ("OnTick.outputs:tick", "PublishTransformTree.inputs:execIn"),
                ("OnTick.outputs:tick", "PublishClock.inputs:execIn"),

                # context
                ("Context.outputs:context", "PublishJointState.inputs:context"),
                ("Context.outputs:context", "SubscribeJointState.inputs:context"),
                ("Context.outputs:context", "PublishTransformTree.inputs:context"),
                ("Context.outputs:context", "PublishClock.inputs:context"),

                # commands/joints
                ("SubscribeJointState.outputs:jointNames", "ArticulationController.inputs:jointNames"),
                ("SubscribeJointState.outputs:positionCommand", "ArticulationController.inputs:positionCommand"),

                # timestamps (sim time)
                ("ReadSimTime.outputs:simulationTime", "PublishJointState.inputs:timeStamp"),
                ("ReadSimTime.outputs:simulationTime", "PublishTransformTree.inputs:timeStamp"),
                ("ReadSimTime.outputs:simulationTime", "PublishClock.inputs:timeStamp"),
            ],
            keys.SET_VALUES: [
                ("Context.inputs:domain_id", ros_domain_id),
                ("ArticulationController.inputs:robotPath", robot_root),

                ("PublishJointState.inputs:topicName", "/dsr01/joint_states"),
                ("SubscribeJointState.inputs:topicName", "/joint_states"),
                ("PublishTransformTree.inputs:targetPrims", target_list),
                # ("PublishClock.inputs:topicName", "/clock"),
            ],
        },
    )
    set_targets(
        prim=wait_stage().GetPrimAtPath(f"{GRAPH_PATH}/Robot/PublishJointState"),
        attribute="inputs:targetPrim",
        target_prim_paths=[robot_root],
    )
except Exception as e:
    print(f"[Robot Graph] Error: {e}")

# -----------------------------------------------------------------------------
# Graph 2: Camera -> ROS (RGB/Depth/CameraInfo)
# -----------------------------------------------------------------------------
try:
    camera_frame = camera_path.split("/")[-1]
    keys = og.Controller.Keys
    (ros_camera_graph, _, _, _) = og.Controller.edit(
        {
            "graph_path": f"{GRAPH_PATH}/Camera",
            "evaluator_name": "push",
            "pipeline_stage": og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND,
        },
        {
            keys.CREATE_NODES: [
                ("OnStart", "omni.graph.action.OnImpulseEvent"),  # once
                ("OnTick", "omni.graph.action.OnTick"),            # per-frame
                ("CreateViewport", "omni.isaac.core_nodes.IsaacCreateViewport"),
                ("GetRenderProduct", "omni.isaac.core_nodes.IsaacGetViewportRenderProduct"),
                ("SetCamera", "omni.isaac.core_nodes.IsaacSetCameraOnRenderProduct"),
                ("CameraHelperRgb", "omni.isaac.ros2_bridge.ROS2CameraHelper"),
                ("CameraHelperInfo", "omni.isaac.ros2_bridge.ROS2CameraInfoHelper"),
                ("CameraHelperDepth", "omni.isaac.ros2_bridge.ROS2CameraHelper"),
            ],
            keys.CONNECT: [
                # Once: build viewport & render product
                ("OnStart.outputs:execOut", "CreateViewport.inputs:execIn"),
                ("CreateViewport.outputs:execOut", "GetRenderProduct.inputs:execIn"),
                ("CreateViewport.outputs:viewport", "GetRenderProduct.inputs:viewport"),
                ("GetRenderProduct.outputs:execOut", "SetCamera.inputs:execIn"),
                ("GetRenderProduct.outputs:renderProductPath", "SetCamera.inputs:renderProductPath"),

                # Per-frame: publish images/info
                ("OnTick.outputs:tick", "CameraHelperRgb.inputs:execIn"),
                ("OnTick.outputs:tick", "CameraHelperInfo.inputs:execIn"),
                ("OnTick.outputs:tick", "CameraHelperDepth.inputs:execIn"),
                ("GetRenderProduct.outputs:renderProductPath", "CameraHelperRgb.inputs:renderProductPath"),
                ("GetRenderProduct.outputs:renderProductPath", "CameraHelperInfo.inputs:renderProductPath"),
                ("GetRenderProduct.outputs:renderProductPath", "CameraHelperDepth.inputs:renderProductPath"),
            ],
            keys.SET_VALUES: [
                ("CreateViewport.inputs:name", ROS_VIEWPORT_NAME),
                ("CreateViewport.inputs:viewportId", 2),
                ("CameraHelperRgb.inputs:frameId",  camera_frame),
                ("CameraHelperInfo.inputs:frameId", camera_frame),
                ("CameraHelperDepth.inputs:frameId", camera_frame),
                ("CameraHelperRgb.inputs:topicName", "rgb"),
                ("CameraHelperRgb.inputs:type", "rgb"),
                ("CameraHelperInfo.inputs:topicName", "camera_info"),
                ("CameraHelperDepth.inputs:topicName", "depth"),
                ("CameraHelperDepth.inputs:type", "depth"),
                ("SetCamera.inputs:cameraPrim", [Sdf.Path(camera_path)]),
            ],
        },
    )
    # fire once
    og.Controller.set(
        og.Controller.attribute(f"{GRAPH_PATH}/Camera/OnStart.state:enableImpulse"),
        True
    )
    og.Controller.evaluate_sync(ros_camera_graph)
except Exception as e:
    print(f"[Camera Graph] Error: {e}")

# -----------------------------------------------------------------------------
# Camera Intrinsics
# -----------------------------------------------------------------------------
def set_realsense_intrinsics(cam_path: str):
    stg = wait_stage()
    prim = stg.GetPrimAtPath(cam_path)
    if not prim or not prim.IsValid():
        raise RuntimeError(f"Camera prim not found or not ready: {cam_path}")
    cam = UsdGeom.Camera(prim)
    if not cam or not cam.GetPrim().IsValid():
        raise RuntimeError(f"Prim exists but is not a UsdGeom.Camera: {cam_path}")
    cam.GetHorizontalApertureAttr().Set(20.955)
    cam.GetVerticalApertureAttr().Set(15.7)
    cam.GetFocalLengthAttr().Set(18.8)
    cam.GetFocusDistanceAttr().Set(400.0)

set_realsense_intrinsics(camera_path)

# -----------------------------------------------------------------------------
# Simulation Loop
# -----------------------------------------------------------------------------
simulation_context.initialize_physics()
simulation_context.play()

while simulation_app.is_running():
    simulation_context.step(render=True)

simulation_context.stop()
simulation_app.close()
