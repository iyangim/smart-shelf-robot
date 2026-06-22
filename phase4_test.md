# Phase 4: 실물 로봇 배포 및 하드웨어 정합 테스트 가이드

본 문서는 스마트 매대 정리 로봇 프로젝트 **Phase 4**의 Sim-to-Real 및 VLA 빌드 환경 구축, ROS 2 Humble 인터페이스 연동, 핸드아이 캘리브레이션 정밀도 검증, 이중 안전 가드라인 및 대시보드 실시간 모니터링 체계를 테스트하기 위한 실행 가이드입니다.

---

## 1. 빌드 환경 준비 및 ROS 2 패키지 컴파일 테스트 (Build & Compile Test)

### 1.1 파이썬 빌드 의존성 설정
* **검증 방법**: 콘다 환경에서 아래 패키지들의 정상 설치 및 버전을 확인합니다.
  ```bash
  # colcon 빌드 툴 및 lark 설치
  pip install colcon-common-extensions lark
  
  # ROS 2 Humble 빌드 템플릿 호환성을 위한 empy 다운그레이드
  pip install "empy==3.3.4"
  ```

### 1.2 패키지 컴파일 실행
* **수행 명령어**:
  ```bash
  # 기존 빌드 캐시 초기화 후 빌드 실행
  rm -rf build/custom_interfaces install/custom_interfaces
  source /opt/ros/humble/setup.bash
  colcon build --symlink-install --packages-select custom_interfaces smart_shelf_robot
  ```
* **결과 평가 지표**: 빌드가 실패 패키지 없이 완료되어야 합니다 (`2 packages finished`).

### 1.3 인터페이스 패키지 등록 여부 확인
* **수행 명령어**:
  ```bash
  source install/setup.bash
  # 패키지 등록 검색
  ros2 pkg list | grep -E "custom_interfaces|smart_shelf_robot"
  
  # 액션 인터페이스 규격 확인
  ros2 interface show custom_interfaces/action/ShelfManipulate
  ```

---

## 2. ROS 2 VLA-Diffusion 노드 연동 테스트 (VLA & Inference Test)

### 2.1 VLA 비동기 제어 브릿지 노드 기동
* **수행 명령어**:
  ```bash
  ros2 run smart_shelf_robot vla_bridge_node
  ```
* **검증 방법**:
  - `MultiThreadedExecutor` 구동을 통해 이미지 구독 및 액션 서버 처리가 독립된 스레드에서 병렬 동작하는지 확인합니다.
  - 다른 터미널에서 액션 목표를 전송하여 상태를 확인합니다:
    ```bash
    ros2 action send_goal /shelf_manipulate custom_interfaces/action/ShelfManipulate "{instruction: 'align snack box on the second shelf'}" --feedback
    ```

### 2.2 Diffusion Policy 실시간 추론 및 필터 검증
* **수행 명령어 (추론 노드 기동)**:
  ```bash
  ros2 run smart_shelf_robot diffusion_inference_node
  ```
* **검증 방법**:
  - `/dsr01/servol_cmd` (Twist) 명령어가 30Hz 주기로 일정하게 발행되는지 확인합니다:
    ```bash
    ros2 topic hz /dsr01/servol_cmd
    ```
  - EMA 필터 동작 하에 속도 변화율이 완만하고 안정적인지 모니터링합니다.

---

## 3. 센서 좌표 캘리브레이션 및 FSM 안전 가드라인 테스트

### 3.1 Hand-Eye Calibration 및 카메라 파라미터 매트릭스 검증
* **Hand-Eye Calibration 정밀도 평가**:
  - `calibration_result.npz`에서 추출한 카메라-로봇 베이스 3D 변환 행렬($T_{\text{cam2base}}$)을 실제 로봇 픽앤플레이스 작업에 주입했을 때, 공간 물리 정밀 오차 범위가 **5mm 이하**로 유지되는지 목표 지점 도달 테스트를 수행합니다.
  - `object_tracking_node.py` 실행 시 `T_cam_to_base`와 `T_cam2base` 키 네이밍이 호환되어 정상 동작하는지 테스트합니다.
* **동적 카메라 매트릭스 보정 검증**:
  - [pointcloud_node.py](file:///home/iyangim/smart-shelf-robot/src/custom/vision/pointcloud_node.py) 구동 중 `/camera/depth/camera_info` 토픽의 동적 내부 파라미터 $fx, fy, cx, cy$가 정상 로드 및 파싱되며, 렌즈 왜곡에 따른 3D 재투영 오차가 보정되는지 검증합니다.

### 3.2 유한 상태 머신(FSM) 및 이중 안전장치 구동성 평가
* **소프트웨어 변위 가드 차단 테스트**:
  - 추론 결과가 비정상적인 액션 점프(순간적 이상 치수 발생)를 지시할 때, 안전 필터가 동작하여 궤적을 부드럽게 스무딩하는지 모니터링합니다.
* **하드웨어 긴급 정지 검증**:
  - 로봇의 관절 각도가 정해진 물리 한계점(Joint Limit)에 도달하거나 모터 토크 이상치(과전류)가 검출될 때 `emergency_safety_guard.py`가 이를 선제 감지하여 긴급 정지 서비스를 자동 호출, 모터 전원을 즉각 차단하는지 안전 구역 내에서 점검합니다.

### 3.3 웹 텔레메트리 대시보드 검증
* **백엔드 집계 서버 기동**:
  ```bash
  python3 src/dashboard/server.py
  ```
* **프론트엔드 연동 테스트**:
  - 웹브라우저를 통해 React 프론트엔드 대시보드([web/](file:///home/iyangim/smart-shelf-robot/web/))에 접속합니다.
  - 웹소켓을 통한 6축 관절 실시간 각도, 모터 전류 텔레메트리 그래프, 실시간 RealSense 카메라 비디오 스트림이 웹 화면상에 끊김 없이 시각화되는지 성능을 평가합니다.
