# Phase 1: 개발 환경 및 강화학습 시스템 규격 정의서 (Specification)

본 문서는 스마트 매대 정리 로봇 프로젝트 **Phase 1** 단계에서 구축 완료된 개발 환경 사양 및 강화학습(RL) 아키텍처의 스펙을 재정의합니다.

---

## 1. 하드웨어 및 운영체제 사양 (Hardware & OS Spec)

| 항목 | 상세 사양 | 비고 |
|------|-----------|------|
| **OS** | Ubuntu 22.04 LTS | ROS 2 Humble 및 Isaac Sim 공식 지원 환경 |
| **GPU** | NVIDIA RTX 5080 Laptop (16GB VRAM) | 대규모 병렬 물리 연산 및 렌더링 가속 |
| **NVIDIA Driver** | 580.x 이상 (535.x 이상 필수) | Omniverse/Isaac Sim 물리 엔진 구동 용도 |
| **CUDA** | 12.8 (호스트 cuRobo용) / 13.0 (Isaac Sim 내장) | 이원화된 가속 런타임 환경 정합 |

---

## 2. 시뮬레이터 및 의존성 라이브러리 스펙 (Software Stack)

| 구분 | 제품/라이브러리 | 버전 | 설치 환경 및 실행 방식 |
|------|-----------------|------|-------------------------|
| **물리 엔진** | NVIDIA Isaac Sim | 5.1.0-rc.19 | 3D USD 에셋 렌더링 및 카메라 센서 모사 |
| **RL 환경 프레임워크** | NVIDIA Isaac Lab | 2.3.2 | 경량 벡터화 환경 제어 API 및 로봇 제이션 |
| **런타임 파이썬** | Python | 3.11.13 | Isaac Sim 내장 파이썬 쉘 (`python.sh`)로 강제 구동 |
| **딥러닝 프레임워크** | PyTorch | 2.7.0+cu128 | GPU 가속 기반 텐서 연산 지원 |
| **RL 알고리즘 백엔드** | skrl | 2.1.0 (v2.x) | PyTorch 기반 경량 강화학습 프레임워크 |
| **환경 설정 파서** | hydra-core | 1.3.2 | 학습 태스크 매니저 설정 파싱 및 YAML 관리 |

---

## 3. 강화학습 (RL) 및 PPO 알고리즘 설정 규격 (RL Config Spec)

* **알고리즘**: PPO (Proximal Policy Optimization)
* **신경망 구조 (Policy & Value Networks)**:
  * **타입**: MLP (Multi-Layer Perceptron)
  * **은닉층 (Hidden Layers)**: `[64, 64]`
  * **활성화 함수 (Activation)**: ELU (Exponential Linear Unit)
* **학습 하이퍼파라미터 (Hyperparameters)**:
  * **학습률 (Learning Rate)**: `1.0e-03`
  * **미니배치 에폭 수 (Epochs)**: `5`
  * **할인 인자 (Discount Factor, $\gamma$)**: `0.99`
  * **경로 탐색 모드 (Evaluation Mode)**: `skrl v2.x` API 규격 적용 (`enable_training_mode(False)`)
* **입력 데이터 매핑**:
  * **관측값 키 (Observation Key)**: `OBSERVATIONS` (일반 관측치, `STATES` 키 미사용)
  * **수동 보정 사항**: `play.py` 내 `act` 함수 호출 시 `states` 위치 인자에 `None` 지정 명시화

---

## 4. Phase 1 검증 대상 태스크 스펙 (Target RL Tasks)

Phase 1에서 환경의 정합성을 검증하기 위해 Franka Panda 로봇 에셋을 활용하여 아래 3대 기초 조작 태스크를 완료하였습니다.

1. **Reach Task** (`Template-Reach-v0` / `Template-Reach-Play-v0`)
   - **목표**: 로봇의 최종 툴플랜지를 공간 상의 임의의 목표 3D 좌표로 이동 및 수렴
2. **Lift Task** (`Template-Lift-v0`)
   - **목표**: 작업대 위에 무작위로 스폰된 단일 큐브 블록을 그리퍼로 안전하게 집어 올려 지면으로부터 수직 상승
3. **Stack Task** (`Template-Stack-v0`)
   - **목표**: 집어 올린 큐브 블록을 아래에 고정된 다른 타겟 블록 상단에 정렬하여 충돌 없이 적층

---

## 5. 실행 및 디버깅 명령어 표준 (Execution Spec)

* **의존성 설치 (Isaac Sim 내장 환경)**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh -m pip install hydra-core
  ```
* **Reach 태스크 학습 수행 (Train)**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/train.py --task=Template-Reach-v0
  ```
* **학습 모델 시각 검증 및 비디오 녹화 (Play)**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/play.py \
      --task=Template-Reach-Play-v0 \
      --checkpoint=logs/skrl/reach_franka/<TIMESTAMP>/checkpoints/best_agent.pt --video
  ```
