# -*- coding: utf-8 -*-
# Task 4: Shelf Placing & Alignment — MDP 환경 기반 설정
# ~/smart-shelf-robot/src/custom/rl/envs/place/place_env_cfg.py
#
# task_define.md 의 Task 4 "Shelf Placing & Alignment (매대 정밀 적재)" 명세에 따라
# franka_isaaclab 의 stack_env_cfg.py 구조를 벤치마킹하여 설계합니다.
#
# Scene:   두산 E0509 + RH-P12-RN-A + 매대(선반) + 파지된 물체 + 빈 슬롯
# Obs:     관절 상태 + EE Pose + 슬롯 Pose + 공차 + 물체 Pose + 그리퍼 + action
# Action:  관절 6개 ΔJoint + 그리퍼 해제 = [6+1]
# Reward:  Alignment → Insertion → Release & Retreat (Stage-based)
# Term:    타임아웃 + 낙하 + 충돌 + 성공

from dataclasses import MISSING

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import CurriculumTermCfg as CurrTerm
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors.frame_transformer.frame_transformer_cfg import FrameTransformerCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import GroundPlaneCfg, UsdFileCfg
from isaaclab.utils import configclass

from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR

from . import mdp


##
# Scene definition
# - 매대 앞에서 물체를 빈 슬롯에 정렬 배치하는 장면
##

@configclass
class ShelfPlaceSceneCfg(InteractiveSceneCfg):
    """Task 4 Place 씬 설정.

    로봇, EE 프레임, 물체, 슬롯(배치 목표)은 파생 클래스에서 지정합니다.
    매대, 지면, 조명은 공통으로 설정됩니다.
    """

    # 파생 클래스에서 설정할 항목
    robot: ArticulationCfg = MISSING
    ee_frame: FrameTransformerCfg = MISSING
    object: RigidObjectCfg = MISSING          # 파지 중인 물체
    slot: RigidObjectCfg = MISSING             # 배치 목표 슬롯 마커

    # 매대 (고정체)
    shelf = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Shelf",
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=[0.5, 0.0, 0.0],
            rot=[1.0, 0.0, 0.0, 0.0],
        ),
        spawn=UsdFileCfg(
            usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/Sektion_Cabinet/sektion_cabinet_instanceable.usd",
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
        ),
    )

    # 지면
    plane = AssetBaseCfg(
        prim_path="/World/GroundPlane",
        init_state=AssetBaseCfg.InitialStateCfg(pos=[0, 0, -1.05]),
        spawn=GroundPlaneCfg(),
    )

    # 조명
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(color=(0.75, 0.75, 0.75), intensity=3000.0),
    )


##
# MDP settings — task_define.md Task 4 명세 기반
##

@configclass
class ActionsCfg:
    """행동 공간 명세.

    task_define.md: Action Space [6 + 1]
    - 조인트 제어 명령
    - 그리퍼 강제 해제 신호
    """
    arm_action: mdp.JointPositionActionCfg | mdp.RelativeJointPositionActionCfg = MISSING
    gripper_action: mdp.BinaryJointPositionActionCfg = MISSING


@configclass
class ObservationsCfg:
    """관측 공간 명세.

    task_define.md Task 4 Observation Space:
    - 관절 정보 (12)
    - EE Pose (7)
    - 타겟 슬롯 Pose (7)
    - 슬롯 내부 진입 허용 공차 벡터 (3)
    - 물체 위치 (3)
    - 그리퍼 상태 (2)
    - 이전 행동 (7)
    → 총 ~41 dim
    """

    @configclass
    class PolicyCfg(ObsGroup):
        """정책 학습용 관측 그룹."""

        # 관절 상대 각도 (6)
        joint_pos = ObsTerm(func=mdp.joint_pos_rel)
        # 관절 상대 속도 (6)
        joint_vel = ObsTerm(func=mdp.joint_vel_rel)
        # EE 위치 (3)
        eef_pos = ObsTerm(func=mdp.ee_frame_pos)
        # EE 쿼터니언 (4)
        eef_quat = ObsTerm(func=mdp.ee_frame_quat)
        # 타겟 슬롯 위치 (3)
        slot_position = ObsTerm(func=mdp.slot_position_in_robot_root_frame)
        # 타겟 슬롯 쿼터니언 (4)
        slot_orientation = ObsTerm(func=mdp.slot_orientation_in_robot_root_frame)
        # 슬롯 진입 공차 벡터 (3)
        slot_tolerance = ObsTerm(func=mdp.slot_tolerance_vector)
        # 파지 중인 물체 위치 (3)
        object_position = ObsTerm(func=mdp.object_position_in_robot_root_frame)
        # 그리퍼 상태 (2)
        gripper = ObsTerm(func=mdp.gripper_state)
        # 이전 행동 (7)
        actions = ObsTerm(func=mdp.last_action)

        def __post_init__(self):
            self.enable_corruption = True
            self.concatenate_terms = True

    # 관측 그룹
    policy: PolicyCfg = PolicyCfg()


@configclass
class EventCfg:
    """이벤트 설정 — 리셋 시 슬롯 위치 변동."""

    reset_all = EventTerm(func=mdp.reset_scene_to_default, mode="reset")


@configclass
class RewardsCfg:
    """보상 항 설정.

    task_define.md Task 4 보상 설계:
    - Alignment Reward:  물체 정면 ↔ 슬롯 깊이 방향 코사인 유사도
    - Insertion Reward:  슬롯 중심까지의 거리 기반
    - Release & Retreat Bonus: 배치 + 해제 + 후퇴
    """

    # Stage 1: 물체-슬롯 방향 정렬 보상
    alignment = RewTerm(
        func=mdp.alignment_reward,
        weight=2.0,
    )

    # Stage 2: 슬롯 내부 진입 보상
    insertion = RewTerm(
        func=mdp.insertion_reward,
        params={"std": 0.05},
        weight=10.0,
    )

    # Stage 3: 배치 + 해제 + 안전 후퇴 보너스
    release_retreat = RewTerm(
        func=mdp.release_retreat_bonus,
        params={
            "placement_threshold": 0.03,
            "retreat_distance": 0.08,
        },
        weight=20.0,
    )

    # 패널티: 급격한 액션 변화
    action_rate = RewTerm(func=mdp.action_rate_l2, weight=-1e-4)

    # 패널티: 과도한 관절 속도
    joint_vel = RewTerm(
        func=mdp.joint_vel_l2,
        weight=-1e-4,
        params={"asset_cfg": SceneEntityCfg("robot")},
    )


@configclass
class TerminationsCfg:
    """종료 조건 설정."""

    # 에피소드 타임아웃
    time_out = DoneTerm(func=mdp.time_out, time_out=True)

    # 물체 낙하
    object_dropping = DoneTerm(
        func=mdp.object_dropped,
        params={"minimum_height": -0.05, "object_cfg": SceneEntityCfg("object")},
    )

    # 배치 성공
    placement_success = DoneTerm(
        func=mdp.object_placed_success,
        params={
            "placement_threshold": 0.03,
            "retreat_distance": 0.08,
        },
    )


@configclass
class CurriculumCfg:
    """커리큘럼 설정.

    task_define.md: Curriculum 기반 강화학습 — 초기에는 넓은 슬롯,
    점진적으로 공차 축소하여 난이도 상승.
    패널티 가중치도 학습 진행에 따라 증가.
    """

    action_rate = CurrTerm(
        func=mdp.modify_reward_weight,
        params={"term_name": "action_rate", "weight": -1e-1, "num_steps": 10000},
    )

    joint_vel = CurrTerm(
        func=mdp.modify_reward_weight,
        params={"term_name": "joint_vel", "weight": -1e-1, "num_steps": 10000},
    )


##
# Environment configuration
##

@configclass
class PlaceEnvCfg(ManagerBasedRLEnvCfg):
    """Task 4: Shelf Placing & Alignment 환경 설정 기반 클래스.

    파생 클래스에서 로봇, 그리퍼, 물체, 슬롯 에셋을 바인딩합니다.
    """

    # Scene settings
    scene: ShelfPlaceSceneCfg = ShelfPlaceSceneCfg(num_envs=4096, env_spacing=2.5)
    # Basic settings
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    # MDP settings
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    events: EventCfg = EventCfg()
    curriculum: CurriculumCfg = CurriculumCfg()

    # 미사용 매니저
    commands = None

    # 슬롯 공차 파라미터 (커리큘럼에서 조정 가능)
    slot_tolerance = [0.03, 0.02, 0.15]

    def __post_init__(self):
        """Post initialization."""
        # 일반 설정
        self.decimation = 2
        self.episode_length_s = 10.0  # Place 태스크는 정밀 정렬 시간 확보
        # 시뮬레이션 설정
        self.sim.dt = 0.01  # 100Hz
        self.sim.render_interval = self.decimation

        self.sim.physx.bounce_threshold_velocity = 0.2
        self.sim.physx.gpu_found_lost_aggregate_pairs_capacity = 1024 * 1024 * 4
        self.sim.physx.gpu_total_aggregate_pairs_capacity = 16 * 1024
        self.sim.physx.friction_correlation_distance = 0.00625
