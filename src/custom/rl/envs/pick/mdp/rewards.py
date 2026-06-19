# -*- coding: utf-8 -*-
# Task 2: Object Pick-up — 보상 함수 (Reward Functions)
# ~/smart-shelf-robot/src/custom/rl/envs/pick/mdp/rewards.py
#
# task_define.md 에 정의된 Pick-up 보상 설계를 Isaac Lab ManagerBasedRLEnv
# 에서 사용 가능한 텐서 연산 함수로 구현합니다.
#
# 보상 구성 (Stage-based):
#   Stage 1 — Reach Reward:  그리퍼→물체 거리 감소 보상
#   Stage 2 — Grasp Bonus:   접촉 + 손가락 닫힘 시 정적 보상
#   Stage 3 — Lift Reward:   물체가 바구니 바닥 위 임계치 이상 시 보상
#   Penalty — Action Penalty: 갑작스러운 액션 변화량 억제

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import RigidObject, Articulation
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import FrameTransformer

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


##
# Stage 1: Reach Reward — 그리퍼 중심과 물체 중심 사이의 거리 기반 보상
# task_define.md: r_reach = tanh(ω · ‖p_ee − p_obj‖)
##

def reach_reward(
    env: ManagerBasedRLEnv,
    std: float = 0.1,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
    ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame"),
) -> torch.Tensor:
    """그리퍼 엔드이펙터와 대상 물체 사이의 거리가 가까울수록 높은 보상.

    tanh-kernel 을 사용하여 0~1 범위의 연속 보상을 생성합니다.
    task_define.md 의 Reach Reward 명세를 구현합니다.

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        std: tanh 커널의 표준편차(작을수록 가까이에서 급격한 보상 증가).
        object_cfg: 대상 물체 Scene entity 설정.
        ee_frame_cfg: 엔드이펙터 프레임 센서 설정.

    Returns:
        (num_envs,) 크기의 보상 텐서.
    """
    obj: RigidObject = env.scene[object_cfg.name]
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]

    # 물체 위치 (num_envs, 3)
    obj_pos_w = obj.data.root_pos_w
    # 엔드이펙터 위치 (num_envs, 3)
    ee_pos_w = ee_frame.data.target_pos_w[..., 0, :]

    # 유클리드 거리
    distance = torch.norm(obj_pos_w - ee_pos_w, dim=1)

    return 1.0 - torch.tanh(distance / std)


##
# Stage 2: Grasp Bonus — 그리퍼가 물체를 실제로 파지했을 때 정적 보상
# task_define.md: 그리퍼가 물체와 접촉(Contact Axis 체크)하고
#                 손가락 사이 거리가 물체 폭보다 작아지면 부여
##

def grasp_bonus(
    env: ManagerBasedRLEnv,
    diff_threshold: float = 0.04,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
    ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame"),
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """그리퍼가 물체를 파지했을 때(가까이 + 그리퍼 닫힘) 보상.

    엔드이펙터-물체 거리가 diff_threshold 이내이고,
    그리퍼 관절이 열림 위치에서 충분히 닫혀 있으면 파지로 판정합니다.

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        diff_threshold: EE-물체 최대 허용 거리 (m).
        object_cfg: 대상 물체 설정.
        ee_frame_cfg: 엔드이펙터 프레임 설정.
        robot_cfg: 로봇 설정.

    Returns:
        (num_envs,) 크기의 이진 보상 텐서 (0.0 또는 1.0).
    """
    obj: RigidObject = env.scene[object_cfg.name]
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]
    robot: Articulation = env.scene[robot_cfg.name]

    obj_pos = obj.data.root_pos_w
    ee_pos = ee_frame.data.target_pos_w[:, 0, :]
    pose_diff = torch.norm(obj_pos - ee_pos, dim=1)

    # 그리퍼 파지 판정
    if hasattr(env.cfg, "gripper_joint_names"):
        gripper_joint_ids, _ = robot.find_joints(env.cfg.gripper_joint_names)
        gripper_open_val = torch.tensor(
            env.cfg.gripper_open_val, dtype=torch.float32
        ).to(env.device)

        # 그리퍼가 열림 위치에서 충분히 멀어졌는지 (= 닫혔는지)
        gripper_closed = torch.abs(
            robot.data.joint_pos[:, gripper_joint_ids[0]] - gripper_open_val
        ) > env.cfg.gripper_threshold

        grasped = torch.logical_and(pose_diff < diff_threshold, gripper_closed)
        return grasped.float()

    # 그리퍼 설정이 없는 경우 거리 조건만으로 판정
    return (pose_diff < diff_threshold).float()


##
# Stage 3: Lift Reward — 물체가 바구니 바닥면보다 충분히 높이 들어올려졌을 때 보상
# task_define.md: 물체가 z_bottom 보다 임계치 이상으로 높아졌을 때 누적 보상
##

def lift_reward(
    env: ManagerBasedRLEnv,
    minimal_height: float = 0.06,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
) -> torch.Tensor:
    """물체가 최소 높이 이상으로 들어올려졌을 때 보상.

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        minimal_height: 리프트 성공으로 간주할 최소 z 높이 (m).
        object_cfg: 대상 물체 설정.

    Returns:
        (num_envs,) 크기의 이진 보상 텐서 (0.0 또는 1.0).
    """
    obj: RigidObject = env.scene[object_cfg.name]
    return torch.where(obj.data.root_pos_w[:, 2] > minimal_height, 1.0, 0.0)
