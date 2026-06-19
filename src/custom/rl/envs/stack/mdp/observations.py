# -*- coding: utf-8 -*-
# Task 3: Stacking — 관측 함수 (Observation Functions)
# ~/smart-shelf-robot/src/custom/rl/envs/stack/mdp/observations.py

from __future__ import annotations

import torch
from typing import TYPE_CHECKING, Literal

import isaaclab.utils.math as math_utils
from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import FrameTransformer

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def cube_positions_in_world_frame(
    env: ManagerBasedRLEnv,
    cube_1_cfg: SceneEntityCfg = SceneEntityCfg("cube_1"),
    cube_2_cfg: SceneEntityCfg = SceneEntityCfg("cube_2"),
) -> torch.Tensor:
    cube_1: RigidObject = env.scene[cube_1_cfg.name]
    cube_2: RigidObject = env.scene[cube_2_cfg.name]
    return torch.cat((cube_1.data.root_pos_w - env.scene.env_origins, cube_2.data.root_pos_w - env.scene.env_origins), dim=1)


def cube_orientations_in_world_frame(
    env: ManagerBasedRLEnv,
    cube_1_cfg: SceneEntityCfg = SceneEntityCfg("cube_1"),
    cube_2_cfg: SceneEntityCfg = SceneEntityCfg("cube_2"),
) -> torch.Tensor:
    cube_1: RigidObject = env.scene[cube_1_cfg.name]
    cube_2: RigidObject = env.scene[cube_2_cfg.name]
    return torch.cat((cube_1.data.root_quat_w, cube_2.data.root_quat_w), dim=1)


def object_obs(
    env: ManagerBasedRLEnv,
    cube_1_cfg: SceneEntityCfg = SceneEntityCfg("cube_1"),
    cube_2_cfg: SceneEntityCfg = SceneEntityCfg("cube_2"),
    ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame"),
) -> torch.Tensor:
    cube_1: RigidObject = env.scene[cube_1_cfg.name]
    cube_2: RigidObject = env.scene[cube_2_cfg.name]
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]

    cube_1_pos_w = cube_1.data.root_pos_w
    cube_1_quat_w = cube_1.data.root_quat_w

    cube_2_pos_w = cube_2.data.root_pos_w
    cube_2_quat_w = cube_2.data.root_quat_w

    ee_pos_w = ee_frame.data.target_pos_w[:, 0, :]
    gripper_to_cube_1 = cube_1_pos_w - ee_pos_w
    gripper_to_cube_2 = cube_2_pos_w - ee_pos_w

    cube_1_to_2 = cube_1_pos_w - cube_2_pos_w

    return torch.cat(
        (
            cube_1_pos_w - env.scene.env_origins,
            cube_1_quat_w,
            cube_2_pos_w - env.scene.env_origins,
            cube_2_quat_w,
            gripper_to_cube_1,
            gripper_to_cube_2,
            cube_1_to_2,
        ),
        dim=1,
    )


def ee_frame_pos(env: ManagerBasedRLEnv, ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame")) -> torch.Tensor:
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]
    return ee_frame.data.target_pos_w[:, 0, :] - env.scene.env_origins[:, 0:3]


def ee_frame_quat(env: ManagerBasedRLEnv, ee_frame_cfg: SceneEntityCfg = SceneEntityCfg("ee_frame")) -> torch.Tensor:
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]
    return ee_frame.data.target_quat_w[:, 0, :]


def gripper_pos(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    robot: Articulation = env.scene[robot_cfg.name]

    if hasattr(env.cfg, "gripper_joint_names"):
        gripper_joint_ids, _ = robot.find_joints(env.cfg.gripper_joint_names)
        assert len(gripper_joint_ids) >= 2, "Observation gripper_pos requires at least 2 gripper joints"
        finger_joint_1 = robot.data.joint_pos[:, gripper_joint_ids[0]].clone().unsqueeze(1)
        finger_joint_2 = robot.data.joint_pos[:, gripper_joint_ids[1]].clone().unsqueeze(1)
        return torch.cat((finger_joint_1, finger_joint_2), dim=1)
    else:
        raise NotImplementedError("[Error] Cannot find gripper_joint_names in the environment config")


def object_grasped(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg,
    ee_frame_cfg: SceneEntityCfg,
    object_cfg: SceneEntityCfg,
    diff_threshold: float = 0.06,
) -> torch.Tensor:
    robot: Articulation = env.scene[robot_cfg.name]
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]
    obj: RigidObject = env.scene[object_cfg.name]

    object_pos = obj.data.root_pos_w
    end_effector_pos = ee_frame.data.target_pos_w[:, 0, :]
    pose_diff = torch.linalg.vector_norm(object_pos - end_effector_pos, dim=1)

    grasped = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)

    if hasattr(env.cfg, "gripper_joint_names"):
        gripper_joint_ids, _ = robot.find_joints(env.cfg.gripper_joint_names)
        assert len(gripper_joint_ids) >= 2

        grasped = torch.logical_and(
            pose_diff < diff_threshold,
            torch.abs(
                robot.data.joint_pos[:, gripper_joint_ids[0]]
                - torch.tensor(env.cfg.gripper_open_val, dtype=torch.float32).to(env.device)
            )
            > env.cfg.gripper_threshold,
        )
        grasped = torch.logical_and(
            grasped,
            torch.abs(
                robot.data.joint_pos[:, gripper_joint_ids[1]]
                - torch.tensor(env.cfg.gripper_open_val, dtype=torch.float32).to(env.device)
            )
            > env.cfg.gripper_threshold,
        )

    return grasped


def object_stacked(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg,
    upper_object_cfg: SceneEntityCfg,
    lower_object_cfg: SceneEntityCfg,
    xy_threshold: float = 0.05,
    height_threshold: float = 0.005,
    height_diff: float = 0.0468,
) -> torch.Tensor:
    robot: Articulation = env.scene[robot_cfg.name]
    upper_object: RigidObject = env.scene[upper_object_cfg.name]
    lower_object: RigidObject = env.scene[lower_object_cfg.name]

    pos_diff = upper_object.data.root_pos_w - lower_object.data.root_pos_w
    height_dist = torch.linalg.vector_norm(pos_diff[:, 2:], dim=1)
    xy_dist = torch.linalg.vector_norm(pos_diff[:, :2], dim=1)

    stacked = torch.logical_and(xy_dist < xy_threshold, (height_dist - height_diff) < height_threshold)

    if hasattr(env.cfg, "gripper_joint_names"):
        gripper_joint_ids, _ = robot.find_joints(env.cfg.gripper_joint_names)
        assert len(gripper_joint_ids) >= 2
        stacked = torch.logical_and(
            torch.isclose(
                robot.data.joint_pos[:, gripper_joint_ids[0]],
                torch.tensor(env.cfg.gripper_open_val, dtype=torch.float32).to(env.device),
                atol=1e-3,
                rtol=1e-3,
            ),
            stacked,
        )
        stacked = torch.logical_and(
            torch.isclose(
                robot.data.joint_pos[:, gripper_joint_ids[1]],
                torch.tensor(env.cfg.gripper_open_val, dtype=torch.float32).to(env.device),
                atol=1e-3,
                rtol=1e-3,
            ),
            stacked,
        )
    else:
        raise ValueError("No gripper_joint_names found in environment config")

    return stacked
