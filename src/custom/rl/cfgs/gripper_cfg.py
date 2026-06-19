# -*- coding: utf-8 -*-
# Robotis RH-P12-RN-A 그리퍼 설정
# ~/smart-shelf-robot/src/custom/rl/cfgs/gripper_cfg.py
#
# task_define.md 의 Task 2(Pick-up) 및 Task 4(Place) 에서 공통 사용되는
# 그리퍼 물리 설정 및 제어 파라미터를 정의합니다.

import os
import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg

##
# Robotis RH-P12-RN-A 그리퍼 물리 상수
##

# 그리퍼 관절 이름 (USD 에셋 내 관절명)
GRIPPER_JOINT_NAMES = ["gripper_rh_r1", "gripper_rh_l1", "gripper_rh_r2", "gripper_rh_l2"]

# 그리퍼 개구량 범위 (rad 단위)
GRIPPER_OPEN_WIDTH = 1.101     # RH-P12-RN-A 최대 개구각 1.101 rad
GRIPPER_CLOSE_WIDTH = 0.0      # 완전 닫힘

# 물성별 목표 파지 전류 (mA) - main_controller_node.py 와 동기화
GRIPPER_CURRENT_MAP = {
    "can":       800.0,
    "bottle":    400.0,
    "snack_bag": 200.0,
}

# 그리퍼 상태 판별 임계치 (rad)
GRIPPER_GRASP_THRESHOLD = 0.1  # 개구각이 이 값 이하이면 파지 중으로 간주 (rad)


##
# 그리퍼 액추에이터 설정
##

GRIPPER_ACTUATOR_CFG = ImplicitActuatorCfg(
    joint_names_expr=GRIPPER_JOINT_NAMES,
    stiffness=200.0,    # 그리퍼 손가락 강성
    damping=20.0,       # 그리퍼 손가락 감쇠
    friction=0.05,
)


##
# 그리퍼 제어 명령 표현식 (BinaryJointPositionActionCfg 용)
##

GRIPPER_OPEN_COMMAND = {
    "gripper_rh_r1": GRIPPER_OPEN_WIDTH,
    "gripper_rh_l1": GRIPPER_OPEN_WIDTH,
    "gripper_rh_r2": GRIPPER_OPEN_WIDTH,
    "gripper_rh_l2": GRIPPER_OPEN_WIDTH,
}
GRIPPER_CLOSE_COMMAND = {
    "gripper_rh_r1": GRIPPER_CLOSE_WIDTH,
    "gripper_rh_l1": GRIPPER_CLOSE_WIDTH,
    "gripper_rh_r2": GRIPPER_CLOSE_WIDTH,
    "gripper_rh_l2": GRIPPER_CLOSE_WIDTH,
}

