# -*- coding: utf-8 -*-
# Task 3: Stacking — 두산 E0509 + RH-P12-RN-A 특화 환경 설정
# ~/smart-shelf-robot/src/custom/rl/envs/stack/doosan_stack_env_cfg.py

import os
import sys

from isaaclab.assets import RigidObjectCfg
from isaaclab.sensors import FrameTransformerCfg
from isaaclab.sensors.frame_transformer.frame_transformer_cfg import OffsetCfg
from isaaclab.sim.schemas.schemas_cfg import RigidBodyPropertiesCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import UsdFileCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import SceneEntityCfg

# Import local modules
from . import mdp
from .mdp import doosan_stack_events
from .stack_env_cfg import StackEnvCfg

# Pre-defined configs
from isaaclab.markers.config import FRAME_MARKER_CFG  # isort: skip

# Insert package path to load assets and configs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from cfgs.doosan_shelf_assets_cfg import DOOSAN_E0509_WITH_GRIPPER_CFG  # noqa: E402
from cfgs.gripper_cfg import (  # noqa: E402
    GRIPPER_JOINT_NAMES,
    GRIPPER_OPEN_COMMAND,
    GRIPPER_CLOSE_COMMAND,
    GRIPPER_OPEN_WIDTH,
    GRIPPER_GRASP_THRESHOLD,
)


@configclass
class EventCfg:
    """Configuration for events during episode resets."""

    # Set default joint positions for the Doosan arm and gripper
    init_doosan_arm_pose = EventTerm(
        func=doosan_stack_events.set_default_joint_pose,
        mode="reset",
        params={
            # joint1 to joint6 + gripper_rh_l1/l2/r1/r2
            "default_pose": [0.0, -0.8, 1.57, 0.0, 0.8, 0.0, 1.101, 1.101, 1.101, 1.101],
        },
    )

    # Randomize robot joint states (arm joints only, keeping gripper intact)
    randomize_doosan_joint_state = EventTerm(
        func=doosan_stack_events.randomize_joint_by_gaussian_offset,
        mode="reset",
        params={
            "mean": 0.0,
            "std": 0.02,
            "asset_cfg": SceneEntityCfg("robot"),
        },
    )

    # Randomize position of stacking cubes on the table
    randomize_cube_positions = EventTerm(
        func=doosan_stack_events.randomize_object_pose,
        mode="reset",
        params={
            "pose_range": {"x": (0.4, 0.6), "y": (-0.15, 0.15), "z": (0.025, 0.025), "yaw": (-1.0, 1.0)},
            "min_separation": 0.12,
            "asset_cfgs": [SceneEntityCfg("cube_1"), SceneEntityCfg("cube_2")],
        },
    )


@configclass
class DoosanCubeStackEnvCfg(StackEnvCfg):
    """Doosan E0509 + RH-P12-RN-A Stacking Environment Config."""

    def __post_init__(self):
        # Post-initialization of parent class
        super().__post_init__()

        # Register events
        self.events = EventCfg()

        # Set Doosan as robot in scene
        self.scene.robot = DOOSAN_E0509_WITH_GRIPPER_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
        self.scene.robot.spawn.semantic_tags = [("class", "robot")]

        # Add semantics to mount structures
        self.scene.table.spawn.semantic_tags = [("class", "table")]
        self.scene.plane.semantic_tags = [("class", "ground")]

        # Configure action controllers
        # We use absolute JointPositionActionCfg for arm joints (1-6)
        self.actions.arm_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=["joint_?[1-6]"],
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

        # Configure Cubes (blue and red)
        cube_properties = RigidBodyPropertiesCfg(
            solver_position_iteration_count=16,
            solver_velocity_iteration_count=1,
            max_angular_velocity=1000.0,
            max_linear_velocity=1000.0,
            max_depenetration_velocity=5.0,
            disable_gravity=False,
        )

        # Stacking Cube 1 (Target Object)
        self.scene.cube_1 = RigidObjectCfg(
            prim_path="{ENV_REGEX_NS}/Cube_1",
            init_state=RigidObjectCfg.InitialStateCfg(pos=[0.45, -0.05, 0.025], rot=[1, 0, 0, 0]),
            spawn=UsdFileCfg(
                usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/Blocks/blue_block.usd",
                scale=(1.0, 1.0, 1.0),
                rigid_props=cube_properties,
                semantic_tags=[("class", "cube_1")],
            ),
        )

        # Stacking Cube 2 (Base Object)
        self.scene.cube_2 = RigidObjectCfg(
            prim_path="{ENV_REGEX_NS}/Cube_2",
            init_state=RigidObjectCfg.InitialStateCfg(pos=[0.55, 0.05, 0.025], rot=[1, 0, 0, 0]),
            spawn=UsdFileCfg(
                usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/Blocks/red_block.usd",
                scale=(1.0, 1.0, 1.0),
                rigid_props=cube_properties,
                semantic_tags=[("class", "cube_2")],
            ),
        )

        # Configure End-effector Frame and Finger Trackers
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
                FrameTransformerCfg.FrameCfg(
                    prim_path="{ENV_REGEX_NS}/Robot/gripper_rh_p12_rn_r1",
                    name="tool_rightfinger",
                    offset=OffsetCfg(
                        pos=(0.0, 0.0, 0.046),
                    ),
                ),
                FrameTransformerCfg.FrameCfg(
                    prim_path="{ENV_REGEX_NS}/Robot/gripper_rh_p12_rn_l1",
                    name="tool_leftfinger",
                    offset=OffsetCfg(
                        pos=(0.0, 0.0, 0.046),
                    ),
                ),
            ],
        )


@configclass
class DoosanCubeStackEnvCfg_PLAY(DoosanCubeStackEnvCfg):
    """Play mode config for visual inspection."""

    def __post_init__(self):
        super().__post_init__()
        # Reduce environment counts for faster rendering in UI
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        # Disable observation noise/corruption
        self.observations.policy.enable_corruption = False
