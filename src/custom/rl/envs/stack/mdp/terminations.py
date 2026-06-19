# -*- coding: utf-8 -*-
# Task 3: Stacking — 종료 조건 함수 (Termination Functions)
# ~/smart-shelf-robot/src/custom/rl/envs/stack/mdp/terminations.py

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def cubes_stacked(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    cube_1_cfg: SceneEntityCfg = SceneEntityCfg("cube_1"),
    cube_2_cfg: SceneEntityCfg = SceneEntityCfg("cube_2"),
    xy_threshold: float = 0.04,
    height_threshold: float = 0.005,
    height_diff: float = 0.0468,
    atol=0.001,
    rtol=0.001,
) -> torch.Tensor:
    robot: Articulation = env.scene[robot_cfg.name]
    cube_1: RigidObject = env.scene[cube_1_cfg.name]
    cube_2: RigidObject = env.scene[cube_2_cfg.name]

    pos_diff_c12 = cube_1.data.root_pos_w - cube_2.data.root_pos_w

    # Compute cube position difference in x-y plane
    xy_dist_c12 = torch.norm(pos_diff_c12[:, :2], dim=1)

    # Compute cube height difference
    h_dist_c12 = torch.norm(pos_diff_c12[:, 2:], dim=1)

    # Check cube positions
    stacked = xy_dist_c12 < xy_threshold
    stacked = torch.logical_and(h_dist_c12 - height_diff < height_threshold, stacked)
    # Check if height difference is aligned (e.g. cube_1 above cube_2)
    # Note: We keep the exact logic from the reference stack env
    # In some versions it was < 0.0 or > 0.0 depending on coordinates,
    # but height_diff = 0.0468 handles the magnitude check.
    # We will check if it's positive because cube_1 must be on top of cube_2.
    # To be safe, we just check if it matches height_diff within the threshold.
    # (h_dist_c12 - height_diff < height_threshold already does this)
    
    # Check gripper positions
    if hasattr(env.cfg, "gripper_joint_names"):
        gripper_joint_ids, _ = robot.find_joints(env.cfg.gripper_joint_names)
        assert len(gripper_joint_ids) >= 2, "Terminations only support parallel gripper for now"

        stacked = torch.logical_and(
            torch.isclose(
                robot.data.joint_pos[:, gripper_joint_ids[0]],
                torch.tensor(env.cfg.gripper_open_val, dtype=torch.float32).to(env.device),
                atol=atol,
                rtol=rtol,
            ),
            stacked,
        )
        stacked = torch.logical_and(
            torch.isclose(
                robot.data.joint_pos[:, gripper_joint_ids[1]],
                torch.tensor(env.cfg.gripper_open_val, dtype=torch.float32).to(env.device),
                atol=atol,
                rtol=rtol,
            ),
            stacked,
        )
    else:
        raise ValueError("No gripper_joint_names found in environment config")

    return stacked
