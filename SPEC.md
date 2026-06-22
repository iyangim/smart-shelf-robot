# Technical Specification (SPEC.md) - Smart Shelf Robot 4-Phase Roadmap

This document outlines the milestones, data flow, and solutions to technical bottlenecks for the 4-phase **smart-shelf-robot** integration plan.

---

## 1. Project Phase Breakdown

### Phase 1: Franka-to-Doosan Core RL Porting (3 Tasks)
* **Objective**: Port and run the three basic manipulation tasks originally defined in `franka_isaaclab` identically on the Doosan E0509 robot.
* **Tasks**:
  * **Reach** (`Template-Doosan-Reach-v0`): Move end-effector flange to target coordinate.
  * **Lift** (`Doosan-Lift-v0`): Grab a single cube on the table and lift it.
  * **Stack** (`Doosan-Stack-v0`): Grab one cube and stack it on top of another.
* **Verification**: Headless/GUI training validation using `scripts/skrl/train.py` and `scripts/skrl/play.py`.

### Phase 2: Shelf-based 4-Step Simulation Setup (4 Tasks)
* **Objective**: Build the target shelf layout in simulation and execute the full sequential manipulation task.
* **Tasks**:
  * **Task 1: Scan & Detect**: Segment shelf empty slots and object poses.
  * **Task 2: Pick-up (Basket)** (`Doosan-Pick-v0`): Grab items from a basket.
  * **Task 3: Obstacle-Free Transit**: Navigate without collision using cuRobo/LCP planner.
  * **Task 4: Place (Shelf)** (`Doosan-Place-v0`): Align and insert items into shelf slots.
* **Verification**: Complete sequential run in virtual simulation mode.

### Phase 3: Real Robot Integration & Testing
* **Objective**: Connect to the physical Doosan E0509 robot and RH-P12-RN-A gripper, run basic validation, and deploy the trained RL policies.
* **Tasks**:
  * Verify joint trajectory commands (`servol_rt`) and torque safety monitoring via `emergency_safety_guard.py`.
  * Align real RealSense camera depth inputs using `pose_estimation_node.py` and `calibration_result.npz`.
  * Execute real Pick-and-Place tasks.
* **Verification**: Running FSM (`main_controller_node.py`) in Real Mode.

### Phase 4: VLA-guided Virtual-to-Real Deployment
* **Objective**: Implement natural language control using a VLA model (Vision-Language-Action), verify the behaviors in simulation, and execute on the physical robot.
* **Tasks**:
  * Connect `vla_bridge_node.py` to parse language commands.
  * Integrate diffusion model policy inferences for long-horizon task coordination.
  * Validate end-to-end VLA control flow in simulation before driving the physical hardware.
* **Verification**: End-to-end language instruction follow-through.

---

## 2. ROS 2 Data Flow

```
[Camera Color Pub] ──> /camera/color/image_raw ──> [detection_node.py]
                                                           │
                                                           ▼ (Class + 2D Pose /object_pose_2d)
[Camera Depth Pub] ──> /camera/aligned_depth_to_color/image_raw ────> [pose_estimation_node.py]
[Camera Info Pub]  ──> /camera/depth/camera_info ───────────────────/
                                                           │
                                                           ▼ (3D Pose /object_pose)
                                                  [main_controller_node.py] (FSM)
                                                           │
                                                           ▼ (Action/Service Requests)
                                                  [arm_controller_node.py] / [gripper_node.py]
```

---

## 3. Potential Technical Bottlenecks & Solutions

### Bottleneck A: Missing YOLO Weight File (`pose_robust_seg.pt`)
* **Solution**: Implement parameter override in `detection_node.py` so users can load custom weights, and print descriptive errors if weights are missing.

### Bottleneck B: Non-Standard ROS 2 Package Structure
* **Solution**: Create `package.xml` and `CMakeLists.txt` inside `src/custom/` to define the package `smart_shelf_robot` and register its scripts as Python/C++ executables.

### Bottleneck C: RealSense Depth-Color Registration Drift
* **Solution**: Enforce subscription to `/camera/aligned_depth_to_color/image_raw` instead of standard depth maps, and dynamically update camera matrices utilizing `/camera/depth/camera_info` inside `pointcloud_node.py` and `pose_estimation_node.py`.
