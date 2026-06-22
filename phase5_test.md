# Phase 5: VLA 모델 연동 및 모사 학습 시스템 테스트 가이드

본 문서는 스마트 매대 정리 로봇 프로젝트 **Phase 5**의 LeRobot 데이터 수집, 데이터 포맷 변환 및 전처리 유틸리티, Docker 훈련 환경 인프라, 3대 모사 학습 정책 모델(BC, ACT, Diffusion Policy) 및 실시간 추론 제어 루프를 종합 테스트하기 위한 실행 가이드입니다.

---

## 1. LeRobot 전문가 데이터 수집 및 포맷 변환 검증 (Dataset & Conversion Test)

### 1.1 전문가 데이터 수집 노드 가동성 평가
* **데이터셋 빌더 구동**:
  ```bash
  ~/smart-shelf-robot/third_party/IsaacLab/_isaac_sim/python.sh src/custom/rl/doosan_lerobot_dataset_builder.py
  ```
* **수집 데이터 검사**:
  - 수집 프로세스 구동 시 `/dsr01/joint_states` 및 `/camera/color/image_raw` 토픽이 동기화 기록되는지 확인합니다.
  - Hugging Face LeRobot 표준 포맷에 부합하는 Parquet 메타데이터와 동기화 MP4 녹화 비디오 파일이 저장소 내에 안정적으로 생성되는지 검증합니다.

### 1.2 데이터셋 포맷 다중 변환 검증
* **Zarr 고속 포맷 변환 테스트**:
  ```bash
  python3 convert_to_zarr.py --input_dir=data/raw_logs --output=data/dataset.zarr
  ```
  - 변환 결과 Zarr 데이터 구조가 손상 없이 로드되는지 확인합니다.
* **HDF5 압축 변환 테스트**:
  ```bash
  python3 convert_zarr_to_hdf5.py
  ```
  - 최종 훈련 프레임워크 호환용 HDF5 이진 압축 구조 파일이 정상적으로 저장되는지 확인합니다.

---

## 2. Docker 기반 훈련 환경 인프라 검증 (Container Infrastructure Test)

### 2.1 GPU 연동 및 컨테이너 구동 여부 확인
* **컨테이너 빌드 및 구동 명령어**:
  ```bash
  cd src/rl/imitation_learning
  docker compose up -d
  ```
* **동작 점검 사항**:
  - GPU 가속 및 볼륨 바인딩 검증을 위해 컨테이너 내부 GPU 드라이버를 확인합니다.
    ```bash
    docker compose exec imitation-learning-env nvidia-smi
    # CUDA 12.1+ 환경 및 RTX 5080 디바이스 인식 상태 확인
    ```
  - Python 3.10+, PyTorch 2.2+ 패키지 버전이 사양서와 부합하며, 비디오 내보내기 라이브러리(`moviepy`, `ffmpeg`)가 컨테이너 환경 내에 에러 없이 정상 탑재되어 동작하는지 점검합니다.

---

## 3. 모사 학습 정책 모델 및 실시간 추론 성능 평가 (Policy & VLA Inference Test)

### 3.1 정책별 모델(BC, ACT, Diffusion) 학습 구동 검증
컨테이너 내부 가상 환경에서 모델들의 훈련 스크립트가 무오류로 기동되는지 테스트합니다.
* **Behavioral Cloning (BC) 훈련 테스트**:
  ```bash
  docker compose exec imitation-learning-env python3 train_bc.py --config-name=doosan_bc_config
  ```
* **Action Chunking with Transformers (ACT) 훈련 테스트**:
  ```bash
  docker compose exec imitation-learning-env python3 train_act.py --config-name=doosan_act_config
  ```
* **Diffusion Policy 훈련 테스트**:
  ```bash
  docker compose exec imitation-learning-env python3 train_diffusion.py --config-name=doosan_pick_shelf
  ```
* **검증 통과 기준**:
  - 모델 가중치 빌딩 및 노이즈 주입/제거(Denoising) 연산 루프가 데이터 손실 없이 구동되는지 확인합니다.

### 3.2 다중 모달 VLA 및 실시간 추론 루프 성능 평가
* **텍스트-비전 입력 결합 검증**:
  - DistilBERT/CLIP 언어 인코더와 ResNet/ViT 비전 백본을 통한 입력 임베딩 결합이 오차 없이 정상 병합되는지 확인합니다.
* **시간축 궤적 블렌딩(Temporal Ensembling) 평가**:
  - 실시간 예측 시 10Hz ~ 20Hz 타깃 제어 속도 하에서 출력 액션 청크(N-step 연속 궤적)가 가중 평균 필터를 통해 로봇 관절의 단절이나 충격 없이 부드럽게 이어지는지 성능을 시각적으로 평가합니다.
* **외란 대응 탄력성(Robustness) 검증**:
  - 로봇의 구동 중 물체가 밀리는 등의 외란 발생 시, 이미지 프레임 변경 사항이 확산 역과정(Denoising Process) 피드백 루프에 즉각 반영되어 최종 수평 도달 궤적이 동적으로 정상 재계획 및 보정 수행되는지 평가합니다.
