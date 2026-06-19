# -*- coding: utf-8 -*-
# Task 2: Object Pick-up — Gym 환경 등록
# ~/smart-shelf-robot/src/custom/rl/envs/pick/__init__.py
#
# Isaac Lab Gymnasium 인터페이스에 Pick-up 태스크 환경을 등록합니다.
# 등록 ID:
#   - Doosan-Pick-v0      : 학습용 환경 (4096 envs)
#   - Doosan-Pick-Play-v0 : 추론/시연용 환경 (50 envs)
#
# 사용 예:
#   python scripts/skrl/train.py --task=Doosan-Pick-v0 --headless
#   python scripts/skrl/play.py --task=Doosan-Pick-Play-v0

import gymnasium as gym

from . import agents

##
# Register Gym environments.
##

gym.register(
    id="Doosan-Pick-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.doosan_pick_env_cfg:DoosanPickEnvCfg",
        "skrl_cfg_entry_point": f"{agents.__name__}:doosan_pick_skrl_ppo_cfg.yaml",
    },
)

gym.register(
    id="Doosan-Pick-Play-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.doosan_pick_env_cfg:DoosanPickEnvCfg_PLAY",
        "skrl_cfg_entry_point": f"{agents.__name__}:doosan_pick_skrl_ppo_cfg.yaml",
    },
)
