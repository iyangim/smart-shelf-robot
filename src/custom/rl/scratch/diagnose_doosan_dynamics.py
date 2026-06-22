import os
import argparse
from isaaclab.app import AppLauncher

# Set up app launcher
parser = argparse.ArgumentParser(description="Diagnose Doosan robot USD dynamics properties.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args(args=["--headless"])
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd, UsdPhysics, UsdGeom

def diagnose_asset(usd_file):
    print("============================================================")
    print(f"DIAGNOSING USD ASSET: {usd_file}")
    print("============================================================")
    stage = Usd.Stage.Open(usd_file)
    if not stage:
        print("[ERROR] Failed to open USD stage.")
        return

    # 1. Inspect Joints and Limits
    print("\n--- Joint Limits Check ---")
    joint_count = 0
    locked_joints = []
    unset_limits = []
    
    for prim in stage.Traverse():
        if prim.IsA(UsdPhysics.RevoluteJoint):
            joint_count += 1
            joint = UsdPhysics.RevoluteJoint(prim)
            name = prim.GetName()
            min_limit = joint.GetLowerLimitAttr().Get()
            max_limit = joint.GetUpperLimitAttr().Get()
            
            print(f"Joint: {prim.GetPath()}")
            print(f"  Limits: Lower={min_limit}, Upper={max_limit}")
            
            if min_limit is None or max_limit is None:
                unset_limits.append(name)
            elif abs(max_limit - min_limit) < 1e-4:
                locked_joints.append(name)
                
    print(f"\nSummary of Joints: {joint_count} revolute joints found.")
    if locked_joints:
        print(f"[WARNING] Locked joints (limits range ~0): {locked_joints}")
    if unset_limits:
        print(f"[WARNING] Joints with unset limits: {unset_limits}")

    # 2. Inspect Mass & Inertia Properties
    print("\n--- Rigid Body Mass & Inertia Check ---")
    rigid_body_count = 0
    zero_mass_links = []
    unusual_inertia_links = []
    
    for prim in stage.Traverse():
        # Check if the prim has a RigidBodyAPI applied
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            rigid_body_count += 1
            print(f"Rigid Body Link: {prim.GetPath()}")
            
            # Check MassAPI
            if prim.HasAPI(UsdPhysics.MassAPI):
                mass_api = UsdPhysics.MassAPI(prim)
                mass = mass_api.GetMassAttr().Get()
                com = mass_api.GetCenterOfMassAttr().Get()
                inertia = mass_api.GetDiagonalInertiaAttr().Get()
                
                print(f"  Mass: {mass}")
                print(f"  Center of Mass: {com}")
                print(f"  Diagonal Inertia: {inertia}")
                
                if mass is None or mass <= 0.0:
                    zero_mass_links.append(prim.GetName())
                if inertia is not None:
                    # check if any diagonal value is non-positive
                    if any(i <= 0.0 for i in inertia):
                        unusual_inertia_links.append(f"{prim.GetName()} (non-positive diagonal)")
            else:
                print("  [WARNING] MassAPI NOT applied directly to this rigid body prim.")
                zero_mass_links.append(prim.GetName())

    print(f"\nSummary of Rigid Bodies: {rigid_body_count} rigid bodies found.")
    if zero_mass_links:
        print(f"[CRITICAL] Links with zero or unset mass: {zero_mass_links}")
    if unusual_inertia_links:
        print(f"[WARNING] Links with unusual/invalid diagonal inertia: {unusual_inertia_links}")
    
    print("============================================================")

if __name__ == "__main__":
    usd_file = "/home/iyangim/smart-shelf-robot/src/custom/rl/assets/doosan_e0509_with_gripper.usd"
    diagnose_asset(usd_file)
    simulation_app.close()
