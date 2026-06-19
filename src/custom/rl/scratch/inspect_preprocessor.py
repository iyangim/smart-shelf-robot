import torch

checkpoint_path = "/home/iyangim/franka_isaaclab/logs/skrl/reach_doosan_e0509/2026-06-18_18-29-26_ppo_torch/checkpoints/best_agent.pt"
checkpoint = torch.load(checkpoint_path)
preprocessor = checkpoint["observation_preprocessor"]
print("Preprocessor state dict:")
for k, v in preprocessor.items():
    print(k, v)
