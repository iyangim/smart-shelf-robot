# -*- coding: utf-8 -*-
# Task 3: Object Stacking — Gym 환경 등록
# ~/smart-shelf-robot/src/custom/rl/envs/stack/__init__.py

import gymnasium as gym
from . import agents

gym.register(
    id="Doosan-Stack-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.doosan_stack_env_cfg:DoosanCubeStackEnvCfg",
        "skrl_cfg_entry_point": f"{agents.__name__}:doosan_stack_skrl_ppo_cfg.yaml",
    },
)

gym.register(
    id="Doosan-Stack-Play-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.doosan_stack_env_cfg:DoosanCubeStackEnvCfg_PLAY",
        "skrl_cfg_entry_point": f"{agents.__name__}:doosan_stack_skrl_ppo_cfg.yaml",
    },
)
