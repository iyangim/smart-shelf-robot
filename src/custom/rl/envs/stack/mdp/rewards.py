# -*- coding: utf-8 -*-
# Task 3: Stacking — 보상 함수 (Reward Functions)
# ~/smart-shelf-robot/src/custom/rl/envs/stack/mdp/rewards.py

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import RigidObject, Articulation
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import FrameTransformer

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def object_ee_distance(
    env: ManagerBasedRLEnv,
    std: float,
    object_cfg: SceneEntityCfg = SceneEntityCfg("cube_1"),
    ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame"),
) -> torch.Tensor:
    """Reward for moving end-effector close to cube_1."""
    obj: RigidObject = env.scene[object_cfg.name]
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]

    cube_pos_w = obj.data.root_pos_w
    ee_w = ee_frame.data.target_pos_w[..., 0, :]
    distance = torch.norm(cube_pos_w - ee_w, dim=1)

    return 1 - torch.tanh(distance / std)


def cube_grasped(
    env: ManagerBasedRLEnv,
    cube_cfg: SceneEntityCfg = SceneEntityCfg("cube_1"),
    ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame"),
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    diff_threshold: float = 0.04,
) -> torch.Tensor:
    """Reward when cube_1 is grasped (close + gripper closed)."""
    cube: RigidObject = env.scene[cube_cfg.name]
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]
    robot: Articulation = env.scene[robot_cfg.name]

    cube_pos = cube.data.root_pos_w
    ee_pos = ee_frame.data.target_pos_w[:, 0, :]
    pose_diff = torch.norm(cube_pos - ee_pos, dim=1)

    if hasattr(env.cfg, "gripper_joint_names"):
        gripper_joint_ids, _ = robot.find_joints(env.cfg.gripper_joint_names)
        assert len(gripper_joint_ids) >= 2

        grasped = torch.logical_and(
            pose_diff < diff_threshold,
            torch.abs(
                robot.data.joint_pos[:, gripper_joint_ids[0]]
                - torch.tensor(env.cfg.gripper_open_val, dtype=torch.float32).to(env.device)
            ) > env.cfg.gripper_threshold,
        )
        grasped = torch.logical_and(
            grasped,
            torch.abs(
                robot.data.joint_pos[:, gripper_joint_ids[1]]
                - torch.tensor(env.cfg.gripper_open_val, dtype=torch.float32).to(env.device)
            ) > env.cfg.gripper_threshold,
        )
        return grasped.float()

    return torch.zeros(env.num_envs, device=env.device)


def object_is_lifted(
    env: ManagerBasedRLEnv,
    minimal_height: float,
    object_cfg: SceneEntityCfg = SceneEntityCfg("cube_1"),
) -> torch.Tensor:
    """Reward for lifting cube_1 above minimal height."""
    obj: RigidObject = env.scene[object_cfg.name]
    return torch.where(obj.data.root_pos_w[:, 2] > minimal_height, 1.0, 0.0)


def cubes_stacking_reward(
    env: ManagerBasedRLEnv,
    std: float,
    cube_1_cfg: SceneEntityCfg = SceneEntityCfg("cube_1"),
    cube_2_cfg: SceneEntityCfg = SceneEntityCfg("cube_2"),
) -> torch.Tensor:
    """Reward for aligning cube_1 above cube_2 in XY plane AND lowering it."""
    cube_1: RigidObject = env.scene[cube_1_cfg.name]
    cube_2: RigidObject = env.scene[cube_2_cfg.name]

    pos_diff = cube_1.data.root_pos_w - cube_2.data.root_pos_w
    xy_dist = torch.norm(pos_diff[:, :2], dim=1)

    # Only reward if cube_1 is lifted
    is_lifted = cube_1.data.root_pos_w[:, 2] > 0.05

    target_height = 0.0468
    height_proximity = 1.0 - torch.tanh(torch.abs(pos_diff[:, 2] - target_height) / 0.05)

    reward = (1 - torch.tanh(xy_dist / std)) * is_lifted.float() * (1.0 + height_proximity)
    return reward


def cube_height_alignment(
    env: ManagerBasedRLEnv,
    std: float = 0.03,
    target_height: float = 0.0468,
    cube_1_cfg: SceneEntityCfg = SceneEntityCfg("cube_1"),
    cube_2_cfg: SceneEntityCfg = SceneEntityCfg("cube_2"),
) -> torch.Tensor:
    """Reward for placing cube_1 at correct height above cube_2."""
    cube_1: RigidObject = env.scene[cube_1_cfg.name]
    cube_2: RigidObject = env.scene[cube_2_cfg.name]

    pos_diff = cube_1.data.root_pos_w - cube_2.data.root_pos_w
    height_diff = pos_diff[:, 2]

    # Reward proximity to target height
    height_error = torch.abs(height_diff - target_height)
    reward = 1 - torch.tanh(height_error / std)

    # Only reward if aligned in XY
    xy_dist = torch.norm(pos_diff[:, :2], dim=1)
    is_aligned = xy_dist < 0.08

    return reward * is_aligned.float()


def stacking_success(
    env: ManagerBasedRLEnv,
    cube_1_cfg: SceneEntityCfg = SceneEntityCfg("cube_1"),
    cube_2_cfg: SceneEntityCfg = SceneEntityCfg("cube_2"),
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    xy_threshold: float = 0.04,
    height_threshold: float = 0.005,
    height_diff: float = 0.0468,
) -> torch.Tensor:
    """Large bonus when cubes are successfully stacked."""
    cube_1: RigidObject = env.scene[cube_1_cfg.name]
    cube_2: RigidObject = env.scene[cube_2_cfg.name]
    robot: Articulation = env.scene[robot_cfg.name]

    pos_diff = cube_1.data.root_pos_w - cube_2.data.root_pos_w
    xy_dist = torch.norm(pos_diff[:, :2], dim=1)
    h_dist = torch.abs(pos_diff[:, 2] - height_diff)

    stacked = torch.logical_and(
        xy_dist < xy_threshold,
        h_dist < height_threshold
    )

    if hasattr(env.cfg, "gripper_joint_names"):
        gripper_joint_ids, _ = robot.find_joints(env.cfg.gripper_joint_names)
        assert len(gripper_joint_ids) >= 2
        gripper_open = torch.isclose(
            robot.data.joint_pos[:, gripper_joint_ids[0]],
            torch.tensor(env.cfg.gripper_open_val, dtype=torch.float32).to(env.device),
            atol=1e-3,
        )
        stacked_with_release = torch.logical_and(stacked, gripper_open)
        return stacked_with_release.float()

    return stacked.float()
