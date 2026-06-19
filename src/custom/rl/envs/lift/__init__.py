# -*- coding: utf-8 -*-
# Franka Transfer Group - Task 2: Lift — Gym 환경 등록
# ~/smart-shelf-robot/src/custom/rl/envs/lift/__init__.py

import gymnasium as gym
from . import agents

gym.register(
    id="Doosan-Lift-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.doosan_lift_env_cfg:DoosanLiftEnvCfg",
        "skrl_cfg_entry_point": f"{agents.__name__}:doosan_lift_skrl_ppo_cfg.yaml",
    },
)

gym.register(
    id="Doosan-Lift-Play-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.doosan_lift_env_cfg:DoosanLiftEnvCfg_PLAY",
        "skrl_cfg_entry_point": f"{agents.__name__}:doosan_lift_skrl_ppo_cfg.yaml",
    },
)
