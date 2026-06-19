# -*- coding: utf-8 -*-
# Task 2: Object Pick-up — MDP 환경 기반 설정 (Base Environment Configuration)
# ~/smart-shelf-robot/src/custom/rl/envs/pick/pick_env_cfg.py
#
# task_define.md 의 Task 2 "Object Pick-up (물품 정밀 파지)" 명세에 따라
# franka_isaaclab 의 lift_env_cfg.py 구조를 벤치마킹하여 설계합니다.
#
# Scene:   두산 E0509 + RH-P12-RN-A + 바구니 + 대상 물체
# Obs:     관절 상태 + EE Pose + 물체 Pose + 그리퍼 상태 + last_action
# Action:  관절 6개 ΔJoint + 그리퍼 바이너리 = [6+1]
# Reward:  Reach → Grasp → Lift (Stage-based)
# Term:    타임아웃 + 낙하 + 성공

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
# - 바구니 안의 물체를 로봇이 파지하는 장면
##

@configclass
class BasketPickSceneCfg(InteractiveSceneCfg):
    """Task 2 Pick-up 씬 설정.

    로봇, 엔드이펙터 프레임, 대상 물체는 파생 클래스에서 지정합니다.
    바구니, 지면, 조명은 공통으로 설정됩니다.
    """

    # 파생 클래스에서 설정할 항목
    robot: ArticulationCfg = MISSING
    ee_frame: FrameTransformerCfg = MISSING
    object: RigidObjectCfg = MISSING

    # 바구니 — 물품이 담겨 있는 수납 용기 (고정체)
    basket = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Basket",
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=[0.4, 0.0, 0.0],
            rot=[1.0, 0.0, 0.0, 0.0],
        ),
        spawn=UsdFileCfg(
            usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/KLT_Bin/small_KLT.usd",
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
# MDP settings — task_define.md Task 2 명세 기반
##

@configclass
class CommandsCfg:
    """Pick-up 태스크의 명령 항 (현재 사용하지 않음).

    Pick 태스크는 물체 위치를 직접 관측하므로 별도 command generator 불필요.
    """
    pass


@configclass
class ActionsCfg:
    """행동 공간 명세.

    task_define.md: Action Space [6 + 1]
    - 관절 6개의 목표 조인트 위치 변위량 (Δq)
    - 그리퍼 제어 명령 (0: 열림, 1: 닫힘)
    """
    arm_action: mdp.JointPositionActionCfg | mdp.RelativeJointPositionActionCfg = MISSING
    gripper_action: mdp.BinaryJointPositionActionCfg = MISSING


@configclass
class ObservationsCfg:
    """관측 공간 명세.

    task_define.md: Observation Space [~33 dim]
    - 관절 각도/속도 (12)
    - 엔드이펙터 Pose (7)
    - 대상 물체 Pose (7)
    - 그리퍼 상태 (2)
    - 이전 행동 (7)
    """

    @configclass
    class PolicyCfg(ObsGroup):
        """정책 학습용 관측 그룹."""

        # 두산 E0509 관절 상대 각도 (6)
        joint_pos = ObsTerm(func=mdp.joint_pos_rel)
        # 두산 E0509 관절 상대 속도 (6)
        joint_vel = ObsTerm(func=mdp.joint_vel_rel)
        # 엔드이펙터(그리퍼 중심) 위치 (3)
        eef_pos = ObsTerm(func=mdp.ee_frame_pos)
        # 엔드이펙터 쿼터니언 자세 (4)
        eef_quat = ObsTerm(func=mdp.ee_frame_quat)
        # 대상 물체의 로봇 좌표계 상 위치 (3)
        object_position = ObsTerm(func=mdp.object_position_in_robot_root_frame)
        # 대상 물체의 쿼터니언 자세 (4)
        object_orientation = ObsTerm(func=mdp.object_orientation_in_robot_root_frame)
        # 그리퍼 상태: 개구량 + 의사 토크 (2)
        gripper = ObsTerm(func=mdp.gripper_state)
        # 이전 스텝의 행동 출력 (7)
        actions = ObsTerm(func=mdp.last_action)

        def __post_init__(self):
            self.enable_corruption = True
            self.concatenate_terms = True

    # 관측 그룹
    policy: PolicyCfg = PolicyCfg()


@configclass
class EventCfg:
    """이벤트 설정 — 리셋 시 물체 위치 랜덤화."""

    reset_all = EventTerm(func=mdp.reset_scene_to_default, mode="reset")

    # 바구니 내 물체 위치를 에피소드마다 랜덤 배치
    reset_object_position = EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "pose_range": {
                "x": (-0.05, 0.05),   # 바구니 중심 ±5cm
                "y": (-0.1, 0.1),     # 바구니 좌우 ±10cm
                "z": (0.0, 0.0),      # 바구니 바닥
            },
            "velocity_range": {},
            "asset_cfg": SceneEntityCfg("object", body_names="Object"),
        },
    )


@configclass
class RewardsCfg:
    """보상 항 설정.

    task_define.md Task 2 보상 설계:
    - Reach Reward: tanh(ω · ‖p_ee − p_obj‖)
    - Grasp Bonus: 접촉 + 손가락 닫힘
    - Lift Reward: z > z_bottom + threshold
    - Action Penalty: 가속도/급격한 변화량
    """

    # Stage 1: 그리퍼→물체 접근 보상
    reaching_object = RewTerm(
        func=mdp.reach_reward,
        params={"std": 0.1},
        weight=1.0,
    )

    # Stage 2: 파지 성공 보너스
    grasp_bonus = RewTerm(
        func=mdp.grasp_bonus,
        params={"diff_threshold": 0.04},
        weight=5.0,
    )

    # Stage 3: 물체 리프트 보상
    lifting_object = RewTerm(
        func=mdp.lift_reward,
        params={"minimal_height": 0.06},
        weight=15.0,
    )

    # 패널티: 급격한 액션 변화 억제 (실물 로봇 Jerk 저감)
    action_rate = RewTerm(func=mdp.action_rate_l2, weight=-1e-4)

    # 패널티: 과도한 관절 속도 억제
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

    # 물체가 바구니/지면 아래로 낙하
    object_dropping = DoneTerm(
        func=mdp.object_dropped,
        params={"minimum_height": -0.05, "object_cfg": SceneEntityCfg("object")},
    )


@configclass
class CurriculumCfg:
    """커리큘럼 설정 — 학습 진행에 따라 패널티 가중치 점진적 증가."""

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
class PickEnvCfg(ManagerBasedRLEnvCfg):
    """Task 2: Object Pick-up 환경 설정 기반 클래스.

    파생 클래스에서 로봇, 그리퍼, 물체 에셋을 바인딩합니다.
    """

    # Scene settings
    scene: BasketPickSceneCfg = BasketPickSceneCfg(num_envs=4096, env_spacing=2.5)
    # Basic settings
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    commands: CommandsCfg = CommandsCfg()
    # MDP settings
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    events: EventCfg = EventCfg()
    curriculum: CurriculumCfg = CurriculumCfg()

    def __post_init__(self):
        """Post initialization."""
        # 일반 설정
        self.decimation = 2
        self.episode_length_s = 8.0  # 파지 태스크는 Reach보다 긴 에피소드 필요
        # 시뮬레이션 설정
        self.sim.dt = 0.01  # 100Hz
        self.sim.render_interval = self.decimation

        self.sim.physx.bounce_threshold_velocity = 0.2
        self.sim.physx.gpu_found_lost_aggregate_pairs_capacity = 1024 * 1024 * 4
        self.sim.physx.gpu_total_aggregate_pairs_capacity = 16 * 1024
        self.sim.physx.friction_correlation_distance = 0.00625
