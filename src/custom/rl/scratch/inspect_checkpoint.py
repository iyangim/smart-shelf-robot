import torch

checkpoint_path = "/home/iyangim/franka_isaaclab/logs/skrl/reach_doosan_e0509/2026-06-18_18-29-26_ppo_torch/checkpoints/best_agent.pt"
checkpoint = torch.load(checkpoint_path)
print("Keys in checkpoint:", checkpoint.keys())
if "policy" in checkpoint:
    print("Policy state dict keys:", checkpoint["policy"].keys())
