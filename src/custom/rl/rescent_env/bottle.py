# stage8_main.py line 1215-1232
def _spawn_bottle_prim(_path, _xy, _q, _z, _lie):
    _bm = make_bottle_mesh(_btlspec["radius"], _btlspec["height"])
    _mp = UsdGeom.Mesh.Define(stage, _path)
    _mp.CreatePointsAttr([Gf.Vec3f(*map(float, v)) for v in _bm.vertices])
    _mp.CreateFaceVertexCountsAttr([3] * len(_bm.faces))
    _mp.CreateFaceVertexIndicesAttr([int(i) for f in _bm.faces for i in f])
    _mp.CreateDisplayColorAttr([Gf.Vec3f(0.10, 0.45, 0.95)])
    _bp = _mp.GetPrim()
    _xf2 = UsdGeom.Xformable(_bp)
    _xf2.AddTranslateOp().Set(Gf.Vec3d(float(_xy[0]), float(_xy[1]), float(_z)))
    _xf2.AddOrientOp().Set(Gf.Quatf(float(_q[0]), float(_q[1]), float(_q[2]), float(_q[3])))
    UsdPhysics.RigidBodyAPI.Apply(_bp)
    UsdPhysics.CollisionAPI.Apply(_bp)
    UsdPhysics.MeshCollisionAPI.Apply(_bp).CreateApproximationAttr().Set("convexHull")
    UsdPhysics.MassAPI.Apply(_bp).CreateMassAttr().Set(0.60)
    if _lie:
        _apply_roll_damp(_path)
    return _RigidPrim(_path, name=_path.split("/")[-1])
병 메시 생성 함수:


# pp_geometry.py line 24-43
_BOTTLE_PROFILE = [
    (0.00, 0.0335), (0.02, 0.0340), (0.045, 0.0330), (0.07, 0.0340),
    (0.13, 0.0342), (0.19, 0.0292), (0.26, 0.0340),
    (0.33, 0.0298), (0.40, 0.0270), (0.47, 0.0300), (0.53, 0.0340),
    (0.59, 0.0285), (0.64, 0.0350), (0.78, 0.0350),
    (0.83, 0.0340), (0.88, 0.0285), (0.92, 0.0150),
    (0.945, 0.0130), (0.965, 0.0180), (1.00, 0.0185),
]

def make_bottle_mesh(radius, height, sections=48):
    us = np.array([p[0] for p in _BOTTLE_PROFILE], dtype=np.float64)
    rs = np.array([p[1] for p in _BOTTLE_PROFILE], dtype=np.float64) * (radius / 0.035)
    zs = (us - 0.5) * height
    th = np.linspace(0.0, 2 * np.pi, sections, endpoint=False)
    nr = len(zs)
    verts = [[r * np.cos(t), r * np.sin(t), z] for z, r in zip(zs, rs) for t in th]
    faces = []
    for i in range(nr - 1):
        for j in range(sections):
            a, b = i * sections + j, i * sections + (j + 1) % sections
            c, d = (i + 1) * sections + j, (i + 1) * sections + (j + 1) % sections
            faces += [[a, b, d], [a, d, c]]
    bc = len(verts); verts.append([0.0, 0.0, zs[0]])
    tc = len(verts); verts.append([0.0, 0.0, zs[-1]])
    for j in range(sections):
        faces.append([bc, (j + 1) % sections, j])
        faces.append([tc, (nr - 1) * sections + j, (nr - 1) * sections + (j + 1) % sections])
    return trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces), process=False)

