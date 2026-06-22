# Phase 4: 실물 로봇 배포 및 하드웨어 정합 규격 정의서 (Specification)

본 문서는 스마트 매대 정리 로봇 프로젝트 **Phase 4** 단계에서 구축 완료된 실하드웨어 이식 아키텍처, ROS 2 통신 인터페이스, 센서 정합 및 안전 조치 규격 스펙을 정의합니다.

---

## 1. Sim-to-Real 및 VLA-Diffusion 제어 엔진 스펙 (Inference & VLA Spec)

* **VLA-Diffusion 비동기 제어 브릿지**:
  - 패키지: `smart_shelf_robot`
  - 노드: `vla_bridge_node.py`
  - 역할: 고수준 자연어 명령 수집 및 이미지 구독(`/camera/color/image_raw`), `MultiThreadedExecutor` 스핀을 활용하여 교착 상태(deadlock)를 예방하는 비동기 Action Server 구동
* **Diffusion Policy 실시간 추론 파이프라인**:
  - 노드: `diffusion_inference_node.py`
  - 역할: 30Hz 주기로 동작하며, LeRobot Diffusion Policy 가중치를 시뮬레이션 및 추론하여 `/dsr01/servol_cmd` 토픽으로 7차원 변위 벡터 퍼블리시
  - 필터: 실물 로봇 안전 보호를 위한 지수이동평균(EMA) 필터 적용 ($\alpha = 0.2$)
* **ONNX 모델 변환**:
  - [export_onnx.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/scratch/export_onnx.py) 스크립트를 사용하여 PyTorch `.pt` 가중치를 `policy.onnx`로 내보냄
  - 입력 관측 공간의 평균/분산 정규화(Normalizer) 전처리 연산을 모델에 바인딩

---

## 2. ROS 2 핵심 통신 및 빌드 환경 규격 (ROS 2 Humble Spec)

* **사용자 정의 ROS 2 인터페이스 패키지**: `custom_interfaces`
  - 정의 파일: `action/ShelfManipulate.action`
  - 액션 사양:
    ```text
    # Goal
    string instruction
    ---
    # Result
    bool success
    ---
    # Feedback
    string current_status
    geometry_msgs/PoseStamped macro_target
    ```
* **관절 제어 명령**:
  - 발행 토픽: `/policy/joint_targets`
  - 제어 공식: $q_{\text{target}} = q_{\text{default}} + a \times 0.5$ (안전을 위한 변위 0.5배 스케일링 필터링 탑재)
* **빌드 의존성 및 환경**:
  - 빌드 도구: `colcon` (`colcon-common-extensions` 패키지를 콘다 환경에 주입)
  - 파이선 파서 라이브러리: `lark`
  - 템플릿 매핑 빌드 도구: `empy==3.3.4` (Humble 빌드 호환성을 위해 4.x에서 3.x 버전으로 하향 조정)

---

## 3. 센서 좌표 및 오차 정합 스펙 (Sensor Calibration Spec)

* **핸드아이 캘리브레이션 (Hand-Eye Calibration)**:
  - 변환 매트릭스 파일: [calibration_result.npz](file:///home/iyangim/smart-shelf-robot/src/vision/calibration_result.npz)
  - 내용: Eye-to-Hand 구조 카메라와 로봇 베이스 기준 프레임 간의 3D 공간 변환 행렬 ($T_{\text{cam2base}}$) 수입 적용 (공간 오차 범위 `5mm` 이내 타깃)
  - 예외 처리: [object_tracking_node.py](file:///home/iyangim/smart-shelf-robot/src/external/e0509_gripper_description/scripts/object_tracking_node.py) 내 `T_cam_to_base` 및 `T_cam2base` 키 호환 로더 적용
* **동적 카메라 매트릭스 보정 (Dynamic Intrinsics)**:
  - 파일: [pointcloud_node.py](file:///home/iyangim/smart-shelf-robot/src/custom/vision/pointcloud_node.py)
  - 내용: 내부 파라미터 상수를 하드코딩하지 않고 `/camera/depth/camera_info` 토픽을 실시간으로 파싱하여 $fx, fy, cx, cy$ 값을 갱신하여 3D 재투영 오차 최소화

---

## 4. 시퀀서 및 이중 안전 조치 규격 (Safety & FSM Spec)

* **FSM 메인 컨트롤러**: `main_controller_node.py`
  - 상태 머신 기반 순차 단계 통제: Scan (탐색) ➔ Pick (파지) ➔ Transit (무충돌 이송) ➔ Place (수평 진입 진열) ➔ Home (복귀)
* **이중 안전 가드라인**:
  - **소프트웨어 가드**: 갑작스러운 큰 제어값 변경(액션 점프)에 대비한 변위 차단 완충 필터링 구현
  - **하드웨어 가드**: 관절 구동 한계점(Joint Limit) 제어 및 이상 전압/과전류 발생 시 모터 차단 긴급 정지 기능 연동

---

## 5. 실시간 모니터링 텔레메트리 (Telemetry Dashboard Spec)

* **백엔드 서버**: [server.py](file:///home/iyangim/smart-shelf-robot/src/dashboard/server.py) (ROS 2 토픽 집계 및 JSON Web Socket 전송)
* **프론트엔드**: [web/](file:///home/iyangim/smart-shelf-robot/web/) (React 기반 실시간 시각 대시보드)
* **표시 지표**: 로봇 6축 실시간 조인트 각도/전류, 카메라 컬러 피드 영상 및 상태 알람 로그 시각화

