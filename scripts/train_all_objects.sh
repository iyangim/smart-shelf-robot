#!/bin/bash
# scripts/train_all_objects.sh
# Batch script to train all convenience store object types sequentially.

# Exit on error
set -e

OBJECT_TYPES=("can" "bottle" "cube" "snack_bag")
TASK="Doosan-Pick-v0"

for OBJ in "${OBJECT_TYPES[@]}"; do
    echo "=========================================================================="
    echo "Starting full PPO training for: TASK=$TASK, OBJECT_TYPE=$OBJ"
    echo "=========================================================================="
    
    export OBJECT_TYPE=$OBJ
    ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/train.py --task $TASK --headless
    
    echo "Finished training for: $OBJ"
    echo "=========================================================================="
done
