import onnxruntime as ort
import numpy as np
import torch

checkpoint_path = "/home/iyangim/franka_isaaclab/logs/skrl/reach_doosan_e0509/2026-06-18_18-29-26_ppo_torch/checkpoints/best_agent.pt"
checkpoint = torch.load(checkpoint_path, map_location="cpu")

mean = checkpoint["observation_preprocessor"]["running_mean"].numpy()
std = np.sqrt(checkpoint["observation_preprocessor"]["running_variance"].numpy() + 1e-8)

onnx_path = "/home/iyangim/smart-shelf-robot/src/custom/rl/policy.onnx"
session = ort.InferenceSession(onnx_path)

# Test with mean (should result in zero input to network)
obs_mean = mean.reshape(1, 25).astype(np.float32)
outputs_mean = session.run(None, {"observations": obs_mean})
print("Output action at mean:", outputs_mean[0])

# Test with mean + 0.1 * std (should result in 0.1 input to network)
obs_perturbed = (mean + 0.1 * std).reshape(1, 25).astype(np.float32)
outputs_perturbed = session.run(None, {"observations": obs_perturbed})
print("Output action at perturbed:", outputs_perturbed[0])
