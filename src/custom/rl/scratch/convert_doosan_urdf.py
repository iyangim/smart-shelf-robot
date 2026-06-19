import os
import argparse
from isaaclab.app import AppLauncher

# add argparse arguments
parser = argparse.ArgumentParser(description="Convert Doosan URDF to USD.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args(args=["--headless"])
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from isaaclab.sim.converters.urdf_converter import UrdfConverter
from isaaclab.sim.converters.urdf_converter_cfg import UrdfConverterCfg

# Make output folder
os.makedirs("/home/iyangim/smart-shelf-robot/src/custom/rl/assets", exist_ok=True)

# Configure converter
cfg = UrdfConverterCfg(
    asset_path="/home/iyangim/smart-shelf-robot/src/external/e0509_gripper_description/config/curobo/e0509_gripper.urdf",
    usd_dir="/home/iyangim/smart-shelf-robot/src/custom/rl/assets",
    usd_file_name="doosan_e0509_with_gripper.usd",
    force_usd_conversion=True,
    fix_base=True,
    merge_fixed_joints=False,
    convert_mimic_joints_to_normal_joints=True,
)
cfg.joint_drive.gains.stiffness = 0.0
cfg.joint_drive.gains.damping = 0.0


print("Starting URDF conversion...")
converter = UrdfConverter(cfg)
print("Conversion complete!")
simulation_app.close()
