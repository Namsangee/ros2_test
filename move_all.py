#!/usr/bin/env python3

# Example: trigger one pick/place step
#   ros2 service call /pick_place/next std_srvs/srv/Trigger {}

import time
import threading
from typing import List, Optional, Dict

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from std_srvs.srv import Trigger

from geometry_msgs.msg import PoseStamped, Pose
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    Constraints, PositionConstraint, OrientationConstraint, BoundingVolume,
    JointConstraint, MoveItErrorCodes
)
from shape_msgs.msg import SolidPrimitive
from control_msgs.action import GripperCommand


def movegroup_success(result: MoveGroup.Result) -> bool:
    return result.error_code.val == MoveItErrorCodes.SUCCESS


class PickPlaceCoordinator(Node):
    def __init__(self):
        super().__init__('pick_place_coordinator')

        self.cb_group = ReentrantCallbackGroup()
        self._work_lock = threading.Lock()

        # MoveIt / planner
        self.declare_parameter('group_name', 'manipulator')
        self.declare_parameter('planner_id', 'curobo')
        self.declare_parameter('allowed_planning_time', 10.0)
        self.declare_parameter('num_planning_attempts', 20)
        self.declare_parameter('max_vel_scale', 0.1)
        self.declare_parameter('max_acc_scale', 0.1)

        # Frames / links
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('eef_link', 'grasp_frame')
        self.declare_parameter('tool_frame', 'grasp_frame')

        # Offsets
        self.declare_parameter('grasp_dz', -0.03)

        # Home (joints)
        self.declare_parameter('joint_names', ['joint_1','joint_2','joint_3','joint_4','joint_5','joint_6'])
        self.declare_parameter('home_joint_positions', [0.0, 0.0, 1.57, 0.0, 1.57, 0.0])

        # Color sequence & place poses
        self.declare_parameter('color_sequence', ['red','blue'])
        self.declare_parameter('place_red',  [0.60,  0.20, 0.03, 0.0, 1.0, 0.0, 0.0])
        self.declare_parameter('place_blue', [0.70, -0.20, 0.03, 0.0, 1.0, 0.0, 0.0])

        # Gripper (GripperCommand action)
        self.declare_parameter('gripper_action_name', '/gripper_position_controller/gripper_cmd')
        self.declare_parameter('gripper_open_position', 0.00)
        self.declare_parameter('gripper_close_position', 0.6)
        self.declare_parameter('gripper_max_effort', 50.0)
        self.declare_parameter('gripper_timeout_sec', 5.0)
        self.declare_parameter('gripper_settle_sec', 0.3)

        # Vision topics base
        self.declare_parameter('use_color_split_topics', True)
        self.declare_parameter('vision_pose_topic_base', '/object_pose_world')  # ex) /object_pose_world/<color>
        self.declare_parameter('vision_pose_topic_single', '/object_pose_world')
        self.declare_parameter('vision_wait_timeout', 10.0)

        # Orientation fixation
        self.declare_parameter('fix_orientation', True)
        self.declare_parameter('fixed_quat', [0.0, 1.0, 0.0, 0.0])  # [x,y,z,w]

        # Control vision node parameter for target color
        self.declare_parameter('vision_parameter_node', 'object_pose_estimator_node')
        self.declare_parameter('vision_parameter_name', 'target_object_class')

        # State
        self._color_seq: List[str] = [str(c).lower() for c in self.get_parameter('color_sequence').value]
        self._color_idx: int = 0

        # Clients configuration
        self._move_client = ActionClient(self, MoveGroup, '/move_action', callback_group=self.cb_group)
        self._gripper_client = ActionClient(self, GripperCommand,
                                            self.get_parameter('gripper_action_name').value,
                                            callback_group=self.cb_group)

        # Per-color/single pose storage & events
        self._latest_pose_by_color: Dict[str, Optional[PoseStamped]] = {c: None for c in self._color_seq}
        self._pose_event_by_color: Dict[str, threading.Event] = {c: threading.Event() for c in self._color_seq}
        self._latest_pose_single: Optional[PoseStamped] = None
        self._pose_event_single = threading.Event()

        # Subscriptions
        if bool(self.get_parameter('use_color_split_topics').value):
            base = self.get_parameter('vision_pose_topic_base').value.rstrip('/')
            for color in sorted(set(self._color_seq)):
                topic = f'{base}/{color}'
                self.create_subscription(
                    PoseStamped, topic,
                    lambda msg, col=color: self._pose_cb_color(col, msg),
                    10, callback_group=self.cb_group
                )
                self.get_logger().info(f'[VisionSub] subscribe: {topic}')
        else:
            single = self.get_parameter('vision_pose_topic_single').value
            self.create_subscription(
                PoseStamped, single,
                self._pose_cb_single, 10, callback_group=self.cb_group
            )
            self.get_logger().info(f'[VisionSub] subscribe (single): {single}')

        # Service
        self._srv_next = self.create_service(Trigger, '/pick_place/next', self._on_next, callback_group=self.cb_group)
        self.get_logger().info('[PickPlaceCoordinator] Ready. Call service /pick_place/next to run one step.')

    # Vision callbacks
    def _pose_cb_color(self, color: str, msg: PoseStamped):
        self._latest_pose_by_color[color] = msg
        self._pose_event_by_color[color].set()

    def _pose_cb_single(self, msg: PoseStamped):
        self._latest_pose_single = msg
        self._pose_event_single.set()

    # Cycle trigger
    def _on_next(self, request, response):
        if not self._work_lock.acquire(blocking=False):
            response.success = False
            response.message = 'Busy: previous step still running.'
            return response

        if self._color_idx >= len(self._color_seq):
            self._work_lock.release()
            response.success = False
            response.message = 'Color sequence finished.'
            return response

        color = self._color_seq[self._color_idx]
        self.get_logger().info(f'=== STEP TRIGGERED: target color = {color} ===')
        threading.Thread(target=self._run_one_async, args=(color,), daemon=True).start()
        response.success = True
        response.message = f'Started: {color}'
        return response

    def _run_one_async(self, color: str):
        try:
            ok = self._run_one(color)
            if ok:
                self._color_idx += 1
        finally:
            self._work_lock.release()

    # Utils
    def _wait_for_pose(self, color: str, timeout: float) -> Optional[PoseStamped]:
        if bool(self.get_parameter('use_color_split_topics').value):
            evt = self._pose_event_by_color[color]
            self._latest_pose_by_color[color] = None
            evt.clear()
            if evt.wait(timeout):
                return self._latest_pose_by_color[color]
            return None
        else:
            self._latest_pose_single = None
            self._pose_event_single.clear()
            if self._pose_event_single.wait(timeout):
                return self._latest_pose_single
            return None

    def _offset_z(self, pose: Pose, dz: float) -> Pose:
        p = Pose()
        p.position.x = pose.position.x
        p.position.y = pose.position.y
        p.position.z = pose.position.z + dz
        if bool(self.get_parameter('fix_orientation').value):
            q = list(self.get_parameter('fixed_quat').value)
            p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w = q
        else:
            p.orientation = pose.orientation
        return p

    def _color_to_place_pose(self, color: str) -> Pose:
        name = f'place_{color}'
        prm = self.get_parameter(name)
        if not prm or prm.value is None or len(list(prm.value)) != 7:
            self.get_logger().warn(f'No/invalid parameter "{name}"; fallback to origin.')
            arr = [0.5, 0.0, 0.25, 0.0, 0.0, 0.0, 1.0]
        else:
            arr = list(prm.value)
        p = Pose()
        p.position.x, p.position.y, p.position.z = arr[0], arr[1], arr[2]
        p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w = arr[3], arr[4], arr[5], arr[6]
        return p

    # Main pipeline
    def _run_one(self, color: str) -> bool:
        INTER_DELAY = 0.5

        self._try_set_vision_color(color)

        if not self._gripper_action('open'):
            self._reset_home(); return False
        time.sleep(INTER_DELAY)

        # 1) Wait for a pose for the given color
        pick_ps = self._wait_for_pose(color, timeout=float(self.get_parameter('vision_wait_timeout').value))
        if pick_ps is None:
            self.get_logger().error(f'[Vision] No pose for color "{color}" received in time.')
            self._reset_home()
            return False

        # Direct grasp pose (with z offset if needed)
        grasp_dz = float(self.get_parameter('grasp_dz').value)
        grasp_pose = self._offset_z(pick_ps.pose, grasp_dz)

        # 2) Move to grasp pose -> close gripper
        if not self._move_to_pose(grasp_pose, f'go to grasp (color={color})'):
            self._reset_home(); return False
        time.sleep(INTER_DELAY)

        if not self._gripper_action('close'):
            self._reset_home(); return False
        time.sleep(INTER_DELAY)

        # 3) Move to place pose -> open gripper
        place_pose = self._color_to_place_pose(color)
        if not self._move_to_pose(place_pose, f'go to place (color={color})'):
            self._reset_home(); return False
        time.sleep(INTER_DELAY)

        if not self._gripper_action('open'):
            self._reset_home(); return False
        time.sleep(INTER_DELAY)

        # 4) Return home
        if not self._go_home():
            self._reset_home(); return False

        self.get_logger().info(f'[DONE] {color}')
        return True


        # Alternative approach pipeline (commented):
        # # 1) Wait for vision pose
        # pick_ps = self._wait_for_pose(timeout=float(self.get_parameter('vision_wait_timeout').value))
        # if pick_ps is None:
        #     self.get_logger().error('[Vision] No pose received in time.')
        #     self._reset_home()
        #     return False
        #
        # approach_dz = float(self.get_parameter('approach_dz').value)
        # grasp_dz    = float(self.get_parameter('grasp_dz').value)
        # approach_pose = self._offset_z(pick_ps.pose, approach_dz)
        # grasp_pose    = self._offset_z(pick_ps.pose, grasp_dz)
        #
        # # 2) Approach -> grasp -> lift
        # if not self._move_to_pose(approach_pose, 'approach to pick'):
        #     self._reset_home(); return False
        # if not self._move_to_pose(grasp_pose, 'descend to grasp'):
        #     self._reset_home(); return False
        #
        # if not self._gripper_action('close'):
        #     self._reset_home(); return False
        #
        # if not self._move_to_pose(approach_pose, 'lift after grasp'):
        #     self._reset_home(); return False
        #
        # # 3) Approach to place -> place -> open
        # place_pose = self._color_to_place_pose(color)
        # place_approach = self._offset_z(place_pose, approach_dz)
        #
        # if not self._move_to_pose(place_approach, 'approach to place'):
        #     self._reset_home(); return False
        # if not self._move_to_pose(place_pose, 'place'):
        #     self._reset_home(); return False
        #
        # if not self._gripper_action('open'):
        #     self._reset_home(); return False
        #
        # # 4) Return home
        # if not self._go_home():
        #     self._reset_home(); return False
        #
        # self.get_logger().info(f'[DONE] {color}')
        # return True


    # MoveGroup utils
    def _build_goal_constraints(self, target_pose: Pose,
                                box_xyz=(0.02, 0.02, 0.02),
                                xy_tol=0.1) -> Constraints:
        pos_c = PositionConstraint()
        pos_c.header.frame_id = self.get_parameter('base_frame').value
        pos_c.link_name = self.get_parameter('eef_link').value
        pos_c.weight = 1.0

        bv = BoundingVolume()
        prim = SolidPrimitive()
        prim.type = SolidPrimitive.BOX
        prim.dimensions = [box_xyz[0], box_xyz[1], box_xyz[2]]
        bv.primitives.append(prim)
        bv.primitive_poses.append(target_pose)
        pos_c.constraint_region = bv

        ori_c = OrientationConstraint()
        ori_c.header.frame_id = self.get_parameter('base_frame').value
        ori_c.link_name = self.get_parameter('tool_frame').value
        ori_c.orientation = target_pose.orientation
        ori_c.absolute_x_axis_tolerance = 0.1
        ori_c.absolute_y_axis_tolerance = 0.1
        ori_c.absolute_z_axis_tolerance = 0.1
        ori_c.weight = 1.0

        cs = Constraints()
        cs.position_constraints.append(pos_c)
        cs.orientation_constraints.append(ori_c)
        return cs

    def _try_move_once(self, target_pose: Pose, comment: str,
                       box_xyz=(0.02,0.02,0.02), xy_tol=0.1,
                       plan_time=None, attempts=None) -> bool:
        goal = MoveGroup.Goal()
        goal.request.group_name = self.get_parameter('group_name').value
        goal.request.num_planning_attempts = int(attempts if attempts is not None else self.get_parameter('num_planning_attempts').value)
        goal.request.allowed_planning_time = float(plan_time if plan_time is not None else self.get_parameter('allowed_planning_time').value)
        goal.request.max_velocity_scaling_factor = float(self.get_parameter('max_vel_scale').value)
        goal.request.max_acceleration_scaling_factor = float(self.get_parameter('max_acc_scale').value)
        goal.request.planner_id = self.get_parameter('planner_id').value

        goal.request.goal_constraints = [ self._build_goal_constraints(target_pose, box_xyz, xy_tol) ]
        goal.planning_options.plan_only = False
        goal.planning_options.replan = False

        if comment:
            self.get_logger().info(f'[Move] {comment}')

        self._move_client.wait_for_server()

        done = threading.Event()
        ok = {'v': False}

        def _on_goal(fut):
            try:
                gh = fut.result()
            except Exception as e:
                self.get_logger().error(f'send_goal_async failed: {e}')
                done.set(); return

            if not gh or not gh.accepted:
                self.get_logger().error('MoveGroup goal rejected.')
                done.set(); return

            def _on_res(rfut):
                try:
                    result = rfut.result().result
                    if movegroup_success(result):
                        self.get_logger().info(' -> Move succeeded.')
                        ok['v'] = True
                    else:
                        self.get_logger().error(f' -> Move failed with error_code={result.error_code.val}')
                        ok['v'] = False
                except Exception as e:
                    self.get_logger().error(f'get_result_async failed: {e}')
                    ok['v'] = False
                finally:
                    done.set()

            gh.get_result_async().add_done_callback(_on_res)

        self._move_client.send_goal_async(goal).add_done_callback(_on_goal)
        done.wait()
        return ok['v']

    def _move_to_pose(self, target_pose: Pose, comment: str = '') -> bool:
        if self._try_move_once(target_pose, comment,
                               box_xyz=(0.02,0.02,0.02), xy_tol=0.1):
            return True
        if self._try_move_once(target_pose, comment + ' (retry1 relaxed)',
                               box_xyz=(0.05,0.05,0.05), xy_tol=0.3,
                               plan_time=float(self.get_parameter('allowed_planning_time').value)+5.0,
                               attempts=int(self.get_parameter('num_planning_attempts').value)+10):
            return True
        tp = Pose()
        tp.position.x, tp.position.y, tp.position.z = target_pose.position.x, target_pose.position.y, target_pose.position.z + 0.015
        tp.orientation = target_pose.orientation
        if self._try_move_once(tp, comment + ' (retry2 z+3cm)',
                               box_xyz=(0.05,0.05,0.05), xy_tol=0.3,
                               plan_time=float(self.get_parameter('allowed_planning_time').value)+5.0,
                               attempts=int(self.get_parameter('num_planning_attempts').value)+10):
            return True
        return False

    def _go_home(self) -> bool:
        self.get_logger().info('[Home] go home')
        joint_names: List[str] = list(self.get_parameter('joint_names').value)
        home_pos: List[float] = list(self.get_parameter('home_joint_positions').value)
        if len(joint_names) != len(home_pos):
            self.get_logger().error('joint_names and home_joint_positions length mismatch.')
            return False

        goal = MoveGroup.Goal()
        goal.request.group_name = self.get_parameter('group_name').value
        goal.request.num_planning_attempts = int(self.get_parameter('num_planning_attempts').value)
        goal.request.allowed_planning_time = float(self.get_parameter('allowed_planning_time').value)
        goal.request.max_velocity_scaling_factor = float(self.get_parameter('max_vel_scale').value)
        goal.request.max_acceleration_scaling_factor = float(self.get_parameter('max_acc_scale').value)
        goal.request.planner_id = self.get_parameter('planner_id').value

        cs = Constraints()
        for name, pos in zip(joint_names, home_pos):
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = float(pos)
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            cs.joint_constraints.append(jc)

        goal.request.goal_constraints = [cs]
        goal.planning_options.plan_only = False
        goal.planning_options.replan = False

        self._move_client.wait_for_server()

        done = threading.Event()
        ok = {'v': False}

        def _on_goal(fut):
            try:
                gh = fut.result()
            except Exception as e:
                self.get_logger().error(f'send_goal_async(home) failed: {e}')
                done.set(); return

            if not gh or not gh.accepted:
                self.get_logger().error('Home goal rejected.')
                done.set(); return

            def _on_res(rfut):
                try:
                    result = rfut.result().result
                    if movegroup_success(result):
                        self.get_logger().info(' -> Home reached.')
                        ok['v'] = True
                    else:
                        self.get_logger().error(f' -> Home move failed with error_code={result.error_code.val}')
                        ok['v'] = False
                except Exception as e:
                    self.get_logger().error(f'get_result_async(home) failed: {e}')
                    ok['v'] = False
                finally:
                    done.set()

            gh.get_result_async().add_done_callback(_on_res)

        self._move_client.send_goal_async(goal).add_done_callback(_on_goal)
        done.wait()
        return ok['v']

    # Reset on failure
    def _reset_home(self):
        self.get_logger().warn('[Reset] moving home due to failure...')
        self._go_home()

    # Gripper action
    def _gripper_action(self, cmd: str) -> bool:
        goal = GripperCommand.Goal()
        if cmd == 'close':
            goal.command.position = float(self.get_parameter('gripper_close_position').value)
        else:
            goal.command.position = float(self.get_parameter('gripper_open_position').value)
        goal.command.max_effort = float(self.get_parameter('gripper_max_effort').value)

        timeout = float(self.get_parameter('gripper_timeout_sec').value)

        self.get_logger().info(f'[Gripper] {cmd} -> pos={goal.command.position:.3f}, effort={goal.command.max_effort:.1f}')
        self._gripper_client.wait_for_server()

        done = threading.Event()
        ok = {'v': False}

        def _on_goal(fut):
            try:
                gh = fut.result()
            except Exception as e:
                self.get_logger().error(f'Gripper send_goal failed: {e}')
                done.set(); return

            if not gh or not gh.accepted:
                self.get_logger().error('Gripper goal rejected.')
                done.set(); return

            def _on_res(rfut):
                try:
                    _ = rfut.result().result
                    ok['v'] = True
                except Exception as e:
                    self.get_logger().error(f'Gripper result failed: {e}')
                    ok['v'] = False
                finally:
                    done.set()

            gh.get_result_async().add_done_callback(_on_res)

        self._gripper_client.send_goal_async(goal).add_done_callback(_on_goal)
        done.wait(timeout=timeout)
        time.sleep(float(self.get_parameter('gripper_settle_sec').value))
        return ok['v']

    # Set vision target color parameter
    def _try_set_vision_color(self, color: str):
        node_name = self.get_parameter('vision_parameter_node').value
        param_name = self.get_parameter('vision_parameter_name').value
        try:
            from rcl_interfaces.srv import SetParameters
            from rcl_interfaces.msg import Parameter, ParameterValue
            from rclpy.parameter import Parameter as RclpyParameter

            client = self.create_client(SetParameters, f'/{node_name}/set_parameters', callback_group=self.cb_group)
            if not client.wait_for_service(timeout_sec=0.5):
                self.get_logger().warn('[Vision] parameter service not available; skipping color set.')
                return

            req = SetParameters.Request()
            p = Parameter()
            p.name = param_name
            pv = ParameterValue()
            pv.type = RclpyParameter.Type.STRING.value
            pv.string_value = color
            p.value = pv
            req.parameters = [p]

            done = threading.Event()
            ok_holder = {'ok': False}

            def _on_resp(fut):
                try:
                    resp = fut.result()
                    ok_holder['ok'] = (resp is not None and all(r.successful for r in resp.results))
                except Exception:
                    ok_holder['ok'] = False
                finally:
                    done.set()

            client.call_async(req).add_done_callback(_on_resp)
            done.wait(timeout=1.5)

            if ok_holder['ok']:
                self.get_logger().info(f'[Vision] target color set -> {color}')
            else:
                self.get_logger().warn('[Vision] set_parameters failed or not declared; skipping.')
        except Exception:
            self.get_logger().warn('[Vision] set_parameters not supported in this environment; skipping.')


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceCoordinator()
    exec_ = MultiThreadedExecutor()
    exec_.add_node(node)
    try:
        exec_.spin()
    except KeyboardInterrupt:
        pass
    finally:
        exec_.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
