1. 매대환경: 포함: 3단 매대 + 책상 + 로봇 베이스 좌표계 :shelf_workspace_v2.usd
2. 로봇 : E0509 + RH-P12-RN Gripper: e0509_gripper_isaac.usd
3. 기하/물성 
├─ 순수 기하: pp_geometry.py (_BOTTLE_PROFILE, make_bottle_mesh 등)
├─ 모션: pp_motion.py (plan_grasp, cuRobo 통합)
└─ 물성 바인딩: stage8_main.py (set_gripper_friction, 물체 mass)
4. 물체: 
├─ 과자봉지: snack_bag_module
├─ 캔: 런타임 생성
└─ 페트병 : 런타임 생성