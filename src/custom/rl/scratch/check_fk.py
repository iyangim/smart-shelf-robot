import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Check FK of Doosan.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args(args=["--headless"])
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from franka_isaaclab.assets.robots.doosan import DOOSAN_E0509_CFG

def main():
    # Setup scene
    sim_cfg = sim_utils.SimulationCfg(device="cuda:0")
    sim = sim_utils.SimulationContext(sim_cfg)
    
    # Spawn robot
    robot_cfg = DOOSAN_E0509_CFG.replace(prim_path="/World/Robot")
    robot = Articulation(robot_cfg)
    
    sim.reset()
    sim.step()
    
    # Get body index of link_6
    link_6_idx = robot.find_bodies("link_6")[0]
    print(f"link_6 body index: {link_6_idx}")
    
    # Set joints to zero
    zero_pos = torch.zeros((1, robot.num_joints), device="cuda:0")
    robot.set_joint_position_target(zero_pos)
    robot.write_joint_state_to_sim(zero_pos, torch.zeros_like(zero_pos))
    sim.step()
    
    # Print link_6 pose
    pos = robot.data.body_pos_w[:, link_6_idx]
    quat = robot.data.body_quat_w[:, link_6_idx]
    print(f"Pose at [0,0,0,0,0,0]: pos={pos.cpu().numpy()}, quat={quat.cpu().numpy()}")
    
    # Set joints to [0, 0, 1.57, 0, 1.57, 0] (from apply_doosan.md Step 2)
    pos_step2 = torch.tensor([[0.0, 0.0, 1.5708, 0.0, 1.5708, 0.0]], device="cuda:0")
    robot.set_joint_position_target(pos_step2)
    robot.write_joint_state_to_sim(pos_step2, torch.zeros_like(zero_pos))
    sim.step()
    pos = robot.data.body_pos_w[:, link_6_idx]
    quat = robot.data.body_quat_w[:, link_6_idx]
    print(f"Pose at [0, 0, 1.5708, 0, 1.5708, 0]: pos={pos.cpu().numpy()}, quat={quat.cpu().numpy()}")

    # Set joints to [0, -0.8, 1.57, 0, 0.8, 0] (our home pose)
    pos_our = torch.tensor([[0.0, -0.8, 1.5708, 0.0, 0.8, 0.0]], device="cuda:0")
    robot.set_joint_position_target(pos_our)
    robot.write_joint_state_to_sim(pos_our, torch.zeros_like(zero_pos))
    sim.step()
    pos = robot.data.body_pos_w[:, link_6_idx]
    quat = robot.data.body_quat_w[:, link_6_idx]
    print(f"Pose at [0, -0.8, 1.5708, 0, 0.8, 0]: pos={pos.cpu().numpy()}, quat={quat.cpu().numpy()}")

if __name__ == "__main__":
    main()
    simulation_app.close()
