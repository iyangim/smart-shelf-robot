# -*- coding: utf-8 -*-
# Centralized configurations for dynamic shelf products (Can, Bottle, Snack Bag)
# ~/smart-shelf-robot/src/custom/rl/cfgs/dynamic_objects_cfg.py

import numpy as np
from pxr import Usd, UsdGeom, Gf, UsdPhysics

from isaaclab.sim.utils import clone, get_current_stage, create_prim, bind_physics_material, bind_visual_material
from isaaclab.sim import schemas
import isaaclab.sim as sim_utils
from isaaclab.sim.spawners.shapes.shapes_cfg import ShapeCfg, CylinderCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import UsdFileCfg
from isaaclab.sim.schemas.schemas_cfg import RigidBodyPropertiesCfg
from isaaclab.assets import RigidObjectCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR


# -----------------------------------------------------------------------------
# 1. Mesh Generators (Procedural geometry logic from rescent_env)
# -----------------------------------------------------------------------------

_BOTTLE_PROFILE = [
    (0.00, 0.0335), (0.02, 0.0340), (0.045, 0.0330), (0.07, 0.0340),
    (0.13, 0.0342), (0.19, 0.0292), (0.26, 0.0340),
    (0.33, 0.0298), (0.40, 0.0270), (0.47, 0.0300), (0.53, 0.0340),
    (0.59, 0.0285), (0.64, 0.0350), (0.78, 0.0350),
    (0.83, 0.0340), (0.88, 0.0285), (0.92, 0.0150),
    (0.945, 0.0130), (0.965, 0.0180), (1.00, 0.0185),
]


def _make_bottle_mesh_data(radius: float, height: float, sections: int = 32):
    """Generates bottle vertices and faces (triangles) procedurally."""
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
            faces.append([a, b, d])
            faces.append([a, d, c])
            
    bc = len(verts)
    verts.append([0.0, 0.0, zs[0]])
    tc = len(verts)
    verts.append([0.0, 0.0, zs[-1]])
    
    for j in range(sections):
        faces.append([bc, (j + 1) % sections, j])
        faces.append([tc, (nr - 1) * sections + j, (nr - 1) * sections + (j + 1) % sections])
        
    return verts, faces


def _make_pillow_mesh_data(
    center_half: float = 0.035,
    density: float = 1.0,
    edge_half: float = 0.0012,
    hx: float = 0.06,
    hy: float = 0.086
):
    """Generates snack bag pillow mesh vertices and faces (triangles) procedurally."""
    NU, NV = int(24 * density), int(32 * density)  # Slightly reduced for RL performance

    def half_thick(u, v):
        return edge_half + (center_half - edge_half) * (1.0 - u * u) * (1.0 - v * v)

    pts = []
    idx = {}

    def add(i, j, top):
        key = (i, j, top)
        if key in idx:
            return idx[key]
        u = -1.0 + 2.0 * i / NU
        v = -1.0 + 2.0 * j / NV
        z = half_thick(u, v) * (1.0 if top else -1.0)
        idx[key] = len(pts)
        pts.append([u * hx, v * hy, z])
        return idx[key]

    tris = []

    def quad(a, b, c, d):
        tris.extend([a, b, c, a, c, d])

    # Top surface
    for i in range(NU):
        for j in range(NV):
            quad(add(i, j, True), add(i + 1, j, True), add(i + 1, j + 1, True), add(i, j + 1, True))
            
    # Bottom surface
    for i in range(NU):
        for j in range(NV):
            quad(add(i, j, False), add(i, j + 1, False), add(i + 1, j + 1, False), add(i + 1, j, False))
            
    # Side sealing edge
    loop = []
    for i in range(NU):
        loop.append((i, 0))
    for j in range(NV):
        loop.append((NU, j))
    for i in range(NU, 0, -1):
        loop.append((i, NV))
    for j in range(NV, 0, -1):
        loop.append((0, j))
        
    for k in range(len(loop)):
        i0, j0 = loop[k]
        i1, j1 = loop[(k + 1) % len(loop)]
        quad(add(i0, j0, True), add(i1, j1, True), add(i1, j1, False), add(i0, j0, False))
        
    return pts, tris


# -----------------------------------------------------------------------------
# 2. Custom Spawner Helpers & Functions
# -----------------------------------------------------------------------------

def _spawn_custom_mesh_geom(
    prim_path: str,
    cfg: ShapeCfg,
    vertices: list[Gf.Vec3f],
    faces: list[int],
    translation: tuple[float, float, float] | None = None,
    orientation: tuple[float, float, float, float] | None = None,
    stage: Usd.Stage | None = None,
):
    """Helper to define and configure a custom mesh prim on the USD stage."""
    stage = stage if stage is not None else get_current_stage()

    # 1. Create root Xform
    if not stage.GetPrimAtPath(prim_path).IsValid():
        create_prim(prim_path, prim_type="Xform", translation=translation, orientation=orientation, stage=stage)
    else:
        raise ValueError(f"A prim already exists at path: '{prim_path}'.")

    # 2. Create geometry hierarchy
    geom_prim_path = prim_path + "/geometry"
    mesh_prim_path = geom_prim_path + "/mesh"
    
    create_prim(geom_prim_path, prim_type="Xform", stage=stage)
    
    # Define custom mesh
    mesh = UsdGeom.Mesh.Define(stage, mesh_prim_path)
    mesh.CreatePointsAttr(vertices)
    mesh.CreateFaceVertexCountsAttr([3] * (len(faces) // 3))
    mesh.CreateFaceVertexIndicesAttr(faces)
    mesh.CreateSubdivisionSchemeAttr("none")
    
    # Apply collision properties
    if cfg.collision_props is not None:
        schemas.define_collision_properties(mesh_prim_path, cfg.collision_props, stage=stage)
        # Apply convexHull approximation for custom meshes
        mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim())
        mesh_collision.CreateApproximationAttr().Set("convexHull")
        
    # Apply visual material
    if cfg.visual_material is not None:
        if not cfg.visual_material_path.startswith("/"):
            material_path = f"{geom_prim_path}/{cfg.visual_material_path}"
        else:
            material_path = cfg.visual_material_path
        cfg.visual_material.func(material_path, cfg.visual_material)
        bind_visual_material(mesh_prim_path, material_path, stage=stage)
        
    # Apply physics material
    if cfg.physics_material is not None:
        if not cfg.physics_material_path.startswith("/"):
            material_path = f"{geom_prim_path}/{cfg.physics_material_path}"
        else:
            material_path = cfg.physics_material_path
        cfg.physics_material.func(material_path, cfg.physics_material)
        bind_physics_material(mesh_prim_path, material_path, stage=stage)

    # Apply rigid body APIs to the root prim
    if cfg.mass_props is not None:
        schemas.define_mass_properties(prim_path, cfg.mass_props, stage=stage)
    if cfg.rigid_props is not None:
        schemas.define_rigid_body_properties(prim_path, cfg.rigid_props, stage=stage)


@clone
def spawn_dynamic_bottle(
    prim_path: str,
    cfg: "BottleCfg",
    translation: tuple[float, float, float] | None = None,
    orientation: tuple[float, float, float, float] | None = None,
    **kwargs,
) -> Usd.Prim:
    """Spawns a procedurally generated bottle mesh on the USD stage."""
    stage = get_current_stage()
    verts, faces = _make_bottle_mesh_data(cfg.radius, cfg.height, cfg.sections)
    pts = [Gf.Vec3f(*map(float, v)) for v in verts]
    flat_faces = [int(i) for f in faces for i in f]
    
    _spawn_custom_mesh_geom(prim_path, cfg, pts, flat_faces, translation, orientation, stage)
    return stage.GetPrimAtPath(prim_path)


@clone
def spawn_dynamic_snack_bag(
    prim_path: str,
    cfg: "SnackBagCfg",
    translation: tuple[float, float, float] | None = None,
    orientation: tuple[float, float, float, float] | None = None,
    **kwargs,
) -> Usd.Prim:
    """Spawns a procedurally generated snack bag pillow mesh on the USD stage."""
    stage = get_current_stage()
    verts, faces = _make_pillow_mesh_data(
        center_half=cfg.pillow_center_half,
        density=cfg.pillow_density,
        edge_half=cfg.pillow_edge_half,
        hx=cfg.pillow_hx,
        hy=cfg.pillow_hy
    )
    pts = [Gf.Vec3f(*map(float, v)) for v in verts]
    
    _spawn_custom_mesh_geom(prim_path, cfg, pts, faces, translation, orientation, stage)
    return stage.GetPrimAtPath(prim_path)


@configclass
class BottleCfg(ShapeCfg):
    """Configuration class for the procedural bottle mesh."""
    func = spawn_dynamic_bottle
    radius: float = 0.0335
    height: float = 0.20
    sections: int = 32


@configclass
class SnackBagCfg(ShapeCfg):
    """Configuration class for the procedural snack bag pillow mesh."""
    func = spawn_dynamic_snack_bag
    pillow_hx: float = 0.06
    pillow_hy: float = 0.086
    pillow_center_half: float = 0.035
    pillow_density: float = 1.0
    pillow_edge_half: float = 0.0012


# -----------------------------------------------------------------------------
# 4. Spawner Factory Helper
# -----------------------------------------------------------------------------

# Height offsets from the bottom of the object to its center of mass
OBJECT_HEIGHT_OFFSETS = {
    "cube": 0.02,        # 4cm cube -> 2cm offset
    "can": 0.06,         # 12cm can -> 6cm offset
    "bottle": 0.10,      # 20cm bottle -> 10cm offset
    "snack_bag": 0.035,   # 7cm thick snack bag -> 3.5cm offset
}


def get_dynamic_object_cfg(
    object_type: str,
    prim_path: str,
    pos: list[float] | None = None,
    rot: list[float] | None = None,
) -> RigidObjectCfg:
    """Factory function to get the RigidObjectCfg for the specified object type."""
    if pos is None:
        pos = [0.4, 0.0, 0.055]
    if rot is None:
        rot = [1.0, 0.0, 0.0, 0.0]

    # Shared default physics/rigid properties
    rigid_props = RigidBodyPropertiesCfg(
        solver_position_iteration_count=16,
        solver_velocity_iteration_count=1,
        max_angular_velocity=1000.0,
        max_linear_velocity=1000.0,
        max_depenetration_velocity=5.0,
        disable_gravity=False,
    )

    if object_type == "cube":
        spawn_cfg = UsdFileCfg(
            usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/Blocks/DexCube/dex_cube_instanceable.usd",
            scale=(0.8, 0.8, 0.8),
            rigid_props=rigid_props,
        )
    elif object_type == "can":
        spawn_cfg = CylinderCfg(
            radius=0.0335,
            height=0.12,
            rigid_props=rigid_props,
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(0.85, 0.1, 0.1),  # Red soda can
                roughness=0.5,
            ),
        )
    elif object_type == "bottle":
        spawn_cfg = BottleCfg(
            radius=0.0335,
            height=0.20,
            rigid_props=rigid_props,
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(0.10, 0.45, 0.95),  # Blue plastic bottle
                roughness=0.3,
            ),
        )
    elif object_type == "snack_bag":
        spawn_cfg = SnackBagCfg(
            pillow_hx=0.06,
            pillow_hy=0.086,
            pillow_center_half=0.035,
            rigid_props=rigid_props,
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(0.80, 0.55, 0.20),  # Foil/matte brown snack bag
                roughness=0.6,
            ),
        )
    else:
        raise ValueError(f"Unknown object type: '{object_type}' requested.")

    return RigidObjectCfg(
        prim_path=prim_path,
        init_state=RigidObjectCfg.InitialStateCfg(pos=pos, rot=rot),
        spawn=spawn_cfg,
    )
