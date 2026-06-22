# Phase 4: VLA-guided Virtual-to-Real Deployment - Configuration Specification

Phase 4 introduces Vision-Language-Action (VLA) multi-modal control. Natural language commands are parsed and paired with camera vision and robot joint states to output joint position trajectories. This specification outlines the environment settings, multimodal inputs, network architectures, action configurations, and deployment strategies for Phase 4.

---

## 1. Multimodal Inputs & Dimensions

The observation space is multimodal:
- **Vision (RGB Image)**: Shape `[3, 224, 224]` (3-channel color image from RealSense D435 camera).
- **Language Embeddings**: Shape `[768]` (text instruction encoded via pre-trained BERT or CLIP text model).
- **Robot Low-dim State**: Shape `[9]` (joint positions [6] + ee flange pos [3]).

### Action Space
- **Actions**: Shape `[7]` (6-DOF arm joints control + 1 gripper binary command).
- **Action Horizon**: Diffusion Policy uses an action horizon of 16 steps and a prediction chunk size of 8 steps to reduce latency.

---

## 2. VLA Communication Bridge (`vla_bridge_node.py`)

A ROS 2 bridge node (`vla_bridge_node.py`) coordinates the flow:
1. Receives `/vla/instruction` string commands from the user interface.
2. Encodes the instruction into a 768-dimensional language embedding.
3. Synchronizes color images `/camera/color/image_raw` and `/joint_states`.
4. Executes the model inference to output joint trajectories to `/policy/joint_targets`.

---

## 3. Policy & Model Architecture

- **Visual Encoder**: ResNet-18 backbone pre-trained on ImageNet. Its spatial features are processed via Spatial Softmax to generate 32 keypoints (64 features).
- **Conditioning**: Concatenates visual features (64), language embedding (768), and state features (9) to form an 841-dimensional global conditioning vector.
- **Action Decoder**: 1D Conditional U-Net trained via Denoising Diffusion Probabilistic Models (DDPM).

---

## 4. Multimodal Dataset Configurations

- **Zarr Image Dataset**: `${oc.env:DATA_DIR}/vla_shelf_tasks.zarr`
- **Robomimic HDF5 Dataset**: `data/vla_shelf_tasks_robomimic.hdf5`

---

## 5. Training Commands

```bash
# VLA Image-conditioned Diffusion Policy
python train_diffusion.py \
    --data_path data/vla_shelf_tasks.zarr \
    --output_dir checkpoints/diffusion_policy_vla \
    --batch_size 32 --num_epochs 500
```
