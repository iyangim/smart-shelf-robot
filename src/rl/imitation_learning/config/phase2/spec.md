# Phase 2: Shelf-based 4-Step Simulation Setup - Configuration Specification

Phase 2 focuses on executing a sequential 4-step manipulation pipeline in simulation: Scan & Detect, Pick-up (from basket), Obstacle-Free Transit, and Place (on shelf). This specification outlines the environment settings, state/action dimensions, dataset paths, and training instructions for the two RL-based components in Phase 2: **Pick-up** and **Place**.

---

## 1. Tasks Overview & Dimensions

| Task Name | Gym Environment ID | Action Dim | Observation Dim | Observation Keys |
| :--- | :--- | :--- | :--- | :--- |
| **Pick-up (Basket)** | `Doosan-Pick-v0` | **7** | **35** | `joint_pos` (6), `joint_vel` (6), `eef_pos` (3), `eef_quat` (4), `object_position` (3), `object_orientation` (4), `gripper` (2), `last_action` (7) |
| **Place (Shelf)** | `Doosan-Place-v0` | **7** | **41** | `joint_pos` (6), `joint_vel` (6), `eef_pos` (3), `eef_quat` (4), `slot_position` (3), `slot_orientation` (4), `slot_tolerance` (3), `object_position` (3), `gripper` (2), `last_action` (7) |

---

## 2. Dataset Path Configurations

Dataset paths should follow this naming convention:
- **Diffusion Policy (Zarr)**: `${oc.env:DATA_DIR}/doosan_<task_name>.zarr`
- **Robomimic BC (HDF5)**: `data/doosan_<task_name>_robomimic.hdf5`

---

## 3. Training & Validation Execution

### Diffusion Policy
To train the Diffusion Policy for Phase 2 tasks, run:

```bash
# Pick Task
python train_diffusion.py \
    --data_path data/doosan_pick.zarr \
    --output_dir checkpoints/diffusion_policy_pick \
    --horizon 16 --batch_size 64 --num_epochs 500

# Place Task
python train_diffusion.py \
    --data_path data/doosan_place.zarr \
    --output_dir checkpoints/diffusion_policy_place \
    --horizon 16 --batch_size 64 --num_epochs 500
```

### Robomimic BC
To train the Behavioral Cloning Policy for Phase 2 tasks, run:

```bash
# Pick Task (using Robomimic JSON config)
python train_bc.py --config src/rl/imitation_learning/config/phase2/pick_bc.json

# Place Task (using Robomimic JSON config)
python train_bc.py --config src/rl/imitation_learning/config/phase2/place_bc.json
```
