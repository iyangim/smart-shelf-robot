# Phase 3: 가상 매대 시뮬레이션 통합 및 RL 태스크 규격 정의서 (Specification)

본 문서는 스마트 매대 정리 로봇 프로젝트 **Phase 3** 단계에서 구축 완료된 가상 매대 시뮬레이션 환경, USD 자산, 조작 시나리오 태스크 및 오류 수정 사항에 대한 스펙을 재정의합니다.

---

## 1. 가상 매대 시뮬레이션 USD 에셋 스펙 (USD Assets Spec)

* **자체 로봇 및 월드 에셋**:
  - [shelf_workspace_v2.usd](file:///home/iyangim/smart-shelf-robot/src/custom/rl/assets/shelf_workspace_v2.usd) (매대 환경 월드 데이터)
  - [e0509_gripper_isaac.usd](file:///home/iyangim/smart-shelf-robot/src/custom/rl/assets/e0509_gripper_isaac.usd) (그리퍼 결합 두산 로봇)
* **NVIDIA Nucleus 표준 에셋**:
  - **바스켓**: `small_KLT.usd` (NVIDIA Nucleus 공식 서버 자산으로 로컬 누락 문제 대체)
  - **진열 캐비닛**: `sektion_cabinet_instanceable.usd` (NVIDIA Nucleus 공식 서버 자산으로 로컬 누락 문제 대체)

---

## 2. 가상 매대 조작 시나리오 태스크 스펙 (Group 2 Tasks Spec)

가상 매대 정리의 자동화를 위해 설계된 **Group 2 (Smart-Shelf)**의 4대 핵심 조작 태스크 규격입니다.

1. **Task 1: 스캔 및 탐색 (Scan & Detect)**
   - **목표**: RGB-D 카메라 피드로부터 진열장 슬롯 공간의 바운딩 박스를 검출하고 타깃 포즈를 로봇 기준 프레임(`base_link`)으로 투영
2. **Task 2: 바스켓 물품 집기 (Doosan-Pick-v0)**
   - **목표**: 바스켓(`small_KLT.usd`) 내부 벽면 및 인접 사물과의 충돌을 회피하며 물체를 정밀 파지하여 수직 리프팅 수행
3. **Task 3: 장애물 회피 이송 (Transit)**
   - **목표**: cuRobo 가속 경로 기획(Path Planner)과 결합하여 매대 기둥 및 주변 간섭물을 우회하는 무충돌 6축 관절 궤적 생성
4. **Task 4: 매대 정밀 진열 (Doosan-Place-v0)**
   - **목표**: 수직 하강이 제한된 매대 공간 특성을 고려해 수평 진입 접근 후 물품 안착, 그리퍼 해제, 무충돌 후퇴 시퀀스 학습

---

## 3. 통합 구동 시나리오 모듈 스펙 (Integrated Modules Spec)

* **시나리오 메인 컨트롤러**: [stage8_main.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/rescent_env/stage8_main.py)
  - 월드 초기화, 카메라 뎁스 매핑, cuRobo 궤적 연산 및 실시간 조인트 가이드 전달
* **물성 정의 모듈**: [snack_bag_module.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/rescent_env/snack_bag_module.py)
  - 과자 패키지(Snack Bag) 모델의 물리 속성(Mass, Friction, Collision)을 시뮬레이터 내부에 동적 주입 및 배치

---

## 4. 디버깅 및 트러블슈팅 정합 내역 (Troubleshooting Spec)

1. **Frame Transformer 기준 프레임명 수정**:
   - 기존의 잘못 설정된 `link_0` ➔ 실제 조인트명인 **`base_link`**로 일체 정정
2. **조인트 이산화 명칭 통일**:
   - Place 환경 내 초기 조인트 각도 지정에 쓰이던 `joint1` 형태의 변수를 USD 에셋 명세에 맞춰 **`joint_1`** 형태로 통일
3. **종료 조건 매개변수 오류 디버깅**:
   - `mdp.object_dropped` 종료 필터 내 잘못 할당된 `asset_cfg` 파라미터 ➔ **`object_cfg`**로 수정 적용
4. **Gym 에이전트 경로 에러 방지**:
   - `envs/lift/agents/` 디렉터리에 빈 [\_\_init\_\_.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/envs/lift/agents/__init__.py) 파일을 생성하여 파이썬 모듈 패키지로 인식하게 하고 경로 로더 NoneType 에러 제거
5. **하드코딩 홈 디렉터리 경로 전면 수정**:
   - `stage8_main.py` 및 `snack_bag_module.py`의 이전 개발 서버 경로 `"/home/devuser/..."` ➔ 사용자 워크스페이스인 `"/home/iyangim/smart-shelf-robot/..."`로 일체 자동 치환

---

## 5. 실행 및 훈련 검증 명령어 (Verification Commands)

* **의존성 구문 분석 검증 (Compile Check)**:
  ```bash
  python3 -m py_compile src/custom/rl/rescent_env/stage8_main.py
  python3 -m py_compile src/custom/rl/rescent_env/snack_bag_module.py
  ```
* **가상 매대 태스크 검증 훈련 실행 (Train)**:
  ```bash
  # Pick Task 검증 학습 (10 Iteration)
  third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/train.py --task=Doosan-Pick-v0 --headless --max_iterations 10

  # Place Task 검증 학습 (10 Iteration)
  third_party/IsaacLab/_isaac_sim/python.sh scripts/skrl/train.py --task=Doosan-Place-v0 --headless --max_iterations 10
  ```
