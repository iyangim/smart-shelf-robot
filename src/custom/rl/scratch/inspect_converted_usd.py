import os
import argparse
from isaaclab.app import AppLauncher

# add argparse arguments
parser = argparse.ArgumentParser(description="Inspect converted USD.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args(args=["--headless"])
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd, UsdPhysics

def inspect_usd(file_path):
    print(f"Opening USD file: {file_path}")
    stage = Usd.Stage.Open(file_path)
    if not stage:
        print("Failed to open stage.")
        return

    print("Listing all Physics joints:")
    for prim in stage.Traverse():
        if prim.IsA(UsdPhysics.Joint):
            print(f"Joint Prim: {prim.GetPath()} | Type: {prim.GetTypeName()}")

if __name__ == "__main__":
    usd_file = "/home/iyangim/smart-shelf-robot/src/custom/rl/assets/doosan_e0509_with_gripper.usd"
    inspect_usd(usd_file)
