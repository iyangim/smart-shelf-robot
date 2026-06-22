# Phase 2: 두산 E0509 로봇 강화학습 마이그레이션 규격 정의서 (Specification)

본 문서는 스마트 매대 정리 로봇 프로젝트 **Phase 2** 단계에서 두산 E0509 로봇 환경 마이그레이션 시 튜닝 완료된 물리적 제어 파라미터 및 강화학습(RL) 아키텍처의 스펙을 재정의합니다.

---

## 1. 두산 E0509 로봇 물리 및 제어 스펙 (Robot Asset Spec)

* **대상 에셋 파일**: [doosan.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/doosan.py)
* **액추에이터 파라미터 (Implicit Actuator Cfg)**:
  * **강성 (stiffness)**: `800.0`
  * **댐핑 (damping)**: `40.0`
  * **마찰 계수 (friction)**: `0.1` (고강성 조인트 구동 시 떨림 현상 보정 목적)
* **조인트 구성 매핑**:
  * 조인트명 `joint_1` ~ `joint_6`로 명시적 선언 (USD 조인트명 대조 확인)
* **홈 포즈 설정 (Home Pose)**:
  * 로봇이 작업 매대(지면)를 수직 방향으로 똑바로 내려다보도록 각 조인트 초기 각도 설정
  * `joint_3`: `1.57 rad (90도)`
  * `joint_5`: `1.57 rad (90도)`
  * 기타 조인트: `0.0 rad`

---

## 2. 강화학습 환경 및 행동 공간 규격 (MDP & Action Space Spec)

* **대상 환경 파일**: [doosan_joint_pos_env_cfg.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/doosan_joint_pos_env_cfg.py)
* **제어 모드**: 절대 위치 제어 (**Absolute Joint Position Control**)
  - 상대 제어($\Delta q$) 사용 시 발생하는 관절 누적 드리프트 및 특이점(Singularity) 문제를 방지하기 위해 절대 제어 복구
* **행동 범위 스케일링 (Action Scaling)**:
  - `scale=0.5` 및 `use_default_offset=True`
  - 에이전트의 관절 움직임 한계를 홈 포즈 기준 항상 **$\pm 0.5\text{ rad}$ ($\pm 28.6^\circ$) 영역 안으로 강밀 구속**
* **방향성 구속 (Orientation constraint)**:
  - 타깃 위치 도달 시 손목 축의 방향성 Pitch 제어 범위를 `(math.pi, math.pi)`로 구속

---

## 3. 보상 함수 정의 규격 (Reward Function Spec)

| 보상 항목 (Reward Term) | 가중치 (Weight) | 목적 |
|---------------------|---------------|------|
| **Position Tracking** | `1.0` | 최종 툴플랜지(`link_6`)가 목표 위치에 수렴 유도 |
| **Orientation Tracking** | `-0.1` | 툴플랜지가 수직 아래 방향을 안정적으로 유지하도록 구속 |
| **Action Rate Penalty** | `-0.01` | 제어 명령 변위의 급격한 불연속 변화(떨림 현상) 방지 |
| **Joint Velocity Penalty** | `-0.01` | 관절 구동 속도가 허용 한계를 초과하여 과도하게 움직이는 것 제한 |

---

## 4. 학습 알고리즘 및 등록 태스크 (Training & Registration)

* **학습 백엔드 설정**: [doosan_skrl_ppo_cfg.yaml](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/doosan_skrl_ppo_cfg.yaml)
  - **신경망 구조**: [64, 64] MLP
  - **학습률**: `1.0e-03`
  - **에폭 수**: `5`
  - **로그 저장 폴더**: `reach_doosan_e0509`
* **Gym 등록 태스크**:
  - `Template-Doosan-Reach-v0` (학습 환경)
  - `Template-Doosan-Reach-Play-v0` (시각 재생 및 평가 환경)
* **최적 성능 수렴 성과**:
  - 평균 누적 보상값(Total Reward Mean)이 기존 대비 **48.8% 향상된 `0.7654`**로 안정적인 수렴 확인

---

## 5. 실행 및 검증 명령어 (Execution Commands)

* **정기구학 및 디폴트 포즈 디버깅**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh src/custom/rl/scratch/check_fk.py
  ```
* **두산 Reach 태스크 훈련 실행**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/train.py --task=Template-Doosan-Reach-v0 --headless
  ```
* **가중치 파일 시뮬레이션 플레이 검증**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/play.py \
      --task=Template-Doosan-Reach-Play-v0 \
      --checkpoint=logs/skrl/reach_doosan_e0509/<DATE_DIR>/checkpoints/best_agent.pt --video
  ```
