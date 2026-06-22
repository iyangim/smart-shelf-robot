import sys
import argparse
from isaaclab.app import AppLauncher

# Set up argument parser
parser = argparse.ArgumentParser(description="USD Checker")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# Launch the app (this adds pxr and other omni libraries to sys.path)
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd

def check_usd(path):
    print("========================================")
    print("Opening USD:", path)
    stage = Usd.Stage.Open(path)
    if not stage:
        print("Failed to open USD")
        return
    print("USD loaded successfully!")
    print("Default prim:", stage.GetDefaultPrim())
    print("Prims on stage:")
    for prim in stage.Traverse():
        print("  Prim:", prim.GetPath(), "Type:", prim.GetTypeName())
    print("========================================")

if __name__ == "__main__":
    check_usd("src/custom/rl/assets/shelf_workspace_v2.usd")
    simulation_app.close()
