# -*- coding: utf-8 -*-
# 2.3 두산 E0509 및 스마트 가판대 USD 에셋 임포트 명세
# ~/smart-shelf-robot/src/custom/rl/cfgs/doosan_shelf_assets_cfg.py 

import os
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg


from isaaclab.actuators import ImplicitActuatorCfg

# 1. 두산 E0509 협동로봇 에셋 기하학적 강체 컴포넌트 정의 
DOOSAN_E0509_CFG = ArticulationCfg( 
    prim_path="{ENV_REGEX_EXPR}/robot", 
    spawn=sim_utils.UsdFileCfg( 
        usd_path=os.path.expanduser("~/smart-shelf-robot/src/external/doosan-robot2/dsr_description2/usd/e0509.usd"), 
        rigid_props=sim_utils.RigidBodyPropertiesCfg( 
            disable_gravity=False, 
            retain_accelerations=False, 
            linear_damping=0.0, 
            angular_damping=0.0, 
            max_linear_velocity=1000.0, 
            max_angular_velocity=10.0, 
        ), 
        articulation_props=sim_utils.ArticulationRootPropertiesCfg( 
            enabled_self_collisions=True,  
            solver_position_iteration_count=8,  
            solver_velocity_iteration_count=2 
        ), 
    ), 
    init_state=ArticulationCfg.InitialStateCfg( 
        joint_pos={ 
            "joint_1": 0.0, 
            "joint_2": 0.0, 
            "joint_3": 1.57,  # 가판대 진열 접근을 위한 기본 홈 포즈(Home Pose) 설정 
            "joint_4": 0.0, 
            "joint_5": 1.57, 
            "joint_6": 0.0, 
        }, 
        pos=(0.0, 0.0, 0.0), 
        rot=(1.0, 0.0, 0.0, 0.0), 
    ), 
    actuators={
        "doosan_arm": ImplicitActuatorCfg(
            joint_names_expr=["joint_?[1-6]"],
            stiffness=800.0,
            damping=40.0,
            friction=0.1,
        ),
    },
    soft_joint_pos_limit_factor=1.0,
) 

# 2. 편의점 스마트 진열대 가판대 환경 구조화 정의 
SMART_SHELF_CFG = AssetBaseCfg( 
    prim_path="{ENV_REGEX_EXPR}/smart_shelf", 
    spawn=sim_utils.UsdFileCfg( 
        usd_path=os.path.expanduser("~/smart-shelf-robot/src/custom/rl/assets/convenience_shelf.usd"), 
        # 물품 파지 충격력에 가판대가 물리적으로 튕겨나가지 않도록 강제 고정 고정체(Static Object) 처리 
        rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True) 
    ) 
) 


# ──────────────────────────────────────────────────────────────────────────────
# task_define.md Task 2/4 공통: 그리퍼 통합 로봇 및 바구니 환경 에셋
# ──────────────────────────────────────────────────────────────────────────────

from isaaclab.actuators import ImplicitActuatorCfg

# 3. 두산 E0509 + Robotis RH-P12-RN-A 그리퍼 통합 에셋
#    Pick/Place 태스크에서 그리퍼 제어가 필요한 환경에서 사용합니다.
#    (그리퍼 USD가 로봇 USD에 통합된 형태를 전제합니다. 
#     별도 USD인 경우 Articulation 병합 또는 FixedJoint로 연결 필요)
DOOSAN_E0509_WITH_GRIPPER_CFG = ArticulationCfg(
    prim_path="{ENV_REGEX_EXPR}/robot",
    spawn=sim_utils.UsdFileCfg(
        usd_path=os.path.expanduser(
            "~/smart-shelf-robot/src/custom/rl/assets/doosan_e0509_with_gripper.usd"
        ),
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            retain_accelerations=False,
            linear_damping=0.0,
            angular_damping=0.0,
            max_linear_velocity=1000.0,
            max_angular_velocity=10.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            solver_position_iteration_count=8,
            solver_velocity_iteration_count=2,
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        joint_pos={
            "joint_1": 0.0,
            "joint_2": -0.8,   # Task 2 접근에 유리한 어깨 하향 자세
            "joint_3": 1.57,
            "joint_4": 0.0,
            "joint_5": 0.8,    # 손목 하향 — 바구니/매대 방향 정렬
            "joint_6": 0.0,
            "gripper_rh_r1": 1.09,  # RH-P12-RN-A 완전 개방 (1.09 rad to stay safely within USD limits)
            "gripper_rh_l1": 1.09,
            "gripper_rh_r2": 1.09,
            "gripper_rh_l2": 1.09,
        },
        pos=(0.0, 0.0, 0.0),
        rot=(1.0, 0.0, 0.0, 0.0),
    ),
    actuators={
        "doosan_arm": ImplicitActuatorCfg(
            joint_names_expr=["joint_?[1-6]"],
            stiffness=800.0,
            damping=40.0,
            friction=0.1,
        ),
        "gripper": ImplicitActuatorCfg(
            joint_names_expr=["gripper_rh_.*"],
            stiffness=200.0,
            damping=20.0,
            friction=0.05,
        ),
    },
    soft_joint_pos_limit_factor=1.0,
)


# 4. 바구니(Basket) 에셋 — Task 2 Pick-up 환경에서 물품 수납 용기
BASKET_CFG = AssetBaseCfg(
    prim_path="{ENV_REGEX_EXPR}/basket",
    spawn=sim_utils.UsdFileCfg(
        usd_path=os.path.expanduser(
            "~/smart-shelf-robot/src/custom/rl/assets/basket.usd"
        ),
        # 바구니도 가판대와 마찬가지로 고정체(Static Object) 처리
        rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
    ),
    init_state=AssetBaseCfg.InitialStateCfg(
        pos=(0.4, 0.0, 0.0),  # 로봇 전방 40cm 지점
        rot=(1.0, 0.0, 0.0, 0.0),
    ),
)
