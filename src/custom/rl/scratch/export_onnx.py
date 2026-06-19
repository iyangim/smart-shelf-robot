import torch
import torch.nn as nn

class DoosanPolicy(nn.Module):
    def __init__(self, checkpoint_path):
        super().__init__()
        # Define architecture
        self.net = nn.Sequential(
            nn.Linear(25, 64),
            nn.ELU(),
            nn.Linear(64, 64),
            nn.ELU()
        )
        self.policy_layer = nn.Linear(64, 6)
        
        # Load state dict
        checkpoint = torch.load(checkpoint_path, map_location="cpu")
        state_dict = checkpoint["policy"]
        
        # Extract matching weights
        self.net[0].weight.data.copy_(state_dict["net_container.0.weight"])
        self.net[0].bias.data.copy_(state_dict["net_container.0.bias"])
        self.net[2].weight.data.copy_(state_dict["net_container.2.weight"])
        self.net[2].bias.data.copy_(state_dict["net_container.2.bias"])
        self.policy_layer.weight.data.copy_(state_dict["policy_layer.weight"])
        self.policy_layer.bias.data.copy_(state_dict["policy_layer.bias"])
        
        # Load preprocessor params
        mean = checkpoint["observation_preprocessor"]["running_mean"]
        variance = checkpoint["observation_preprocessor"]["running_variance"]
        self.register_buffer("mean", mean.float())
        self.register_buffer("std", torch.sqrt(variance + 1e-8).float())

    def forward(self, obs):
        # Apply preprocessor
        scaled_obs = (obs - self.mean) / self.std
        # Forward pass
        features = self.net(scaled_obs)
        action = self.policy_layer(features)
        return action

if __name__ == "__main__":
    checkpoint_path = "/home/iyangim/franka_isaaclab/logs/skrl/reach_doosan_e0509/2026-06-18_18-29-26_ppo_torch/checkpoints/best_agent.pt"
    model = DoosanPolicy(checkpoint_path)
    model.eval()
    
    # Test inference with dummy input
    dummy_input = torch.randn(1, 25)
    output = model(dummy_input)
    print("Dummy output action:", output)
    
    # Export to ONNX
    onnx_path = "/home/iyangim/smart-shelf-robot/src/custom/rl/policy.onnx"
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=["observations"],
        output_names=["actions"],
        dynamic_axes={"observations": {0: "batch_size"}, "actions": {0: "batch_size"}}
    )
    print(f"Exported ONNX model successfully to {onnx_path}")
