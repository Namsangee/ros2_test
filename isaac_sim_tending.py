# /clock 발행 기능 추가

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
# Paths / Constants
# -----------------------------------------------------------------------------
ROBOT_MOUNT_PRIM      = "/Root"
ROBOT_USD_PATH        = "/ros2_ws/src/curobo/cumotion_pkg/config/usd/m1013_gripper.usd" # docker
# ROBOT_USD_PATH        = "/home/gijung/ros2_ws/src/curobo/cumotion_pkg/config/usd/m1013_gripper.usd" # local
BACKGROUND_STAGE_PRIM = "/background"
BACKGROUND_USD_PATH   = "/Isaac/Environments/Simple_Room/simple_room.usd"
GRAPH_PATH            = "/ActionGraph"
ROS_VIEWPORT_NAME     = "ros_camera_viewport"


MACHINE_PRIM_PATH = "/Environment/Machine"                 # 스테이지에 놓을 부모 Xform 경로
MACHINE_USD_PATH  = "/ros2_ws/src/curobo/cumotion_pkg/config/etc/machine/machine.usdc"          # << 여기에 본인 machine.usd 경로 지정


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
    """Check if prim exists at given path."""
    stg = omni.usd.get_context().get_stage()
    if not stg:
        return False
    p = stg.GetPrimAtPath(path)
    return bool(p and p.IsValid())

def find_robot_root_candidates():
    return ["/Root/m1013/m1013", "/Root/m1013", "/m1013/m1013", "/m1013"]

def pick_robot_root():
    """Return first valid robot root candidate, fallback to /Root/m1013."""
    wait_stage()
    for p in find_robot_root_candidates():
        if prim_exists(p):
            return p
    return "/Root/m1013"

def find_camera_path():
    """Find camera prim path under robot root, fallback to recursive search."""
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
    """Find prim named 'grasp_frame' under robot root."""
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


if not os.path.exists(MACHINE_USD_PATH):
    raise FileNotFoundError(f"Machine USD not found: {MACHINE_USD_PATH}")

# 없으면 부모 Xform 생성 + 위치/회전/스케일 설정
if not prim_exists(MACHINE_PRIM_PATH):
    prims.create_prim(
        MACHINE_PRIM_PATH,
        "Xform",
        # 원하는 위치 (m): x, y, z
        position=np.array([-1.8, 0.0, 0.0], dtype=float),   # 예: 로봇 오른쪽으로 0.8 m
        # 원하는 회전 (deg): z- yaw, y- pitch, x- roll
        orientation=rotations.gf_rotation_to_np_array(
            Gf.Rotation(Gf.Vec3d(0,0,1), -90.0) *          # yaw 180°
            Gf.Rotation(Gf.Vec3d(0,1,0),   0.0)  *          # pitch 0°
            Gf.Rotation(Gf.Vec3d(1,0,0),   0.0)             # roll 0°
        ),
        scale=np.array([1.0, 1.0, 1.0], dtype=float),
    )

# machine.usd를 해당 Xform 아래에 reference
stage.add_reference_to_stage(MACHINE_USD_PATH, MACHINE_PRIM_PATH)

for _ in range(10):
    simulation_app.update()
    time.sleep(0.02)

# Add cube from screenshot values
prims.create_prim(
    "/Cube",
    "Cube",
    position=np.array([-0.04694, 0.33183, 0.10395]),
    scale=np.array([0.04, 0.4, 0.15])
)

# Blue cube
blue_box_prim = prims.create_prim("/blue_box", "Xform", position=np.array([-0.2, 0.025, 0.05]))
cube_prim = prims.create_prim("/blue_box/cube", "Cube")
cube_geom = UsdGeom.Cube(cube_prim)
cube_geom.GetSizeAttr().Set(0.04)
material_prim = prims.create_prim("/blue_box/material", "Material")
material = UsdShade.Material(material_prim)
shader = UsdShade.Shader.Define(stage.get_current_stage(), "/blue_box/material/shader")
shader.CreateIdAttr("UsdPreviewSurface")
shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set((0, 0, 230/255.0))
material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
UsdShade.MaterialBindingAPI(cube_prim).Bind(material)
UsdPhysics.RigidBodyAPI.Apply(cube_prim)
UsdPhysics.CollisionAPI.Apply(cube_prim)
mass_api = UsdPhysics.MassAPI.Apply(cube_prim)
mass_api.GetMassAttr().Set(0.05)

# Red cube
red_box_prim = prims.create_prim("/red_cube", "Xform", position=np.array([0.1646, -0.02, 0.055]))
red_cube_geom_prim = prims.create_prim("/red_cube/cube", "Cube")
red_cube_geom = UsdGeom.Cube(red_cube_geom_prim)
red_cube_geom.GetSizeAttr().Set(0.04)
red_material_prim = prims.create_prim("/red_cube/material", "Material")
red_material = UsdShade.Material(red_material_prim)
red_shader = UsdShade.Shader.Define(stage.get_current_stage(), "/red_cube/material/shader")
red_shader.CreateIdAttr("UsdPreviewSurface")
red_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set((1.0, 0.0, 0.0))
red_material.CreateSurfaceOutput().ConnectToSource(red_shader.ConnectableAPI(), "surface")
UsdShade.MaterialBindingAPI(red_cube_geom_prim).Bind(red_material)
UsdPhysics.RigidBodyAPI.Apply(red_cube_geom_prim)
UsdPhysics.CollisionAPI.Apply(red_cube_geom_prim)
mass_api = UsdPhysics.MassAPI.Apply(red_cube_geom_prim)
mass_api.GetMassAttr().Set(0.05)

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
# Graph 1: Robot <-> ROS (JointStates, Commands) + TF (Robot + Camera)  [SIM TIME + /clock]
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
                ("OnImpulseEvent", "omni.graph.action.OnImpulseEvent"),
                ("Context", "omni.isaac.ros2_bridge.ROS2Context"),
                ("ReadSimTime", "omni.isaac.core_nodes.IsaacReadSimulationTime"),    # ✅ sim time
                ("PublishClock", "omni.isaac.ros2_bridge.ROS2PublishClock"),         # ✅ /clock 퍼블리시
                ("PublishTransformTree", "omni.isaac.ros2_bridge.ROS2PublishTransformTree"),
                ("PublishJointState", "omni.isaac.ros2_bridge.ROS2PublishJointState"),
                ("SubscribeJointState", "omni.isaac.ros2_bridge.ROS2SubscribeJointState"),
                ("ArticulationController", "omni.isaac.core_nodes.IsaacArticulationController"),
            ],
            keys.CONNECT: [
                # 실행 트리거
                ("OnImpulseEvent.outputs:execOut", "PublishJointState.inputs:execIn"),
                ("OnImpulseEvent.outputs:execOut", "SubscribeJointState.inputs:execIn"),
                ("OnImpulseEvent.outputs:execOut", "ArticulationController.inputs:execIn"),
                ("OnImpulseEvent.outputs:execOut", "PublishTransformTree.inputs:execIn"),
                ("OnImpulseEvent.outputs:execOut", "PublishClock.inputs:execIn"),     # ✅ clock도 주기적으로 퍼블리시

                # 컨텍스트
                ("Context.outputs:context", "PublishJointState.inputs:context"),
                ("Context.outputs:context", "SubscribeJointState.inputs:context"),
                ("Context.outputs:context", "PublishTransformTree.inputs:context"),
                ("Context.outputs:context", "PublishClock.inputs:context"),          # ✅

                # 명령/조인트 연결
                ("SubscribeJointState.outputs:jointNames", "ArticulationController.inputs:jointNames"),
                ("SubscribeJointState.outputs:positionCommand", "ArticulationController.inputs:positionCommand"),

                # ✅ sim time 타임스탬프를 각 퍼블리셔에 연결
                ("ReadSimTime.outputs:simulationTime", "PublishJointState.inputs:timeStamp"),
                ("ReadSimTime.outputs:simulationTime", "PublishTransformTree.inputs:timeStamp"),
                ("ReadSimTime.outputs:simulationTime", "PublishClock.inputs:timeStamp"),
            ],
            keys.SET_VALUES: [
                ("Context.inputs:domain_id", ros_domain_id),
                ("ArticulationController.inputs:robotPath", robot_root),

                # 토픽 이름
                ("PublishJointState.inputs:topicName", "/dsr01/joint_states"),
                ("SubscribeJointState.inputs:topicName", "/joint_states"),
                # ("SubscribeJointState.inputs:topicName", "/isaac/joint_states"),

                # TF 대상
                ("PublishTransformTree.inputs:targetPrims", target_list),

                # (선택) clock 토픽 이름을 바꾸고 싶다면 아래 주석 해제
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
                ("OnTick", "omni.graph.action.OnTick"),
                ("CreateViewport", "omni.isaac.core_nodes.IsaacCreateViewport"),
                ("GetRenderProduct", "omni.isaac.core_nodes.IsaacGetViewportRenderProduct"),
                ("SetCamera", "omni.isaac.core_nodes.IsaacSetCameraOnRenderProduct"),
                ("CameraHelperRgb", "omni.isaac.ros2_bridge.ROS2CameraHelper"),
                ("CameraHelperInfo", "omni.isaac.ros2_bridge.ROS2CameraInfoHelper"),
                ("CameraHelperDepth", "omni.isaac.ros2_bridge.ROS2CameraHelper"),
            ],
            keys.CONNECT: [
                ("OnTick.outputs:tick", "CreateViewport.inputs:execIn"),
                ("CreateViewport.outputs:execOut", "GetRenderProduct.inputs:execIn"),
                ("CreateViewport.outputs:viewport", "GetRenderProduct.inputs:viewport"),
                ("GetRenderProduct.outputs:execOut", "SetCamera.inputs:execIn"),
                ("GetRenderProduct.outputs:renderProductPath", "SetCamera.inputs:renderProductPath"),
                ("SetCamera.outputs:execOut", "CameraHelperRgb.inputs:execIn"),
                ("SetCamera.outputs:execOut", "CameraHelperInfo.inputs:execIn"),
                ("SetCamera.outputs:execOut", "CameraHelperDepth.inputs:execIn"),
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
    try:
        og.Controller.set(
            og.Controller.attribute(f"{GRAPH_PATH}/Robot/OnImpulseEvent.state:enableImpulse"),
            True
        )
    except Exception:
        pass

simulation_context.stop()
simulation_app.close()
