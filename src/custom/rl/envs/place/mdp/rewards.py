# -*- coding: utf-8 -*-
# Task 4: Shelf Placing & Alignment — 보상 함수 (Reward Functions)
# ~/smart-shelf-robot/src/custom/rl/envs/place/mdp/rewards.py
#
# task_define.md 에 정의된 Place 보상 설계를 Isaac Lab ManagerBasedRLEnv
# 에서 사용 가능한 텐서 연산 함수로 구현합니다.
#
# 보상 구성:
#   Stage 1 — Alignment Reward:   물체 정면 ↔ 슬롯 깊이 방향 코사인 유사도
#   Stage 2 — Insertion Reward:   슬롯 내부 축 방향 진입 깊이
#   Stage 3 — Release & Retreat:  내려놓기 + 그리퍼 열기 + 안전 수납 보너스
#   Penalty — Action/Velocity:     급격한 제어 입력 억제

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import RigidObject, Articulation
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import FrameTransformer

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


##
# Stage 1: Alignment Reward
# task_define.md: 물체의 정면 벡터와 매대 슬롯의 깊이 방향 벡터가
#                 평행을 이룰 때 주어지는 코사인 유사도 보상
##

def alignment_reward(
    env: ManagerBasedRLEnv,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
    slot_cfg: SceneEntityCfg = SceneEntityCfg("slot"),
) -> torch.Tensor:
    """물체의 정면 벡터와 매대 슬롯 깊이 방향 벡터의 코사인 유사도 보상.

    물체가 슬롯에 올바른 방향으로 정렬되어야 삽입이 가능합니다.
    두 방향 벡터가 평행할수록 높은 보상을 부여합니다.

    물체의 정면 벡터는 쿼터니언으로부터 로컬 X축을 추출하여 계산합니다.
    슬롯의 깊이 방향 벡터는 슬롯 쿼터니언의 로컬 X축입니다.

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        object_cfg: 물체 Scene entity 설정.
        slot_cfg: 슬롯 Scene entity 설정.

    Returns:
        (num_envs,) 크기의 보상 텐서 (-1 ~ 1, 1이 완전 정렬).
    """
    obj: RigidObject = env.scene[object_cfg.name]
    slot: RigidObject = env.scene[slot_cfg.name]

    # 물체 쿼터니언 → 로컬 X축(정면 벡터) 추출
    obj_quat = obj.data.root_quat_w  # [qw, qx, qy, qz]
    qw, qx, qy, qz = obj_quat[:, 0], obj_quat[:, 1], obj_quat[:, 2], obj_quat[:, 3]
    obj_forward_x = 1.0 - 2.0 * (qy**2 + qz**2)
    obj_forward_y = 2.0 * (qx * qy + qw * qz)
    obj_forward_z = 2.0 * (qx * qz - qw * qy)
    obj_forward = torch.stack([obj_forward_x, obj_forward_y, obj_forward_z], dim=-1)

    # 슬롯 쿼터니언 → 로컬 X축(깊이 방향 벡터) 추출
    slot_quat = slot.data.root_quat_w
    sw, sx, sy, sz = slot_quat[:, 0], slot_quat[:, 1], slot_quat[:, 2], slot_quat[:, 3]
    slot_depth_x = 1.0 - 2.0 * (sy**2 + sz**2)
    slot_depth_y = 2.0 * (sx * sy + sw * sz)
    slot_depth_z = 2.0 * (sx * sz - sw * sy)
    slot_depth = torch.stack([slot_depth_x, slot_depth_y, slot_depth_z], dim=-1)

    # 코사인 유사도 (내적 / ||a|| · ||b||)
    # 단위 벡터이므로 내적만으로 충분
    cos_sim = torch.sum(obj_forward * slot_depth, dim=-1)

    return cos_sim


##
# Stage 2: Insertion Reward
# task_define.md: 슬롯 입구를 통과하여 내부 축 방향 깊숙이
#                 안정적으로 진입할 때 부여되는 보상
##

def insertion_reward(
    env: ManagerBasedRLEnv,
    std: float = 0.05,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
    slot_cfg: SceneEntityCfg = SceneEntityCfg("slot"),
) -> torch.Tensor:
    """물체가 매대 슬롯 중심에 가까이 진입할수록 높은 보상.

    물체와 슬롯 중심 사이의 3D 거리를 tanh-kernel로 변환하여
    연속적인 보상을 생성합니다. 물체가 슬롯 중심에 가까울수록 1에 수렴합니다.

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        std: tanh 커널 표준편차.
        object_cfg: 물체 설정.
        slot_cfg: 슬롯 설정.

    Returns:
        (num_envs,) 크기의 보상 텐서 (0 ~ 1).
    """
    obj: RigidObject = env.scene[object_cfg.name]
    slot: RigidObject = env.scene[slot_cfg.name]

    obj_pos = obj.data.root_pos_w
    slot_pos = slot.data.root_pos_w

    distance = torch.norm(obj_pos - slot_pos, dim=1)

    return 1.0 - torch.tanh(distance / std)


##
# Stage 3: Release & Retreat Bonus
# task_define.md: 물체를 내려놓은 상태에서 그리퍼를 열고,
#                 물체를 건드리지 않은 채 외곽 방향으로 안전하게 수납할 때 보상
##

def release_retreat_bonus(
    env: ManagerBasedRLEnv,
    placement_threshold: float = 0.03,
    retreat_distance: float = 0.08,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
    slot_cfg: SceneEntityCfg = SceneEntityCfg("slot"),
    ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame"),
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """물체 배치 + 그리퍼 해제 + 안전 후퇴 시 보너스.

    다음 3가지 조건이 모두 만족되면 보상:
    1. 물체가 슬롯 중심에 placement_threshold 이내
    2. 그리퍼가 열린 상태
    3. EE가 물체에서 retreat_distance 이상 떨어짐

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        placement_threshold: 물체-슬롯 최대 허용 거리 (m).
        retreat_distance: 그리퍼 후퇴 최소 거리 (m).
        object_cfg: 물체 설정.
        slot_cfg: 슬롯 설정.
        ee_frame_cfg: EE 프레임 설정.
        robot_cfg: 로봇 설정.

    Returns:
        (num_envs,) 크기의 이진 보상 텐서 (0.0 또는 1.0).
    """
    obj: RigidObject = env.scene[object_cfg.name]
    slot: RigidObject = env.scene[slot_cfg.name]
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]
    robot: Articulation = env.scene[robot_cfg.name]

    # 조건 1: 물체가 슬롯에 충분히 가까운지
    obj_slot_dist = torch.norm(obj.data.root_pos_w - slot.data.root_pos_w, dim=1)
    placed = obj_slot_dist < placement_threshold

    # 조건 2: 그리퍼가 열린 상태인지
    gripper_open = torch.ones(env.num_envs, dtype=torch.bool, device=env.device)
    if hasattr(env.cfg, "gripper_joint_names"):
        gripper_joint_ids, _ = robot.find_joints(env.cfg.gripper_joint_names)
        gripper_open = torch.isclose(
            robot.data.joint_pos[:, gripper_joint_ids[0]],
            torch.tensor(env.cfg.gripper_open_val, dtype=torch.float32).to(env.device),
            atol=1e-3,
        )

    # 조건 3: EE가 물체에서 충분히 후퇴했는지
    ee_pos = ee_frame.data.target_pos_w[:, 0, :]
    ee_obj_dist = torch.norm(ee_pos - obj.data.root_pos_w, dim=1)
    retreated = ee_obj_dist > retreat_distance

    # 세 조건 모두 만족
    success = torch.logical_and(placed, torch.logical_and(gripper_open, retreated))
    return success.float()
