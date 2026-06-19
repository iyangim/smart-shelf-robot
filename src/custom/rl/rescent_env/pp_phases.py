import numpy as np
from pp_geometry import robotiq_grasp_to_rhp12, grasp_to_world

def query_graspgen(grasp_client, pc_obj, cube_tgt_pos, cube_quat, num_grasps=400):
    """
    Remote grasp inference query using GraspGen ZMQ server.
    Converts local robotiq grasps to RH-P12 gripper and projects them to the world frame.
    """
    local_grasps, scores = grasp_client.infer(
        pc_obj,
        num_grasps=num_grasps,
        grasp_threshold=-1.0,
        remove_outliers=False
    )
    
    grasps_w = []
    for g in local_grasps:
        # Convert Robotiq model's default grasp to RH-P12 frame
        g_rhp12 = robotiq_grasp_to_rhp12(g)
        # Transform the local gripper pose to the world frame using object state
        g_world = grasp_to_world(g_rhp12, cube_tgt_pos, cube_quat)
        grasps_w.append(g_world)
        
    return np.array(grasps_w), np.array(scores)
