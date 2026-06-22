import os
from isaaclab.app import AppLauncher

# Set up app launcher
import argparse
parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args(args=["--headless"])
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd, PhysxSchema, Sdf

usd_file = "/home/iyangim/smart-shelf-robot/src/custom/rl/assets/doosan_e0509_with_gripper.usd"
print(f"Opening USD: {usd_file}")
stage = Usd.Stage.Open(usd_file)

l1_prim = stage.GetPrimAtPath("/e0509_with_gripper/joints/gripper_rh_l1")
l2_prim = stage.GetPrimAtPath("/e0509_with_gripper/joints/gripper_rh_l2")

if l1_prim.IsValid():
    mimic_api = PhysxSchema.PhysxMimicJointAPI(l1_prim, "rotX")
    rel = mimic_api.GetReferenceJointRel()
    rel.SetTargets([Sdf.Path("/e0509_with_gripper/joints/gripper_rh_r1")])
    print(f"Set l1 reference joint to gripper_rh_r1: {rel.GetTargets()}")

if l2_prim.IsValid():
    mimic_api = PhysxSchema.PhysxMimicJointAPI(l2_prim, "rotX")
    rel = mimic_api.GetReferenceJointRel()
    rel.SetTargets([Sdf.Path("/e0509_with_gripper/joints/gripper_rh_r2")])
    print(f"Set l2 reference joint to gripper_rh_r2: {rel.GetTargets()}")

stage.GetRootLayer().Save()
print("Saved USD stage.")

simulation_app.close()
