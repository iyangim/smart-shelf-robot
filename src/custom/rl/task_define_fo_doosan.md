실물 Doosan E0509 로봇과 Robotis RH-P12-RN-A 그리퍼, Intel RealSense D455F 카메라 환경에 맞추어 전체 공정을 체계적으로 분할하고, [iyangim/franka_isaaclab](https://github.com/iyangim/franka_isaaclab)의 Task 정의 스타일(MDP Observation/Action, 단계별 Reward)을 벤치마킹하여 **Sim-to-Real과 하이브리드 제어가 가능하도록 태스크 가이드를 설계**했습니다.

현재 수행하려는 전체 시나리오는 고차원 작업(Task Planning)이 필요하므로, 강화학습(RL) 단독으로 전체를 학습하기보다는 **[Tom-Forsyth/LCPMotionPlanner](https://github.com/Tom-Forsyth/LCPMotionPlanner)와 같은 환경 결정론적 모션 플래너 알고리즘과 강화학습을 결합한 하이브리드 방식**이 실물 로봇 적용(Sim-to-Real)에 가장 안전하고 효율적입니다.

---

## 1. 전체 파이프라인 태스크 분할 (Task Decomposition)

전체 공정을 로봇의 제어 특성과 센서 데이터 흐름에 따라 **4가지 핵심 태스크**로 분할합니다.

```
[Task 1: Scan & Detect] ➔ [Task 2: Pick-up (RL)] ➔ [Task 3: Transit (LCP)] ➔ [Task 4: Place (RL)]
   (매대 비어있는 정보 탐색)      (바구니 물품 파지)         (매대 앞까지 안전 이동)      (정밀 배치 및 정렬)

```

---

## 2. 각 태스크별 상세 정의 및 추천 알고리즘

### Task 1: Shelf & Basket Scan (매대 및 바구니 인지)

* **목적**: RealSense D455F 카메라를 활용하여 매대의 비어있는 공간(Target Slot)과 바구니 안의 물품(Object)의 3D 포즈를 추정합니다.
* **수행 방식**:
* 로봇을 Scan 포즈로 이동시킨 뒤, 카메라 피드로부터 YOLO 또는 SAM을 사용하여 물체와 매대 슬롯을 세그멘테이션합니다.
* Depth 데이터를 결합하여 베이스 좌표계 기준 물체의 3D 위치 및 자세($[x, y, z, q_w, q_x, q_y, q_z]$)를 계산해 TF 프레임(`/object_frame`, `/empty_slot_frame`)으로 발행합니다.


* **추천 알고리즘**: **YOLOv8/v10 + PointCloud Pose Estimation (결정론적 비전 알고리즘)**

---

### Task 2: Object Pick-up (물품 정밀 파지)

* **목적**: 바구니 안의 임의의 자세로 놓인 물체를 로보티즈 RH-P12-RN-A 그리퍼로 미끄러짐 없이 안전하게 집어 올립니다.
* **추천 알고리즘**: **Model-free 지각-제어 엔드투엔드 강화학습 (PPO)**
* *이유*: 바구니 경계면과의 접촉, 물체의 미끄러짐 등 복잡한 접촉 역학(Contact Dynamics)은 수학적 궤적 계획보다 IsaacLab에서 정밀하게 모사하여 학습된 RL Policy가 실물 환경에서 훨씬 유연하게 대응합니다.



#### 📝 [franka_isaaclab] 스타일 MDP 환경 정의

* **Observation Space (관측치)**: `[24 + Gripper_dim]`
* 두산 로봇 현재 관절 각도 및 속도 (6 DoF)
* 엔드이펙터(그리퍼 중심)의 현재 Pose 및 선속도/각속도
* RealSense로 추정된 바구니 내 타겟 물체의 Pose ($[x, y, z, q_{wxyz}]$)
* RH-P12-RN-A 그리퍼의 현재 손가락 개구량(Opening Width) 및 가해지는 의사 토크 정보


* **Action Space (행동 출력)**: `[6 + 1]`
* 두산 로봇 관절 6개의 목표 조인트 위치 변위량 ($\Delta q$) 또는 조인트 속도 명령
* 그리퍼 제어 명령 (0: 열림, 1: 닫힘 / 물성에 따른 목표 파지력 제어 신호)


* **Reward Function (보상 설계)**:
* `Reach Reward`: 그리퍼 중심과 물체 중심 사이의 거리가 가까워질 수록 큰 보상 ($r_{\text{reach}} = \tanh(\omega \cdot \|p_{\text{ee}} - p_{\text{obj}}\|$))
* `Grasp Bonus`: 그리퍼가 물체와 접촉(Contact Axis 체크)하고 손가락 사이 거리가 물체 폭보다 작아지면 부여되는 정적 보상
* `Lift Reward`: 물체가 바구니 바닥 지면($z_{\text{bottom}}$)보다 임계치 이상으로 높아졌을 때 주는 누적 보상
* `Action Penalty`: 실물 로봇의 저크(Jerk)를 줄이기 위한 가속도 및 갑작스러운 액션 변화량 패널티



---

### Task 3: Obstacle-Free Transit (매대 이동)

* **목적**: 물품을 파지한 상태에서 바구니 주변 및 매대 프레임과 충돌하지 않고 안전하게 비어있는 매대 슬롯 앞까지 이동합니다.
* **추천 알고리즘**: **[LCPMotionPlanner](https://github.com/Tom-Forsyth/LCPMotionPlanner) (Task Space Complementarity-based Planner)**
* *이유*: 물체를 안전하게 쥐고 이동하는 구간은 강화학습으로 학습하려면 장애물 회피 시 과도한 탐색 시간이 걸리고 실물 적용 시 위험합니다.
* 작업 공간(Task Space) 내에서 매대 기둥 등의 장애물 회피 조건을 선형 상보성 문제(LCP, Linear Complementarity Problem)로 공식화하고, 이를 자코비안 영공간(Jacobian Null-Space Projection)에 투영하는 LCP 플래너를 사용하면, 엔드이펙터가 물건을 수평으로 유지하는 구속 조건을 엄격히 만족하면서도 주변 구조물을 유연하게 우회하는 안전한 최적 궤적을 실시간으로 계산해낼 수 있습니다.



---

### Task 4: Shelf Placing & Alignment (매대 정밀 적재)

* **목적**: 슬롯 내부의 벽면이나 다른 물품과 충돌하지 않고, 좁은 매대 공간 안에 물체를 정확히 정렬하여 내려놓은 뒤 그리퍼를 안전하게 빼냅니다.
* **추천 알고리즘**: **Curriculum 기반 강화학습 (PPO) 또는 가상 임피던스 제어**
* *이유*: 매대 깊숙이 물건을 밀어 넣을 때 발생하는 접촉력과 좁은 틈새 공차 문제를 해결하는 데 탁월합니다.



#### 📝 [franka_isaaclab] 스타일 MDP 환경 정의

* **Observation Space (관측치)**:
* 두산 로봇 현재 관절 정보 및 엔드이펙터 포즈
* 타겟 매대 빈 슬롯 중심의 3D Pose 및 슬롯 내부 진입 허용 공차 벡터
* 그리퍼 정보


* **Action Space (행동 출력)**: `[6 + 1]` (조인트 제어 명령 및 그리퍼 강제 해제 신호)
* **Reward Function (보상 설계)**:
* `Alignment Reward`: 물체의 정면 벡터와 매대 슬롯의 깊이 방향 벡트가 평행을 이룰 때 주어지는 코사인 유사도 보상
* `Insertion Reward`: 슬롯 입구를 통과하여 내부 축 방향($x$ 또는 $y$) 깊숙이 안정적으로 진입할 때 부여되는 보상
* `Release & Retreat Bonus`: 물체를 내려놓은 상태에서 그리퍼를 열고, 물체를 건드리지 않은 채 외곽 방향으로 안전하게 조인트를 수납할 때 주는 보상



---

## 3. 실하드웨어 이식을 위한 개발 로드맵 추천

1. **Task 2와 Task 4의 가상 학습 (IsaacLab)**: 두산 E0509와 RH-P12-RN-A 자산(Asset)을 로드하여 각각 **물품 파지(Pick)** 환경과 **매대 적재(Place)** 독립 환경을 생성하고 SKRL 패키지를 통해 최적의 Policy(`*.onnx`)를 개별 도출합니다.
2. **LCP 모션 플래너 코어 연동**: `src/custom/motion/`에 C++ 또는 Python 바인딩된 LCPMotionPlanner 라이브러리를 배치하고, 매대와 바구니의 경계면(Primitive Shapes)을 장애물로 등록합니다.
3. **ROS2 메인 상태머신(`main_controller_node.py`) 설계**:
* `State 0`: 초기 홈 자세 이동
* `State 1`: Task 1 수행 (비전 토픽 대기 및 타겟 포즈 확정)
* `State 2`: Task 2 구동 (파지 RL 추론 노드 활성화 ➔ 물건 집기 성공 확인)
* `State 3`: Task 3 구동 (LCP 플래너에 목적지 전달 ➔ 실물 드라이버 궤적 추종 구동)
* `State 4`: Task 4 구동 (적재 RL 추론 노드 활성화 ➔ 배치 완료 후 초기 자세 복귀)



v2.


# Smart Shelf Robot 4-태스크 파이프라인 구현 계획서

본 계획서는 `task_define.md` 및 `EXECUTION_GUIDE.md`를 바탕으로, 편의점 매대 정리 로봇(`smart-shelf-robot`)의 실제 목표 작업인 4단계 파이프라인([Task 1: Scan] ➔ [Task 2: Pick-up] ➔ [Task 3: Transit] ➔ [Task 4: Place])을 단계적으로 구축하기 위한 상세 실행 계획입니다.

이전 Franka 로봇의 학습 정의를 두산 로봇에 반영하기 위해 작성된 기존 RL 환경 설정 코드(예: `envs/pick/`, `envs/place/` 하위 파일) 및 이전 태스크 정의는 그대로 유지하며 변경하지 않습니다.

---

## 1. 배경 및 현황

현재 로봇 시스템은 ROS2 Humble, Isaac Sim, RealSense D455F 카메라, Robotis RH-P12-RN-A 그리퍼로 구성되어 있으며, 로컬 환경 설정 파일들이 다음과 같이 준비되어 있습니다:
1. **파지력 설정** (`config/grasp_force_params.yaml`): 물품 클래스(`snack`, `bottle`, `can`)별 전류값과 파지 전략 명세
2. **적재 위치 설정** (`config/place_targets.yaml`): 물품 클래스별 매대 적재 좌표(`base_link` 기준) 및 홈 관절 상태
3. **에셋 변환 설정** (`src/custom/rl/assets/config.yaml`): URDF에서 USD 에셋으로 변환을 위한 물리 제약/제어 타입 명세

본 계획서에서는 실제 하드웨어 구동 및 가상 모드 통합 테스트를 위해 **Task 1: Scan & Detect**부터 순차적으로 필요한 구성 요소를 준비하고 실행 계획을 갱신합니다.

---

## 2. User Review Required

> [!IMPORTANT]
> **하드코딩된 파일 경로 수정**
> - 현재 `detection_node.py` 및 `pose_estimation_node.py`에 YOLO 모델 가중치(`pose_robust_seg.pt`) 및 핸드아이 캘리브레이션 결과(`calibration_result.npz`)의 기본 경로가 `/home/fastcampus/...`로 외부 환경 경로로 지정되어 있습니다.
> - 이를 현재 사용자 환경인 `/home/iyangim/smart-shelf-robot/...` 하위 혹은 환경 변수 기반으로 동적 로드하도록 변경해야 합니다.

> [!WARNING]
> **RealSense 뎁스-컬러 이미지 정합 정합성**
> - `EXECUTION_GUIDE.md` 9절에 명시된 바와 같이, RealSense 렌즈 오프셋으로 인한 3D 위치 오차를 막기 위해 비전 노드들이 구독하는 뎁스 토픽을 `/camera/depth/image_rect_raw`에서 `/camera/aligned_depth_to_color/image_raw`로 일괄 변경해야 합니다.

---

## 3. 태스크별 상세 실행 및 구성 계획 (Task-by-Task Configuration)

### 3.1. Task 1: Scan & Detect (매대 및 바구니 인지)
- **목표**: RealSense 카메라 토픽을 정합하여 YOLO/SAM 기반 2D 감지 및 3D 포즈를 추정하고 `/shelf/empty_slot` 및 `/object_pose` 발행을 검증합니다.
- **예정 변경 사항**:
  - `src/custom/vision/pose_estimation_node.py` 및 `pointcloud_node.py` 수정:
    - 뎁스 구독 토픽을 `/camera/aligned_depth_to_color/image_raw`로 변경
    - `DEFAULT_CALIB` 경로를 `/home/iyangim/smart-shelf-robot/` 내부의 실제 경로로 수정 (또는 환경 파라미터로 매칭)
    - `pointcloud_node.py` 내의 하드코딩된 내부 파라미터를 `/camera/depth/camera_info` 토픽에서 동적으로 수신받아 3D PCA 연산의 정합성을 보장하도록 개선

### 3.2. Task 2: Object Pick-up (물품 정밀 파지)
- **목표**: 바구니 안의 물품을 감지한 후 물성에 맞는 파지력으로 안전하게 파지합니다.
- **예정 구성**:
  - `config/grasp_force_params.yaml`에 정의된 클래스별 전류 파라미터(`force`, `max_force`, `position`)를 `main_controller_node.py` 및 `gripper_node.py`에서 파지 단계(`GRASPING`) 수행 시 동적으로 로드하여 `/gripper/grasp` 액션의 전류값 한계치로 설정합니다.
  - Robotis RH-P12-RN-A 그리퍼의 4개 관절 구동(`gripper_rh_r1`, `gripper_rh_l1`, `gripper_rh_r2`, `gripper_rh_l2`)에 개구량을 반영합니다.

### 3.3. Task 3: Obstacle-Free Transit (매대 이동)
- **목표**: 물품 파지 완료 상태에서 매대 슬롯까지 충돌 없이 안전하게 이동하기 위한 LCP 모션 플래너를 준비합니다.
- **예정 구성**:
  - `src/custom/motion/arm_controller_node.py`와 cuRobo 플래너 노드(`curobo_planner_node.py`)의 연결 상태 점검
  - 바구니 프레임 및 매대 슬롯 주변의 장애물 구체 정보(`e0509_spheres.yml`)를 기반으로 충돌 방지 궤적 생성을 활성화합니다.

### 3.4. Task 4: Shelf Placing & Alignment (매대 정밀 적재)
- **목표**: 빈 매대 슬롯에 물품을 정렬하여 내려놓고 안전하게 로봇을 수납합니다.
- **예정 구성**:
  - `config/place_targets.yaml`에 명세된 각 물품 클래스별 목표 위치 및 자세를 로드하여 `/place_target` 토픽으로 발행
  - `main_controller_node.py`의 `PLACING` 상태에서 타겟 위치 하강 ➔ 그리퍼 릴리즈(`/gripper/open`) ➔ z축 방향으로 안전 수납(Retreat) 서비스 순차 트리거 구현 및 검증

---

## 4. Verification Plan

### Automated Tests
- 비전 및 모션 노드들이 업데이트된 설정과 토픽 구조 하에서 정상 임포트되는지 확인:
  ```bash
  python3 -c "import rclpy; from custom.vision.pose_estimation_node import PoseEstimationNode; print('Vision OK')"
  python3 -c "import rclpy; from custom.integration.main_controller_node import MainControllerNode; print('Integration OK')"
  ```

### Manual Verification
- `bringup.launch.py`를 Virtual 모드로 런칭하여 `/camera/aligned_depth_to_color/image_raw` 토픽 발행 상태 확인
- `ros2 topic echo /object_pose` 명령을 통해 발행되는 3D 좌표가 base_link 기준으로 유효한 값인지 검증
