# Phase 1: 개발 환경 및 강화학습 시스템 테스트 가이드

본 문서는 스마트 매대 정리 로봇 프로젝트 **Phase 1**의 개발 환경 사양 정합성, RL 알고리즘 구동 및 기본 태스크 수렴을 확인하기 위한 실행 검증 및 성능 평가 테스트 가이드입니다.

---

## 1. 개발 환경 정합성 검증 (Environment Verification)

### 1.1 하드웨어 및 운영체제 정보 확인
가동 환경이 사양에 정의된 하드웨어 및 OS 스펙과 부합하는지 명령어를 통해 검증합니다.
* **OS 버전 확인**:
  ```bash
  lsb_release -a
  # 출력결과에 Ubuntu 22.04 LTS가 표기되는지 확인
  ```
* **GPU 드라이버 및 VRAM 용량 확인**:
  ```bash
  nvidia-smi
  # Driver 버전이 580.x 이상(최소 535.x 이상)인지, RTX 5080 Laptop (16GB VRAM) 장치가 올바르게 표시되는지 확인
  ```
* **CUDA 런타임 버전 확인**:
  ```bash
  nvcc --version
  # 호스트 CUDA 환경이 12.8인지 확인
  ```

### 1.2 소프트웨어 스택 버전 검증
Isaac Sim 내장 파이썬 환경의 핵심 의존성 패키지 버전을 검사합니다.
* **Isaac Sim 런타임 버전 검증**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh -c "import isaacsim; print(isaacsim.__version__)"
  # '5.1.0-rc.19' 또는 이에 호환되는 5.1.0 버전이 출력되는지 검증
  ```
* **Isaac Lab 버전 검증**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh -c "import isaaclab; print(isaaclab.__version__)"
  # '2.3.2' 버전이 정상 출력되는지 검증
  ```
* **PyTorch 및 skrl 버전 검증**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh -c "import torch; import skrl; print('Torch:', torch.__version__); print('skrl:', skrl.__version__)"
  # Torch: 2.7.0+cu128, skrl: 2.1.0 (v2.x 규격) 출력 확인
  ```

---

## 2. 의존성 및 설정 디버깅 검증 (Troubleshooting Test)

### 2.1 Hydra 의존성 확인
* **테스트 방법**: Hydra 설치 누락 상태에서 발생하는 `ImportError` 해결 여부 검증
* **확인 단계**:
  1. `hydra-core` 패키지 설치:
     ```bash
     ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh -m pip install hydra-core
     ```
  2. 다음 명령어로 임포트 오류가 발생하지 않는지 검증:
     ```bash
     ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh -c "import hydra"
     ```

### 2.2 입력 키 설정 검증
* **테스트 방법**: skrl v2.x 규격에 맞게 설정 파일 내 관측값 입력 키가 변경되었는지 확인
* **검증 대상 파일**: `skrl_ppo_cfg.yaml` (또는 관련 RL 설정 파일)
* **확인 사항**:
  - `STATES`가 아닌 `OBSERVATIONS`로 입력 매핑이 구성되어 있는지 확인하여 `NoneType object has no attribute shape` 에러의 재발을 방지합니다.

---

## 3. 강화학습(RL) 실행 및 수렴 검증 (Execution & Performance Evaluation)

### 3.1 Reach 태스크 학습 구동 (Train)
* **테스트 명령어**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/train.py --task=Template-Reach-v0
  ```
* **성능 평가 지표 (수렴 기준)**:
  - **학습 연산 속도**: 콘솔에 표기되는 연산 속도가 약 **15 it/s** 이상을 지속적으로 유지하는지 확인합니다.
  - **보상 수렴 곡선**: 훈련 과정 중 `Total Reward Mean` 지표가 지속적으로 우상향하여 최종 목표 위치 수렴 레벨에 부합하는지 TensorBoard 로그 등을 통해 검증합니다.

### 3.2 평가 스크립트 API 규격 검증 (Play)
* **테스트 명령어**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/play.py \
      --task=Template-Reach-Play-v0 \
      --checkpoint=logs/skrl/reach_franka/<TIMESTAMP>/checkpoints/best_agent.pt --video
  ```
* **동작 검증 기준**:
  - `skrl v2.x` API가 정상 적용되어 `enable_training_mode(False)`로 작동해야 합니다.
  - `act()` 함수 호출 시 `states` 위치 인자에 `None`이 올바르게 지정되어 오류 없이 시각화 창이 구동되는지 확인합니다.
  - `--video` 옵션 적용 시 시뮬레이션 플레이 녹화 파일이 지정 경로에 성공적으로 저장되는지 확인합니다.
