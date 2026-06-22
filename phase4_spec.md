# Phase 4: 실물 로봇 배포 및 하드웨어 정합 규격 정의서 (Specification)

본 문서는 스마트 매대 정리 로봇 프로젝트 **Phase 4** 단계에서 구축 완료된 실하드웨어 이식 아키텍처, ROS 2 통신 인터페이스, 센서 정합 및 안전 조치 규격 스펙을 재정의합니다.

---

## 1. Sim-to-Real 정책 변환 및 추론 엔진 스펙 (Inference Spec)

* **ONNX 모델 변환**:
  - [export_onnx.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/scratch/export_onnx.py) 스크립트를 사용하여 PyTorch `.pt` 가중치를 `policy.onnx`로 내보냄
  - 입력 관측 공간의 평균/분산 정규화(Normalizer) 전처리 연산을 모델에 바인딩
* **ROS 2 추론 노드 스펙**: [policy_node.py](file:///home/iyangim/smart-shelf-robot/src/rl/policy_node.py)
  - **인공지능 추론 런타임**: `onnxruntime` (20Hz 이상 실시간 피드백 주기 달성)
  - **관절 매핑 정렬**: `/joint_states` 수신 시 각도 매핑의 무결성을 유지하기 위해 조인트 이름 기반 정렬 로직 적용
  - **타깃 변환**: 대상 물체 포즈 정보를 수신하여 `[w, x, y, z]` 쿼터니언 형태로 정합 후 정책 주입

---

## 2. ROS 2 핵심 통신 인터페이스 규격 (ROS 2 Humble Spec)

* **관절 제어 명령**:
  - 발행 토픽: `/policy/joint_targets`
  - 제어 공식: $q_{\text{target}} = q_{\text{default}} + a \times 0.5$ (안전을 위한 변위 0.5배 스케일링 필터링 탑재)
* **비전 토픽 구독**:
  - 컬러 카메라 피드: `/camera/color/image_raw`
  - 컬러 매핑 깊이 피드: `/camera/aligned_depth_to_color/image_raw`
  - 렌즈 내부 파라미터 정보: `/camera/depth/camera_info`
  - 타깃 위치 정보: `/object_pose` 및 세그멘테이션 포인트클라우드 `/object_pointcloud`

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
