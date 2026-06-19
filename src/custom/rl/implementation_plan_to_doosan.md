# task_define.md 기반 태스크 정의 파일 설정 계획

`task_define.md`에 정의된 4-태스크 파이프라인을 Isaac Lab / franka_isaaclab 스타일의 MDP 환경 정의 코드로 구현합니다.

## 배경 및 현황

현재 `src/custom/rl/` 디렉토리에는 기존 **Reach 태스크** 관련 파일들만 존재합니다:
- `envs/doosan_joint_pos_env_cfg.py` — Reach 환경 설정 (상위 `ReachEnvCfg` 상속)
- `envs/rewards.py` — 매대 보상 함수 (거리 + 정렬)
- `envs/doosan_skrl_ppo_cfg.yaml` — PPO 하이퍼파라미터
- `cfgs/doosan_shelf_assets_cfg.py` — 로봇/가판대 에셋 설정
- `cfgs/sensory_cfg.py` — 카메라 센서 설정
- `doosan.py` — 로봇 ArticulationCfg

`task_define.md`는 4개 태스크를 정의하며, 이 중 **Task 2(Pick-up)**와 **Task 4(Place)**가 RL 학습 대상입니다.
Task 1(Scan)은 결정론적 비전, Task 3(Transit)은 LCP 모션 플래너로, RL 환경 정의가 불필요합니다.

## User Review Required

> [!IMPORTANT]
> **디렉토리 구조 설계 결정**
> - 현재 `envs/` 하위에 Reach 태스크 파일들이 평면적으로 배치되어 있습니다.
> - 새로운 Pick/Place 태스크 추가 시, `envs/pick/` 및 `envs/place/` 하위 디렉토리로 분리하는 구조를 제안합니다.
> - 기존 Reach 관련 파일들은 현 위치를 유지합니다.

> [!IMPORTANT]
> **그리퍼 USD 에셋 부재**
> - Robotis RH-P12-RN-A 그리퍼의 USD 파일이 현재 프로젝트에 존재하지 않습니다.
> - 그리퍼 USD 경로를 placeholder로 지정하고, 실제 파일이 준비되면 교체하는 방식으로 진행합니다.
> - 그리퍼 조인트 이름은 `gripper_joint`로 가정합니다.

> [!WARNING]
> **Observation 차원 변경**
> - 기존 Reach 태스크의 obs 차원은 25 (joint_pos_rel:6 + joint_vel_rel:6 + ee_pose_command:7 + last_action:6)입니다.
> - Task 2(Pick-up)는 물체 Pose(7) + 그리퍼 상태(2)가 추가되어 약 33차원, Task 4(Place)는 슬롯 Pose(7) + 공차 벡터(3) + 그리퍼 상태(2)가 추가되어 약 36차원이 됩니다.
> - 기존 `policy_node.py`의 추론 로직은 별도 업데이트가 필요합니다(이번 작업 범위 외).

## Open Questions

> [!IMPORTANT]
> **그리퍼 관절 이름 및 물리 파라미터**: RH-P12-RN-A의 URDF/USD에서 그리퍼 관절 이름이 확인되지 않았습니다. `gripper_joint`로 가정하여 진행해도 괜찮을까요?

> [!IMPORTANT]
> **물체 에셋**: Pick 태스크의 대상 물체(캔/병/과자봉지)는 Isaac Sim 기본 에셋(DexCube 등)을 임시 대체물로 사용해도 괜찮을까요?

---

## Proposed Changes

### 1. 공용 에셋 설정 업데이트

#### [MODIFY] [doosan_shelf_assets_cfg.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/cfgs/doosan_shelf_assets_cfg.py)
- 그리퍼 포함 로봇 통합 에셋 `DOOSAN_E0509_WITH_GRIPPER_CFG` 정의 추가
- RH-P12-RN-A 그리퍼 액추에이터 파라미터(stiffness, damping) 설정
- 바구니(basket) 환경 에셋 `BASKET_CFG` 정의 추가

#### [NEW] [gripper_cfg.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/cfgs/gripper_cfg.py)
- Robotis RH-P12-RN-A 그리퍼 독립 설정 파일
- 그리퍼 관절 이름, 개구량 범위, 목표 파지력 매핑

---

### 2. Task 2: Pick-up 태스크 정의 (RL 환경)

#### [NEW] `envs/pick/` 디렉토리 구조:

#### [NEW] [pick_env_cfg.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/pick/pick_env_cfg.py)
- `franka_isaaclab`의 `lift_env_cfg.py`를 벤치마킹한 MDP 환경 기반 클래스
- **Scene**: 두산 E0509 + RH-P12-RN-A + 바구니 + 물체 + 조명
- **Observations** `[~33 dim]`:
  - `joint_pos_rel` (6): 관절 상대 각도
  - `joint_vel_rel` (6): 관절 상대 속도
  - `ee_pos` (3) + `ee_quat` (4): 엔드이펙터 포즈
  - `object_pos_in_robot_frame` (3) + `object_quat` (4): 타겟 물체 상대 포즈
  - `gripper_state` (2): 손가락 개구량 + 의사 토크
  - `last_action` (6+1=7): 이전 행동
- **Actions** `[6 + 1]`:
  - 관절 6개의 상대 위치 변위(`RelativeJointPositionActionCfg`, scale=0.05)
  - 그리퍼 열기/닫기 명령(`BinaryJointPositionActionCfg`)
- **Rewards**:
  - `Reach Reward`: $r = \tanh(\omega \cdot \|p_{ee} - p_{obj}\|)$ (weight=1.0)
  - `Grasp Bonus`: 접촉 + 손가락 닫힘 시 정적 보상 (weight=5.0)
  - `Lift Reward`: 물체 z 높이 > 바구니 바닥 + 임계치 시 (weight=15.0)
  - `Action Penalty`: 액션 변화율 L2 패널티 (weight=-1e-4)
  - `Joint Velocity Penalty`: 관절 속도 L2 패널티 (weight=-1e-4)
- **Terminations**: 타임아웃 + 물체 낙하
- **Events**: 리셋 시 물체 위치 랜덤화

#### [NEW] [doosan_pick_env_cfg.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/pick/doosan_pick_env_cfg.py)
- `PickEnvCfg`를 상속한 두산 E0509 특화 환경
- 로봇/그리퍼/물체 에셋 바인딩
- `DoosanPickEnvCfg_PLAY` 포함

#### [NEW] [mdp/](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/pick/mdp/) 디렉토리:
  - `__init__.py` — isaaclab.envs.mdp 전체 re-export + 커스텀 함수
  - `rewards.py` — `reach_reward`, `grasp_bonus`, `lift_reward` (task_define.md 명세 기반)
  - `observations.py` — `object_position_in_robot_root_frame`, `gripper_state`
  - `terminations.py` — `object_dropped`, `object_lifted_success`

#### [NEW] [agents/](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/pick/agents/) 디렉토리:
  - `__init__.py`
  - `doosan_pick_skrl_ppo_cfg.yaml` — PPO 하이퍼파라미터 (layers=[128,64], rollouts=24, lr=3e-4)

#### [NEW] [\_\_init\_\_.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/pick/__init__.py)
- Gym 환경 등록: `Doosan-Pick-v0`, `Doosan-Pick-Play-v0`

---

### 3. Task 4: Place 태스크 정의 (RL 환경)

#### [NEW] `envs/place/` 디렉토리 구조:

#### [NEW] [place_env_cfg.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/place/place_env_cfg.py)
- `franka_isaaclab`의 `stack_env_cfg.py`를 벤치마킹한 MDP 환경 기반 클래스
- **Scene**: 두산 E0509 + RH-P12-RN-A + 매대(선반) + 물체(파지된 상태) + 조명
- **Observations**:
  - `joint_pos_rel` (6) + `joint_vel_rel` (6)
  - `ee_pos` (3) + `ee_quat` (4): 엔드이펙터 포즈
  - `slot_pos` (3) + `slot_quat` (4): 타겟 매대 빈 슬롯 Pose
  - `slot_tolerance_vec` (3): 슬롯 내부 진입 허용 공차 벡터
  - `gripper_state` (2)
  - `last_action` (7)
- **Actions** `[6 + 1]`: 관절 제어 + 그리퍼 해제 신호
- **Rewards**:
  - `Alignment Reward`: 물체 정면 벡터 · 슬롯 깊이 방향 벡터 코사인 유사도 (weight=2.0)
  - `Insertion Reward`: 슬롯 내부 축 방향 진입 깊이 기반 (weight=10.0)
  - `Release & Retreat Bonus`: 내려놓기 + 그리퍼 열기 + 안전 수납 시 (weight=20.0)
  - `Action Penalty` (weight=-1e-4)
  - `Joint Velocity Penalty` (weight=-1e-4)
- **Terminations**: 타임아웃 + 물체 낙하 + 충돌 감지
- **Curriculum**: 초기에는 넓은 슬롯 → 점진적으로 공차 축소

#### [NEW] [doosan_place_env_cfg.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/place/doosan_place_env_cfg.py)
- `PlaceEnvCfg`를 상속한 두산 E0509 특화 환경
- `DoosanPlaceEnvCfg_PLAY` 포함

#### [NEW] [mdp/](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/place/mdp/) 디렉토리:
  - `__init__.py`
  - `rewards.py` — `alignment_reward`, `insertion_reward`, `release_retreat_bonus`
  - `observations.py` — `slot_position_in_robot_frame`, `slot_tolerance`, `gripper_state`
  - `terminations.py` — `object_placed_success`, `collision_detected`

#### [NEW] [agents/](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/place/agents/) 디렉토리:
  - `__init__.py`
  - `doosan_place_skrl_ppo_cfg.yaml` — PPO 하이퍼파라미터

#### [NEW] [\_\_init\_\_.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/place/__init__.py)
- Gym 환경 등록: `Doosan-Place-v0`, `Doosan-Place-Play-v0`

---

### 4. 기존 파일 업데이트

#### [MODIFY] [rewards.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/rewards.py)
- 기존 `compute_shelf_rewards`에 독스트링 보완 및 타 태스크 참조 주석 추가
- 이 함수는 기존 Reach 태스크용으로 유지

#### [MODIFY] [task.md](file:///home/iyangim/smart-shelf-robot/src/custom/rl/cfgs/task.md)
- 새로 추가되는 Pick/Place 태스크 관련 체크리스트 항목 추가

---

## 생성 파일 목록 요약

| 태스크 | 파일 | 역할 |
|--------|------|------|
| 공용 | `cfgs/gripper_cfg.py` | RH-P12-RN-A 그리퍼 설정 |
| Pick | `envs/pick/__init__.py` | Gym 환경 등록 |
| Pick | `envs/pick/pick_env_cfg.py` | MDP 환경 기반 설정 (Scene/Obs/Act/Rew/Term) |
| Pick | `envs/pick/doosan_pick_env_cfg.py` | 두산 E0509 특화 환경 |
| Pick | `envs/pick/mdp/__init__.py` | MDP 모듈 export |
| Pick | `envs/pick/mdp/rewards.py` | Reach/Grasp/Lift 보상 함수 |
| Pick | `envs/pick/mdp/observations.py` | 물체 위치, 그리퍼 상태 관측 |
| Pick | `envs/pick/mdp/terminations.py` | 낙하/성공 종료 조건 |
| Pick | `envs/pick/agents/__init__.py` | 에이전트 패키지 |
| Pick | `envs/pick/agents/doosan_pick_skrl_ppo_cfg.yaml` | PPO 설정 |
| Place | `envs/place/__init__.py` | Gym 환경 등록 |
| Place | `envs/place/place_env_cfg.py` | MDP 환경 기반 설정 |
| Place | `envs/place/doosan_place_env_cfg.py` | 두산 E0509 특화 환경 |
| Place | `envs/place/mdp/__init__.py` | MDP 모듈 export |
| Place | `envs/place/mdp/rewards.py` | Alignment/Insertion/Release 보상 |
| Place | `envs/place/mdp/observations.py` | 슬롯 위치, 공차, 그리퍼 관측 |
| Place | `envs/place/mdp/terminations.py` | 배치 성공/충돌 종료 조건 |
| Place | `envs/place/agents/__init__.py` | 에이전트 패키지 |
| Place | `envs/place/agents/doosan_place_skrl_ppo_cfg.yaml` | PPO 설정 |

---

## Verification Plan

### Automated Tests
- Python import 검증: 각 모듈의 임포트 체인이 정상 동작하는지 확인
  ```bash
  python -c "from envs.pick.pick_env_cfg import PickEnvCfg; print('Pick OK')"
  python -c "from envs.place.place_env_cfg import PlaceEnvCfg; print('Place OK')"
  ```

### Manual Verification
- 코드 스타일이 `franka_isaaclab`의 Lift/Stack 태스크 패턴과 일관되는지 리뷰
- `task_define.md`의 Observation/Action/Reward 명세와 구현 코드의 일치 여부 확인
- 실제 Isaac Lab 환경에서의 실행은 그리퍼 USD 에셋이 준비된 후 진행
