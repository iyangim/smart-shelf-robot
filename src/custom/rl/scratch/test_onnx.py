import torch
import torch.nn as nn
from skrl.models.torch import Model

# Let's load the checkpoint
checkpoint_path = "/home/iyangim/franka_isaaclab/logs/skrl/reach_doosan_e0509/2026-06-18_18-29-26_ppo_torch/checkpoints/best_agent.pt"
checkpoint = torch.load(checkpoint_path)

# Let's see the policy state dict keys
print("Policy state dict keys:")
for k in checkpoint["policy"].keys():
    print(k)

# Let's write a helper to load the state dict into a custom PyTorch model representing the policy network.
# According to the config:
# layers: [64, 64]
# activations: elu
# class: GaussianMixin
# It has a shared network net_container (2 layers of 64 with ELU), then policy_layer and value_layer?
# Wait! Let's check the keys in policy:
# 'log_std_parameter'
# 'net_container.0.weight', 'net_container.0.bias'
# 'net_container.2.weight', 'net_container.2.bias'
# 'policy_layer.weight', 'policy_layer.bias'
# 'value_layer.weight', 'value_layer.bias'
