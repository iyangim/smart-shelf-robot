# -*- coding: utf-8 -*-
# Task 4: Shelf Placing & Alignment — 종료 조건 함수 (Termination Functions)
# ~/smart-shelf-robot/src/custom/rl/envs/place/mdp/terminations.py
#
# Place 태스크의 에피소드 종료 조건을 정의합니다.
# - 물체가 매대/지면 아래로 낙하한 경우 (실패)
# - 물체가 성공적으로 배치된 경우 (성공)

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import RigidObject, Articulation
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import FrameTransformer

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def object_dropped(
    env: ManagerBasedRLEnv,
    minimum_height: float = -0.05,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
) -> torch.Tensor:
    """물체가 지면 아래로 낙하했는지 판별.

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        minimum_height: 낙하 판정 z 좌표 임계치 (m).
        object_cfg: 대상 물체 설정.

    Returns:
        (num_envs,) 크기의 불리언 텐서.
    """
    obj: RigidObject = env.scene[object_cfg.name]
    return obj.data.root_pos_w[:, 2] < minimum_height


def object_placed_success(
    env: ManagerBasedRLEnv,
    placement_threshold: float = 0.03,
    retreat_distance: float = 0.08,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
    slot_cfg: SceneEntityCfg = SceneEntityCfg("slot"),
    ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame"),
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """물체가 매대 슬롯에 성공적으로 배치되었는지 판별.

    성공 판정 조건:
    1. 물체가 슬롯 중심에 placement_threshold 이내
    2. 그리퍼가 열린 상태
    3. EE가 물체에서 retreat_distance 이상 후퇴

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        placement_threshold: 물체-슬롯 최대 허용 거리 (m).
        retreat_distance: EE-물체 최소 후퇴 거리 (m).
        object_cfg: 물체 설정.
        slot_cfg: 슬롯 설정.
        ee_frame_cfg: EE 프레임 설정.
        robot_cfg: 로봇 설정.

    Returns:
        (num_envs,) 크기의 불리언 텐서.
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

    # 조건 3: EE가 물체에서 후퇴했는지
    ee_pos = ee_frame.data.target_pos_w[:, 0, :]
    ee_obj_dist = torch.norm(ee_pos - obj.data.root_pos_w, dim=1)
    retreated = ee_obj_dist > retreat_distance

    return torch.logical_and(placed, torch.logical_and(gripper_open, retreated))


def collision_detected(
    env: ManagerBasedRLEnv,
    force_threshold: float = 50.0,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """매대 구조물과의 과도한 충돌 감지.

    로봇 엔드이펙터에 가해지는 외력이 force_threshold 를 초과하면
    충돌로 판단하여 에피소드를 종료합니다.

    ※ Isaac Lab의 물리 엔진 접촉력 센서(ContactSensor)가
      활성화되어 있을 때만 정확하게 작동합니다.
      센서가 없는 경우 False(미종료)를 반환합니다.

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        force_threshold: 충돌 판정 힘 임계치 (N).
        robot_cfg: 로봇 설정.

    Returns:
        (num_envs,) 크기의 불리언 텐서.
    """
    # ContactSensor 기반 충돌 감지
    # 접촉력 센서가 Scene에 등록되어 있으면 사용, 없으면 비종료 반환
    if "contact_sensor" in env.scene:
        contact_sensor = env.scene["contact_sensor"]
        # 접촉력 크기
        contact_forces = contact_sensor.data.net_forces_w  # (num_envs, num_bodies, 3)
        max_force = torch.norm(contact_forces, dim=-1).max(dim=-1).values
        return max_force > force_threshold

    # 센서가 없는 경우 충돌 미감지 (에피소드 계속)
    return torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
