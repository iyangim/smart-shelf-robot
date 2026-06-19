# -*- coding: utf-8 -*-
# Task 2: Object Pick-up — 관측 함수 (Observation Functions)
# ~/smart-shelf-robot/src/custom/rl/envs/pick/mdp/observations.py
#
# task_define.md 의 Pick-up Observation Space 명세에 따라
# 물체의 로봇 기저 좌표계 상 위치/자세, 그리퍼 상태를 관측합니다.

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import RigidObject, Articulation
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import FrameTransformer
from isaaclab.utils.math import subtract_frame_transforms

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def object_position_in_robot_root_frame(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
) -> torch.Tensor:
    """로봇 기저 좌표계 기준 대상 물체의 3D 위치.

    task_define.md: RealSense로 추정된 바구니 내 타겟 물체의 Pose [x, y, z]
    (로봇 좌표계 변환 적용)

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        robot_cfg: 로봇 Scene entity 설정.
        object_cfg: 대상 물체 Scene entity 설정.

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


def object_orientation_in_robot_root_frame(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
) -> torch.Tensor:
    """로봇 기저 좌표계 기준 대상 물체의 쿼터니언 자세.

    task_define.md: 타겟 물체의 Pose [q_w, q_x, q_y, q_z]

    Returns:
        (num_envs, 4) 크기의 쿼터니언 텐서.
    """
    obj: RigidObject = env.scene[object_cfg.name]
    # 월드 좌표계 쿼터니언을 그대로 반환 (로봇 기저 회전 보정은 후속 처리 가능)
    return obj.data.root_quat_w


def gripper_state(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """RH-P12-RN-A 그리퍼의 현재 상태: 개구량 + 의사 토크.

    task_define.md: 그리퍼의 현재 손가락 개구량(Opening Width) 및
    가해지는 의사 토크 정보를 관측 공간에 포함.

    Returns:
        (num_envs, 2) 크기의 텐서 — [개구량, 힘/토크 추정치].
    """
    robot: Articulation = env.scene[robot_cfg.name]

    if hasattr(env.cfg, "gripper_joint_names"):
        gripper_joint_ids, _ = robot.find_joints(env.cfg.gripper_joint_names)
        # 그리퍼 관절 위치 (개구량)
        opening_width = robot.data.joint_pos[:, gripper_joint_ids[0]].unsqueeze(-1)
        # 그리퍼 관절에 가해지는 토크 (의사 파지력 추정)
        applied_torque = robot.data.applied_torque[:, gripper_joint_ids[0]].unsqueeze(-1)
        return torch.cat([opening_width, applied_torque], dim=-1)

    # 그리퍼 설정이 없는 경우 영 벡터 반환
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
