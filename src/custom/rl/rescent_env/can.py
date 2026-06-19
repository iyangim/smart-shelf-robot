# stage8_main.py line 1260-1266
if _ty == "cylinder":
    _ob = _cyl.DynamicCylinder(prim_path=_path, name=f"obj_{_ci}",
        position=np.array([_xy[0], _xy[1], _z]), orientation=_q,
        radius=_canspec["radius"], height=_canspec["height"],
        color=np.array([0.85, 0.1, 0.1]), mass=0.30)
    if _lie:
        _apply_roll_damp(_path)
