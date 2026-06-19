# -*- coding: utf-8 -*-
# Task 2: Object Pick-up — 종료 조건 함수 (Termination Functions)
# ~/smart-shelf-robot/src/custom/rl/envs/pick/mdp/terminations.py
#
# Pick-up 태스크의 에피소드 종료 조건을 정의합니다.
# - 물체가 바구니/테이블 아래로 낙하한 경우 (실패)
# - 물체가 성공적으로 들어올려진 경우 (성공)

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import RigidObject
from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def object_dropped(
    env: ManagerBasedRLEnv,
    minimum_height: float = -0.05,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
) -> torch.Tensor:
    """물체가 지면 아래로 낙하했는지 판별.

    물체의 z 좌표가 minimum_height 아래로 떨어지면 에피소드를 종료합니다.
    바구니에서 물체가 밖으로 떨어진 실패 상황을 포착합니다.

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        minimum_height: 낙하 판정 z 좌표 임계치 (m).
        object_cfg: 대상 물체 설정.

    Returns:
        (num_envs,) 크기의 불리언 텐서.
    """
    obj: RigidObject = env.scene[object_cfg.name]
    return obj.data.root_pos_w[:, 2] < minimum_height


def object_lifted_success(
    env: ManagerBasedRLEnv,
    success_height: float = 0.15,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
) -> torch.Tensor:
    """물체가 성공적으로 충분한 높이까지 들어올려졌는지 판별.

    물체의 z 좌표가 success_height 를 초과하면 에피소드를 성공 종료합니다.
    파지 후 들어올리기(Lift) 단계가 완료된 상태를 의미합니다.

    Args:
        env: ManagerBasedRLEnv 환경 인스턴스.
        success_height: 성공 판정 z 좌표 임계치 (m).
        object_cfg: 대상 물체 설정.

    Returns:
        (num_envs,) 크기의 불리언 텐서.
    """
    obj: RigidObject = env.scene[object_cfg.name]
    return obj.data.root_pos_w[:, 2] > success_height
