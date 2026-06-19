# -*- coding: utf-8 -*-
# Task 4: Shelf Placing & Alignment — 관측 함수 (Observation Functions)
# ~/smart-shelf-robot/src/custom/rl/envs/place/mdp/observations.py
#
# task_define.md 의 Place Observation Space 명세에 따라
# 매대 빈 슬롯의 Pose, 내부 진입 허용 공차, 그리퍼 상태를 관측합니다.

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import RigidObject, Articulation
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import FrameTransformer
from isaaclab.utils.math import subtract_frame_transforms

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def slot_position_in_robot_root_frame(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    slot_cfg: SceneEntityCfg = SceneEntityCfg("slot"),
) -> torch.Tensor:
    """로봇 기저 좌표계 기준 타겟 매대 빈 슬롯의 3D 위치.

    task_define.md: 타겟 매대 빈 슬롯 중심의 3D Pose

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        robot_cfg: 로봇 설정.
        slot_cfg: 매대 슬롯 설정.

    Returns:
        (num_envs, 3) 크기의 위치 텐서.
    """
    robot: Articulation = env.scene[robot_cfg.name]
    slot: RigidObject = env.scene[slot_cfg.name]

    slot_pos_w = slot.data.root_pos_w[:, :3]
    slot_pos_b, _ = subtract_frame_transforms(
        robot.data.root_pos_w, robot.data.root_quat_w, slot_pos_w
    )
    return slot_pos_b


def slot_orientation_in_robot_root_frame(
    env: ManagerBasedRLEnv,
    slot_cfg: SceneEntityCfg = SceneEntityCfg("slot"),
) -> torch.Tensor:
    """타겟 매대 빈 슬롯의 쿼터니언 자세.

    Returns:
        (num_envs, 4) 크기의 쿼터니언 텐서.
    """
    slot: RigidObject = env.scene[slot_cfg.name]
    return slot.data.root_quat_w


def slot_tolerance_vector(
    env: ManagerBasedRLEnv,
) -> torch.Tensor:
    """매대 슬롯 내부 진입 허용 공차 벡터.

    task_define.md: 슬롯 내부 진입 허용 공차 벡터
    슬롯의 폭(x), 높이(y), 깊이(z) 방향의 허용 오차를 나타냅니다.

    환경 cfg 에 `slot_tolerance` 속성이 있으면 그 값을 사용하고,
    없으면 기본값 [±3cm, ±2cm, 15cm] 을 사용합니다.

    Returns:
        (num_envs, 3) 크기의 공차 벡터 텐서.
    """
    # 슬롯 공차: [x_tolerance, y_tolerance, z_depth]
    if hasattr(env.cfg, "slot_tolerance"):
        tol = env.cfg.slot_tolerance
    else:
        tol = [0.03, 0.02, 0.15]  # 기본 공차: 좌우 3cm, 상하 2cm, 깊이 15cm

    tolerance = torch.tensor(tol, dtype=torch.float32, device=env.device)
    return tolerance.unsqueeze(0).expand(env.num_envs, -1)


def object_position_in_robot_root_frame(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
) -> torch.Tensor:
    """로봇 기저 좌표계 기준 파지 중인 물체의 3D 위치.

    Returns:
        (num_envs, 3) 크기의 위치 텐서.
    """
    robot: Articulation = env.scene[robot_cfg.name]
    obj: RigidObject = env.scene[object_cfg.name]

    object_pos_w = obj.data.root_pos_w[:, :3]
    object_pos_b, _ = subtract_frame_transforms(
        robot.data.root_pos_w, robot.data.root_quat_w, object_pos_w
    )
    return object_pos_b


def gripper_state(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """RH-P12-RN-A 그리퍼의 현재 상태: 개구량 + 의사 토크.

    Returns:
        (num_envs, 2) 크기의 텐서 — [개구량, 토크 추정치].
    """
    robot: Articulation = env.scene[robot_cfg.name]

    if hasattr(env.cfg, "gripper_joint_names"):
        gripper_joint_ids, _ = robot.find_joints(env.cfg.gripper_joint_names)
        opening_width = robot.data.joint_pos[:, gripper_joint_ids[0]].unsqueeze(-1)
        applied_torque = robot.data.applied_torque[:, gripper_joint_ids[0]].unsqueeze(-1)
        return torch.cat([opening_width, applied_torque], dim=-1)

    return torch.zeros(env.num_envs, 2, device=env.device)


def ee_frame_pos(
    env: ManagerBasedRLEnv,
    ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame"),
) -> torch.Tensor:
    """엔드이펙터 프레임의 월드 좌표 위치.

    Returns:
        (num_envs, 3) 크기의 위치 텐서.
    """
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]
    return ee_frame.data.target_pos_w[:, 0, :]


def ee_frame_quat(
    env: ManagerBasedRLEnv,
    ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame"),
) -> torch.Tensor:
    """엔드이펙터 프레임의 월드 좌표 쿼터니언 자세.

    Returns:
        (num_envs, 4) 크기의 쿼터니언 텐서.
    """
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]
    return ee_frame.data.target_quat_w[:, 0, :]
