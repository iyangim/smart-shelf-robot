import os
from isaaclab.app import AppLauncher

# Set up app launcher
import argparse
parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args(args=["--headless"])
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd, PhysxSchema

usd_file = "/home/iyangim/smart-shelf-robot/src/custom/rl/assets/doosan_e0509_with_gripper.usd"
print(f"Opening USD: {usd_file}")
stage = Usd.Stage.Open(usd_file)

for prim in stage.Traverse():
    if "gripper_rh_l" in prim.GetName():
        print(f"\nPrim: {prim.GetPath()}")
        print(f"  Applied schemas: {prim.GetAppliedSchemas()}")
        for prop_name in prim.GetPropertyNames():
            if "mimic" in prop_name or "reference" in prop_name:
                prop = prim.GetProperty(prop_name)
                if isinstance(prop, Usd.Relationship):
                    print(f"    Relationship: {prop_name} targets: {prop.GetTargets()}")
                else:
                    print(f"    Attribute: {prop_name} value: {prop.Get()}")

simulation_app.close()
