import os
from pxr import Usd, UsdPhysics

usd_file = "/home/iyangim/smart-shelf-robot/src/external/doosan-robot2/dsr_description2/usd/e0509.usd"
print(f"Opening USD file: {usd_file}")
stage = Usd.Stage.Open(usd_file)
if not stage:
    print("Failed to open stage.")
    exit(1)

print("Listing all Physics joints and their limits:")
for prim in stage.Traverse():
    if prim.IsA(UsdPhysics.Joint):
        print(f"\nJoint Prim: {prim.GetPath()}")
        if prim.IsA(UsdPhysics.RevoluteJoint):
            rev_joint = UsdPhysics.RevoluteJoint(prim)
            low = rev_joint.GetLowerLimitAttr().Get()
            high = rev_joint.GetUpperLimitAttr().Get()
            print(f"  Type: Revolute")
            print(f"  Limits: Lower={low}, Upper={high}")
