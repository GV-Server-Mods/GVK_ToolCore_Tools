"""Salvage Beam Turret base: the trim ring with its two ears, the crate-top corners, and their decals.

Run inside GVK_SalvagerTurret.blend after kiosk_build.py (its step 7 narrows the canister's foot into a shaft that
stands in this ring). Rebuilds GVK_SalvagerTurret_Visual's mesh from the kept BASE_src mesh (the base as it was
before this script, kept on the first run) and replaces its child GVK_SalvagerTurret_Ring, so every run starts clean.
Block frame, crate top at z ZT. Sizes below are in the top frame: z up from the crate top, the canister's own frame.
Layout: round 5 of the ring mock-ups (owner, 2026-11-08: "lets just continue with this for now") and round 2 of the
crate-top corners (owner, 2026-11-08: "Build both").
"""
import bpy, bmesh, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ZT = -1.25                                 # the crate top in the block frame
RING_OB = 'GVK_SalvagerTurret_Ring'
# plan outline (CCW): the 64-gon r 1.18 with an ear each side out to x 1.246 (|y| 0.33), filleted where they meet
OUTLINE = [
    (-1.12167, -0.36356), (-1.09018, -0.45157), (-1.04067, -0.55625), (-0.98113, -0.65557), (-0.91215, -0.74858),
    (-0.83439, -0.83439), (-0.74858, -0.91215), (-0.65557, -0.98113), (-0.55625, -1.04067), (-0.45157, -1.09018),
    (-0.34254, -1.12919), (-0.23021, -1.15733), (-0.11566, -1.17432), (-0.0, -1.18), (0.11566, -1.17432),
    (0.23021, -1.15733), (0.34254, -1.12919), (0.45157, -1.09018), (0.55625, -1.04067), (0.65557, -0.98113),
    (0.74858, -0.91215), (0.83439, -0.83439), (0.91215, -0.74858), (0.98113, -0.65557), (1.04067, -0.55625),
    (1.09018, -0.45157), (1.12167, -0.36356), (1.13225, -0.34622), (1.14886, -0.33453), (1.16875, -0.3304),
    (1.246, -0.3304), (1.246, 0.3304), (1.16875, 0.3304), (1.14886, 0.33453), (1.13225, 0.34622), (1.12167, 0.36356),
    (1.09018, 0.45157), (1.04067, 0.55625), (0.98113, 0.65557), (0.91215, 0.74858), (0.83439, 0.83439),
    (0.74858, 0.91215), (0.65557, 0.98113), (0.55625, 1.04067), (0.45157, 1.09018), (0.34254, 1.12919),
    (0.23021, 1.15733), (0.11566, 1.17432), (0.0, 1.18), (-0.11566, 1.17432), (-0.23021, 1.15733),
    (-0.34254, 1.12919), (-0.45157, 1.09018), (-0.55625, 1.04067), (-0.65557, 0.98113), (-0.74858, 0.91215),
    (-0.83439, 0.83439), (-0.91215, 0.74858), (-0.98113, 0.65557), (-1.04067, 0.55625), (-1.09018, 0.45157),
    (-1.12167, 0.36356), (-1.13225, 0.34622), (-1.14886, 0.33453), (-1.16875, 0.3304), (-1.246, 0.3304),
    (-1.246, -0.3304), (-1.16875, -0.3304), (-1.14886, -0.33453), (-1.13225, -0.34622)]
SEG = 64
# outer rim, foot up: (inset, z, inset on the ears' tip faces, follows the crate top); a rolled edge into the flat band
PROF_OUT = [(0.007, 0.0, 0.0, True), (0.0, 0.007, 0.0, True), (0.0, 0.055, 0.0, False), (0.007, 0.070, 0.007, False),
            (0.050, 0.113, 0.050, False), (0.065, 0.120, 0.065, False)]
PROF_IN = [(0.964, 0.120), (0.957, 0.117), (0.930, 0.090), (0.8857, 0.090), (0.880, 0.0843), (0.860, 0.020)]   # inner edge, band down: (r, z)
# the ring's top and its rolled rim in Keen's plain dark grey at Keen's scale, UVK, both ways (owner, 2026-11-08: the
# ring's "scratched texture on top ... needs to follow keen style for that grey metal", and the "main bevel looks like it
# stretches the grey textures vertically too much"; they were PaintedMetalScratched_Darker and the brackets' Doodads
# rolled-edge strip, 21 px across the whole rim)
FACE_MAT, RIM_MAT = 'PaintedMetal_Darker', 'PaintedMetal_Darker'
TIP_X, CORNER, UVK = 1.24, 0.0057, 0.4     # ears' tip faces past TIP_X; their 45-degree corner chamfer; planar UV scale
BLK, TONGUE_BEV = (0.985, 1.246, -0.25, 0.006), 0.008     # tongues under the ears, fitted to the bracket ends (x0, x1, z, gap)
FOOT_CLAMP = -0.012                        # the ring's foot drops onto the crate top, at most this far
OFF = 0.0015                               # decals off their surface
SEAM_V, SEAM_US = (0.4834, 0.5166), 0.5    # Atlas4 piece 3 across V; U per metre along the line
BOX = {'bolt': (0.9399, 0.752, 0.999, 0.8105), 'A3-4': (0.0088, 0.8218, 0.1772, 0.9902), 'A3-7': (0.5029, 0.8193, 0.6211, 0.9927),
       'A3-15': (0.0049, 0.6929, 0.0586, 0.8071), 'A3-29': (0.0024, 0.2524, 0.1851, 0.4355)}
# ring decal layout (round 5): one pitch circle at r 1.06, groove at r 0.995, ear legs at |y| 0.24, vent seams over the strap
# handles' edges with 45-degree corner legs, carried facet by facet over the rolled rim
ATL, SEAM = 'Atlas3_Darker', 'Atlas4_Darker'
RG, YS, JOG, Z_TOP, PC = 0.995, 0.24, 0.028, 0.12, 1.06
UF = 1.246
ROLL = [(0.065, 0.120), (0.050, 0.113), (0.007, 0.070), (0.0, 0.055)]     # tip rollover (inset, z), band edge down to the flat
UT, ZW = UF - ROLL[0][0], ROLL[-1][1]
ZB, SLOPE = -0.222, 0.4
X1 = math.sqrt(RG ** 2 - (YS + JOG) ** 2); X2 = X1 + JOG; TA = math.degrees(math.atan2(YS + JOG, X1))
VENTS = [(75.5, 1), (104.5, -1), (255.5, 1), (284.5, -1)]       # seam angle, side its panel centre is on
# crate-top corners (round 2): the plate edge PE; Atlas3 piece 29's dark outline in box units (x right, y down from the right
# angle): leg inset 0.022, corner chamfer x + y = 0.195, hypotenuse x + y = 1.189. The grey (unpainted) bracket corner: legs at
# 1.095, chamfer on x + y = 2.0625; the ring wall at 45 degrees r 1.18. V_GAP from the vent's outline to the ring and to the
# grey corner's tip; the sides come out 6 cm, since the art's corner chamfer is smaller than the bracket's
QUADS = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
PE, V_GAP, RW = 1.03, 0.03, 1.18
VS = (2.0625 - math.sqrt(2) * V_GAP - math.sqrt(2) * (RW + V_GAP)) / (1.189 - 0.195)
VC = (2.0625 - math.sqrt(2) * V_GAP + 0.195 * VS) / 2

base = bpy.data.objects['GVK_SalvagerTurret_Visual']
if 'BASE_src' not in bpy.data.meshes:
    keep = base.data.copy(); keep.name = 'BASE_src'; keep.use_fake_user = True
SRC = bpy.data.meshes['BASE_src']


def mat(name):
    """The material the base already uses, else the SEUT library's, else any of that name."""
    for m in list(SRC.materials) + [m for m in bpy.data.materials if m.library] + list(bpy.data.materials):
        if m and m.name == name: return m
    raise KeyError(name)


# ---- 1. base: drop the +X grab bar and the old ring, blend the top plate flush into the corner brackets ----
def rad(v): return max(abs(v.co.x), abs(v.co.y))


def flatten(bm, mi):
    """The raised top plate (+-PE, z 0) stood up to 11.5 mm above the brackets' sloped crowns (owner, 2026-11-08: "That needs
    to all be blended flat"): cut the crowns at the plate outline, drop the parts under the plate, set the rest level with it."""
    cm = {mi['Doodads'], mi['Chrome']}

    def crown(f):
        zs = [v.co.z - ZT for v in f.verts]
        return f.material_index in cm and f.normal.z > 0.7 and min(zs) > -0.045 and max(zs) < 0.002 and max(rad(v) for v in f.verts) > 1.0
    for co, no in (((PE, 0, 0), (1, 0, 0)), ((-PE, 0, 0), (1, 0, 0)), ((0, PE, 0), (0, 1, 0)), ((0, -PE, 0), (0, 1, 0))):
        fs = [f for f in bm.faces if crown(f) and min(rad(v) for v in f.verts) < PE - 1e-5]
        bmesh.ops.bisect_plane(bm, geom=fs + list({e for f in fs for e in f.edges}) + list({v for f in fs for v in f.verts}),
                               dist=1e-6, plane_co=co, plane_no=no)
    inside = [f for f in bm.faces if crown(f) and abs(f.calc_center_median().x) < PE and abs(f.calc_center_median().y) < PE]
    bmesh.ops.delete(bm, geom=inside, context='FACES')
    vs = {v for f in bm.faces if crown(f) for v in f.verts if rad(v) < 1.18}     # the rolled outer edge (1.18 up) keeps its shape
    for v in vs: v.co.z = ZT
    bm.normal_update()
    return len(inside), len(vs)


def plain_bevels(bm, mi):
    """The box's worn bevels in Keen's plain paint (owner, 2026-11-08: "lots of ugly scratched metal bevels around it"):
    the scratched chamfers round the panels and the keypads become the plain paint they sit in, and the rounded box edges,
    the dark Doodads arms with their white wear lines, the plain dark grey of the trim ring. UVs: the painted chamfers keep
    theirs (0.43 to 0.53 per metre already), the rest are box projected at UVK."""
    dd = next(m for m in SRC.materials if m.name == 'Doodads')
    img = next(n.image for n in dd.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and n.image.filepath.endswith('_cm.TIF'))
    W, H = img.size; px = [0.0] * (W * H * 4); img.pixels.foreach_get(px)
    uvl = bm.loops.layers.uv.active

    def dark_share(f):     # share of the face's UV area on the atlas's dark arms (sRGB luminance under 0.42)
        uv = [l[uvl].uv.copy() for l in f.loops]; us, vs = [p.x for p in uv], [p.y for p in uv]; n = hit = 0
        for a in range(16):
            for b in range(16):
                x = min(us) + (a + 0.5) / 16 * (max(us) - min(us)); y = min(vs) + (b + 0.5) / 16 * (max(vs) - min(vs))
                c = False
                for i in range(len(uv)):
                    p, q = uv[i], uv[(i + 1) % len(uv)]
                    if (p.y > y) != (q.y > y) and x < (q.x - p.x) * (y - p.y) / (q.y - p.y) + p.x: c = not c
                if not c: continue
                k = (min(H - 1, int((y % 1) * H)) * W + min(W - 1, int((x % 1) * W))) * 4
                n += 1; hit += 0.2126 * px[k] + 0.7152 * px[k + 1] + 0.0722 * px[k + 2] < 0.42
        return hit / n if n else 0.0
    pc, dk, sc, sd, do = mi['PaintedMetal_Colorable'], mi['PaintedMetal_Darker'], mi['PaintedMetalScratched_Colorable'], mi['PaintedMetalScratched_Darker'], mi['Doodads']
    re_uv = []; cnt = [0, 0, 0]
    for f in bm.faces:
        if f.material_index == sc: f.material_index = pc; cnt[0] += 1
        elif f.material_index == sd: f.material_index = dk; re_uv.append(f); cnt[1] += 1
        elif f.material_index == do and dark_share(f) >= 0.8: f.material_index = dk; re_uv.append(f); cnt[2] += 1
    for f in re_uv:
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            c = l.vert.co
            l[uvl].uv = (c.y * UVK, c.z * UVK) if ax == 0 else ((c.x * UVK, c.z * UVK) if ax == 1 else (c.x * UVK, c.y * UVK))
    return cnt


def lift_decals(bm, mi):
    """Keen's keypad decals in the port frames sit 0.45 to 0.9 mm off their face (round 7 decal audit): each two-face
    island moved out along its normal to OFF, measured from its centre."""
    d = mi['Decals']; host = bmesh.new(); vm = {}
    for f in bm.faces:
        if f.material_index == d: continue
        vs = [vm[v] if v in vm else vm.setdefault(v, host.verts.new(v.co)) for v in f.verts]
        try: host.faces.new(vs)
        except ValueError: pass
    bvh = BVHTree.FromBMesh(host); seen = set(); n = 0
    for f in bm.faces:
        if f.material_index != d or f in seen: continue
        st, grp = [f], set(); seen.add(f)
        while st:
            g = st.pop(); grp.add(g)
            for h in {h for e in g.edges for h in e.link_faces if h.material_index == d and h not in seen}: seen.add(h); st.append(h)
        c, nn = f.calc_center_median(), f.normal.copy(); hit = bvh.ray_cast(c + nn * 1e-4, -nn, 0.02)
        if hit[0] is None: continue
        for v in {v for g in grp for v in g.verts}: v.co += nn * (OFF - (hit[3] - 1e-4))
        n += 1
    host.free(); return n


me = SRC.copy(); me.name = 'GVK_SalvagerTurret_Visual_build'
bm = bmesh.new(); bm.from_mesh(me)
mi = {m.name: i for i, m in enumerate(me.materials)}
rr = lambda v: math.hypot(v.co.x, v.co.y)
kill = [f for f in bm.faces if (f.material_index == mi['Metal_Dull'] and min(v.co.x for v in f.verts) > 1.12 and min(v.co.z for v in f.verts) - ZT > -0.13)
        or (f.material_index == mi['PaintedMetal_Darker'] and all(v.co.z - ZT > -0.001 and 0.85 < rr(v) < 1.065 for v in f.verts))]
bmesh.ops.delete(bm, geom=kill, context='FACES')
print('base: removed grab bar and old ring,', len(kill), 'faces; flatten: removed %d faces under the plate, levelled %d verts' % flatten(bm, mi))
print('plain bevels: %d painted chamfers, %d dark chamfers, %d rounded edges' % tuple(plain_bevels(bm, mi)))
bm.normal_update(); print('keypad decals lifted to 1.5 mm:', lift_decals(bm, mi))
# name plates above the five ports, back from the first model (owner, 2026-11-08: "I kinda liked that panel with the text
# on it ... so it would say the "SALVAGE BEAM TURRET""; "Proud, like vanilla": its face 1.9 cm out of the cell, as Keen's
# keypad frames stand 3.6 cm out). NAMEPLATE_src holds the five plates cut from the first model's base
# (C:\SE_Assets\TestMod\GVK_SalvagerTurret.blend, 2026-10-20); they are plain dark paint here, their bevels were scratched.
# The text is Keen's TextAtlas, one quad a letter at tight glyph boxes, 1.5 mm off each plate's flat face
NP_CAP, NP_GAP, NP_WORD = 0.08, 0.008, 0.032               # cap height (the first model's); letter and word gaps
GLYPH = {'A': (0.0205, 0.8604, 0.0977, 0.9805), 'B': (0.1709, 0.8604, 0.249, 0.9805), 'E': (0.6143, 0.8604, 0.6855, 0.9805),
         'G': (0.8828, 0.8604, 0.9609, 0.9805), 'L': (0.5215, 0.6943, 0.5801, 0.8164), 'M': (0.6348, 0.6943, 0.75, 0.8164),
         'R': (0.4668, 0.5283, 0.5439, 0.6484), 'S': (0.6094, 0.5283, 0.7031, 0.6484), 'T': (0.7539, 0.5283, 0.8389, 0.6484),
         'U': (0.8984, 0.5283, 0.9746, 0.6494), 'V': (0.0156, 0.3623, 0.0986, 0.4844)}   # read from TextAtlas_alphamask
NP_TEXT = 'SALVAGE BEAM TURRET'


def name_plates(bm, mi):
    src = bpy.data.meshes['NAMEPLATE_src']; uvl = bm.loops.layers.uv.active
    pb = bmesh.new(); pb.from_mesh(src); pb.normal_update(); dk = mi['PaintedMetal_Darker']
    vm = {v: bm.verts.new(v.co) for v in pb.verts}; plate = []
    for f in pb.faces:
        g = bm.faces.new([vm[v] for v in f.verts]); g.material_index = dk; g.smooth = f.smooth; plate.append(g)
    for e in pb.edges:
        if not e.smooth: bm.edges.get([vm[v] for v in e.verts]).smooth = False
    pb.free(); bm.normal_update()
    for f in plate:
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            c = l.vert.co
            l[uvl].uv = (c.y * UVK, c.z * UVK) if ax == 0 else ((c.x * UVK, c.z * UVK) if ax == 1 else (c.x * UVK, c.y * UVK))
    if 'TextAtlas' not in mi:
        me.materials.append(mat('TextAtlas')); mi['TextAtlas'] = len(me.materials) - 1
    fronts = {}                                            # each plate's flat face: the faces furthest out along its axis
    for f in plate:
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        if abs(n[ax]) < 0.999: continue
        key = (ax, 1 if n[ax] > 0 else -1); d = f.calc_center_median()[ax] * key[1]
        if d < 1.2: continue                               # past the crate's face; the plates' backs, edges and tops are not
        if key not in fronts or d > fronts[key][0] + 1e-5: fronts[key] = (d, [f])
        elif abs(d - fronts[key][0]) < 1e-5: fronts[key][1].append(f)
    lay = []; x = 0.0                                      # (letter, left edge, width) along the line; the atlas is square
    for i, ch in enumerate(NP_TEXT):
        if ch == ' ': x += NP_WORD - NP_GAP; continue
        u0, v0, u1, v1 = GLYPH[ch]; wd = NP_CAP * (u1 - u0) / (v1 - v0)
        lay.append((ch, x, wd)); x += wd + NP_GAP
    tw = x - NP_GAP
    out = 0
    for (ax, sg), (d, fs) in fronts.items():
        vs = [v.co for f in fs for v in f.verts]
        c = Vector([(min(p[i] for p in vs) + max(p[i] for p in vs)) / 2 for i in range(3)])
        n = Vector([0.0] * 3); n[ax] = sg
        up = Vector((0, 0, 1)) if ax != 2 else Vector((0, math.copysign(1, c.y), 0))   # away from the port below it, on the bottom too
        rt = (-n).cross(up)
        o = c + n * OFF - rt * (tw / 2)
        for ch, x, wd in lay:
            u0, v0, u1, v1 = GLYPH[ch]; cs = ((0, 0), (1, 0), (1, 1), (0, 1))
            q = [bm.verts.new(o + rt * (x + a * wd) + up * (b - 0.5) * NP_CAP) for a, b in cs]
            g = bm.faces.new(q); g.normal_update()
            if g.normal.dot(n) < 0: g.normal_flip()
            g.material_index = mi['TextAtlas']; g.smooth = False
            for l in g.loops:
                a, b = cs[q.index(l.vert)]; l[uvl].uv = (u0 + a * (u1 - u0), v0 + b * (v1 - v0))
            out += 1
    return len(plate), out, len(fronts), round(tw, 3)


print('name plates: %d plate faces, %d letters on %d plates, text %.3f m wide' % name_plates(bm, mi))
bvh = BVHTree.FromBMesh(bm)
bm.to_mesh(me); bm.free()
old = base.data; old_name = old.name if old is not SRC else 'GVK_SalvagerTurret_Visual_Mesh'; base.data = me
if old.users == 0 and old is not SRC: bpy.data.meshes.remove(old)
me.name = old_name


def ground(p):
    """Crate-top height (top frame) under p."""
    hit = bvh.ray_cast(Vector((p.x, p.y, ZT + 0.6)), Vector((0, 0, -1)))
    return hit[0].z - ZT if hit[0] else 0.0


# ---- 2. the ring and ears: one plate, face and rim materials, built in the top frame ----
def inset(pts, d):
    """Offset a CCW polygon inward by d along mitred vertex normals."""
    out = []; n = len(pts)
    for i in range(n):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        e1 = (p1 - p0).normalized(); e2 = (p2 - p1).normalized()
        n1 = Vector((-e1.y, e1.x)); n2 = Vector((-e2.y, e2.x))
        m = (n1 + n2).normalized(); out.append(tuple(p1 + m * (d / max(0.2, m.dot(n1)))))
    return out


def loft(b, a, c):
    n = len(a); return [b.faces.new((a[i], a[(i + 1) % n], c[(i + 1) % n], c[i])) for i in range(n)]


MATS = list(dict.fromkeys([FACE_MAT, RIM_MAT])); RIM_I = MATS.index(RIM_MAT)
def mix(name):
    if name not in MATS: MATS.append(name)
    return MATS.index(name)


bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
RIM = []                                   # rim loops, foot up, each a list of Vectors


def build_plate():
    O = [Vector(p) for p in OUTLINE]; n0 = len(O)
    tip = [abs(p.x) > TIP_X for p in O]
    foot = [Vector(p) for p in inset(OUTLINE, PROF_OUT[0][0])]
    H = []                                 # crate-top height under each foot vertex: the lowest over its two half edges
    for i in range(n0):
        if tip[i]: H.append(0.0); continue
        p = foot[i]; hs = [ground(p + (q - p) * t) for q in (foot[i - 1], foot[(i + 1) % n0]) for t in (0.0, 0.2, 0.4, 0.5)]
        H.append(max(FOOT_CLAMP, min(0.0, min(hs))))
    print('foot drop min/max', round(min(H), 4), round(max(H), 4))
    for d, z, dt, drop in PROF_OUT:        # each tip corner splits into a 45-degree chamfer that shrinks as the loop insets
        A_ = [Vector(p) for p in (inset(OUTLINE, d) if d else OUTLINE)]
        B_ = [Vector(p) for p in (inset(OUTLINE, dt) if dt else OUTLINE)]
        L = []
        for i in range(n0):
            zz = z + (H[i] if drop else 0.0)
            if tip[i]:
                K = B_[i]; c = max(0.0008, CORNER - 0.586 * dt)
                for q in (O[i - 1], O[(i + 1) % n0]):
                    w = K + (q - O[i]).normalized() * c; L.append(Vector((w.x, w.y, zz)))
            else:
                L.append(Vector((A_[i].x, A_[i].y, zz)))
        RIM.append(L)
    n = len(RIM[0])
    vts = [[bm.verts.new(p) for p in L] for L in RIM]
    vmap = {v: (k, i) for k, row in enumerate(vts) for i, v in enumerate(row)}
    rim_faces = []
    for a_, b_ in zip(vts, vts[1:]): rim_faces += loft(bm, a_, b_)
    ins = [[bm.verts.new((r * math.cos(2 * math.pi * i / SEG), r * math.sin(2 * math.pi * i / SEG), z)) for i in range(SEG)] for r, z in PROF_IN]
    for a_, b_ in zip(ins, ins[1:]): loft(bm, a_, b_)
    o2, h2 = vts[-1], ins[0]
    edges = [bm.edges.get((o2[i], o2[(i + 1) % len(o2)])) for i in range(len(o2))] + [bm.edges.get((h2[i], h2[(i + 1) % len(h2)])) for i in range(len(h2))]
    res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges, normal=(0, 0, 1))
    print('band faces', len([g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]))
    # tongues: blocks under the ears fitted to the bracket ends (plane y = 0.2348 + 0.4017 * (x + z - 0.9932) above its diagonal)
    u0, u1, zb, gap = BLK; yb = 0.2348 - gap
    yp = lambda x, z: 0.2348 + 0.4017 * max(0.0, x + z - 0.9932) - gap
    xg, xe = 0.9932 - zb, 0.9932
    assert u1 >= xg, (u1, xg)
    bev = []
    for s in (1, -1):
        P = {t_: [bm.verts.new((s * x, t_ * y, z)) for x, y, z in
                  ((u0, yb, zb), (xg, yb, zb), (u1, yp(u1, zb), zb), (u1, yp(u1, 0.0), 0.0), (xe, yb, 0.0), (u0, yb, 0.0))] for t_ in (1, -1)}
        iA, iG, iB, iD, iE, iF = range(6)
        for t_ in (1, -1):
            p = P[t_]; bm.faces.new([p[iA], p[iG], p[iE], p[iF]]); bm.faces.new([p[iG], p[iB], p[iD], p[iE]])
        p, q = P[1], P[-1]
        bm.faces.new([p[iB], p[iD], q[iD], q[iB]]); bm.faces.new([p[iA], p[iG], p[iB], q[iB], q[iG], q[iA]])
        bm.faces.new([p[iA], q[iA], q[iF], p[iF]]); bm.faces.new([p[iF], p[iE], p[iD], q[iD], q[iE], q[iF]])
        bev += [(p[iB], p[iD]), (q[iB], q[iD]), (p[iB], q[iB])]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.bevel(bm, geom=[bm.edges.get(e) for e in bev], offset=TONGUE_BEV, offset_type='WIDTH', segments=1, profile=0.5,
                    affect='EDGES', clamp_overlap=True)
    bm.normal_update()
    for f in bm.faces:                     # planar UVs on the face material
        nn = f.normal; ax = max(range(3), key=lambda i: abs(nn[i]))
        for l in f.loops:
            c = l.vert.co; p2 = [c[i] for i in range(3) if i != ax]; l[uvl].uv = (0.5 + UVK * p2[0], 0.5 + UVK * p2[1])
    # rim: the rollover, wall and foot, except the ears' flat tip faces, unrolled: U round the ring, V up the profile, both
    # at UVK (U rounded to whole tiles round, so it meets itself)
    plen = [0.0]
    for (d0, z0, *_), (d1, z1, *_) in zip(PROF_OUT, PROF_OUT[1:]): plen.append(plen[-1] + math.hypot(d1 - d0, z1 - z0))
    W = RIM[next(k for k, e in enumerate(PROF_OUT) if e[0] == 0)]
    S = [0.0]
    for i in range(1, n): S.append(S[-1] + (W[i].to_2d() - W[i - 1].to_2d()).length)
    Ltot = S[-1] + (W[0].to_2d() - W[-1].to_2d()).length
    UK = round(UVK * Ltot) / Ltot
    nt = 0
    for f in rim_faces:
        if all(abs(v.co.x) > TIP_X for v in f.verts) and abs(f.normal.x) > 0.99:
            f.material_index = 0; nt += 1; continue
        f.material_index = RIM_I
        idx = {vmap[v][1] for v in f.verts}
        for l in f.loops:
            k, i = vmap[l.vert]; s_ = Ltot if (i == 0 and n - 1 in idx) else S[i]
            l[uvl].uv = (UK * s_, UVK * plen[k])
    print('tip face quads', nt, 'rim quads', len(rim_faces) - nt)


def rim_pt(theta, k):
    """Point of rim loop k where the ray from the axis at theta (degrees) crosses it, and the loop's CCW tangent there."""
    a = math.radians(theta); dv = Vector((math.cos(a), math.sin(a)))
    L = RIM[k]; n = len(L)
    for i in range(n):
        p, q = L[i], L[(i + 1) % n]; p2, q2 = p.to_2d(), q.to_2d(); e = q2 - p2
        den = dv.x * e.y - dv.y * e.x
        if abs(den) < 1e-9: continue
        t = (p2.x * e.y - p2.y * e.x) / den; u = (p2.x * dv.y - p2.y * dv.x) / den
        if t > 0 and -1e-9 <= u <= 1 + 1e-9: return p.lerp(q, u), (q - p).normalized()
    raise ValueError(('no rim hit', theta, k))


build_plate()


# ---- 3. decals: vent slots, bolts and seams on the ring and ears, a corner vent on each white crate-top corner ----
def arc(a0, a1, r=RG):
    k0, k1 = math.floor(a0 / 5.625) + 1, math.ceil(a1 / 5.625) - 1
    angs = [a0] + [5.625 * k for k in range(k0, k1 + 1)] + [a1]
    return [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), Z_TOP) for a in angs]


def roll_pieces(s, y, down):
    """Seam pieces over the tip rollover at y, one per facet, band edge down to the tip face (or back up)."""
    pts = [(s * (UF - d), y, z) for d, z in ROLL]; out = []
    for (x0, _, z0), (x1, _, z1) in zip(pts, pts[1:]):
        dx, dz = abs(x1 - x0), z1 - z0; L = math.hypot(dx, dz)
        out.append(((s * -dz / L, 0, dx / L), [(x0, y, z0), (x1, y, z1)]))
    if not down: out = [(nn, p[::-1]) for nn, p in out[::-1]]
    return [(SEAM, nn, p, None, 0) for nn, p in out]


def ear(s):
    first, last = (-YS, YS) if s > 0 else (YS, -YS)       # the loop comes in on this side and leaves on the other
    yb = YS - SLOPE * abs(ZB)
    tipf = [(s * UF, first, ZW), (s * UF, first, 0.0), (s * UF, math.copysign(yb, first), ZB), (s * UF, math.copysign(yb, last), ZB),
            (s * UF, last, 0.0), (s * UF, last, ZW)]
    return roll_pieces(s, first, True) + [(SEAM, (s, 0, 0), tipf, None, 0)] + roll_pieces(s, last, False)


def overlaps(dec, paths):
    """Decal-decal and decal-seam overlaps on each flat plane (separating axis test, 0.5 mm tolerance)."""
    items = []
    for m_, pc, c, nn, up, w, h, phi in dec:
        nn = Vector(nn).normalized(); v = Vector(up).normalized(); u = v.cross(nn)
        if phi: cp, sp = math.cos(phi), math.sin(phi); u, v = u * cp + v * sp, v * cp - u * sp
        c = Vector(c); items.append((pc + '@' + ','.join('%.3f' % q for q in c), nn, [c + u * (a * w / 2) + v * (b * h / 2) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]))
    for m_, nn, pts, apex, xo, *rest in paths:
        nn = Vector(nn).normalized()
        for p0, p1 in zip(pts, pts[1:]):
            p0, p1 = Vector(p0), Vector(p1); d = (p1 - p0).normalized(); r = d.cross(nn) * 0.0099
            p0, p1 = p0 + d * 0.002, p1 - d * 0.002
            items.append(('seam', nn, [p0 - r, p0 + r, p1 + r, p1 - r]))
    groups = {}
    for nm, nn, q in items:
        groups.setdefault((round(nn.x, 2), round(nn.y, 2), round(nn.z, 2), round(nn.dot(q[0]), 3)), []).append((nm, nn, q))
    bad = []
    for g in groups.values():
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                (na, nn, qa), (nb, _, qb) = g[i], g[j]
                if na == 'seam' and nb == 'seam': continue
                ax = nn.orthogonal().normalized(); ay = nn.cross(ax)
                pa = [Vector((p.dot(ax), p.dot(ay))) for p in qa]; pb = [Vector((p.dot(ax), p.dot(ay))) for p in qb]
                sep = False
                for poly in (pa, pb):
                    for k in range(4):
                        e = poly[(k + 1) % 4] - poly[k]; m = Vector((-e.y, e.x)).normalized()
                        a_ = [p.dot(m) for p in pa]; b_ = [p.dot(m) for p in pb]
                        if min(a_) > max(b_) - 0.0005 or min(b_) > max(a_) - 0.0005: sep = True; break
                    if sep: break
                if not sep: bad.append((na, nb))
    return bad


def layout():
    """(decals, seam paths, raw faces). Decal: (mat, piece, centre, normal, up, w, h, turn). Path: (mat, normal, points,
    apex of a pointed start or None, extra offset[, flip V]), V1 on the right. Raw: (mat, normal, points, uvs)."""
    dec, paths, raw = [], [], []
    # groove: one loop, counter-clockwise in plan: +Y side, -X ear, -Y side, +X ear
    paths.append((SEAM, (0, 0, 1), [(UT, YS, Z_TOP), (X2, YS, Z_TOP)] + arc(TA, 180 - TA) + [(-X2, YS, Z_TOP), (-UT, YS, Z_TOP)], None, 0))
    paths += ear(-1)
    paths.append((SEAM, (0, 0, 1), [(-UT, -YS, Z_TOP), (-X2, -YS, Z_TOP)] + arc(180 + TA, 360 - TA) + [(X2, -YS, Z_TOP), (UT, -YS, Z_TOP)], None, 0))
    paths += ear(1)
    # vent panels front and back: seams over the strap handles' edges, a 45-degree leg into the groove, then down the rim
    for th, sg in VENTS:
        a = math.radians(th); rh = Vector((math.cos(a), math.sin(a), 0)); t = Vector((-math.sin(a), math.cos(a), 0))
        C2 = rh * (RG + 0.05) + Vector((0, 0, Z_TOP)); dl = (-rh + sg * t).normalized(); C1 = C2 + dl * 0.04
        b = C1.to_2d().dot(dl.to_2d()); tt = -b - math.sqrt(b * b - C1.to_2d().length_squared + RG ** 2)
        top, _ = rim_pt(th, 5)
        paths.append((SEAM, (0, 0, 1), [C1, C2, top], C1 + dl * tt, 0.001, True))
        for k in (5, 4, 3, 2):     # loop 1 meets the crate top; the foot chamfer below it is buried in the plate
            pu, tu = rim_pt(th, k); pl, _ = rim_pt(th, k - 1)
            paths.append((SEAM, tu.cross(pu - pl).normalized(), [pu, pl], None, 0, True))
    # vent slots and bolts on the pitch circle
    for cen in (90, 270):
        for k in range(-4, 5):
            a = math.radians(cen + 2.4 * k)
            dec.append((ATL, 'A3-15', (PC * math.cos(a), PC * math.sin(a), Z_TOP), (0, 0, 1), (math.cos(a), math.sin(a), 0), 0.025, 0.06, 0))
        for e, r in ((-12.5, 1.075), (12.5, 1.075), (-17.5, PC), (17.5, PC)):
            a = math.radians(cen + e); dec.append((ATL, 'bolt', (r * math.cos(a), r * math.sin(a), Z_TOP), (0, 0, 1), (0, 1, 0), 0.04, 0.04, e))
    for t_ in (45, 135, 225, 315):
        a = math.radians(t_); dec.append((ATL, 'A3-4', (PC * math.cos(a), PC * math.sin(a), Z_TOP), (0, 0, 1), (math.cos(a), math.sin(a), 0), 0.085, 0.085, 0))
    for t_ in range(0, 360, 45):
        a = math.radians(t_); dec.append((ATL, 'bolt', (0.908 * math.cos(a), 0.908 * math.sin(a), 0.09), (0, 0, 1), (math.cos(a), math.sin(a), 0), 0.04, 0.04, 0))     # square to the radius: a turned 4 cm bolt overhangs the 4.4 cm step
    for s in (1, -1):
        dec.append((ATL, 'A3-4', (s * 1.11, 0, Z_TOP), (0, 0, 1), (0, 1, 0), 0.12, 0.12, 0))
        for y in (0.19, -0.19): dec.append((ATL, 'bolt', (s * 1.11, y, Z_TOP), (0, 0, 1), (0, 1, 0), 0.04, 0.04, 0.7 * y + s))
        for k in range(-4, 5): dec.append((ATL, 'A3-15', (s * UF, 0.046 * k, 0.0175), (s, 0, 0), (0, 0, 1), 0.022, 0.045, 0))
        dec.append((ATL, 'A3-7', (s * UF, 0, -0.11), (s, 0, 0), (0, 0, 1), 0.11, 0.162, 0))
        for y in (0.15, -0.15): dec.append((ATL, 'bolt', (s * UF, y, -0.11), (s, 0, 0), (0, 0, 1), 0.04, 0.04, 2 * y))
    # crate-top corners: Atlas3 piece 29, its right angle to the corner and its hypotenuse to the ring, turned (never mirrored)
    bx = BOX['A3-29']
    for sx, sy in QUADS:
        ang = math.radians(math.degrees(math.atan2(sy, sx)) - 45); c, s_ = math.cos(ang), math.sin(ang)
        rot = lambda v: Vector((v[0] * c - v[1] * s_, v[0] * s_ + v[1] * c, 0.0))
        ud, vd, C = rot((0, -1)), rot((1, 0)), rot((VC, VC))
        ab = [(0, 1), (1, 1), (1, 0.775), (0.225, 0), (0, 0)]  # the box less the empty corner past the art's diagonal edge
        P = [C + ud * (a * VS) + vd * ((b - 1) * VS) for a, b in ab]
        U = [(bx[0] + a * (bx[2] - bx[0]), bx[1] + b * (bx[3] - bx[1])) for a, b in ab]
        if (P[1] - P[0]).cross(P[2] - P[1]).z < 0: P, U = P[::-1], U[::-1]
        raw.append(('Atlas3_Colorable', (0, 0, 1), [tuple(p) for p in P], U))
    return dec, paths, raw


dec, paths, raw = layout()
bad = overlaps(dec, paths)
print('decals', len(dec), 'seam paths', len(paths), 'corner vents', len(raw), 'VS %.4f VC %.4f' % (VS, VC), 'overlaps', len(bad), bad[:12])
assert not bad
nd = 0
for m_, pc, c, nn, up, w, h, phi in dec:
    nn = Vector(nn).normalized(); v = Vector(up).normalized(); u = v.cross(nn)
    if phi: cp, sp = math.cos(phi), math.sin(phi); u, v = u * cp + v * sp, v * cp - u * sp
    c = Vector(c) + nn * OFF; bx = BOX[pc]; cs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    f = bm.faces.new([bm.verts.new(c + u * (a * w / 2) + v * (b * h / 2)) for a, b in cs]); f.material_index = mix(m_); nd += 1
    for l, (a, b) in zip(f.loops, cs): l[uvl].uv = (bx[0] if a < 0 else bx[2], bx[1] if b < 0 else bx[3])
U0 = 0.0
for m_, nn, pts, apex, xo, *rest in paths:
    nn = Vector(nn).normalized(); P_ = [Vector(p) + nn * (OFF + xo) for p in pts]; h = 0.01
    sv0, sv1 = (SEAM_V[1], SEAM_V[0]) if (rest and rest[0]) else SEAM_V
    ds = [(P_[i + 1] - P_[i]).normalized() for i in range(len(P_) - 1)]; rs = [d.cross(nn) for d in ds]
    Ls, Rs, Ss = [], [], [0.0]
    for i in range(len(P_)):
        if i == 0: m, sc = rs[0], h
        elif i == len(P_) - 1: m, sc = rs[-1], h
        else: m = (rs[i - 1] + rs[i]).normalized(); sc = h / max(0.3, m.dot(rs[i]))
        Ls.append(bm.verts.new(P_[i] - m * sc)); Rs.append(bm.verts.new(P_[i] + m * sc))
        if i: Ss.append(Ss[-1] + (P_[i] - P_[i - 1]).length)
    k_ = mix(m_)
    for i in range(len(P_) - 1):
        f = bm.faces.new([Ls[i], Rs[i], Rs[i + 1], Ls[i + 1]]); f.material_index = k_; nd += 1
        for l, (uu, vv) in zip(f.loops, ((Ss[i], sv0), (Ss[i], sv1), (Ss[i + 1], sv1), (Ss[i + 1], sv0))): l[uvl].uv = ((U0 + uu) * SEAM_US, vv)
    if apex is not None:
        ap = bm.verts.new(Vector(apex) + nn * (OFF + xo)); f = bm.faces.new([ap, Rs[0], Ls[0]]); f.material_index = k_; nd += 1
        tl = (Vector(apex) + nn * (OFF + xo) - P_[0]).length
        for l, (uu, vv) in zip(f.loops, ((-tl, (sv0 + sv1) / 2), (0.0, sv1), (0.0, sv0))): l[uvl].uv = ((U0 + uu) * SEAM_US, vv)
    U0 += Ss[-1]
for m_, nn, pts, uvs in raw:
    nn = Vector(nn).normalized(); f = bm.faces.new([bm.verts.new(Vector(p) + nn * OFF) for p in pts]); f.material_index = mix(m_); nd += 1
    for l, uv_ in zip(f.loops, uvs): l[uvl].uv = uv_

# ---- 4. into the block frame, as a child of the base: smooth, sharp over 30 degrees, weighted normals ----
bmesh.ops.translate(bm, vec=(0, 0, ZT), verts=bm.verts[:])
rme = bpy.data.meshes.new(RING_OB + '_Mesh')
for m_ in MATS: rme.materials.append(mat(m_))
bm.to_mesh(rme); bm.free()
rme.shade_smooth(); rme.set_sharp_from_angle(angle=math.radians(30))
ob = bpy.data.objects.get(RING_OB)
if ob is None:
    ob = bpy.data.objects.new(RING_OB, rme)
    for col in base.users_collection: col.objects.link(ob)
    ob.parent = base; ob.matrix_parent_inverse.identity()
    wn = ob.modifiers.new('WeightedNormal', 'WEIGHTED_NORMAL'); wn.mode = 'FACE_AREA'; wn.keep_sharp = True
else:
    oldm = ob.data; ob.data = rme
    if oldm.users == 0: bpy.data.meshes.remove(oldm)
rme.name = RING_OB + '_Mesh'
xs = [v.co.x for v in rme.vertices]; ys = [v.co.y for v in rme.vertices]; zs = [v.co.z for v in rme.vertices]
print('ring faces', len(rme.polygons), 'decal faces', nd, 'materials', MATS,
      'x %.4f..%.4f y %.4f..%.4f z %.4f..%.4f' % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
