# Task Checklist

## Phase 1: Reach 태스크 (완료)
- [x] Create robot asset configuration `doosan.py`
- [x] Create environment task configuration `doosan_joint_pos_env_cfg.py`
- [x] Register new environments in `reach/__init__.py`
- [x] Create PPO agent configuration `doosan_skrl_ppo_cfg.yaml`
- [x] Run zero-action evaluation sanity check to verify E0509 USD asset loading
- [x] Test training launch to verify training configuration and reward structure
- [x] Separate projects (replaced symlinks in `franka_isaaclab` with independent physical copies)
- [x] Analyze `smart-shelf-robot` learning libraries (`skrl` and Hugging Face `lerobot`) and compare with `franka_isaaclab`
- [x] Postpone Git commits until final execution is complete

## Phase 2: 4-태스크 파이프라인 정의 (task_define.md 기반)

### 공용 에셋 설정
- [x] Create gripper configuration `cfgs/gripper_cfg.py` (RH-P12-RN-A)
- [x] Update `cfgs/doosan_shelf_assets_cfg.py` (그리퍼 통합 로봇 + 바구니 에셋)

### Task 2: Pick-up (RL 환경)
- [x] Create `envs/pick/mdp/__init__.py`
- [x] Create `envs/pick/mdp/rewards.py` (Reach/Grasp/Lift 보상)
- [x] Create `envs/pick/mdp/observations.py` (물체 위치, 그리퍼 상태)
- [x] Create `envs/pick/mdp/terminations.py` (낙하/성공 종료)
- [x] Create `envs/pick/pick_env_cfg.py` (MDP 환경 기반 설정)
- [x] Create `envs/pick/doosan_pick_env_cfg.py` (두산 E0509 특화)
- [x] Create `envs/pick/agents/__init__.py`
- [x] Create `envs/pick/agents/doosan_pick_skrl_ppo_cfg.yaml`
- [x] Create `envs/pick/__init__.py` (Gym 환경 등록: Doosan-Pick-v0)

### Task 4: Place (RL 환경)
- [x] Create `envs/place/mdp/__init__.py`
- [x] Create `envs/place/mdp/rewards.py` (Alignment/Insertion/Release 보상)
- [x] Create `envs/place/mdp/observations.py` (슬롯 위치, 공차, 그리퍼)
- [x] Create `envs/place/mdp/terminations.py` (배치 성공/충돌 종료)
- [x] Create `envs/place/place_env_cfg.py` (MDP 환경 기반 설정)
- [x] Create `envs/place/doosan_place_env_cfg.py` (두산 E0509 특화)
- [x] Create `envs/place/agents/__init__.py`
- [x] Create `envs/place/agents/doosan_place_skrl_ppo_cfg.yaml`
- [x] Create `envs/place/__init__.py` (Gym 환경 등록: Doosan-Place-v0)

### 기존 파일 업데이트
- [x] Update `envs/rewards.py` 독스트링 보완
- [x] Update `cfgs/task.md` 체크리스트 (이 파일)

### 후속 작업 (미완료)
- [ ] RH-P12-RN-A 그리퍼 USD 에셋 생성 및 로봇 통합
- [ ] 바구니(basket) USD 에셋 생성
- [ ] Isaac Lab에서 Pick/Place 환경 실행 검증
- [ ] LCP Motion Planner 연동 (Task 3: Transit)
- [ ] ROS2 main_controller_node.py 상태머신 확장
