import os
from isaaclab.app import AppLauncher

# Set up app launcher
import argparse
parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args(args=["--headless"])
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd, UsdPhysics, Gf

usd_file = "/home/iyangim/smart-shelf-robot/src/custom/rl/assets/doosan_e0509_with_gripper.usd"
print(f"Opening USD: {usd_file}")
stage = Usd.Stage.Open(usd_file)

for prim in stage.Traverse():
    if prim.IsA(UsdPhysics.RevoluteJoint):
        joint = UsdPhysics.RevoluteJoint(prim)
        name = prim.GetName()
        print(f"Revolute Joint: {prim.GetPath()}")
        
        # Check limit attributes
        min_attr = joint.GetLowerLimitAttr()
        max_attr = joint.GetUpperLimitAttr()
        print(f"  Lower limit: {min_attr.Get() if min_attr.HasValue() else 'NOT SET'}")
        print(f"  Upper limit: {max_attr.Get() if max_attr.HasValue() else 'NOT SET'}")
        
        # Check if mimic joint
        if "gripper_rh_l" in name:
            print(f"  -> Setting limits to [0.0, 63.1] (or appropriate values) for {name}")
            joint.CreateLowerLimitAttr().Set(0.0)
            joint.CreateUpperLimitAttr().Set(63.1) # 1.101 in degrees is ~63.1

# Save stage
stage.GetRootLayer().Save()
print("Saved USD stage.")

simulation_app.close()
