# Phase 4 Theory: 3D Computer Vision & Coordinate Calibration

This document outlines the projection geometry, Hand-Eye extrinsic calibration math, and point cloud registration pipelines required to align sensor observations with the robot's physical coordinate system.

---

## 1. Camera Projection Geometry: Pinhole Model

A camera maps a 3D point $P_w = [X_w, Y_w, Z_w, 1]^T$ in the world coordinate system to a 2D pixel coordinate $p = [u, v, 1]^T$ on the image plane.

### 1.1 Homogeneous Projection Equation
The projection is defined as:

$$s \begin{bmatrix} u \\ v \\ 1 \end{bmatrix} = K \begin{bmatrix} R & t \end{bmatrix} \begin{bmatrix} X_w \\ Y_w \\ Z_w \\ 1 \end{bmatrix}$$

Where:
- $s$ represents a scaling factor.
- $K \in \mathbb{R}^{3 \times 3}$ is the Camera Intrinsic Matrix:

$$K = \begin{bmatrix} f_x & 0 & c_u \\ 0 & f_y & c_v \\ 0 & 0 & 1 \end{bmatrix}$$

- $R \in \mathbb{R}^{3 \times 3}, t \in \mathbb{R}^3$ are the Extrinsic Rotation Matrix and Translation Vector representing camera orientation.

---

## 2. Hand-Eye Calibration: Coordinate Transformations

For an Eye-in-Hand setup, the camera is mounted on the robot's end-effector. The object pose relative to the robot base must be resolved dynamically.

### 2.1 Transformation Chain
The pose of the object $T_{base}^{object}$ is computed as:

$$T_{base}^{object} = T_{base}^{flange}(q) \cdot T_{flange}^{camera} \cdot T_{camera}^{object}$$

Where:
- $T_{base}^{flange}(q)$ is obtained from forward kinematics.
- $T_{flange}^{camera}$ is the static Hand-Eye calibration matrix.
- $T_{camera}^{object}$ is computed by the vision network (e.g., pose estimation model).

### 2.2 Calibration Equation
The static matrix $X = T_{flange}^{camera}$ is solved using pairs of movements ($A_i$ and $B_i$) via the relation:

$$A X = X B$$

Where $A$ represents relative end-effector movement and $B$ represents relative camera movement.

---

## 3. Structural Diagrams

### 3.1 Transformation Frame Chain
```mermaid
graph TD
    Base[Robot Base: {B}] -- Forward Kinematics --> Flange[End-Effector Flange: {F}]
    Flange -- Hand-Eye Calibration Matrix: X --> Camera[Camera Optical Center: {C}]
    Camera -- Deep Pose Estimation --> Object[Object Target: {O}]
    Base -. Object Pose in Robot Frame .-> Object
```

### 3.2 Point Cloud Preprocessing Pipeline
```mermaid
flowchart LR
    Raw[Raw Depth Image] --> Cloud[Point Cloud Generation]
    Cloud --> Pass[Passband Filter: Box clip]
    Pass --> Down[Voxel Grid Downsampling]
    Down --> RANSAC[RANSAC Plane Segmentation]
    RANSAC --> Align[Aligned Point Cloud]
```

---

## 4. Plotting Script: 3D Coordinate Frames

Below is a Python script to visualize 3D coordinate frames (Base, Flange, Camera, Object) in space.

```python
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def plot_coordinate_frames():
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Origins
    O_base = np.array([0, 0, 0])
    O_flange = np.array([0.4, 0.2, 0.5])
    O_camera = O_flange + np.array([0.05, 0.0, 0.08])
    O_object = O_camera + np.array([0.2, 0.1, -0.3])
    
    # Helper to draw axes
    def draw_axes(origin, R, label, scale=0.1):
        colors = ['red', 'green', 'blue'] # RGB -> XYZ
        for i in range(3):
            ax.quiver(origin[0], origin[1], origin[2], 
                      R[0, i], R[1, i], R[2, i], 
                      color=colors[i], length=scale, normalize=True)
        ax.text(origin[0], origin[1], origin[2], label, fontsize=10, fontweight='bold')

    # Identity rotation for Base
    R_base = np.eye(3)
    # Simple arbitrary rotations for other frames
    R_flange = np.array([[0.866, -0.5, 0], [0.5, 0.866, 0], [0, 0, 1]])
    R_camera = R_flange @ np.array([[1, 0, 0], [0, 0.866, -0.5], [0, 0.5, 0.866]])
    R_object = np.eye(3)
    
    draw_axes(O_base, R_base, " Base {B}")
    draw_axes(O_flange, R_flange, " Flange {F}")
    draw_axes(O_camera, R_camera, " Camera {C}")
    draw_axes(O_object, R_object, " Object {O}")
    
    # Plot links / paths
    ax.plot([O_base[0], O_flange[0]], [O_base[1], O_flange[1]], [O_base[2], O_flange[2]], 'k-', label='Robot Links')
    ax.plot([O_flange[0], O_camera[0]], [O_flange[1], O_camera[1]], [O_flange[2], O_camera[2]], 'm--', label='Hand-Eye Joint')
    ax.plot([O_camera[0], O_object[0]], [O_camera[1], O_object[1]], [O_camera[2], O_object[2]], 'c:', label='Optical Ray')
    
    ax.set_xlim([-0.1, 0.8])
    ax.set_ylim([-0.2, 0.6])
    ax.set_zlim([-0.1, 0.7])
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title("3D Coordinate Transformation Chains")
    ax.legend()
    
    plt.savefig("coordinate_transform_chains.png")
    plt.show()

if __name__ == "__main__":
    plot_coordinate_frames()
```

*Image Generation Prompt for Graph*:
`3D coordinate system axis representation with labeled frames for robot base, flange, camera and object, colored lines indicating axes directions, clean presentation layout.`
