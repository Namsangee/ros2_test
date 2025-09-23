#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DatasetMaker for Isaac Sim /rgb topic
- Capture on demand (GUI button or service)
- Auto capture N shots while nudging robot a little each shot
- Augment images to add K more
- Build YOLO-style folder structure
"""

import os, sys, time, math, threading, random, shutil, glob
from datetime import datetime
from typing import Optional, Tuple, List

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.duration import Duration
from rclpy.action import ActionClient

from std_srvs.srv import Trigger
from std_msgs.msg import Header
from sensor_msgs.msg import Image
from geometry_msgs.msg import Pose

# MoveIt action & constraints (lightweight subset)
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, PositionConstraint, OrientationConstraint, BoundingVolume
from shape_msgs.msg import SolidPrimitive

from tf2_ros import Buffer, TransformListener, TransformException
from cv_bridge import CvBridge

import numpy as np
import cv2
from PIL import Image as PILImage, ImageEnhance, ImageFilter

# ---------------- Parameters (defaults) ----------------
DEFAULT_RGB_TOPIC = '/rgb'
DEFAULT_GROUP     = 'manipulator_gripper'
DEFAULT_BASE      = 'base_link'
DEFAULT_EEF       = 'grasp_frame'     # position constraint link
DEFAULT_TOOL      = 'grasp_frame'     # orientation constraint link

# nudge limits (per step, meters/radians)
NUDGE_XY_MAX = 0.03       # ±3 cm
NUDGE_Z_MAX  = 0.02       # ±2 cm
NUDGE_YAW_MAX= math.radians(8.0)  # ±8 deg

# planning tunables
PLAN_TIME   = 10.0
ATTEMPTS    = 50
VEL_SCALE   = 0.2
ACC_SCALE   = 0.2
BOX_XYZ     = (0.03, 0.03, 0.03)   # small position box
XY_TOL      = 0.1                  # ensure X/Y relaxed to at least this

# ------------------------------------------------------

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p

def split_train_val(files: List[str], ratio: float = 0.8):
    n = len(files)
    k = int(n * ratio)
    return files[:k], files[k:]

def _normalize_quat(x: float, y: float, z: float, w: float) -> Tuple[float,float,float,float]:
    n = math.sqrt(x*x + y*y + z*z + w*w)
    if n <= 0.0 or not math.isfinite(n):
        return 0.0, 0.0, 0.0, 1.0
    return x/n, y/n, z/n, w/n

class RobotNudger:
    """Minimal MoveGroup client that nudges EEF pose slightly around current TF pose."""
    def __init__(self, node: Node):
        self.node = node
        self.cb_group = ReentrantCallbackGroup()
        self.move_client = ActionClient(node, MoveGroup, '/move_action', callback_group=self.cb_group)
        self.tf = Buffer(cache_time=Duration(seconds=5.0))
        self.tf_listener = TransformListener(self.tf, node)

    def _eef_pose_in_base(self, base_frame: str, eef_frame: str) -> Optional[Pose]:
        try:
            tf = self.tf.lookup_transform(base_frame, eef_frame, rclpy.time.Time(), timeout=Duration(seconds=0.5))
            # Convert to Pose
            p = Pose()
            p.position.x = tf.transform.translation.x
            p.position.y = tf.transform.translation.y
            p.position.z = tf.transform.translation.z
            p.orientation = tf.transform.rotation
            return p
        except TransformException as e:
            self.node.get_logger().warn(f'[Nudge] TF {eef_frame}->{base_frame} failed: {e}')
            return None

    @staticmethod
    def _quat_from_yaw(yaw: float) -> Tuple[float,float,float,float]:
        # roll=pitch=0
        cy = math.cos(yaw*0.5); sy = math.sin(yaw*0.5)
        return (0.0, 0.0, sy, cy)

    @staticmethod
    def _pose_add_delta(p: Pose, dx: float, dy: float, dz: float, dyaw: float) -> Pose:
        qx,qy,qz,qw = _normalize_quat(p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w)
        # compose yaw only (approx): world-frame yaw delta (simple & sufficient for small nudge)
        dqx,dqy,dqz,dqw = RobotNudger._quat_from_yaw(dyaw)
        # quaternion multiply: q * dq
        rx = qw*dqx + qx*dqw + qy*dqz - qz*dqy
        ry = qw*dqy - qx*dqz + qy*dqw + qz*dqx
        rz = qw*dqz + qx*dqy - qy*dqx + qz*dqw
        rw = qw*dqw - qx*dqx - qy*dqy - qz*dqz

        out = Pose()
        out.position.x = p.position.x + dx
        out.position.y = p.position.y + dy
        out.position.z = p.position.z + dz
        out.orientation.x, out.orientation.y, out.orientation.z, out.orientation.w = _normalize_quat(rx,ry,rz,rw)
        return out

    def _build_constraints(self, node: Node, target: Pose) -> Constraints:
        box_xyz = list(BOX_XYZ)
        box_xyz[0] = max(box_xyz[0], 2.0*XY_TOL)
        box_xyz[1] = max(box_xyz[1], 2.0*XY_TOL)

        pos_c = PositionConstraint()
        pos_c.header.frame_id = node.get_parameter('base_frame').value
        pos_c.link_name = node.get_parameter('eef_link').value
        pos_c.weight = 1.0
        prim = SolidPrimitive()
        prim.type = SolidPrimitive.BOX
        prim.dimensions = box_xyz
        bv = BoundingVolume()
        bv.primitives.append(prim)
        bv.primitive_poses.append(target)
        pos_c.constraint_region = bv

        ori_c = OrientationConstraint()
        ori_c.header.frame_id = node.get_parameter('base_frame').value
        ori_c.link_name = node.get_parameter('tool_frame').value
        ori_c.orientation = target.orientation
        # roll/pitch 작은 허용, yaw는 비교적 자유
        ori_c.absolute_x_axis_tolerance = math.radians(10)
        ori_c.absolute_y_axis_tolerance = math.radians(10)
        ori_c.absolute_z_axis_tolerance = math.pi
        ori_c.weight = 1.0

        cs = Constraints()
        cs.position_constraints.append(pos_c)
        cs.orientation_constraints.append(ori_c)
        return cs

    def nudge_once(self, base_frame: str, eef_frame: str, group_name: str) -> bool:
        cur = self._eef_pose_in_base(base_frame, eef_frame)
        if cur is None:
            return False
        dx = random.uniform(-NUDGE_XY_MAX, NUDGE_XY_MAX)
        dy = random.uniform(-NUDGE_XY_MAX, NUDGE_XY_MAX)
        dz = random.uniform(-NUDGE_Z_MAX,  NUDGE_Z_MAX)
        dyaw = random.uniform(-NUDGE_YAW_MAX, NUDGE_YAW_MAX)
        target = self._pose_add_delta(cur, dx, dy, dz, dyaw)

        goal = MoveGroup.Goal()
        goal.request.group_name = group_name
        goal.request.num_planning_attempts = ATTEMPTS
        goal.request.allowed_planning_time = PLAN_TIME
        goal.request.max_velocity_scaling_factor = VEL_SCALE
        goal.request.max_acceleration_scaling_factor = ACC_SCALE
        goal.request.goal_constraints = [self._build_constraints(self.node, target)]
        goal.planning_options.plan_only = False
        goal.planning_options.replan = False

        if not self.move_client.wait_for_server(timeout_sec=5.0):
            self.node.get_logger().error('[Nudge] MoveGroup action server not available')
            return False

        done = threading.Event()
        ok = {'v': False}

        def _on_goal(fut):
            try:
                gh = fut.result()
                if not gh or not gh.accepted:
                    self.node.get_logger().error('[Nudge] goal rejected')
                    done.set(); return
                def _on_res(rfut):
                    try:
                        res = rfut.result().result
                        ok['v'] = (res.error_code.val == 1)  # SUCCESS
                    except Exception as e:
                        self.node.get_logger().error(f'[Nudge] get_result failed: {e}')
                        ok['v'] = False
                    finally:
                        done.set()
                gh.get_result_async().add_done_callback(_on_res)
            except Exception as e:
                self.node.get_logger().error(f'[Nudge] send_goal failed: {e}')
                done.set()

        self.move_client.send_goal_async(goal).add_done_callback(_on_goal)
        done.wait(timeout=30.0)
        return ok['v']


class DatasetMaker(Node):
    def __init__(self):
        super().__init__('dataset_maker')
        self.cb_group = ReentrantCallbackGroup()
        self.bridge = CvBridge()

        # ---------- parameters ----------
        self.declare_parameter('rgb_topic', DEFAULT_RGB_TOPIC)
        self.declare_parameter('save_root', os.path.expanduser(
            f'~/dataset_{datetime.now().strftime("%Y%m%d_%H%M%S")}'))
        self.declare_parameter('use_gui', True)
        self.declare_parameter('auto_shots', 50)
        self.declare_parameter('aug_extra', 100)   # 추가 생성 개수
        self.declare_parameter('group_name', DEFAULT_GROUP)
        self.declare_parameter('base_frame', DEFAULT_BASE)
        self.declare_parameter('eef_link', DEFAULT_EEF)
        self.declare_parameter('tool_frame', DEFAULT_TOOL)

        topic = self.get_parameter('rgb_topic').value
        self.create_subscription(Image, topic, self._img_cb, 10, callback_group=self.cb_group)
        self.get_logger().info(f'[Sub] {topic}')

        # storage
        root = self.get_parameter('save_root').value
        self.root = ensure_dir(root)
        self.dir_raw = ensure_dir(os.path.join(root, 'images', 'raw'))
        self.dir_aug = ensure_dir(os.path.join(root, 'images', 'aug'))
        self.dir_train = ensure_dir(os.path.join(root, 'images', 'train'))
        self.dir_val = ensure_dir(os.path.join(root, 'images', 'val'))
        self.dir_lbl_tr = ensure_dir(os.path.join(root, 'labels', 'train'))
        self.dir_lbl_vl = ensure_dir(os.path.join(root, 'labels', 'val'))
        self.get_logger().info(f'[Dirs] root={self.root}')

        # services
        self.srv_capture = self.create_service(Trigger, '/dataset/capture_once', self._srv_capture_once, callback_group=self.cb_group)
        self.srv_auto = self.create_service(Trigger, '/dataset/auto_capture', self._srv_auto_capture, callback_group=self.cb_group)
        self.srv_aug = self.create_service(Trigger, '/dataset/augment', self._srv_augment, callback_group=self.cb_group)
        self.srv_pack = self.create_service(Trigger, '/dataset/pack', self._srv_pack, callback_group=self.cb_group)

        # robot nudger
        self.nudger = RobotNudger(self)

        # latest image
        self._img_lock = threading.Lock()
        self._last_img: Optional[np.ndarray] = None

        # GUI
        if bool(self.get_parameter('use_gui').value):
            threading.Thread(target=self._run_gui, daemon=True).start()

    # ------------- image callback -------------
    def _img_cb(self, msg: Image):
        try:
            cv = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            with self._img_lock:
                self._last_img = cv
        except Exception as e:
            self.get_logger().warn(f'cv_bridge failed: {e}')

    # ------------- capture helpers ------------
    def _save_one(self) -> Optional[str]:
        with self._img_lock:
            if self._last_img is None:
                return None
            img = self._last_img.copy()
        fname = datetime.now().strftime('rgb_%Y%m%d_%H%M%S_%f')[:-3] + '.png'
        path = os.path.join(self.dir_raw, fname)
        cv2.imwrite(path, img)
        return path

    def _capture_once(self) -> Tuple[bool,str]:
        path = self._save_one()
        if path is None:
            return False, 'No image received yet.'
        return True, f'Saved: {path}'

    def _auto_capture(self) -> Tuple[bool,str]:
        n = int(self.get_parameter('auto_shots').value)
        base = self.get_parameter('base_frame').value
        eef  = self.get_parameter('eef_link').value
        group= self.get_parameter('group_name').value

        saved = 0
        for i in range(n):
            # 1) nudge the robot a little
            ok_move = self.nudger.nudge_once(base, eef, group)
            if not ok_move:
                self.get_logger().warn(f'[Auto] nudge {i+1}/{n} failed; continuing anyway')
            # small settle
            time.sleep(0.4)

            # 2) capture
            p = self._save_one()
            if p:
                saved += 1
                self.get_logger().info(f'[Auto] {i+1}/{n} -> {p}')
            else:
                self.get_logger().warn(f'[Auto] {i+1}/{n} -> no image')
        return True, f'Auto-captured {saved}/{n} images into {self.dir_raw}'

    # ------------- augmentation ---------------
    @staticmethod
    def _augment_pil(im: PILImage.Image) -> PILImage.Image:
        # Random pipeline (simple, deterministic enough)
        if random.random() < 0.5:
            im = im.transpose(PILImage.FLIP_LEFT_RIGHT)
        # small rotation
        angle = random.uniform(-12, 12)
        im = im.rotate(angle, resample=PILImage.BILINEAR, expand=False, fillcolor=None)
        # brightness/contrast
        im = ImageEnhance.Brightness(im).enhance(random.uniform(0.8, 1.2))
        im = ImageEnhance.Contrast(im).enhance(random.uniform(0.8, 1.2))
        # slight blur or noise
        if random.random() < 0.5:
            im = im.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.0, 1.2)))
        else:
            arr = np.array(im).astype(np.float32)
            noise = np.random.normal(0, random.uniform(2.0, 8.0), size=arr.shape)
            arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
            im = PILImage.fromarray(arr)
        return im

    def _augment(self) -> Tuple[bool,str]:
        target_extra = int(self.get_parameter('aug_extra').value)
        raws = sorted(glob.glob(os.path.join(self.dir_raw, '*.png')))
        if not raws:
            return False, 'No raw images to augment.'
        count = 0
        idx_cycle = 0
        while count < target_extra:
            src = raws[idx_cycle % len(raws)]
            idx_cycle += 1
            try:
                im = PILImage.open(src).convert('RGB')
                aug = self._augment_pil(im)
                base = os.path.splitext(os.path.basename(src))[0]
                out = os.path.join(self.dir_aug, f'{base}_aug{count:04d}.png')
                aug.save(out)
                count += 1
            except Exception as e:
                self.get_logger().warn(f'Aug fail on {src}: {e}')
        return True, f'Generated {count} augmented images -> {self.dir_aug}'

    # ------------- packing dataset -----------
    def _pack_dataset(self) -> Tuple[bool,str]:
        # clear train/val
        for d in (self.dir_train, self.dir_val, self.dir_lbl_tr, self.dir_lbl_vl):
            shutil.rmtree(d, ignore_errors=True)
            ensure_dir(d)

        imgs = sorted(glob.glob(os.path.join(self.dir_raw, '*.png'))) + \
               sorted(glob.glob(os.path.join(self.dir_aug, '*.png')))
        if not imgs:
            return False, 'No images found in raw/aug.'
        random.shuffle(imgs)
        tr, vl = split_train_val(imgs, 0.8)

        def copy_files(files, dst_img, dst_lbl):
            for p in files:
                shutil.copy2(p, os.path.join(dst_img, os.path.basename(p)))
            # labels는 빈 파일(또는 미생성) — 라벨링툴로 생성 예정
            # 필요시 여기서 .txt 빈 파일을 함께 생성할 수도 있음

        copy_files(tr, self.dir_train, self.dir_lbl_tr)
        copy_files(vl, self.dir_val, self.dir_lbl_vl)

        readme = os.path.join(self.root, 'README.txt')
        with open(readme, 'w') as f:
            f.write(
                "YOLO-style dataset skeleton generated.\n"
                "images/{train,val}  : all images (raw + aug)\n"
                "labels/{train,val}  : (empty) prepare your labels here (*.txt)\n"
            )
        return True, f'Packed dataset: train={len(tr)} val={len(vl)} (root={self.root})'

    # ------------- services ------------------
    def _srv_capture_once(self, req, res):
        ok, msg = self._capture_once()
        res.success, res.message = ok, msg
        return res

    def _srv_auto_capture(self, req, res):
        def _work():
            ok, msg = self._auto_capture()
            self.get_logger().info(msg)
        threading.Thread(target=_work, daemon=True).start()
        res.success, res.message = True, 'Started auto capture in background.'
        return res

    def _srv_augment(self, req, res):
        ok, msg = self._augment()
        res.success, res.message = ok, msg
        return res

    def _srv_pack(self, req, res):
        ok, msg = self._pack_dataset()
        res.success, res.message = ok, msg
        return res

    # ------------- GUI (Tkinter) ------------
    def _run_gui(self):
        try:
            import tkinter as tk
            from tkinter import messagebox
        except Exception as e:
            self.get_logger().warn(f'GUI unavailable: {e}')
            return
        root = tk.Tk()
        root.title("Dataset Maker")
        root.geometry("360x240")

        lbl = tk.Label(root, text=f"Root: {self.root}", wraplength=320, justify='left')
        lbl.pack(pady=6)

        def on_cap():
            ok, msg = self._capture_once()
            messagebox.showinfo("Capture", msg)

        def on_auto():
            threading.Thread(target=lambda: messagebox.showinfo("Auto", self._auto_capture()[1]), daemon=True).start()

        def on_aug():
            ok, msg = self._augment()
            messagebox.showinfo("Augment", msg)

        def on_pack():
            ok, msg = self._pack_dataset()
            messagebox.showinfo("Pack", msg)

        tk.Button(root, text="Capture Once", command=on_cap).pack(fill='x', padx=12, pady=4)
        tk.Button(root, text="Auto 50 Shots", command=on_auto).pack(fill='x', padx=12, pady=4)
        tk.Button(root, text="Augment +100", command=on_aug).pack(fill='x', padx=12, pady=4)
        tk.Button(root, text="Pack Dataset", command=on_pack).pack(fill='x', padx=12, pady=8)

        root.mainloop()


# ---------------- main ---------------------
def main(args=None):
    rclpy.init(args=args)
    node = DatasetMaker()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
