# -*- coding: utf-8 -*-
# Task 2: Object Pick-up — 두산 E0509 + RH-P12-RN-A 특화 환경 설정
# ~/smart-shelf-robot/src/custom/rl/envs/pick/doosan_pick_env_cfg.py
#
# PickEnvCfg 기반 클래스를 상속받아 두산 E0509 로봇과 Robotis RH-P12-RN-A
# 그리퍼를 바인딩하고, task_define.md Task 2 의 Action Space 명세에 따라
# 상대 조인트 위치 제어(ΔJoint)와 그리퍼 바이너리 제어를 설정합니다.
#
# 벤치마킹 참조: franka_isaaclab lift/joint_pos_env_cfg.py

import os

from isaaclab.assets import RigidObjectCfg
from isaaclab.sensors import FrameTransformerCfg
from isaaclab.sensors.frame_transformer.frame_transformer_cfg import OffsetCfg
from isaaclab.sim.schemas.schemas_cfg import RigidBodyPropertiesCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import UsdFileCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR

from . import mdp
from .pick_env_cfg import PickEnvCfg

##
# Pre-defined configs
##
from isaaclab.markers.config import FRAME_MARKER_CFG  # isort: skip

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from cfgs.dynamic_objects_cfg import get_dynamic_object_cfg  # noqa: E402
from cfgs.doosan_shelf_assets_cfg import DOOSAN_E0509_WITH_GRIPPER_CFG  # noqa: E402
from cfgs.gripper_cfg import (  # noqa: E402
    GRIPPER_JOINT_NAMES,
    GRIPPER_OPEN_COMMAND,
    GRIPPER_CLOSE_COMMAND,
    GRIPPER_OPEN_WIDTH,
    GRIPPER_GRASP_THRESHOLD,
)


@configclass
class DoosanPickEnvCfg(PickEnvCfg):
    """두산 E0509 + RH-P12-RN-A 를 사용한 Pick-up 환경.

    task_define.md Task 2 명세:
    - Action Space: [6 + 1] 조인트 변위 + 그리퍼 바이너리
    - Observation: 관절 + EE + 물체 + 그리퍼 → ~33 dim
    """

    # 대상 물품 종류 ("cube", "can", "bottle", "snack_bag")
    object_type: str = os.getenv("OBJECT_TYPE", "cube")

    def __post_init__(self):
        # 부모 초기화
        super().__post_init__()

        # ── 로봇 에셋 ──────────────────────────────────────────
        self.scene.robot = DOOSAN_E0509_WITH_GRIPPER_CFG.replace(
            prim_path="{ENV_REGEX_NS}/Robot"
        )

        # ── 행동 공간 설정 ─────────────────────────────────────
        # task_define.md: 관절 6개의 목표 조인트 위치 변위량 (Δq)
        # implementation_plan.md: RelativeJointPositionActionCfg, scale=0.05
        self.actions.arm_action = mdp.RelativeJointPositionActionCfg(
            asset_name="robot",
            joint_names=["joint_?[1-6]"],
            scale=0.05,
            use_zero_offset=True,
        )
        # task_define.md: 그리퍼 제어 명령 (0: 열림, 1: 닫힘)
        self.actions.gripper_action = mdp.BinaryJointPositionActionCfg(
            asset_name="robot",
            joint_names=GRIPPER_JOINT_NAMES,
            open_command_expr=GRIPPER_OPEN_COMMAND,
            close_command_expr=GRIPPER_CLOSE_COMMAND,
        )

        # ── 그리퍼 파지 판정 파라미터 (보상/종료 함수에서 참조) ───
        self.gripper_joint_names = GRIPPER_JOINT_NAMES
        self.gripper_open_val = GRIPPER_OPEN_WIDTH
        self.gripper_threshold = GRIPPER_GRASP_THRESHOLD

        # ── 대상 물체 설정 ─────────────────────────────────────
        # 바구니 안의 파지 대상 물체 (CFG 팩토리를 통해 동적 생성)
        from cfgs.dynamic_objects_cfg import OBJECT_HEIGHT_OFFSETS
        z_offset = 0.035 + OBJECT_HEIGHT_OFFSETS[self.object_type]
        self.scene.object = get_dynamic_object_cfg(
            self.object_type,
            prim_path="{ENV_REGEX_NS}/Object",
            pos=[0.4, 0.0, z_offset],
            rot=[1.0, 0.0, 0.0, 0.0],
        )

        # ── 엔드이펙터 프레임 설정 ────────────────────────────
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
                        # link_6(플랜지) → 그리퍼 중심까지의 오프셋
                        pos=[0.0, 0.0, 0.12],
                    ),
                ),
            ],
        )


@configclass
class DoosanPickEnvCfg_PLAY(DoosanPickEnvCfg):
    """추론/시연 모드용 축소 환경."""

    def __post_init__(self):
        super().__post_init__()
        # 시연 시 소규모 환경
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        # 관측 노이즈 비활성화
        self.observations.policy.enable_corruption = False
