# -*- coding: utf-8 -*-
# Franka Transfer Group - Task 2: Lift — 두산 E0509 + RH-P12-RN-A 환경 설정
# ~/smart-shelf-robot/src/custom/rl/envs/lift/doosan_lift_env_cfg.py

import os
import sys
import math

import isaaclab.sim as sim_utils
from isaaclab.assets import AssetBaseCfg, RigidObjectCfg
from isaaclab.sensors import FrameTransformerCfg
from isaaclab.sensors.frame_transformer.frame_transformer_cfg import OffsetCfg
from isaaclab.sim.schemas.schemas_cfg import RigidBodyPropertiesCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import UsdFileCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import SceneEntityCfg

# Import standard lift MDP
import isaaclab_tasks.manager_based.manipulation.lift.mdp as mdp
from isaaclab_tasks.manager_based.manipulation.lift.lift_env_cfg import LiftEnvCfg

# Pre-defined configs
from isaaclab.markers.config import FRAME_MARKER_CFG

# Insert package path to load assets and configs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from cfgs.doosan_shelf_assets_cfg import DOOSAN_E0509_WITH_GRIPPER_CFG
from cfgs.gripper_cfg import (
    GRIPPER_JOINT_NAMES,
    GRIPPER_OPEN_COMMAND,
    GRIPPER_CLOSE_COMMAND,
    GRIPPER_OPEN_WIDTH,
    GRIPPER_GRASP_THRESHOLD,
)

# Custom events for joint resetting (similar to stack events)
from envs.stack.mdp.doosan_stack_events import set_default_joint_pose, randomize_joint_by_gaussian_offset


@configclass
class EventCfg:
    """Configuration for events during episode resets."""

    # Set default joint positions for the Doosan arm and gripper
    init_doosan_arm_pose = EventTerm(
        func=set_default_joint_pose,
        mode="reset",
        params={
            # joint1 to joint6 + gripper_rh_l1/l2/r1/r2
            "default_pose": [0.0, -0.8, 1.57, 0.0, 0.8, 0.0, 1.09, 1.09, 1.09, 1.09],
        },
    )

    # Randomize robot joint states (arm joints only, keeping gripper intact)
    randomize_doosan_joint_state = EventTerm(
        func=randomize_joint_by_gaussian_offset,
        mode="reset",
        params={
            "mean": 0.0,
            "std": 0.02,
            "asset_cfg": SceneEntityCfg("robot"),
        },
    )

    # Randomize position of target object (DexCube) on the table
    reset_object_position = EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "pose_range": {"x": (-0.1, 0.1), "y": (-0.25, 0.25), "z": (0.0, 0.0)},
            "velocity_range": {},
            "asset_cfg": SceneEntityCfg("object", body_names="Object"),
        },
    )


@configclass
class DoosanLiftEnvCfg(LiftEnvCfg):
    """Doosan E0509 + RH-P12-RN-A Lift Environment Config."""

    def __post_init__(self):
        # Post-initialization of parent class
        super().__post_init__()

        # Register events
        self.events = EventCfg()

        # Set Doosan as robot in scene
        self.scene.robot = DOOSAN_E0509_WITH_GRIPPER_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
        self.scene.robot.spawn.semantic_tags = [("class", "robot")]

        # Add robot mount stand
        self.scene.mount = AssetBaseCfg(
            prim_path="{ENV_REGEX_NS}/Mount",
            spawn=sim_utils.UsdFileCfg(
                usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/Mounts/Stand/stand_instanceable.usd",
                scale=(2.0, 2.0, 2.0),
            ),
            init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, 0.0), rot=(1.0, 0.0, 0.0, 0.0)),
        )

        # Override table to match Task 1 (Reach)
        self.scene.table.init_state.pos = (0.55, 0.0, 0.0)
        self.scene.table.init_state.rot = (0.70711, 0.0, 0.0, 0.70711)
        self.scene.table.spawn.scale = (1.0, 1.0, 1.0)

        # Add semantics to mount structures
        self.scene.table.spawn.semantic_tags = [("class", "table")]
        self.scene.plane.semantic_tags = [("class", "ground")]

        # Configure action controllers
        # We use absolute JointPositionActionCfg for arm joints (1-6)
        self.actions.arm_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=["joint_[1-6]"],
            scale=0.5,
            use_default_offset=True,
        )
        self.actions.gripper_action = mdp.BinaryJointPositionActionCfg(
            asset_name="robot",
            joint_names=GRIPPER_JOINT_NAMES,
            open_command_expr=GRIPPER_OPEN_COMMAND,
            close_command_expr=GRIPPER_CLOSE_COMMAND,
        )

        # Gripper configuration variables referenced by observations & rewards
        self.gripper_joint_names = GRIPPER_JOINT_NAMES
        self.gripper_open_val = GRIPPER_OPEN_WIDTH
        self.gripper_threshold = GRIPPER_GRASP_THRESHOLD

        # Configure target Object (DexCube)
        self.scene.object = RigidObjectCfg(
            prim_path="{ENV_REGEX_NS}/Object",
            init_state=RigidObjectCfg.InitialStateCfg(pos=[0.55, 0.0, 0.032], rot=[1, 0, 0, 0]),
            spawn=UsdFileCfg(
                usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/Blocks/DexCube/dex_cube_instanceable.usd",
                scale=(0.8, 0.8, 0.8),
                rigid_props=RigidBodyPropertiesCfg(
                    solver_position_iteration_count=16,
                    solver_velocity_iteration_count=1,
                    max_angular_velocity=1000.0,
                    max_linear_velocity=1000.0,
                    max_depenetration_velocity=5.0,
                    disable_gravity=False,
                ),
                semantic_tags=[("class", "object")],
            ),
        )

        # Configure End-effector Frame and command generator body target
        self.commands.object_pose.body_name = "link_6"
        self.commands.object_pose.ranges.pos_x = (0.45, 0.65)

        marker_cfg = FRAME_MARKER_CFG.copy()
        marker_cfg.markers["frame"].scale = (0.1, 0.1, 0.1)
        marker_cfg.prim_path = "/Visuals/FrameTransformer"
        self.scene.ee_frame = FrameTransformerCfg(
            prim_path="{ENV_REGEX_NS}/Robot/base_link",
            debug_vis=False,
            visualizer_cfg=marker_cfg,
            target_frames=[
                FrameTransformerCfg.FrameCfg(
                    prim_path="{ENV_REGEX_NS}/Robot/link_6",
                    name="end_effector",
                    offset=OffsetCfg(
                        pos=[0.0, 0.0, 0.12],  # Flange to center of gripper fingertips
                    ),
                ),
            ],
        )


@configclass
class DoosanLiftEnvCfg_PLAY(DoosanLiftEnvCfg):
    """Play mode config for visual inspection."""

    def __post_init__(self):
        super().__post_init__()
        # Reduce environment counts for faster rendering in UI
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        # Disable observation noise/corruption
        self.observations.policy.enable_corruption = False
