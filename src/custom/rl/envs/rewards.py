# -*- coding: utf-8 -*-
# ~/smart-shelf-robot/src/custom/rl/envs/rewards.py
#
# 기존 Reach 태스크용 보상 함수.
# 이 파일은 기존 doosan_joint_pos_env_cfg.py(Reach 태스크)에서 참조됩니다.
#
# 신규 태스크별 보상 함수 위치:
#   - Task 2 (Pick-up):  envs/pick/mdp/rewards.py
#   - Task 4 (Place):    envs/place/mdp/rewards.py

import torch 

def compute_shelf_rewards( 
    product_pos: torch.Tensor,  
    target_pos: torch.Tensor,  
    product_rot: torch.Tensor,  
    w_1: float = 2.0,  
    w_2: float = 1.0 
) -> torch.Tensor: 
    """기존 Reach 태스크용 매대 보상 함수 — Tensor 기반 병렬 환경 대응.

    물체의 매대 목표 지점까지의 거리 패널티와 물체 직립 정렬 보상을
    가중 합산하여 반환합니다.

    이 함수는 Reach 태스크 전용입니다. Pick-up(Task 2) 및 Place(Task 4)
    태스크의 보상은 각각 envs/pick/mdp/rewards.py 와
    envs/place/mdp/rewards.py 에 별도로 정의되어 있습니다.

    Args:
        product_pos: (num_envs, 3) 물체 위치 텐서.
        target_pos: (num_envs, 3) 타겟 매대 격자점 위치 텐서.
        product_rot: (num_envs, 4) 물체 쿼터니언 [qw, qx, qy, qz].
        w_1: 거리 패널티 가중치 (기본값 2.0).
        w_2: 정렬 보상 가중치 (기본값 1.0).

    Returns:
        (num_envs,) 크기의 통합 보상 텐서.
    """
 
    # 1. 타겟 매대 격자점까지의 거리 패널티 계산 
    dist = torch.norm(product_pos - target_pos, dim=-1) 
    r_dist = -torch.square(dist) 
        
    # 2. 물품의 상방 회전 벡터 추출 (Quaternion에서 Z축 방향 벡터 계산) [cite: 240, 241]
    # product_rot layout: [qw, qx, qy, qz] 
    qw, qx, qy, qz = product_rot[:, 0], product_rot[:, 1], product_rot[:, 2], product_rot[:, 3] 
        
    # 회전 행렬의 3번째 열 벡터(물체의 로컬 Z축) 연산 
    z_bx = 2 * (qx * qz + qw * qy) 
    z_by = 2 * (qy * qz - qw * qx) 
    z_bz = qw**2 - qx**2 - qy**2 + qz**2 
        
    # 세계 좌표계의 수직 축인 [0, 0, 1]과의 내적값은 결국 z_bz와 동일함 [cite: 241, 242]
    r_align = z_bz 
        
    # 3. 통합 가속 보상 텐서 일괄 반환 
    return (w_1 * r_dist) + (w_2 * r_align) 