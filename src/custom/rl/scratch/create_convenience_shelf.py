import os
import argparse
import shutil
from isaaclab.app import AppLauncher

# Set up argument parser
parser = argparse.ArgumentParser(description="Create convenience shelf USD from shelf_workspace_v2.usd")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args(args=["--headless"])

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd

def create_shelf():
    src_path = "src/custom/rl/assets/shelf_workspace_v2.usd"
    dst_path = "src/custom/rl/assets/convenience_shelf.usd"
    
    print(f"Copying {src_path} to {dst_path}...")
    shutil.copyfile(src_path, dst_path)
    
    print(f"Opening stage: {dst_path}")
    stage = Usd.Stage.Open(dst_path)
    if not stage:
        print("Failed to open stage")
        return
        
    print("Removing robot and environment prims from convenience_shelf...")
    prims_to_remove = [
        "/World/Robot",
        "/World/defaultGroundPlane",
        "/physicsScene",
        "/base",
        "/Viewport_Measure"
    ]
    
    for path in prims_to_remove:
        prim = stage.GetPrimAtPath(path)
        if prim.IsValid():
            stage.RemovePrim(path)
            print(f"Removed {path}")
        else:
            print(f"Prim {path} not found")
            
    print("Saving convenience_shelf stage...")
    stage.Save()
    print("Generation complete!")

if __name__ == "__main__":
    create_shelf()
    simulation_app.close()
