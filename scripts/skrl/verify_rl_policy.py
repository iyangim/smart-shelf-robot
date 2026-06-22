import argparse
import sys
import os
import time
import torch
import numpy as np

from isaaclab.app import AppLauncher

# Set up arguments
parser = argparse.ArgumentParser(description="Verify an RL checkpoint for health and abnormalities.")
parser.add_argument("--task", type=str, required=True, help="Task name (e.g. Doosan-Lift-Play-v0)")
parser.add_argument("--checkpoint", type=str, required=True, help="Path to checkpoint .pt file")
parser.add_argument("--num_envs", type=int, default=4, help="Number of environments to run")
parser.add_argument("--steps", type=int, default=100, help="Number of evaluation steps")
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()

# Launch simulation app
sys.argv = [sys.argv[0]] + hydra_args
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import gymnasium as gym
import skrl
from isaaclab_rl.skrl import SkrlVecEnvWrapper
from skrl.utils.runner.torch import Runner
from isaaclab_tasks.utils.hydra import hydra_task_config
from isaaclab.envs import ManagerBasedRLEnvCfg, DirectRLEnvCfg, DirectMARLEnvCfg

# Add custom path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import custom.rl.envs.reach
import custom.rl.envs.pick
import custom.rl.envs.place
import custom.rl.envs.stack
import custom.rl.envs.lift

@hydra_task_config(args_cli.task, "skrl_cfg_entry_point")
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, experiment_cfg: dict):
    env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device
    env_cfg.seed = 42

    # Create env
    env = gym.make(args_cli.task, cfg=env_cfg)
    env = SkrlVecEnvWrapper(env, ml_framework="torch")

    # Instantiate runner and agent
    experiment_cfg["trainer"]["close_environment_at_exit"] = False
    experiment_cfg["agent"]["experiment"]["write_interval"] = 0
    experiment_cfg["agent"]["experiment"]["checkpoint_interval"] = 0
    runner = Runner(env, experiment_cfg)

    print(f"[INFO] Loading checkpoint from: {args_cli.checkpoint}")
    runner.agent.load(args_cli.checkpoint)
    runner.agent.enable_training_mode(False)

    obs, _ = env.reset()
    
    # Metrics collection
    rewards_list = []
    joint_positions = []
    nans_detected = False
    frozen_arm = False
    nan_details = []

    print(f"[INFO] Starting evaluation for {args_cli.steps} steps...")
    for step in range(args_cli.steps):
        with torch.inference_mode():
            outputs = runner.agent.act(obs, None, timestep=0, timesteps=0)
            actions = outputs[-1].get("mean_actions", outputs[0])
            obs, rewards, terminated, truncated, info = env.step(actions)

            # Check for NaNs
            if torch.isnan(obs).any():
                nans_detected = True
                nan_details.append(f"Step {step}: NaN in observation")
            if torch.isnan(actions).any():
                nans_detected = True
                nan_details.append(f"Step {step}: NaN in action")
            if torch.isnan(rewards).any():
                nans_detected = True
                nan_details.append(f"Step {step}: NaN in reward")

            rewards_list.append(rewards.cpu().numpy())
            
            # Fetch joint positions directly from env scene
            try:
                robot = env.unwrapped.scene.robot
                joint_positions.append(robot.data.joint_pos.clone().cpu().numpy())
            except Exception as e:
                pass

    # Check for frozen joints (abnormal/stuck state)
    if len(joint_positions) > 0:
        joint_pos_arr = np.array(joint_positions)  # shape (steps, num_envs, num_joints)
        # Calculate standard deviation over steps for each joint in each env
        std_per_joint = np.std(joint_pos_arr, axis=0)  # shape (num_envs, num_joints)
        mean_std_per_env = np.mean(std_per_joint, axis=0) # shape (num_joints,)
        
        # Check first 6 joints (Doosan arm)
        arm_stds = mean_std_per_env[:6]
        print(f"Arm Joint Position STDs over evaluation: {arm_stds}")
        if np.all(arm_stds < 1e-3):
            frozen_arm = True

    # Check rewards
    mean_reward = np.mean(rewards_list)
    print(f"Mean reward over run: {mean_reward}")

    # Diagnosis report
    is_healthy = not nans_detected and not frozen_arm
    print("\n" + "="*50)
    print("           DIAGNOSTIC VERIFICATION REPORT")
    print("="*50)
    print(f"Task: {args_cli.task}")
    print(f"Checkpoint: {args_cli.checkpoint}")
    print(f"Status: {'HEALTHY' if is_healthy else 'ABNORMAL / FAILURE DETECTED'}")
    print("-"*50)
    print(f"NaN Detected: {nans_detected}")
    if nans_detected:
        for detail in nan_details[:5]:
            print(f"  - {detail}")
    print(f"Frozen Arm Joints Detected: {frozen_arm}")
    if frozen_arm:
        print("  - Rationale: The standard deviation of Doosan arm joints is less than 0.001 radians over 100 steps.")
        print("  - Probable causes: Physics simulation lock, model outputting zero/identity commands, or collision limits.")
    print(f"Mean Reward: {mean_reward:.4f}")
    print("="*50)

    env.close()
    
    if not is_healthy:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
    simulation_app.close()
