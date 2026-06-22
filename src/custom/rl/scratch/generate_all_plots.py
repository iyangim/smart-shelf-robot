import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Ensure output directory is the project root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def ppo_clipping_plot():
    r = np.linspace(0.5, 1.5, 500)
    epsilon = 0.2
    
    # Advantage > 0
    adv_pos = 1.0
    obj_unclipped_pos = r * adv_pos
    obj_clipped_pos = np.clip(r, 1 - epsilon, 1 + epsilon) * adv_pos
    obj_ppo_pos = np.minimum(obj_unclipped_pos, obj_clipped_pos)
    
    # Advantage < 0
    adv_neg = -1.0
    obj_unclipped_neg = r * adv_neg
    obj_clipped_neg = np.clip(r, 1 - epsilon, 1 + epsilon) * adv_neg
    obj_ppo_neg = np.minimum(obj_unclipped_neg, obj_clipped_neg)
    
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    
    # Positive Advantage Plot
    ax[0].plot(r, obj_unclipped_pos, '--', label='Unclipped r*A', color='gray')
    ax[0].plot(r, obj_ppo_pos, '-', label='PPO Objective', color='blue', linewidth=2.5)
    ax[0].axvline(1.0, color='black', linestyle=':', alpha=0.5)
    ax[0].axvline(1 - epsilon, color='red', linestyle=':', label='1-eps')
    ax[0].axvline(1 + epsilon, color='green', linestyle=':', label='1+eps')
    ax[0].set_title("Positive Advantage ($A > 0$)")
    ax[0].set_xlabel("Ratio $r(\\theta)$")
    ax[0].set_ylabel("Surrogate Objective")
    ax[0].legend()
    ax[0].grid(True, alpha=0.3)
    
    # Negative Advantage Plot
    ax[1].plot(r, obj_unclipped_neg, '--', label='Unclipped r*A', color='gray')
    ax[1].plot(r, obj_ppo_neg, '-', label='PPO Objective', color='orange', linewidth=2.5)
    ax[1].axvline(1.0, color='black', linestyle=':', alpha=0.5)
    ax[1].axvline(1 - epsilon, color='red', linestyle=':')
    ax[1].axvline(1 + epsilon, color='green', linestyle=':')
    ax[1].set_title("Negative Advantage ($A < 0$)")
    ax[1].set_xlabel("Ratio $r(\\theta)$")
    ax[1].set_ylabel("Surrogate Objective")
    ax[1].legend()
    ax[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = os.path.join(ROOT_DIR, "ppo_clipping_function.png")
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Generated: {output_path}")

def joint_trajectory_plot():
    t = np.linspace(0, 5, 200)
    
    # Simulate trajectories for a 3-DOF subsystem
    q1 = np.sin(t) * 0.5 + 0.1 * t
    q2 = np.cos(1.5 * t) * 0.4
    q3 = np.sin(2.0 * t) * 0.3 - 0.2
    
    dq1 = np.gradient(q1, t)
    dq2 = np.gradient(q2, t)
    dq3 = np.gradient(q3, t)
    
    fig, ax = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # Joint Positions
    ax[0].plot(t, q1, label='Joint 1', color='darkblue')
    ax[0].plot(t, q2, label='Joint 2', color='darkgreen')
    ax[0].plot(t, q3, label='Joint 3', color='darkred')
    ax[0].set_ylabel("Position (rad)")
    ax[0].set_title("Joint Positions over Time")
    ax[0].legend()
    ax[0].grid(True, alpha=0.3)
    
    # Joint Velocities
    ax[1].plot(t, dq1, '--', label='Joint 1 Vel', color='blue')
    ax[1].plot(t, dq2, '--', label='Joint 2 Vel', color='green')
    ax[1].plot(t, dq3, '--', label='Joint 3 Vel', color='red')
    ax[1].set_xlabel("Time (s)")
    ax[1].set_ylabel("Velocity (rad/s)")
    ax[1].set_title("Joint Velocities over Time")
    ax[1].legend()
    ax[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = os.path.join(ROOT_DIR, "joint_space_trajectories.png")
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Generated: {output_path}")

def impedance_step_response_plot():
    t = np.linspace(0, 2.0, 500)
    target = 1.0
    
    # Underdamped
    omega_n = 10.0
    zeta_under = 0.3
    wd = omega_n * np.sqrt(1 - zeta_under**2)
    val_under = target * (1 - (np.exp(-zeta_under * omega_n * t) * 
                  (np.cos(wd * t) + (zeta_under * omega_n / wd) * np.sin(wd * t))))
    
    # Critically damped
    zeta_critical = 1.0
    val_critical = target * (1 - np.exp(-omega_n * t) * (1 + omega_n * t))
    
    # Overdamped
    zeta_over = 1.5
    s1 = -omega_n * (zeta_over - np.sqrt(zeta_over**2 - 1))
    s2 = -omega_n * (zeta_over + np.sqrt(zeta_over**2 - 1))
    c1 = s2 / (s2 - s1)
    c2 = -s1 / (s2 - s1)
    val_over = target * (1 - (c1 * np.exp(s1 * t) + c2 * np.exp(s2 * t)))
    
    plt.figure(figsize=(10, 6))
    plt.plot(t, val_under, label='Underdamped ($\zeta = 0.3$)', color='red')
    plt.plot(t, val_critical, label='Critically Damped ($\zeta = 1.0$)', color='green', linewidth=2.5)
    plt.plot(t, val_over, label='Overdamped ($\zeta = 1.5$)', color='blue')
    plt.axhline(target, color='black', linestyle='--', label='Target $x_{des}$')
    plt.title("Operational Space Impedance Controller Step Response")
    plt.xlabel("Time (s)")
    plt.ylabel("Position Error / Response")
    plt.legend()
    plt.grid(True, alpha=0.3)
    output_path = os.path.join(ROOT_DIR, "impedance_step_response.png")
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Generated: {output_path}")

def coordinate_frames_plot():
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
    
    output_path = os.path.join(ROOT_DIR, "coordinate_transform_chains.png")
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Generated: {output_path}")

def diffusion_denoising_plot():
    steps = [0, 5, 20, 50] # Selection of diffusion steps
    n_points = 100
    x = np.linspace(0, 1.0, n_points)
    
    # Ground truth trajectory
    y_gt = np.sin(x * np.pi) * 0.5 + 0.2 * np.sin(3 * x * np.pi)
    
    plt.figure(figsize=(12, 8))
    
    # Generate denoising process
    np.random.seed(42)
    for idx, k in enumerate(steps):
        # Noise level decreases as step index k decreases
        noise_level = (k / 50.0)
        noise = np.random.normal(0, 0.15, n_points) * noise_level
        y_k = y_gt * (1.0 - noise_level) + noise
        
        alpha = 0.3 if k != 0 else 1.0
        linewidth = 1.5 if k != 0 else 3.0
        label = f'Step {k} (Noise level: {noise_level:.2f})' if k != 0 else 'Step 0 (Final Target Trajectory)'
        color = plt.cm.plasma(1.0 - noise_level)
        
        plt.plot(x, y_k, label=label, alpha=alpha, linewidth=linewidth, color=color)
        if k != 0:
            plt.scatter(x[::5], y_k[::5], color=color, alpha=0.3, s=15)
            
    plt.title("Action Trajectory Denoising Process (Diffusion Policy)")
    plt.xlabel("Trajectory Step / Normalized Time")
    plt.ylabel("Action Output Dimension (e.g. Flange X Pos)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    output_path = os.path.join(ROOT_DIR, "diffusion_trajectory_denoising.png")
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    ppo_clipping_plot()
    joint_trajectory_plot()
    impedance_step_response_plot()
    coordinate_frames_plot()
    diffusion_denoising_plot()
    print("All plots successfully generated in project root.")
