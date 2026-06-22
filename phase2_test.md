# Phase 2: 두산 E0509 로봇 강화학습 마이그레이션 테스트 가이드

본 문서는 스마트 매대 정리 로봇 프로젝트 **Phase 2**의 두산 E0509 협동 로봇 자산 변환, 물리 및 제어 스펙 튜닝, 강화학습 정책 수렴 성능 평가를 위한 실행 검증 및 테스트 가이드입니다.

---

## 1. 물리 파라미터 및 기하학적 정합성 검증 (Asset & Geometry Verification)

### 1.1 정기구학(FK) 및 디폴트 포즈 검증
로봇 조인트의 한계 범위 및 홈 포즈(Home Pose) 설정이 올바르게 물리 엔진 상에 반영되는지 검사합니다.
* **테스트 명령어**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh src/custom/rl/scratch/check_fk.py
  ```
* **수행 및 검증 기준**:
  - 스크립트 실행 후 출력되는 조인트 초기화 자세가 매대(지면)를 수직 하강 방향으로 정상적으로 내려다보는지 확인합니다.
  - **홈 포즈 각도 정합성**: `joint_3`은 `1.57 rad (90도)`, `joint_5`는 `1.57 rad (90도)`, 나머지 조인트(`joint_1`, `joint_2`, `joint_4`, `joint_6`)는 `0.0 rad` 근처로 설정되어 특이점(Singularity) 현상이 제거되었는지 가시적으로 검증합니다.

### 1.2 액추에이터 제어 속성 확인
* **대상 파일**: [doosan.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/doosan.py)
* **물리 파라미터 타겟 값 검증**:
  - `stiffness` (강성): `800.0`
  - `damping` (감쇠): `40.0`
  - `friction` (마찰 계수): `0.1`
  - 해당 파라미터가 정확하게 반영되어, 급격한 각도 제어 시 관절 부위의 불필요한 떨림(오실레이션) 현상이 억제되는지 확인합니다.

---

## 2. MDP 및 제어 방식 안정성 평가 (Control Mode Test)

### 2.1 절대 위치 제어(Absolute Joint Position Control) 동작 검증
상대 제어($\Delta q$) 대비 절대 위치 제어의 작동 및 제한 조건을 검증합니다.
* **관절 동작 범위 스케일링 설정**:
  - `scale=0.5` 및 `use_default_offset=True` 인가 여부를 `doosan_joint_pos_env_cfg.py`에서 확인합니다.
* **행동 제한 테스트**:
  - 에이전트가 내리는 제어 명령에 의해 각 관절이 항상 홈 포즈 기준 **$\pm 0.5\text{ rad}$ ($\pm 28.6^\circ$) 이내**로 강제 구속되는지 테스트합니다. 이를 통해 자가 충돌(Self-Collision)이나 특이점으로 인한 드라이버 셧다운이 일어나지 않는지 확인합니다.

### 2.2 방향성 구속 및 보상 설계 평가
* **오리엔테이션 피치 제어**:
  - 툴플랜지가 목표에 접근할 때 피치 범위 제한인 `(math.pi, math.pi)`에 의해 제어되는지 확인합니다.
* **보상 가중치 튜닝 평가**:
  - Orientation Tracking 보상 가중치가 `-0.1`로 인가되어, 로봇 손목의 무의미한 회전이 억제되고 최종 툴플랜지(`link_6`)가 안정적인 수직 아래 방향을 유지하며 목표를 지향하는지 관측합니다.

---

## 3. 학습 실행 및 성능 지표 검증 (Training & Inference Evaluation)

### 3.1 두산 Reach 태스크 훈련 실행
* **테스트 명령어**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/train.py --task=Template-Doosan-Reach-v0 --headless
  ```
* **수렴 성능 기준**:
  - 훈련 로그 저장 폴더가 `reach_doosan_e0509` 하위 경로에 올바르게 기록되는지 확인합니다.
  - **평균 누적 보상값(Total Reward Mean) 검증**: 기존 성능(`0.5144` 내외) 대비 최소 **`0.7654`** 이상으로 48.8% 이상 대폭 상회 및 수렴하는지 확인합니다.

### 3.2 평가 시각화 및 ONNX 모델 변환 테스트
* **학습 체크포인트 플레이 검증**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/play.py \
      --task=Template-Doosan-Reach-Play-v0 \
      --checkpoint=logs/skrl/reach_doosan_e0509/<DATE_DIR>/checkpoints/best_agent.pt --video
  ```
* **ONNX 모델 배포용 파일 변환 검증**:
  - PyTorch 체크포인트를 아래 명령 등을 통해 ONNX 포맷으로 변환 시 에러 없이 파일이 추출되는지 확인합니다.
    ```bash
    ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh src/custom/rl/scratch/export_onnx.py
    # 변환된 'policy.onnx' 파일 생성 여부 확인
    ```
