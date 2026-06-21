# -*- coding: utf-8 -*-
# Doosan E0509 - Task 1: Reach — Gym 환경 등록
# ~/smart-shelf-robot/src/custom/rl/envs/reach/__init__.py

import gymnasium as gym
from . import agents

gym.register(
    id="Doosan-Reach-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.doosan_reach_env_cfg:DoosanReachEnvCfg",
        "skrl_cfg_entry_point": f"{agents.__name__}:doosan_reach_skrl_ppo_cfg.yaml",
    },
)

gym.register(
    id="Doosan-Reach-Play-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.doosan_reach_env_cfg:DoosanReachEnvCfg_PLAY",
        "skrl_cfg_entry_point": f"{agents.__name__}:doosan_reach_skrl_ppo_cfg.yaml",
    },
)
