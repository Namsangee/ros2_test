#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, time
import numpy as np

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
from omni.isaac.core.utils import extensions, prims, rotations, stage, viewports
from omni.isaac import nucleus
from omni.isaac.core.utils.prims import set_targets, create_prim
from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf, UsdPhysics
try:
    from pxr import PhysxSchema
except Exception:
    PhysxSchema = None

_settings = carb.settings.get_settings()
def _set(k, v):
    try: _settings.set(k, v)
    except Exception: pass

_set("/renderer/multiGpu/enabled", False)
_set("/rtx/aa/enabled", True)
_set("/rtx/denoiser/enabled", True)
_set("/rtx/reflections/enabled", True)
_set("/rtx/indirectDiffuse/enabled", True)
_set("/renderer/textureStreaming/enabled", True)
for key in ["/app/viewport/selection/enableOutline",
            "/app/viewport/selection/enableHighlight",
            "/app/viewport/selection/outline/enabled",
            "/app/viewport/selection/highlight/enabled"]:
    _set(key, False)

ROBOT_MOUNT_PRIM = "/Root"
ROBOT_USD_PATH = "/ros2_ws/src/curobo/cumotion_pkg/config/usd/m1013_gripper.usd"
BACKGROUND_STAGE_PRIM = "/background"
BACKGROUND_USD_PATH = "/ros2_ws/src/curobo/cumotion_pkg/config/usd/room.usd"
MACHINE_MOUNT_PATH = "/Environment/Machine"
MACHINE_USD_PATH = "/ros2_ws/src/curobo/cumotion_pkg/config/etc/machine/machine.usd"
PLATE_MOUNT_PATH = "/Environment/Plate"
PLATE_USD_PATH = "/ros2_ws/src/curobo/cumotion_pkg/config/etc/plate/plate.usd"
GRAPH_PATH = "/ActionGraph"
ROS_VIEWPORT_NAME = "ros_camera_viewport"
IDENTITY_QUAT = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)

def wait_stage(timeout: float = 10.0):
    ctx = omni.usd.get_context()
    t0 = time.time()
    while time.time() - t0 < timeout:
        stg = ctx.get_stage()
        if stg: return stg
        simulation_app.update(); time.sleep(0.05)
    return ctx.get_stage()

def prim_exists(path: str) -> bool:
    stg = omni.usd.get_context().get_stage()
    if not stg: return False
    p = stg.GetPrimAtPath(path)
    return bool(p and p.IsValid())

def pick_robot_root():
    wait_stage()
    for p in ["/Root/m1013/m1013", "/Root/m1013", "/m1013/m1013", "/m1013"]:
        if prim_exists(p): return p
    return "/Root/m1013"

def find_camera_path():
    stg = wait_stage()
    robot_root = pick_robot_root()
    for c in ["/Root/m1013/d435i_camera/realsense_camera",
              "/Root/m1013/m1013/d435i_camera/realsense_camera",
              f"{robot_root}/d435i_camera/realsense_camera",
              f"{robot_root}/realsense_camera"]:
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
    for c in [f"{robot_root}/grasp_frame",
              f"{robot_root}/gripper_frame/grasp_frame",
              "/Root/m1013/m1013/grasp_frame",
              "/Root/m1013/gripper_frame/grasp_frame"]:
        p = stg.GetPrimAtPath(c)
        if p and p.IsValid(): return str(p.GetPath())
    root_prim = stg.GetPrimAtPath(robot_root)
    if root_prim and root_prim.IsValid():
        for p in Usd.PrimRange(root_prim):
            if p.GetName() == "grasp_frame": return str(p.GetPath())
    return None

def add_background(background_path: str, prim_path: str):
    assets_root_path = nucleus.get_assets_root_path()
    if background_path.startswith("/Isaac"):
        if not assets_root_path: return
        stage.add_reference_to_stage(assets_root_path + background_path, prim_path); return
    if os.path.isabs(background_path):
        if not os.path.exists(background_path):
            raise FileNotFoundError(background_path)
        stage.add_reference_to_stage(f"file://{background_path}", prim_path); return
    stage.add_reference_to_stage(background_path, prim_path)

def _norm_usd_path(p: str) -> str:
    assets_root = nucleus.get_assets_root_path()
    if p.startswith("/Isaac"):
        if not assets_root: raise RuntimeError("No Nucleus assets root for /Isaac path")
        return assets_root + p
    if os.path.isabs(p):
        if not os.path.exists(p): raise FileNotFoundError(p)
        return "file://" + p
    return p

def fix_plate(usd_path: str, mount_path: str):
    stg = wait_stage()
    if not prim_exists(mount_path): prims.create_prim(mount_path, "Xform")
    prim = stg.GetPrimAtPath(mount_path)
    try: prim.GetReferences().ClearReferences()
    except Exception: pass
    stage.add_reference_to_stage(_norm_usd_path(usd_path), mount_path)
    for _ in range(3): simulation_app.update()
    root = stg.GetPrimAtPath(mount_path)
    for p in Usd.PrimRange(root):
        m = UsdGeom.Mesh(p)
        if not m: continue
        try: m.GetSubdivisionSchemeAttr().Set("none")
        except Exception: pass
        try: m.CreateDoubleSidedAttr(True)
        except Exception: pass

def _apply_collision_to_gprims_static(root_prim: Usd.Prim):
    for p in Usd.PrimRange(root_prim):
        gprim = UsdGeom.Gprim(p)
        if not gprim: continue
        UsdPhysics.CollisionAPI.Apply(p)
        try: p.CreateAttribute("physics:collisionEnabled", Sdf.ValueTypeNames.Bool).Set(True)
        except Exception: pass
        if UsdGeom.Mesh(p):
            try:
                mc = UsdPhysics.MeshCollisionAPI.Apply(p)
                mc.CreateApproximationAttr().Set("sdf")
            except Exception:
                try: p.CreateAttribute("physics:approximation", Sdf.ValueTypeNames.Token).Set("sdf")
                except Exception: pass

def _apply_collision_to_gprims_dynamic(root_prim: Usd.Prim, approx: str = "convexHull"):
    for p in Usd.PrimRange(root_prim):
        gprim = UsdGeom.Gprim(p)
        if not gprim: continue
        UsdPhysics.CollisionAPI.Apply(p)
        try: p.CreateAttribute("physics:collisionEnabled", Sdf.ValueTypeNames.Bool).Set(True)
        except Exception: pass
        if UsdGeom.Mesh(p):
            try:
                mc = UsdPhysics.MeshCollisionAPI.Apply(p)
                mc.CreateApproximationAttr().Set(approx)
            except Exception:
                try: p.CreateAttribute("physics:approximation", Sdf.ValueTypeNames.Token).Set(approx)
                except Exception: pass

def add_static_colliders(root_path: str):
    stg = omni.usd.get_context().get_stage()
    root = stg.GetPrimAtPath(root_path)
    if not root or not root.IsValid(): return
    _apply_collision_to_gprims_static(root)

def add_rigid_body(root_path: str, mass: float = 1.0, kinematic: bool = False):
    stg = omni.usd.get_context().get_stage()
    root = stg.GetPrimAtPath(root_path)
    if not root or not root.IsValid(): return
    UsdPhysics.RigidBodyAPI.Apply(root)
    UsdPhysics.MassAPI.Apply(root).CreateMassAttr(mass)
    if kinematic:
        set_ok = False
        try:
            if PhysxSchema is not None:
                api = PhysxSchema.PhysxRigidBodyAPI.Apply(root)
                if hasattr(api, "CreateKinematicEnabledAttr"):
                    api.CreateKinematicEnabledAttr(True); set_ok = True
        except Exception: pass
        if not set_ok:
            try:
                attr = root.CreateAttribute("physxRigidBody:kinematicEnabled", Sdf.ValueTypeNames.Bool)
                attr.Set(True)
            except Exception: pass
    _apply_collision_to_gprims_dynamic(root, approx="convexHull")

def _plate_top_z(plate_root: str) -> float:
    stg = omni.usd.get_context().get_stage()
    prim = stg.GetPrimAtPath(plate_root)
    if not prim or not prim.IsValid(): return 0.0
    try:
        bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(),
                                       includedPurposes=[UsdGeom.Tokens.default_,
                                                         UsdGeom.Tokens.render,
                                                         UsdGeom.Tokens.proxy],
                                       useExtentsHint=True)
        world_bbox = bbox_cache.ComputeWorldBound(prim)
        aligned = world_bbox.ComputeAlignedRange()
        return float(aligned.GetMax()[2])
    except Exception:
        return 0.0

def spawn_cylinders_grid(plate_root: str,
                         base_path: str = "/Environment/Cylinders",
                         rows: int = 5, cols: int = 5,
                         spacing: float = 0.12,
                         hole_d: float = 0.05,
                         cyl_h: float = 0.30,
                         mass: float = 0.8,
                         z_epsilon: float = 0.001):
    top_z = _plate_top_z(plate_root)
    radius = hole_d * 0.5
    half_h = cyl_h * 0.5
    x0 = - (cols - 1) * spacing * 0.5
    y0 = - (rows - 1) * spacing * 0.5
    for r in range(rows):
        for c in range(cols):
            x = x0 + c * spacing
            y = y0 + r * spacing
            z = top_z + half_h + z_epsilon
            cyl_path = f"{base_path}/cyl_{r}_{c}"
            create_prim(prim_path=cyl_path, prim_type="Xform",
                        position=np.array([x, y, z], dtype=float),
                        orientation=IDENTITY_QUAT)
            geom_path = cyl_path + "/geom"
            create_prim(geom_path, "Cylinder")
            cyl = UsdGeom.Cylinder(wait_stage().GetPrimAtPath(geom_path))
            cyl.GetRadiusAttr().Set(radius)
            cyl.GetHeightAttr().Set(cyl_h)
            cyl.CreateAxisAttr("Z")
            UsdGeom.Gprim(wait_stage().GetPrimAtPath(geom_path)).CreateDoubleSidedAttr(True)
            try:
                stg = wait_stage()
                mat_path = cyl_path + "/Material"
                mat = UsdShade.Material.Define(stg, mat_path)
                shader = UsdShade.Shader.Define(stg, mat_path + "/Shader")
                shader.CreateIdAttr("UsdPreviewSurface")
                shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.18, 0.18, 0.18))
                shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.5)
                shader.CreateInput("metallic",  Sdf.ValueTypeNames.Float).Set(0.0)
                mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
                UsdShade.MaterialBindingAPI(stg.GetPrimAtPath(geom_path)).Bind(mat)
            except Exception as _e:
                print("[Material] Failed to assign dark gray on", geom_path, ":", _e)
            add_rigid_body(cyl_path, mass=mass, kinematic=False)
            create_prim(prim_path=cyl_path + "/grasp_frame", prim_type="Xform",
                        position=np.array([0.0, 0.0, half_h], dtype=float),
                        orientation=IDENTITY_QUAT)

def make_static_sdf_collider(root_path: str):
    stg = omni.usd.get_context().get_stage()
    root = stg.GetPrimAtPath(root_path)
    if not root or not root.IsValid(): return
    _apply_collision_to_gprims_static(root)

settings = carb.settings.get_settings()
settings.set("/physics/physx/useGpuDynamics", True)
settings.set("/physics/physx/enableGPUBroadPhase", True)
for k in ["/physics/physx/enableSDFCollisions", "/physics/physx/enableSDFCollision"]:
    try: settings.set(k, True)
    except Exception: pass
for k in ["/physics/cooking/meshSDFEnabled", "/physics/cooking/enableSDF"]:
    try: settings.set(k, True)
    except Exception: pass

if not prim_exists("/World"): prims.create_prim("/World", "Xform")
if not prim_exists("/World/physicsScene"): prims.create_prim("/World/physicsScene", "PhysicsScene")

try:
    stg = omni.usd.get_context().get_stage()
    ps_prim = stg.GetPrimAtPath("/World/physicsScene")
    if PhysxSchema is not None and ps_prim and ps_prim.IsValid():
        ps_api = PhysxSchema.PhysxSceneAPI.Apply(ps_prim)
        if hasattr(ps_api, "CreateEnableGPUDynamicsAttr"): ps_api.CreateEnableGPUDynamicsAttr(True)
        if hasattr(ps_api, "CreateEnableGPUBroadPhaseAttr"): ps_api.CreateEnableGPUBroadPhaseAttr(True)
        for setter in ["CreateEnableSDFCollisionsAttr", "CreateEnableSDFCollisionAttr"]:
            if hasattr(ps_api, setter): getattr(ps_api, setter)(True)
except Exception as _e:
    print("[PhysX GPU/SDF] Scene API setup warning:", _e)

extensions.enable_extension("omni.isaac.ros2_bridge")
simulation_app.update()
simulation_context = SimulationContext(stage_units_in_meters=1.0)

assets_root_path = nucleus.get_assets_root_path()
if assets_root_path is None:
    carb.log_warn("No Nucleus assets root found; proceeding with local assets only.")

viewports.set_camera_view(eye=np.array([1.2, 1.2, 0.8]), target=np.array([0, 0, 0.5]))
add_background(BACKGROUND_USD_PATH, BACKGROUND_STAGE_PRIM)

if not prim_exists("/World"): prims.create_prim("/World", "Xform")
if not prim_exists("/World/physicsScene"): prims.create_prim("/World/physicsScene", "PhysicsScene")

if not os.path.exists(ROBOT_USD_PATH):
    raise FileNotFoundError(f"Robot USD not found: {ROBOT_USD_PATH}")
if not prim_exists("/Root/m1013"):
    prims.create_prim("/Root/m1013", "Xform",
                      position=np.array([0.0, -0.64, -0.23]),
                      orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0,0,1), 90)))
stage.add_reference_to_stage(ROBOT_USD_PATH, "/Root/m1013")

if not os.path.exists(MACHINE_USD_PATH):
    raise FileNotFoundError(f"Machine USD not found: {MACHINE_USD_PATH}")
if not prim_exists(MACHINE_MOUNT_PATH):
    prims.create_prim(MACHINE_MOUNT_PATH, "Xform",
                      position=np.array([-1.5, 0.0, 0.0], dtype=float),
                      orientation=rotations.gf_rotation_to_np_array(
                          Gf.Rotation(Gf.Vec3d(0,0,1), -90.0)),
                      scale=np.array([1.0,1.0,1.0], dtype=float))
stage.add_reference_to_stage(MACHINE_USD_PATH, MACHINE_MOUNT_PATH)

if not os.path.exists(PLATE_USD_PATH):
    raise FileNotFoundError(f"Plate USD not found: {PLATE_USD_PATH}")
if not prim_exists(PLATE_MOUNT_PATH):
    prims.create_prim(PLATE_MOUNT_PATH, "Xform",
                      position=np.array([0.0, 0.0, -0.2], dtype=float),
                      orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0,0,1), 0.0)),
                      scale=np.array([1.0,1.0,1.0], dtype=float))
stage.add_reference_to_stage(PLATE_USD_PATH, PLATE_MOUNT_PATH)

for _ in range(10):
    simulation_app.update(); time.sleep(0.02)
simulation_app.update()

make_static_sdf_collider(PLATE_MOUNT_PATH)
add_static_colliders(MACHINE_MOUNT_PATH)

spawn_cylinders_grid(
    plate_root=PLATE_MOUNT_PATH,
    base_path="/Environment/Cylinders",
    rows=5, cols=5,
    spacing=0.1,
    hole_d=0.045,
    cyl_h=0.10,
    mass=0.8
)

try:
    ros_domain_id = int(os.environ["ROS_DOMAIN_ID"]); print("Using ROS_DOMAIN_ID:", ros_domain_id)
except (ValueError, KeyError):
    ros_domain_id = 0; print("ROS_DOMAIN_ID not set, using 0")

robot_root = pick_robot_root()
camera_path = find_camera_path()
grasp_frame_path = find_grasp_frame_path()
if not grasp_frame_path:
    print("[WARN] grasp_frame prim not found under robot root.")
else:
    print("[INFO] grasp_frame prim:", grasp_frame_path)
if not camera_path: raise RuntimeError("Camera prim not found under /Root/m1013.")
print("[INFO] Robot root:", robot_root)
print("[INFO] Camera prim:", camera_path)

target_list = [Sdf.Path(robot_root), Sdf.Path(camera_path)]
if grasp_frame_path: target_list.append(Sdf.Path(grasp_frame_path))

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
                ("OnTick.outputs:tick", "PublishJointState.inputs:execIn"),
                ("OnTick.outputs:tick", "SubscribeJointState.inputs:execIn"),
                ("OnTick.outputs:tick", "ArticulationController.inputs:execIn"),
                ("OnTick.outputs:tick", "PublishTransformTree.inputs:execIn"),
                ("OnTick.outputs:tick", "PublishClock.inputs:execIn"),
                ("Context.outputs:context", "PublishJointState.inputs:context"),
                ("Context.outputs:context", "SubscribeJointState.inputs:context"),
                ("Context.outputs:context", "PublishTransformTree.inputs:context"),
                ("Context.outputs:context", "PublishClock.inputs:context"),
                ("SubscribeJointState.outputs:jointNames", "ArticulationController.inputs:jointNames"),
                ("SubscribeJointState.outputs:positionCommand", "ArticulationController.inputs:positionCommand"),
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
                ("PublishClock.inputs:topicName", "/clock"),
            ],
        },
    )
    set_targets(prim=wait_stage().GetPrimAtPath(f"{GRAPH_PATH}/Robot/PublishJointState"),
                attribute="inputs:targetPrim",
                target_prim_paths=[robot_root])
except Exception as e:
    print(f"[Robot Graph] Error: {e}")

try:
    camera_frame = camera_path.split("/")[-1]
    keys = og.Controller.Keys
    (ros_camera_graph, _, _, _) = og.Controller.edit(
        {"graph_path": f"{GRAPH_PATH}/Camera",
         "evaluator_name": "push",
         "pipeline_stage": og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND},
        {
            keys.CREATE_NODES: [
                ("OnStart", "omni.graph.action.OnImpulseEvent"),
                ("OnTick", "omni.graph.action.OnTick"),
                ("CreateViewport", "omni.isaac.core_nodes.IsaacCreateViewport"),
                ("GetRenderProduct", "omni.isaac.core_nodes.IsaacGetViewportRenderProduct"),
                ("SetCamera", "omni.isaac.core_nodes.IsaacSetCameraOnRenderProduct"),
                ("CameraHelperRgb", "omni.isaac.ros2_bridge.ROS2CameraHelper"),
                ("CameraHelperInfo", "omni.isaac.ros2_bridge.ROS2CameraInfoHelper"),
                ("CameraHelperDepth", "omni.isaac.ros2_bridge.ROS2CameraHelper"),
            ],
            keys.CONNECT: [
                ("OnStart.outputs:execOut", "CreateViewport.inputs:execIn"),
                ("CreateViewport.outputs:execOut", "GetRenderProduct.inputs:execIn"),
                ("CreateViewport.outputs:viewport", "GetRenderProduct.inputs:viewport"),
                ("GetRenderProduct.outputs:execOut", "SetCamera.inputs:execIn"),
                ("GetRenderProduct.outputs:renderProductPath", "SetCamera.inputs:renderProductPath"),
                ("OnTick.outputs:tick", "CameraHelperRgb.inputs:execIn"),
                ("OnTick.outputs:tick", "CameraHelperInfo.inputs:execIn"),
                ("OnTick.outputs:tick", "CameraHelperDepth.inputs:execIn"),
                ("GetRenderProduct.outputs:renderProductPath", "CameraHelperRgb.inputs:renderProductPath"),
                ("GetRenderProduct.outputs:renderProductPath", "CameraHelperInfo.inputs:renderProductPath"),
                ("GetRenderProduct.outputs:renderProductPath", "CameraHelperDepth.inputs:renderProductPath"),
            ],
            keys.SET_VALUES: [
                ("CreateViewport.inputs:name", ROS_VIEWPORT_NAME),
                ("CameraHelperRgb.inputs:frameId",  camera_frame),
                ("CameraHelperInfo.inputs:frameId", camera_frame),
                ("CameraHelperDepth.inputs:frameId", camera_frame),
                ("CameraHelperRgb.inputs:topicName", "/rgb"),
                ("CameraHelperRgb.inputs:type", "rgb"),
                ("CameraHelperInfo.inputs:topicName", "/camera_info"),
                ("CameraHelperDepth.inputs:topicName", "/depth"),
                ("CameraHelperDepth.inputs:type", "depth"),
            ],
        },
    )
    set_targets(prim=wait_stage().GetPrimAtPath(f"{GRAPH_PATH}/Camera/SetCamera"),
                attribute="inputs:cameraPrim",
                target_prim_paths=[camera_path])
    og.Controller.set(og.Controller.attribute(f"{GRAPH_PATH}/Camera/OnStart.state:enableImpulse"), True)
    og.Controller.evaluate_sync(ros_camera_graph)
except Exception as e:
    print(f"[Camera Graph] Error: {e}")

def set_realsense_intrinsics(cam_path: str):
    stg = wait_stage()
    prim = stg.GetPrimAtPath(cam_path)
    if not prim or not prim.IsValid(): raise RuntimeError(f"Camera prim not ready: {cam_path}")
    cam = UsdGeom.Camera(prim)
    if not cam or not cam.GetPrim().IsValid(): raise RuntimeError(f"Not a UsdGeom.Camera: {cam_path}")
    cam.GetHorizontalApertureAttr().Set(20.955)
    cam.GetVerticalApertureAttr().Set(15.7)
    cam.GetFocalLengthAttr().Set(18.8)
    cam.GetFocusDistanceAttr().Set(400.0)

set_realsense_intrinsics(camera_path)

simulation_context.initialize_physics()
simulation_context.play()
while simulation_app.is_running():
    simulation_context.step(render=True)
simulation_context.stop()
simulation_app.close()
