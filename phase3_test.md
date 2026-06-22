# Phase 3: 가상 매대 시뮬레이션 통합 및 RL 태스크 테스트 가이드

본 문서는 스마트 매대 정리 로봇 프로젝트 **Phase 3**의 가상 매대 시뮬레이션 환경 구축, 외부 USD 자산 연동, 4대 핵심 조작 시나리오 태스크, 디버깅 내역의 실행 및 동작 검증을 위한 테스트 가이드입니다.

---

## 1. USD 에셋 로딩 및 시스템 의존성 검증 (USD Asset Verification)

### 1.1 외부 NVIDIA Nucleus 자산 온라인 로딩 검증
로컬 에셋 누락 문제를 우회하여 NVIDIA Nucleus 공용 서버의 자산이 실시간 캐싱되고 로드되는지 검증합니다.
* **검증 대상 에셋 및 매핑 상태**:
  - 로봇 결합 모델: [e0509_gripper_isaac.usd](file:///home/iyangim/smart-shelf-robot/src/custom/rl/assets/e0509_gripper_isaac.usd)
  - 매대 월드: [shelf_workspace_v2.usd](file:///home/iyangim/smart-shelf-robot/src/custom/rl/assets/shelf_workspace_v2.usd)
  - 바스켓 모델: `small_KLT.usd` (NVIDIA Nucleus 표준 에셋 매핑)
  - 진열장 캐비닛 모델: `sektion_cabinet_instanceable.usd` (NVIDIA Nucleus 표준 에셋 매핑)
* **테스트 방법**:
  - 가상 매대 태스크 실행 시 USD 로더 에러나 에셋 누락 크래시 없이 3D 뷰포트에 정상적으로 로드되는지 확인합니다.

### 1.2 소스 파일 구문 분석(Compile) 검증
워크스페이스 내 주요 모듈이 경로 불일치나 문법 오류 없이 로드되는지 컴파일 분석을 수행합니다.
* **컴파일 검증 명령어**:
  ```bash
  python3 -m py_compile src/custom/rl/rescent_env/stage8_main.py
  python3 -m py_compile src/custom/rl/rescent_env/snack_bag_module.py
  ```
* **동작 검증 기준**:
  - 명령어 실행 후 컴파일 에러 없이 종료되어야 합니다.
  - 특히 기존 개발 서버 경로인 `"/home/devuser/..."`가 사용자 워크스페이스인 `"/home/iyangim/smart-shelf-robot/..."`로 리팩토링되어 정상 인식되는지 검증합니다.

---

## 2. 디버깅 및 트러블슈팅 세부 정합성 확인 (Troubleshooting Verification)

### 2.1 기준 프레임명 수정 검증 (`base_link`)
* **검증 대상 파일**: `doosan_pick_env_cfg.py` 및 `doosan_place_env_cfg.py`
* **확인 사항**:
  - Frame Transformer 내 베이스 타깃 프레임명이 `link_0`에서 실제 조인트명인 **`base_link`**로 완벽하게 수정 반영되었는지 확인합니다. (`ValueError: Not all regular expressions are matched!` 에러 발생 방지)

### 2.2 조인트 변수 명칭 통일성 검증 (`joint_1`)
* **확인 사항**:
  - Place 환경 및 에셋 설정 코드 내 초기 관절 지정 시 기존 `joint1` 형태에서 USD 에셋 규격을 준수하는 언더바 형태인 **`joint_1`** ~ **`joint_6`**로 정확하게 사용 중인지 파싱 검증합니다.

### 2.3 Gym 에이전트 경로 에러 및 종료 조건 검증
* **패키지 정합 확인**:
  - `envs/lift/agents/` 디렉터리에 [\_\_init\_\_.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/lift/agents/__init__.py) 파일이 생성되어 파이썬 패키지로 올바르게 로드되는지 체크합니다.
* **매개변수 체크**:
  - `mdp.object_dropped` 종료 조건에 오기입되어 있던 `asset_cfg` 변수가 **`object_cfg`**로 변경 적용되어 훈련 중 예외를 던지지 않는지 확인합니다.

---

## 3. 조작 시나리오 태스크 통합 학습 검증 (RL Task Verification)

### 3.1 스마트 매대 4대 핵심 조작 시나리오 흐름 평가
1. **Task 1: Scan & Detect**: 카메라 피드 데이터를 로봇 프레임 `base_link` 기준 좌표로 변환하여 RL 에이전트 관측값에 정상 바인딩되는지 평가합니다.
2. **Task 2: Doosan-Pick-v0**: 좁은 바스켓 경계 조건 내에서 벽면과 물체 간 간섭을 최소화하며 물품을 정상 파지 및 리프팅하는지 평가합니다.
3. **Task 3: Transit**: cuRobo 모션 플래너와 연동하여 2.5D 포인트클라우드 장애물을 회피하는 충돌 없는 6축 경로가 생성되는지 검증합니다.
4. **Task 4: Doosan-Place-v0**: 수평 방향 진입 궤적 설계에 따라 매대 슬롯 안착 후 그리퍼가 물품을 놓고 무충돌 탈출 동작을 성공적으로 완료하는지 검증합니다.

### 3.2 훈련 스크립트 실행 및 이상 유무 평가
가상 매대 태스크 환경이 훈련 루프 초기 단계에서 에러 없이 안정적으로 텐서 연산을 지속하는지 10-Iteration 훈련 테스트를 수행합니다.
* **Pick 태스크 10-Iteration 테스트**:
  ```bash
  third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/train.py --task=Doosan-Pick-v0 --headless --max_iterations 10
  ```
* **Place 태스크 10-Iteration 테스트**:
  ```bash
  third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/train.py --task=Doosan-Place-v0 --headless --max_iterations 10
  ```
* **검증 합격 기준**:
  - 두 학습 명령 모두 환경 로드 실패, 경로 탐색기 오류, CUDA 메모리 에러 없이 정상적으로 10 Iteration 학습 로그를 생성하고 종료되어야 합니다.
