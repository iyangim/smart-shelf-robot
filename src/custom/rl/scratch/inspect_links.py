import os
import argparse
from isaaclab.app import AppLauncher

# add argparse arguments
parser = argparse.ArgumentParser(description="Inspect links and joints of converted USD.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args(args=["--headless"])
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd, UsdGeom, UsdPhysics

usd_file = "/home/iyangim/smart-shelf-robot/src/custom/rl/assets/doosan_e0509_with_gripper.usd"
print(f"Opening USD: {usd_file}")
stage = Usd.Stage.Open(usd_file)

print("\n--- Articulation Joints ---")
for prim in stage.Traverse():
    if prim.IsA(UsdPhysics.Joint):
        print(f"Joint: {prim.GetPath()}")

print("\n--- Xforms/Prims (potential links) ---")
for prim in stage.Traverse():
    if prim.IsA(UsdGeom.Xform) or prim.IsA(UsdGeom.Scope):
        name = prim.GetName()
        if "gripper" in name or "link" in name:
            print(f"Geom/Xform Prim: {prim.GetPath()} ({prim.GetTypeName()})")

simulation_app.close()
