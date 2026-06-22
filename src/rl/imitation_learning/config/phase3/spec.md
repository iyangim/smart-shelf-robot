# Phase 3: Real Robot Integration & Testing - Configuration Specification

Phase 3 focuses on deploying trained reinforcement learning and imitation learning policies on the physical **Doosan E0509** robot and **RH-P12-RN-A** gripper. It integrates real camera streams, hand-eye calibration matrix ($T_{\text{cam2base}}$), joint state publishers, safety monitors, and physical datasets. This specification outlines the environment settings, state/action dimensions, dataset paths, calibration details, and deployment guidelines for Phase 3.

---

## 1. Real Robot System Overview & Dimensions

Real-world deployment mirrors simulation state and action dimensions to ensure policy transferability, but observations are driven by physical hardware sensors.

| Task Name | Action Dim | Observation Dim | Observation Keys (Source) |
| :--- | :--- | :--- | :--- |
| **Real Pick-up** | **7** | **35** | `joint_pos` (from `/joint_states`), `joint_vel` (from `/joint_states`), `eef_pos` (flange TF), `eef_quat` (flange TF), `object_position` (RealSense / pointcloud tracker via `/object_pose`), `object_orientation` (RealSense via `/object_pose`), `gripper` (Robotis gripper feed), `last_action` (previous control step cmd) |
| **Real Place** | **7** | **41** | `joint_pos` (from `/joint_states`), `joint_vel` (from `/joint_states`), `eef_pos` (flange TF), `eef_quat` (flange TF), `slot_position` (RealSense / detection node), `slot_orientation` (RealSense / detection node), `slot_tolerance` (3), `object_position` (gripper-held object pose), `gripper` (Robotis gripper feed), `last_action` (previous control step cmd) |

---

## 2. Eye-to-Hand Calibration & Vision Integration

To ensure correct 3D target coordinates in the robot base frame:
- **Intrinsics Calibration**: Subscribed via `/camera/depth/camera_info`.
- **Extrinsics Calibration Matrix ($T_{\text{cam2base}}$)**: Loaded from `src/vision/calibration_result.npz` inside `pose_estimation_node.py` and `pointcloud_node.py`.
- **Depth Alignment**: Depth stream is aligned with the color stream via subscription to `/camera/aligned_depth_to_color/image_raw`.

---

## 3. Safety Guard Configuration

Before running policies, verify safety parameters:
- **Joint Velocity limits** are constrained to under **10%** scale for initial runs.
- **Safety monitor** `emergency_safety_guard.py` checks joint torques and limits command outputs.
- **Emergency stop pendant (E-Stop)** must be hand-held.

---

## 4. Real Dataset Configurations

Real demonstration datasets are collected on the physical robot:
- **Diffusion Zarr Dataset**: `${oc.env:DATA_DIR}/real_<task_name>.zarr`
- **Robomimic HDF5 Dataset**: `data/real_<task_name>_robomimic.hdf5`

---

## 5. Training Commands

```bash
# Real Pick-up Diffusion Policy
python train_diffusion.py \
    --data_path data/real_pick.zarr \
    --output_dir checkpoints/diffusion_policy_real_pick \
    --horizon 16 --batch_size 64 --num_epochs 500

# Real Place Robomimic BC
python train_bc.py --config src/rl/imitation_learning/config/phase3/real_place_bc.json
```
