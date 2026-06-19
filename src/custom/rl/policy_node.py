import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32MultiArray
import numpy as np
import os

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import onnxruntime as ort
    HAS_ORT = True
except ImportError:
    HAS_ORT = False


class DoosanPolicyPyTorch(nn.Module):
    """PyTorch implementation of the trained Doosan E0509 Reach Policy."""
    def __init__(self, checkpoint_path):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(25, 64),
            nn.ELU(),
            nn.Linear(64, 64),
            nn.ELU()
        )
        self.policy_layer = nn.Linear(64, 6)
        
        checkpoint = torch.load(checkpoint_path, map_location="cpu")
        state_dict = checkpoint["policy"]
        
        self.net[0].weight.data.copy_(state_dict["net_container.0.weight"])
        self.net[0].bias.data.copy_(state_dict["net_container.0.bias"])
        self.net[2].weight.data.copy_(state_dict["net_container.2.weight"])
        self.net[2].bias.data.copy_(state_dict["net_container.2.bias"])
        self.policy_layer.weight.data.copy_(state_dict["policy_layer.weight"])
        self.policy_layer.bias.data.copy_(state_dict["policy_layer.bias"])
        
        # Preprocessor buffers
        mean = checkpoint["observation_preprocessor"]["running_mean"]
        variance = checkpoint["observation_preprocessor"]["running_variance"]
        self.register_buffer("mean", mean.float())
        self.register_buffer("std", torch.sqrt(variance + 1e-8).float())

    def forward(self, obs):
        scaled_obs = (obs - self.mean) / self.std
        features = self.net(scaled_obs)
        action = self.policy_layer(features)
        return action


class PolicyNode(Node):
    def __init__(self):
        super().__init__('policy_node')

        # Declare parameters for model loading
        self.declare_parameter('model_type', 'pytorch')  # 'pytorch' or 'onnx'
        # Default path to policy files
        self.declare_parameter('pytorch_model_path', '/home/iyangim/franka_isaaclab/logs/skrl/reach_doosan_e0509/2026-06-18_18-29-26_ppo_torch/checkpoints/best_agent.pt')
        self.declare_parameter('onnx_model_path', '/home/iyangim/smart-shelf-robot/src/custom/rl/policy.onnx')

        self.model_type = self.get_parameter('model_type').get_parameter_value().string_value
        self.pytorch_model_path = self.get_parameter('pytorch_model_path').get_parameter_value().string_value
        self.onnx_model_path = self.get_parameter('onnx_model_path').get_parameter_value().string_value

        # Subscribers
        self.sub_object_pose = self.create_subscription(
            PoseStamped, '/object_pose', self.object_pose_callback, 10)
        self.sub_joint_states = self.create_subscription(
            JointState, '/joint_states', self.joint_states_callback, 10)

        # Publishers
        self.pub_action = self.create_publisher(
            Float32MultiArray, '/policy/action', 10)
        self.pub_joint_targets = self.create_publisher(
            JointState, '/policy/joint_targets', 10)

        # Joint configurations
        self.joint_names = ["joint_1", "joint_2", "joint_3", "joint_4", "joint_5", "joint_6"]
        self.default_joint_pos = np.array([0.0, 0.0, 1.57, 0.0, 1.57, 0.0], dtype=np.float32)
        
        # State variables
        self.object_pose = None
        self.current_joint_positions = np.zeros(6, dtype=np.float32)
        self.current_joint_velocities = np.zeros(6, dtype=np.float32)
        self.last_action = np.zeros(6, dtype=np.float32)
        
        # Inference Timer (10Hz)
        self.timer = self.create_timer(0.1, self.inference_callback)
        
        self.policy = None
        self._load_policy()

    def _load_policy(self):
        if self.model_type == 'pytorch':
            if not HAS_TORCH:
                self.get_logger().error("PyTorch is not installed. Trying ONNX...")
                self.model_type = 'onnx'
            else:
                self.get_logger().info(f"Loading PyTorch model from {self.pytorch_model_path}...")
                try:
                    self.policy = DoosanPolicyPyTorch(self.pytorch_model_path)
                    self.policy.eval()
                    self.get_logger().info("PyTorch model loaded successfully.")
                except Exception as e:
                    self.get_logger().error(f"Failed to load PyTorch model: {e}")
                    
        if self.model_type == 'onnx':
            if not HAS_ORT:
                self.get_logger().error("ONNX Runtime is not installed. Cannot load policy.")
            else:
                self.get_logger().info(f"Loading ONNX model from {self.onnx_model_path}...")
                try:
                    self.policy = ort.InferenceSession(self.onnx_model_path)
                    self.get_logger().info("ONNX model loaded successfully.")
                except Exception as e:
                    self.get_logger().error(f"Failed to load ONNX model: {e}")

    def object_pose_callback(self, msg):
        self.object_pose = msg

    def joint_states_callback(self, msg):
        # Match joint positions and velocities by name to ensure safety
        pos_dict = {}
        vel_dict = {}
        for name, pos, *vel in zip(msg.name, msg.position, msg.velocity):
            pos_dict[name] = pos
            if vel:
                vel_dict[name] = vel[0]
                
        for i, name in enumerate(self.joint_names):
            if name in pos_dict:
                self.current_joint_positions[i] = pos_dict[name]
            if name in vel_dict:
                self.current_joint_velocities[i] = vel_dict[name]

    def inference_callback(self):
        if self.object_pose is None or self.policy is None:
            return
            
        obs = self._get_observation()
        action = self._infer(obs)
        if action is not None:
            self.last_action = action
            # 1. Publish raw action vector
            action_msg = Float32MultiArray()
            action_msg.data = action.tolist()
            self.pub_action.publish(action_msg)
            
            # 2. Compute absolute joint target and publish JointState
            # target = default + action * scale (scale = 0.5)
            target_pos = self.default_joint_pos + action * 0.5
            
            target_msg = JointState()
            target_msg.header.stamp = self.get_clock().now().to_msg()
            target_msg.name = self.joint_names
            target_msg.position = target_pos.tolist()
            self.pub_joint_targets.publish(target_msg)

    def _get_observation(self):
        # 1. joint_pos_rel (6)
        joint_pos_rel = self.current_joint_positions - self.default_joint_pos
        # 2. joint_vel_rel (6)
        joint_vel_rel = self.current_joint_velocities
        # 3. pose_command (7) - target pose relative to robot base
        # Convert ROS w,x,y,z quaternion to standard Isaac Lab order [w, x, y, z]
        target_pos = np.array([
            self.object_pose.pose.position.x,
            self.object_pose.pose.position.y,
            self.object_pose.pose.position.z
        ], dtype=np.float32)
        
        target_rot = np.array([
            self.object_pose.pose.orientation.w,
            self.object_pose.pose.orientation.x,
            self.object_pose.pose.orientation.y,
            self.object_pose.pose.orientation.z
        ], dtype=np.float32)
        
        # 4. last_action (6)
        last_action = self.last_action
        
        # Concatenate observation terms
        obs = np.concatenate([joint_pos_rel, joint_vel_rel, target_pos, target_rot, last_action]).astype(np.float32)
        return obs

    def _infer(self, obs):
        if self.model_type == 'pytorch' and HAS_TORCH:
            with torch.no_grad():
                obs_tensor = torch.from_numpy(obs).unsqueeze(0)
                action_tensor = self.policy(obs_tensor)
                return action_tensor.squeeze(0).numpy()
        elif self.model_type == 'onnx' and HAS_ORT:
            obs_batch = obs.reshape(1, 25)
            outputs = self.policy.run(None, {"observations": obs_batch})
            return outputs[0].squeeze(0)
        return None


def main(args=None):
    rclpy.init(args=args)
    node = PolicyNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
