# Phase 4: 실물 로봇 배포 및 하드웨어 정합 테스트 가이드

본 문서는 스마트 매대 정리 로봇 프로젝트 **Phase 4**의 Sim-to-Real 환경 실배포, ROS 2 Humble 인터페이스 연동, 핸드아이 캘리브레이션 정밀도 검증, 이중 안전 가드라인 및 대시보드 실시간 모니터링 체계를 테스트하기 위한 실행 가이드입니다.

---

## 1. Sim-to-Real 정책 변환 및 추론 성능 평가 (ONNX & Inference Test)

### 1.1 ONNX 모델로의 정상 변환 여부 검증
* **확인 파일**: [export_onnx.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/scratch/export_onnx.py)
* **검증 방법**:
  - 내보내기 수행 후 최종 생성된 `policy.onnx` 모델 내부에 입력 데이터 평균/분산 정규화 전처리(Normalizer) 연산 매핑이 올바르게 고착화되었는지 Netron 뷰어 또는 파이썬 스크립트 모듈 로드를 통해 검증합니다.

### 1.2 ROS 2 추론 노드 통신 주기 및 입력 매핑 검증
* **수행 명령어 (추론 노드 기동)**:
  ```bash
  ros2 run smart_shelf_robot policy_node
  # (실제 패키지 설정 경로 확인 후 실행)
  ```
* **성능 평가 지표 (추론 주기)**:
  - `onnxruntime` 백엔드 구동 하에서 실시간 추론 연산 속도가 **20Hz 이상**의 업데이트 속도를 유지하는지 측정합니다.
  - `/joint_states` 수신 시 임의의 관절 순서 변경에도 조인트 이름 매칭을 통해 정확히 가공된 센서 텐서가 추론 입력으로 공급되는지 확인합니다.

---

## 2. ROS 2 통신 인터페이스 및 센서 캘리브레이션 테스트 (ROS 2 & Calibration Test)

### 2.1 제어 명령 및 비전 토픽 메시지 모니터링
* **제어 궤적 명령 확인**:
  ```bash
  ros2 topic hz /policy/joint_targets
  # 발행 주기 확인
  ros2 topic echo /policy/joint_targets
  # 조인트 절대 명령의 변위 크기가 안전 배수 필터(0.5배 스케일링) 조건인 'q_default + action * 0.5' 범위 내에 속하는지 확인
  ```
* **비전 입력 정합 상태 검사**:
  - `/camera/aligned_depth_to_color/image_raw` 토픽이 누락 없이 퍼블리시되는지 점검합니다.
  - `/object_pose`의 3D 공간 좌표 및 방향 쿼터니언 `[w, x, y, z]` 값이 안정적으로 출력되는지 모니터링합니다.

### 2.2 공간 정합 및 동적 카메라 파라미터 매트릭스 검증
* **Hand-Eye Calibration 정밀도 평가**:
  - `calibration_result.npz`에서 추출한 카메라-로봇 베이스 3D 변환 행렬($T_{\text{cam2base}}$)을 실제 로봇 픽앤플레이스 작업에 주입했을 때, 공간 물리 정밀 오차 범위가 **5mm 이하**로 유지되는지 목표 지점 도달 테스트를 수행합니다.
  - `object_tracking_node.py` 실행 시 `T_cam_to_base`와 `T_cam2base` 키 네이밍이 호환되어 정상 동작하는지 테스트합니다.
* **동적 카메라 매트릭스 보정 검증**:
  - [pointcloud_node.py](file:///home/iyangim/smart-shelf-robot/src/custom/vision/pointcloud_node.py) 구동 중 `/camera/depth/camera_info` 토픽의 동적 내부 파라미터 $fx, fy, cx, cy$가 정상 로드 및 파싱되며, 렌즈 왜곡에 따른 3D 재투영 오차가 보정되는지 검증합니다.

---

## 3. 유한 상태 머신(FSM) 및 실시간 텔레메트리 연동 테스트 (FSM & Telemetry Test)

### 3.1 이중 안전장치 구동성 평가
* **소프트웨어 변위 가드 차단 테스트**:
  - 추론 결과가 비정상적인 액션 점프(순간적 이상 치수 발생)를 지시할 때, 안전 필터가 동작하여 궤적을 부드럽게 스무딩하는지 모니터링합니다.
* **하드웨어 긴급 정지 검증**:
  - 로봇의 관절 각도가 정해진 물리 한계점(Joint Limit)에 도달하거나 모터 토크 이상치(과전류)가 검출될 때 `emergency_safety_guard.py`가 이를 선제 감지하여 긴급 정지 서비스를 자동 호출, 모터 전원을 즉각 차단하는지 안전 구역 내에서 점검합니다.

### 3.2 웹 텔레메트리 대시보드 검증
* **백엔드 집계 서버 기동**:
  ```bash
  python3 src/dashboard/server.py
  ```
* **프론트엔드 연동 테스트**:
  - 웹브라우저를 통해 React 프론트엔드 대시보드([web/](file:///home/iyangim/smart-shelf-robot/web/))에 접속합니다.
  - 웹소켓을 통한 6축 관절 실시간 각도, 모터 전류 텔레메트리 그래프, 실시간 RealSense 카메라 비디오 스트림이 웹 화면상에 끊김 없이 시각화되는지 성능을 평가합니다.
