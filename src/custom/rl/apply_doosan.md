두산 E0509 로봇을 Isaac Lab에 성공적으로 등록하고 태스크를 수행하기 위한 구체적인 **에셋 등록 및 환경 수정 절차**를 안내해 드릴게요. 기존 `franka_isaaclab` 프로젝트의 모듈화된 폴더 구조(`assets/robots/franka.py`)를 그대로 벤치마킹하여 깔끔하게 추가하는 방식입니다.

---

## 🛠️ Step 1. 두산 E0509 USD 에셋 준비

NVIDIA Isaac Sim/Lab은 `USD(Universal Scene Description)` 포맷을 기본으로 사용합니다.

1. 두산 로봇의 공식 **URDF 파일**과 매시(Mesh) 파일들을 준비합니다.
2. Isaac Sim을 실행한 후, 상단 메뉴의 **Extensions -> URDF Importer**를 활용하여 URDF를 **USD 파일**로 변환(Import)합니다.
3. 변환된 `doosan_e0509.usd` 파일을 프로젝트 내 적절한 경로(예: `source/franka_isaaclab/franka_isaaclab/assets/doosan_e0509.usd`)에 저장합니다.

---

## 📄 Step 2. 로봇 자산 설정 파일 생성 (`doosan.py`)

기존 Franka 설정처럼 Isaac Lab의 `ArticulationCfg`를 활용해 두산 로봇의 물리적 특성, 제어기(Actuator), 초기 자세를 정의해야 합니다.

`source/franka_isaaclab/franka_isaaclab/assets/robots/doosan.py` 파일을 생성하고 아래 구조로 작성합니다.

```python
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg

DOOSAN_E0509_CFG = ArticulationCfg(
    prim_path="{ENV_REGEX_NS}/Robot",
    spawn=sim_utils.UsdFileCfg(
        # Step 1에서 변환한 USD 파일 경로 지정
        usd_path="<프로젝트_절대_경로_또는_상대_경로>/doosan_e0509.usd",
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True, 
            solver_position_iteration_count=8, 
            solver_velocity_iteration_count=1
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        # 6개 관절의 초기 각도(Radian) 정의 (URDF에 명시된 Joint 이름 기준)
        joint_pos={
            "joint1": 0.0,
            "joint2": 0.0,
            "joint3": 1.57,  # 기하학적 특이점(Singularity)을 피하기 위한 초기 포즈 권장
            "joint4": 0.0,
            "joint5": 1.57,
            "joint6": 0.0,
        },
    ),
    actuators={
        # 6개 관절을 제어할 드라이브 가인(Stiffness, Damping) 설정
        "arm": ImplicitActuatorCfg(
            joint_names_expr=["joint[1-6]"],
            stiffness=800.0,  # 모터 하드웨어 강성에 맞춰 튜닝 필요
            damping=40.0,
            friction=0.1,
        ),
    },
)

```

---

## ⚙️ Step 3. 환경 설정 파일 수정 (`reach_env_cfg.py`)

로봇이 변경되었으므로 관측(Observation)층과 행동(Action)층의 구성을 업데이트해야 합니다.

```python
from franka_isaaclab.assets.robots.doosan import DOOSAN_E0509_CFG

class ReachEnvCfg(ManagerBasedEnvCfg):
    def __init__(self):
        super().__init__()
        
        # 1. 로봇 에셋을 Franka에서 Doosan으로 교체
        self.scene.robot = DOOSAN_E0509_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")

        # 2. 행동 공간(Action Space) 수정: 7차원 -> 6차원
        self.actions = {
            "arm_action": ActionTerm(
                func=mdp.joint_position_command, 
                dimensions=6  # 6자유도로 변경
            )
        }
        
        # 3. 관측 공간(Observation Space): 차원 수가 24에서 22로 자동 변경됨
        # (joint_pos와 joint_vel이 각각 6차원으로 줄어들기 때문)
        self.observations = {
            "policy": {
                "joint_pos": ObsTerm(func=mdp.joint_pos),     # 6차원
                "joint_vel": ObsTerm(func=mdp.joint_vel),     # 6차원
                "ee_pose": ObsTerm(func=mdp.ee_pose),         # 7차원
                "target_pos": ObsTerm(func=mdp.target_position), # 3차원
            }
        }

```

> 💡 **주의:** `mdp.ee_pose` 함수 내부에서 말단 장치의 좌표를 가져올 때, Franka의 링크 이름(예: `panda_hand`) 대신 두산 E0509의 URDF상 마지막 링크 이름(예: `link6` 또는 `flange`)을 찾아 수정해주어야 에러가 나지 않습니다.

---

## 🧠 Step 4. PPO 신경망 크기 조정 (`skrl_ppo_cfg.yaml`)

입력층(관측)과 출력층(행동)의 물리적 차원이 바뀌었으므로 알고리즘 설정도 동기화합니다.

SKRL 라이브러리는 환경의 차원을 자동으로 감지(Auto-detect)하므로 대개 구조를 직접 명시할 필요는 없지만, 만약 신경망 레이어가 고정되어 있다면 아래와 같이 변경점을 인지하고 계셔야 합니다.

* **기존 (Franka):** Input 24 $\to$ Hidden Layers $\to$ Output 7
* **변경 (두산):** Input 22 $\to$ Hidden Layers $\to$ Output 6

---

현재 두산 로봇의 URDF 파일에서 USD 포맷으로의 변환은 완료된 상태이신가요, 아니면 변환 단계부터 함께 진행하셔야 하나요?