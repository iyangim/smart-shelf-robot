# 스마트 매대 로봇 프로젝트 최종 발표자료

---

## Slide 1: 타이틀 (Title)
### Isaac Lab 기반 강화학습 마이그레이션 및 VLA 통합 설계
- **발표자**: 임인영 (iyangim)
- **일정**: 2026.05.25 ~ 2026.06.22 (4주)
- **목표**: 스마트 매대 진열을 위한 강화학습 환경 구축 및 가상-실물 연동/VLA 제어 시스템 설계

*Diagram Image Prompt*:
`Minimalist flat vector icon design of a robotic arm stacking a box on a shelf, dark theme, technology blue and slate colors, clean presentation slide graphic.`

---

## Slide 2: 프로젝트 로드맵 (Roadmap)
- **1단계**: Franka 로봇 기본 RL 태스크 검증 (Reach, Lift, Stack 완료)
- **2단계**: Doosan E0509 로봇 환경 RL 마이그레이션 (Reach 마이그레이션 진행 중 중단)
- **3단계**: 가상 매대(Shelf) 환경 시뮬레이션 통합 (동적 물품 스캔, 집기, 이동, 배치)
- **4단계**: 실물 로봇 배포 및 하드웨어 정합 (ROS 2 인터페이스, RealSense depth 정렬)
- **5단계**: VLA(Vision-Language-Action) 모델 도입 및 실환경 배포

*Diagram Image Prompt*:
`A horizontal timeline infographic showing 5 phases of a robotics project, clean lines, professional presentation vector style, blue and teal color scheme, transparent background.`

---

## Slide 3: DevOps 초기 환경 구축 시도와 교훈
- **원격 서버 구축 시도**: 프로젝트 초반 4주간 부족한 로컬 컴퓨팅 파워를 극복하고자 Docker Compose를 활용하여 원격 고성능 노트북의 개발 환경을 통합 제어하려 시도함.
- **버전 및 드라이버 민감성**: NVIDIA Omniverse, Isaac Sim의 드라이버 요구사항(X11 포워딩, GPU 드라이버 버전) 및 컨테이너 내부 렌더링 엔진 간의 호환성 문제로 예정된 일정 내에 완료하기 어려웠음.
- **전환 전략**: 컨테이너 디버깅에 소요되는 시간을 단축하기 위해 신속히 실습실 표준 방식(로컬 네이티브 환경 설치)으로 환경 구축을 회항함.
- **핵심 교훈**: 물리 연산 및 가속 렌더링이 필수적인 AI 환경은 컨테이너 가상화보다 물리 장치 호환성을 고려한 베어메탈(로컬) 정합이 유리함.

*Diagram Image Prompt*:
`Docker container boxes stacked next to an Isaac Sim logo, with a red barrier line showing compatibility conflict, technical workflow style, flat vector illustration.`

---

## Slide 4: 개발 환경 정립 및 디렉토리 구조화
- **고성능 장비 할당**: 고성능 노트북이 추가 공급됨에 따라, 혼재되어 있던 스크립트와 학습 파일들을 분할 정립함.
- **저장소 폴더 구성**:
  - `src/custom/`: 로봇 제어 코드 및 강화학습 환경 설정 파일 배치
  - `src/custom_interfaces/`: VLA 통합을 위한 ROS 2 커스텀 액션 및 메시지 구조 정의
  - `scripts/`: 학습 스크립트 및 검증 유틸리티 수집
  - `tools/`: 코드 품질 확인용 린터, 보안 스캐너 배치
- **의의**: 외부 패키지와 고유 개발 소스코드를 명확히 격리하여 의존성 충돌을 차단함.

*Diagram Image Prompt*:
`Clean repository folder tree structure diagram, highlighting "src/custom" and "scripts" subdirectories, minimalist technical blueprint style.`

---

## Slide 5: 강화학습(RL) 도입 결정 및 리서치
- **배경**: 초기 팀 기획 단계에서 수렴의 어려움과 개발 편차로 추진을 보류했던 강화학습 제어 방식을 독립적으로 진행하기로 판단함.
- **논문 분석 및 리서치**: NotebookLM을 주축으로 로봇 조작 제어 분야의 최신 연구 자료를 분석하여, 수렴 가능성이 높은 파라미터 셋과 보상 형태를 도출함.
- **학습 아키텍처 결정**:
  - 다수의 환경을 병렬 구동하여 시뮬레이션 데이터를 수집하기 위해 Isaac Lab Vectorized Env 선정
  - 신속한 안정화가 입증된 SKRL(Simple PyTorch Reinforcement Learning) 프레임워크와 PPO 알고리즘 조합 구축

*Diagram Image Prompt*:
`Concept art of robot reinforcement learning: neural network architecture inputs to a robotic arm action output, flat vector design, high contrast dark blue background.`

---

## Slide 6: Franka Robot 기초 태스크 검증 성공
- **포팅 기준점 마련**: Doosan 로봇에 이식하기 전, 기준 탬플릿인 `franka_isaaclab` 환경에서 조작 성능을 사전 테스트함.
- **3대 기본 태스크 통과**:
  1. **Reach**: 로봇 플랜지를 임의의 공간 좌표로 충돌 없이 이동시킴.
  2. **Lift**: 테이블에 무작위로 위치한 물품을 파지한 뒤 수직 방향으로 부양함.
  3. **Stack**: 두 개의 물체를 정렬하여 하단 물체 위에 안정적으로 정합 적층함.
- **결과**: SKRL 에이전트 파라미터 조율을 거쳐 최종적으로 3가지 태스크 모두 성공 궤적을 획득함.

*Diagram Image Prompt*:
`Sequential diagram showing a Franka robot arm reaching, lifting a blue block, and stacking it on a red block, 3-step visualization, vector graphic.`

---

## Slide 7: AI 협업 방식: Antigravity & Skill Set
- **개발 생산성 도구 사용**: 지능형 AI 에이전트인 Antigravity와의 공동 개발 체계를 구축함.
- **전용 Skill Set 적용**:
  - `git-workflow-master`: 아토믹 커밋 적용 및 PR 전 비밀키 노출 방지
  - `managing-python-dependencies`: ROS 2와 Isaac Sim 가상환경 간 패키지 버전 간섭 사전 방지
  - `ml-best-practices`: 관측 공간 구성 시 차원 오류 해결 및 학습 지표 최적화
- **효과**: 개발 가이드를 주기적으로 호출하여 개발 일관성을 얻고 비정상 동작을 선제적으로 예방함.

*Diagram Image Prompt*:
`An AI assistant avatar sitting next to a human developer, sharing a skill checklist connected to a terminal, clean flat tech illustration.`

---

## Slide 8: Doosan Robot RL 마이그레이션과 시행착오
- **두산 로봇 이식 시도**: 프란카 환경에서 얻은 설정 파라미터 구조를 Doosan E0509 로봇 환경으로 전환하는 마이그레이션을 추진함.
- **발생한 문제**:
  - URDF 변환 모델 적용 시 관성 행렬과 질량 정보 왜곡 발생.
  - Doosan 로봇 고유의 조인트 한계(Joint Limits) 및 물리 구조의 특이점(Singularity)으로 조인트 구동 속도 지연.
  - 관측치 텐서의 차원 일치 실패 및 초기 제어기(Joint Position Controller) 설정 오류로 학습 불안정.
- **현재 진행도**: 2단계(Doosan Reach/Lift 환경 마이그레이션) 도중 조인트 바인딩 문제 및 물리 셋업 꼬임 현상이 발견되어 추가 파라미터 보정을 위한 조정 단계에서 일시 멈춤.

*Diagram Image Prompt*:
`A Doosan robot arm rendering with joint axis markers showing rotation limit warnings in red, simulation error concept, vector art.`

---

## Slide 9: [개념 설계] 3단계: 가상 매대(Shelf) 환경 시뮬레이션
- **통합 개요**: 남정혁 팀원이 설계한 가상 편의점 매대 및 환경 USD 데이터를 결합하여 조작 시나리오 시뮬레이션을 수행함.
- **조작 시나리오 4대 태스크**:
  1. **Task 1: 스캔 & 탐색 (Scan & Detect)**
  2. **Task 2: 바스켓 집기 (Pick-up)**
  3. **Task 3: 충돌 회피 이동 (Transit)**
  4. **Task 4: 매대 수납 (Place)**
- **목표**: 매대 내부의 협소한 제약 환경에서 충돌 없이 유연한 물품 진열 과정을 물리 기반 가상 공간에서 완수함.

*Diagram Image Prompt*:
`Robotic arm extracting a product from a grocery shelf model in a virtual CAD/sim environment, line art with glow accents, 3D viewport style.`

---

## Slide 10: [개념 설계] 3단계: 가상 매대 태스크 세부 아키텍처
- **스캔 및 감지 (Task 1)**: RGB-D 카메라가 획득한 매대 전면 데이터에서 빈 공간 슬롯을 분할 검출하고, 진열 대기 중인 물품들의 3D 포즈(바운딩 박스)를 감지함.
- **바스켓 집기 (Task 2)**: 주변 바스켓 틀과의 기하학적 충돌을 우회하며 협소한 안쪽 영역에서 물체를 그리퍼로 집어 올려 수직 탈출 경로를 확보하는 강화학습 제어 루프를 적용함.
- **장애물 회피 이송 (Task 3)**: 바스켓에서 매대 전면 슬롯까지 물품을 파지한 채 이송할 때, cuRobo 가속 경로 기획(Path Planner)과 결합하여 관절 충돌 없이 매끄럽고 신속한 우회 궤적을 산출함.
- **매대 진열 (Task 4)**: 매대 깊이 공간에 물품을 배치하는 과정으로, 수평 진입 조작 모델과 그리퍼 탈출 경로가 순차 제어로 수행됨.

*Diagram Image Prompt*:
`Infographic showing a 4-step sequence: 1. Camera detecting box -> 2. Gripper picking box -> 3. Path planning line -> 4. Inserting box in shelf, vector graphic.`

---

## Slide 11: [개념 설계] 4단계: 실물 로봇 배포 아키텍처
- **하드웨어 인터페이스 연동**: 시뮬레이션 환경에서 검증한 강화학습 관절 정책을 실물 두산 E0509 및 RH-P12-RN-A 그리퍼에 직접 명령어로 전송함.
- **ROS 2 통신 및 노드 구성**:
  - 관절 궤적을 2ms 주기 이하로 물리 구동 인터페이스에 전파하는 실시간 드라이버 통신 노드 구축
  - FSM(Finite State Machine) 기반 메인 컨트롤러 가동으로 순차 제어 단계 감시
- **하드웨어 보호 및 안전 가드**:
  - 급격한 토크나 속도 이탈을 조기에 발견하고 긴급 정지를 유도하는 `emergency_safety_guard.py` 구축
  - 시뮬레이션과 물리 관절 제한의 하드 코딩 연계를 통해 기계 파손 위험 원천 차단

*Diagram Image Prompt*:
`A real-world physical Doosan E0509 robot arm linked to a control panel and monitor showing ros2 nodes, network lines, clean schematic design.`

---

## Slide 12: [개념 설계] 4단계: 실물 센서 통합 및 공간 정합
- **카메라 좌표 정합 (Calibration)**:
  - RealSense D455F 카메라를 통한 매대 및 적재 공간 인식
  - Eye-in-Hand 혹은 Eye-to-Hand 캘리브레이션을 진행하여 좌표 변환 데이터 `calibration_result.npz`로 고유 로봇 좌표계와 센서 이미지 평면 간 오차 정합 수행
- **센서 왜곡 보정**:
  - 반사광이나 반도투명 포장재 재질 물품 인식 시 점군(Point Cloud) 노이즈를 필터링하는 `pointcloud_node.py` 구성
  - 캘리브레이션 정밀 오차를 5mm 이내로 조율하여 조작 안정성을 보장함

*Diagram Image Prompt*:
`Camera field of view projecting coordinate grid lines onto a physical object, aligned with robotic gripper axes, technical calibration concept, vector illustration.`

---

## Slide 13: [개념 설계] 5단계: VLA(Vision-Language-Action) 모델 연동
- **VLA 도입 목표**: 기존의 엄격히 고정된 FSM 제어 로직을 우회하여, 자연어 명령어 입력을 기반으로 가변적인 조작 작업을 즉각 유도함.
- **구동 프로세스**:
  1. 사용자 지시어 접수 ("매대 상단 오른쪽에 음료 배치해줘")
  2. 로봇 카메라 비주얼 인쇄 이미지 토큰과 자연어 지시를 VLA 백본 모델로 결합
  3. 로봇의 다음 적정 행동(Action) 또는 그리퍼 제어 궤적 엔드포인트를 예측 연산
- **기대 효과**: 정적 환경 정의 없이도 로봇이 새로운 매대 사물 배치 구조를 직관적으로 이해하고 상황 변화에 대처함.

*Diagram Image Prompt*:
`Flowchart showing: Text input ("Put drink on shelf") + Robot camera image -> VLA AI Model -> Robot joint trajectory output, clean dark mode layout.`

---

## Slide 14: [개념 설계] 5단계: 모사학습 및 디퓨전 정책 통합
- **모사학습(Imitation Learning) 연계**:
  - 시뮬레이션 데이터 수집 및 물리 시현(Demonstration) 데이터를 활용하여 대규모 수동 조작 궤적 획득
  - ACT(Action Chunking with Transformers) 신경망 모델 학습을 통한 장기 거동(Long-Horizon) 조작 안정화
- **디퓨전 정책(Diffusion Policy) 적용**:
  - 시간에 따른 상태 천이를 디퓨전 프로세스(Denoising Process)로 학습하여 최적 조작 경로 예측
  - 동적 왜곡 요인(외란) 속에서도 미세 경로의 흔들림을 효과적으로 보정하여 일관성 있는 배치 거동 유지

*Diagram Image Prompt*:
`Visualization of diffusion process denoising a robotic arm motion trajectory curve, from scattered dots to a clean path, vector art.`

---

## Slide 15: 결론 및 향후 개선 과제
- **수행 성과 요약**:
  - 원격 DevOps 환경 문제 봉착 시 신속하게 로컬 정비로 전환하여 개발 시간의 손실을 방지함
  - Franka 기본 태스크 3종 학습 수렴 및 Doosan 이식 시 조인트 특이점 문제 도출
  - 가상 매대 시나리오, 실물 배포 안전 장치, VLA 적용 흐름에 이르는 통합 개념 아키텍처 제시
- **향후 해결 과제**:
  - 두산 E0509 URDF 역학 모델 속성값 정밀 복원 및 관절 회전 각도 불일치 해결
  - RealSense 점군 센서 필터 적용 후 실로봇 궤적 추종 테스트 진행
  - 학습된 정책 온디바이스 로딩 및 모사학습을 연동한 실물 매대 시나리오 최종 실사

*Diagram Image Prompt*:
`Robot hand making a puzzle complete with the final puzzle piece, background has a faint line chart trending upwards, professional final slide visual.`
