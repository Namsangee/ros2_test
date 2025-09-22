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

# 멀티 GPU/RTX 후처리/선택 하이라이트 비활성화 (필요 시 나중에 단계적으로 켜기)
_set("/renderer/multiGpu/enabled", False)
_set("/rtx/aa/enabled", True)
_set("/rtx/denoiser/enabled", True)
_set("/rtx/reflections/enabled", False)
_set("/rtx/indirectDiffuse/enabled", False)
_set("/renderer/textureStreaming/enabled", True)  # VRAM 피크 완화

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
ROBOT_MOUNT_PRIM      = "/Root"
ROBOT_USD_PATH        = "/ros2_ws/src/curobo/cumotion_pkg/config/usd/m1013_gripper.usd"  # docker
BACKGROUND_STAGE_PRIM = "/background"
BACKGROUND_USD_PATH   = "/Isaac/Environments/Simple_Room/simple_room.usd"
GRAPH_PATH            = "/ActionGraph"
ROS_VIEWPORT_NAME     = "ros_camera_viewport"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def wait_stage(timeout: float = 10.0):
    """Wait until USD Stage is ready, return stage."""
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
    stg = omni.usd.get_context().get_stage()
    if not stg:
        return False
    p = stg.GetPrimAtPath(path)
    return bool(p and p.IsValid())

def find_robot_root_candidates():
    return ["/Root/m1013/m1013", "/Root/m1013", "/m1013/m1013", "/m1013"]

def pick_robot_root():
    wait_stage()
    for p in find_robot_root_candidates():
        if prim_exists(p):
            return p
    return "/Root/m1013"

def find_camera_path():
    stg = wait_stage()
    candidates = [
        "/Root/m1013/d435i_camera/realsense_camera",
        "/Root/m1013/m1013/d435i_camera/realsense_camera",
    ]
    robot_root = pick_robot_root()
    candidates += [
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
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit(1)

viewports.set_camera_view(eye=np.array([1.2, 1.2, 0.8]), target=np.array([0, 0, 0.5]))
stage.add_reference_to_stage(assets_root_path + BACKGROUND_USD_PATH, BACKGROUND_STAGE_PRIM)

if not os.path.exists(ROBOT_USD_PATH):
    raise FileNotFoundError(f"Robot USD not found: {ROBOT_USD_PATH}")

if not prim_exists("/Root/m1013"):
    prims.create_prim(
        "/Root/m1013",
        "Xform",
        position=np.array([0.0, -0.64, 0.0]),
        orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0, 0, 1), 90)),
    )

stage.add_reference_to_stage(ROBOT_USD_PATH, "/Root/m1013")

for _ in range(10):
    simulation_app.update()
    time.sleep(0.02)

# # Sample cubes
# prims.create_prim(
#     "/Cube",
#     "Cube",
#     position=np.array([-0.04694, 0.33183, 0.10395]),
#     scale=np.array([0.04, 0.4, 0.15])
# )

# blue_box_prim = prims.create_prim("/blue_box", "Xform", position=np.array([-0.2, 0.025, 0.05]))
# cube_prim = prims.create_prim("/blue_box/cube", "Cube")
# cube_geom = UsdGeom.Cube(cube_prim); cube_geom.GetSizeAttr().Set(0.04)
# material_prim = prims.create_prim("/blue_box/material", "Material")
# material = UsdShade.Material(material_prim)
# shader = UsdShade.Shader.Define(stage.get_current_stage(), "/blue_box/material/shader")
# shader.CreateIdAttr("UsdPreviewSurface")
# shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set((0.0, 0.0, 230/255.0))
# material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
# UsdShade.MaterialBindingAPI(cube_prim).Bind(material)
# UsdPhysics.RigidBodyAPI.Apply(cube_prim)
# UsdPhysics.CollisionAPI.Apply(cube_prim)
# mass_api = UsdPhysics.MassAPI.Apply(cube_prim); mass_api.GetMassAttr().Set(0.05)

# red_box_prim = prims.create_prim("/red_cube", "Xform", position=np.array([0.1646, -0.02, 0.055]))
# red_cube_geom_prim = prims.create_prim("/red_cube/cube", "Cube")
# red_cube_geom = UsdGeom.Cube(red_cube_geom_prim); red_cube_geom.GetSizeAttr().Set(0.04)
# red_material_prim = prims.create_prim("/red_cube/material", "Material")
# red_material = UsdShade.Material(red_material_prim)
# red_shader = UsdShade.Shader.Define(stage.get_current_stage(), "/red_cube/material/shader")
# red_shader.CreateIdAttr("UsdPreviewSurface")
# red_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set((1.0, 0.0, 0.0))
# red_material.CreateSurfaceOutput().ConnectToSource(red_shader.ConnectableAPI(), "surface")
# UsdShade.MaterialBindingAPI(red_cube_geom_prim).Bind(red_material)
# UsdPhysics.RigidBodyAPI.Apply(red_cube_geom_prim)
# UsdPhysics.CollisionAPI.Apply(red_cube_geom_prim)
# mass_api = UsdPhysics.MassAPI.Apply(red_cube_geom_prim); mass_api.GetMassAttr().Set(0.05)

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
                # ("PublishClock.inputs:topicName", "/clock"),  # 기본값 사용 시 주석 유지
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
#   중요: 뷰포트/렌더프로덕트는 '한 번만' 생성 (OnStart), 퍼블리시는 매 프레임(OnTick)
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
    # render=True여도 이제 뷰포트/렌더프로덕트는 재생성되지 않음
    simulation_context.step(render=True)

simulation_context.stop()
simulation_app.close()
