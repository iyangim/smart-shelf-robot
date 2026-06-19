# -*- coding: utf-8 -*-
# Task 4: Shelf Placing & Alignment — 두산 E0509 + RH-P12-RN-A 특화 환경 설정
# ~/smart-shelf-robot/src/custom/rl/envs/place/doosan_place_env_cfg.py
#
# PlaceEnvCfg 기반 클래스를 상속받아 두산 E0509 로봇과 Robotis RH-P12-RN-A
# 그리퍼를 바인딩합니다.
#
# 벤치마킹 참조: franka_isaaclab stack/stack_joint_pos_env_cfg.py

import os

from isaaclab.assets import RigidObjectCfg
from isaaclab.sensors import FrameTransformerCfg
from isaaclab.sensors.frame_transformer.frame_transformer_cfg import OffsetCfg
from isaaclab.sim.schemas.schemas_cfg import RigidBodyPropertiesCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import UsdFileCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR

from . import mdp
from .place_env_cfg import PlaceEnvCfg

##
# Pre-defined configs
##
from isaaclab.markers.config import FRAME_MARKER_CFG  # isort: skip

# 두산 E0509 로봇 에셋 (그리퍼 통합형) — cfgs/doosan_shelf_assets_cfg.py
import sys
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
class DoosanPlaceEnvCfg(PlaceEnvCfg):
    """두산 E0509 + RH-P12-RN-A 를 사용한 Place 환경.

    task_define.md Task 4 명세:
    - Action Space: [6 + 1] 조인트 명령 + 그리퍼 해제 신호
    - 물체를 파지한 상태에서 시작하여 매대 슬롯에 정밀 배치
    """

    def __post_init__(self):
        # 부모 초기화
        super().__post_init__()

        # ── 로봇 에셋 ──────────────────────────────────────────
        self.scene.robot = DOOSAN_E0509_WITH_GRIPPER_CFG.replace(
            prim_path="{ENV_REGEX_NS}/Robot"
        )
        # Place 태스크 초기 자세: 물체를 파지한 상태로 매대 앞에 위치
        self.scene.robot.init_state.joint_pos = {
            "joint_1": 0.0,
            "joint_2": -0.5,   # 매대 높이에 맞춘 어깨 각도
            "joint_3": 1.2,    # 팔꿈치 — 매대 방향 뻗기
            "joint_4": 0.0,
            "joint_5": 0.6,    # 손목 — 수평 정렬
            "joint_6": 0.0,
            "gripper_rh_r1": 0.0,  # 물체를 파지한 상태 (닫힘)
            "gripper_rh_l1": 0.0,
            "gripper_rh_r2": 0.0,
            "gripper_rh_l2": 0.0,
        }

        # ── 행동 공간 설정 ─────────────────────────────────────
        # task_define.md: [6 + 1] 조인트 제어 명령 + 그리퍼 강제 해제 신호
        self.actions.arm_action = mdp.RelativeJointPositionActionCfg(
            asset_name="robot",
            joint_names=["joint_?[1-6]"],
            scale=0.05,     # 매대 내 정밀 이동을 위한 미세 변위
            use_zero_offset=True,
        )
        self.actions.gripper_action = mdp.BinaryJointPositionActionCfg(
            asset_name="robot",
            joint_names=GRIPPER_JOINT_NAMES,
            open_command_expr=GRIPPER_OPEN_COMMAND,
            close_command_expr=GRIPPER_CLOSE_COMMAND,
        )

        # ── 그리퍼 판정 파라미터 ───────────────────────────────
        self.gripper_joint_names = GRIPPER_JOINT_NAMES
        self.gripper_open_val = GRIPPER_OPEN_WIDTH
        self.gripper_threshold = GRIPPER_GRASP_THRESHOLD

        # ── 배치 대상 물체 (파지된 상태로 초기화) ──────────────
        # 초기 위치: EE 근처 (파지 중)
        self.scene.object = RigidObjectCfg(
            prim_path="{ENV_REGEX_NS}/Object",
            init_state=RigidObjectCfg.InitialStateCfg(
                pos=[0.35, 0.0, 0.35],   # 매대 앞 EE 근처
                rot=[1, 0, 0, 0],
            ),
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
            ),
        )

        # ── 매대 빈 슬롯 (배치 목표 마커) ────────────────────
        # 슬롯은 비가시 Rigid Body로, 물체 배치 목표 위치를 나타냅니다.
        self.scene.slot = RigidObjectCfg(
            prim_path="{ENV_REGEX_NS}/Slot",
            init_state=RigidObjectCfg.InitialStateCfg(
                pos=[0.55, 0.0, 0.30],   # 매대 내부 슬롯 중심
                rot=[1, 0, 0, 0],
            ),
            spawn=UsdFileCfg(
                usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/Blocks/DexCube/dex_cube_instanceable.usd",
                scale=(0.3, 0.3, 0.3),  # 작은 마커로 사용
                visible=False,           # 시각적으로 숨김
                rigid_props=RigidBodyPropertiesCfg(
                    kinematic_enabled=True,  # 고정체 — 물리적으로 움직이지 않음
                ),
            ),
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
                        pos=[0.0, 0.0, 0.12],
                    ),
                ),
            ],
        )


@configclass
class DoosanPlaceEnvCfg_PLAY(DoosanPlaceEnvCfg):
    """추론/시연 모드용 축소 환경."""

    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        self.observations.policy.enable_corruption = False
