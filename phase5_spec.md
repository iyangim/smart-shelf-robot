# Phase 5: VLA 모델 연동 및 모사 학습 시스템 규격 정의서 (Specification)

본 문서는 스마트 매대 정리 로봇 프로젝트 **Phase 5** 단계에서 구축 완료된 VLA (Vision-Language-Action) 모델 인터페이스, 모사 학습(Imitation Learning) 알고리즘 및 컨테이너 학습 파이프라인의 스펙을 재정의합니다.

---

## 1. LeRobot 전문가 데이터 수집 규격 (Dataset Collector Spec)

* **수집 모듈**: [doosan_lerobot_dataset_builder.py](file:///home/iyangim/smart-shelf-robot/src/custom/rl/doosan_lerobot_dataset_builder.py)
* **데이터 정합 채널**:
  - 로봇 텔레메트리: `/dsr01/joint_states` (6축 관절 위치/속도/전류 데이터)
  - 카메라 이미지 스트림: `/camera/color/image_raw` (실시간 RGB 컬러 이미지 프레임)
* **저장 규격**: Hugging Face LeRobot 포맷 규격을 준수하여 Parquet 메타데이터 및 동기화 MP4 파일로 실시간 기록

---

## 2. 데이터 포맷 변환 및 전처리 규격 (Data Preprocessing Spec)

대규모 학습 자원 가속화를 위한 이중 변환 유틸리티 규격입니다.

1. **Zarr 포맷 변환**: [convert_to_zarr.py](file:///home/iyangim/smart-shelf-robot/src/rl/imitation_learning/convert_to_zarr.py)
   - 데이터 로딩 속도 최적화를 위해 Parquet 로깅 데이터를 멀티스레드 캐싱 최적화된 Zarr 포맷으로 일차 가공
2. **HDF5 압축 변환**: [convert_zarr_to_hdf5.py](file:///home/iyangim/smart-shelf-robot/src/rl/imitation_learning/convert_zarr_to_hdf5.py)
   - Diffusion Policy 훈련 프레임워크와의 표준 정합을 위해 Zarr 데이터를 최종 HDF5 이진 구조로 압축 수행

---

## 3. Docker 기반 훈련 환경 인프라 스펙 (Container Spec)

호스트 PC의 ROS 2 Humble 환경 및 라이브러리 간의 메이저 패키지 버전 충돌을 막기 위해 가상화 훈련 컨테이너 구성 정의.

* **컨테이너 빌드 정의**: [Dockerfile](file:///home/iyangim/smart-shelf-robot/src/rl/imitation_learning/Dockerfile) (GPU 연동 및 CUDA 라이브러리 내장 빌드)
* **오케스트레이션 구성**: [docker-compose.yaml](file:///home/iyangim/smart-shelf-robot/src/rl/imitation_learning/docker-compose.yaml) (NVIDIA Container Runtime 자원 할당 및 볼륨 매핑)
* **설치 환경**: Python 3.10+, PyTorch 2.2+ (CUDA 12.1+), moviepy, FFmpeg 패키지 사전 빌드 포함

---

## 4. 모사 학습 모델 정책 규격 (Policy Algorithms Spec)

작업 복잡도 및 시차 범위에 맞춰 삼원화된 모사 학습 훈련 정책 규격입니다.

| 정책 모델 (Policy Model) | 훈련 스크립트 | 핵심 특징 및 파라미터 구성 |
|-----------------------|-------------|----------------------------|
| **Behavioral Cloning (BC)** | [train_bc.py](file:///home/iyangim/smart-shelf-robot/src/rl/imitation_learning/train_bc.py) | • 단순 1:1 관측-액션 매핑 지도학습 모델 <br>• 단일 물체 집기 등 단순 거동에 적합 |
| **Action Chunking with Transformers (ACT)** | [train_act.py](file:///home/iyangim/smart-shelf-robot/src/rl/imitation_learning/train_act.py) | • 미래의 연속 N스텝 궤적(Chunk)을 한 번에 예측 <br>• CVAE 기반 시현 분포 잠재 인코딩 탑재 |
| **Diffusion Policy** | [train_diffusion.py](file:///home/iyangim/smart-shelf-robot/src/rl/imitation_learning/train_diffusion.py) | • 확산 모델(Denoising Process) 기반 궤적 생성 <br>• 다중 모달 행동 경로(우회 선택 등) 완벽 일반화 |

---

## 5. 다중 모달 VLA 및 실시간 추론 연동 규격 (VLA & Inference Spec)

* **다중 모달 입력 결합 (Multi-modal Input)**:
  - 자연어 명령어 임베딩 (CLIP / DistilBERT 텍스트 인코더 연동)
  - 실시간 이미지 피드 특징점 추출 (ResNet / ViT 비전 인코더 연동)
* **시간축 궤적 블렌딩 (Temporal Ensembling)**:
  - ACT 및 Diffusion Policy 추론 시, 실시간 제어 주기 마다 생성되는 연속 액션 청크 간 중첩 가중 평균 필터를 적용하여 끊김 없고 유연한 로봇 물리 궤적 연출
* **외란 강건성 (Robustness)**:
  - Denoising 역확산 단계 내 실시간 피드백 반영으로 환경 가변적 오차(미끄러짐 등) 즉각 재계획 보정 수행

---

## 6. 설치 및 구동 표준 명령어 (Execution Commands)

* **훈련 컨테이너 빌드 및 백그라운드 구동**:
  ```bash
  cd src/rl/imitation_learning
  docker compose up -d
  ```
* **Diffusion Policy 훈련 실행**:
  ```bash
  docker compose exec imitation-learning-env python3 train_diffusion.py --config-name=doosan_pick_shelf
  ```
* **Zarr 데이터 셋 검사 및 압축**:
  ```bash
  python3 convert_to_zarr.py --input_dir=data/raw_logs --output=data/dataset.zarr
  ```
