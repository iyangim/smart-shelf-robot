# Phase 1: Core RL Porting (Reach, Lift, Stack) - Configuration Specification

Phase 1 focuses on porting the core reinforcement learning/imitation learning tasks from the Franka robot to the **Doosan E0509** robot with the **RH-P12-RN-A** gripper. This specification outlines the environment settings, state/action dimensions, dataset paths, and training instructions for Phase 1.

---

## 1. Tasks Overview & Dimensions

| Task Name | Gym Environment ID | Action Dim | Observation Dim | Observation Keys |
| :--- | :--- | :--- | :--- | :--- |
| **Reach** | `Template-Doosan-Reach-v0` | **6** | **25** | `joint_pos_rel` (6), `joint_vel_rel` (6), `ee_pose_command` (7), `last_action` (6) |
| **Lift** | `Doosan-Lift-v0` | **7** | **34** | `joint_pos` (6), `joint_vel` (6), `eef_pos` (3), `eef_quat` (4), `object_pos` (3), `object_quat` (4), `gripper_width` (1), `last_action` (7) |
| **Stack** | `Doosan-Stack-v0` | **7** | **41** | `joint_pos` (6), `joint_vel` (6), `eef_pos` (3), `eef_quat` (4), `object_a_pos` (3), `object_a_quat` (4), `object_b_pos` (3), `object_b_quat` (4), `gripper_width` (1), `last_action` (7) |

---

## 2. Dataset Path Configurations

Dataset paths should follow this naming convention:
- **Diffusion Policy (Zarr)**: `${oc.env:DATA_DIR}/doosan_<task_name>.zarr`
- **Robomimic BC (HDF5)**: `data/doosan_<task_name>_robomimic.hdf5`

---

## 3. Training & Validation Execution

### Diffusion Policy
To train the Diffusion Policy for Phase 1 tasks, run:

```bash
# Reach Task
python train_diffusion.py \
    --data_path data/doosan_reach.zarr \
    --output_dir checkpoints/diffusion_policy_reach \
    --horizon 16 --batch_size 64 --num_epochs 500

# Lift Task
python train_diffusion.py \
    --data_path data/doosan_lift.zarr \
    --output_dir checkpoints/diffusion_policy_lift \
    --horizon 16 --batch_size 64 --num_epochs 500

# Stack Task
python train_diffusion.py \
    --data_path data/doosan_stack.zarr \
    --output_dir checkpoints/diffusion_policy_stack \
    --horizon 16 --batch_size 64 --num_epochs 500
```

### Robomimic BC
To train the Behavioral Cloning Policy for Phase 1 tasks, run:

```bash
# Reach Task
python train_bc.py --simple --epochs 500 --batch_size 256

# Or using Robomimic (with JSON config)
python train_bc.py

# Stack Task (using Robomimic JSON config)
python train_bc.py --config src/rl/imitation_learning/config/phase1/stack_bc.json
```
