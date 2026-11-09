"""Salvage Beam Turret canister: kiosk bay, beam surround, side plates, slot and seam decals, and the top.

Run inside GVK_SalvagerTurret.blend. Rebuilds GVK_SalvagerTurret_Azimuth_Visual's mesh from the kept
AZ_base_nokiosk mesh (canister before the kiosk), so every run starts clean. Azimuth frame: front +Y,
z measured from the canister foot. "Front-on x" is x as seen straight from the front.
"""
import bpy, bmesh, math, random
from mathutils import Vector

# ---- parameters (metres) ----
R = 1.12; SEG = 5.625; HALF = math.radians(SEG / 2)
BAY_K = 7                      # bay half-width in facets (7 x 5.625 = 39.375 degrees each side)
BAY_DEPTH = 0.01               # recess depth, the depth of the base mesh's ring grooves
# height cut (owner, 2026-11-08: "shorten the height of the canister about 15%", A of art/height-mock.png: every band
# shorter in proportion): the body between the foot's dark collar (z 0.40) and the lip loses H_CUT, the bay 3.70 ->
# 3.07 m; the top moves down H_CUT unchanged. The base mesh is remapped in step 0; small sizes (grooves, gaps, bevels,
# decals) keep their size
H_CUT = 0.70
BODY_Z = (0.55, 3.62)          # the bay's top and bottom edges on the wall (were 0.58, 4.28)
H_K = (BODY_Z[1] - BODY_Z[0]) / 3.70                 # the bay's height ratio, for positions measured from its middle
Z_WALL = 4.45 - H_CUT          # the wall's top loop, where the top starts
GZB0, GZB1 = round(BODY_Z[0] + 0.005, 3), round(BODY_Z[1] - 0.005, 3)   # bay floor ends (the old groove bottoms; the grooves' outer chamfers are the bay's ends)
FL_CZ = (round(BODY_Z[0] + 0.025, 3), round(BODY_Z[1] - 0.025, 3))      # the floor's corner verts at the grooves' inner chamfers
RING_Z = ((BODY_Z[0], BODY_Z[0] + 0.03), (BODY_Z[1] - 0.03, BODY_Z[1]))   # the base mesh's cut ring grooves, filled outside the bay (owner, 2026-11-07)
GAP = 0.027                    # one gap, along the surface: wall to every part, and part to part
Z0, Z1 = BODY_Z[0] + GAP, BODY_Z[1] - GAP   # bottom and top of the parts, all level
# beam surround: truncated pyramid on the bay floor, rounded corners, front face dipped over its middle third
P_BX, P_BZ = 0.24, (Z0, Z1)          # base footprint (front-on half-width, z range)
P_FX, P_END = 0.195, 0.20            # front face half-width; height of the sloped ends
P_FY = 1.232                         # front face distance from the axis (front corners at r 1.247, inside the 1.25 cell edge)
# owner, 2026-11-07: "I want the beam surround and the chrome plates around it to look a little thicker": front face
# 0.35 -> 0.39 m wide (rim round the glow 35 -> 55 mm), 12 mm further out, steeper slopes
P_CR, P_BEV = 0.03, 0.003            # corner rounding (bevel offset), front rim bevel
DIP = 0.03                           # front face dip over its middle third, 45 degree ramps
P_FZ = (P_BZ[0] + P_END, P_BZ[1] - P_END)
# glow slot: half-width, end margin, corner r, chamfer at its edge, depth of the flat glow below the outer face
GW = 0.14; G_END = 0.11; GR = 0.05; G_CH = 0.005; G_DEPTH = 0.075
# glow UVs: the scan-line half of the atlas (v 0.5 to 1, 64 lines 16 px apart, its first and last rows match so it
# tiles), length along v so the lines run across the strip, repeated G_TILES times along it for denser lines
# (owner, 2026-11-07: "maximize the height of the atlas and make it look more dense"); even in pixels, so u per
# metre is twice v per metre (the atlas is 1024 x 2048)
# u from G_U0: the panel's line breaks stand in three columns at u 0.12, 0.18 and 0.23; G_U0 0.085 centres the middle
# one on the strip (owner, 2026-11-08: "moved over a little so the breaks in the white lines are centered")
# G_UPM: u per metre as on the full-height canister, so the breaks stay centred; the shorter strip packs its two tiles
# 17% closer along it (height cut)
G_TILES, G_U0, G_UPM = 2, 0.085, 0.661
GZ0, GZ1 = P_FZ[0] + G_END, P_FZ[1] - G_END
G_LT = (GZ1 - GZ0) / G_TILES; G_VPM = 0.5 / G_LT


def gap_x(x):
    """Front-on width of GAP measured along the facet at front-on x."""
    return GAP * math.cos(math.radians((math.floor(math.degrees(math.asin(x / R)) / SEG) + 0.5) * SEG))


# side plates and modules: thin shells on the bay floor, front-on outlines
XO = R * math.sin(math.radians(BAY_K * SEG)) - GAP * math.cos(math.radians((BAY_K - 0.5) * SEG))
XI = P_BX + gap_x(P_BX)
SH_BACK, SH_FRONT = -BAY_DEPTH, 0.025   # offsets from the wall surface: on the floor, 25 mm proud (was 2 mm; owner, 2026-11-07: thicker)
SH_BEV = 0.008
MOD_H = 0.257 * (Z1 - Z0); MOD =[(Z0, Z0 + MOD_H), (Z1 - MOD_H, Z1)]; MOD_R = 0.03
PL_Z = (Z0 + MOD_H + GAP, Z1 - MOD_H - GAP)
# side slots (Atlas3 piece 20, tall dark slot) where the stripes were, at 45 degrees (owner's pick, 2026-11-07);
# the lower is the upper's mirror about the bay's middle height, moved 0.15 m further apart (owner, 2026-11-07)
ZMID = (RING_Z[0][1] + RING_Z[1][0]) / 2
ST_C = (64.6, ZMID + (3.72 - 2.43) * H_K)   # upper slot centre: degrees round from the front, z (3.72 at full height)
HO_BOX = (0.0049, 0.4429, 0.0586, 0.6826)   # u0, v0, u1, v1: 110 x 491 px
HO_L = 0.78; HO_W = HO_L * 110 / 491; HO_OFF = 0.0015
# panel seam decals (owner's pick of the sketch art/seam-proposal-side.png, 2026-11-07): a ring at each old groove,
# its band edge level with the bay's end, stepping up SM_STEP at 45 degrees over the middle of each side panel,
# SM_IN in from each panel end; a vertical seam each side, as far from the back as the bay edge is from the front
SM_W, SM_STEP, SM_IN = 0.020, 0.07, (0.30, 0.15)   # line width (Keen's newer blocks 13-23 mm); step; inset bottom, top
SM_Z = BODY_Z     # the rings' centre lines on the bay's top and bottom edges, so each splits round the bay (step 5b)
SM_OFF, SM_STEM_OFF = 0.0015, 0.0025               # stems sit 1 mm higher so their tips draw over the rings
SM_V, SM_US = (0.4834, 0.5166), 0.5                # Atlas4 piece 3 across V; U per metre along the line
TH_BACK = 180 - BAY_K * SEG

SRC = bpy.data.meshes['AZ_base_nokiosk']
obj = bpy.data.objects['GVK_SalvagerTurret_Azimuth_Visual']
me = SRC.copy(); me.name = 'AZ_kiosk_build'
for mn in ('Chrome', 'Atlas4_Colorable', 'Atlas3_Colorable', 'CameraLens', 'Atlas3_Chrome', 'Decals', 'Atlas4_Chrome', 'Atlas4_Darker', 'PaintedMetal_VeryDark', 'Atlas4_VeryDark', 'Rubber', 'Atlas2', 'BlackMetal'):
    if mn not in [m.name for m in me.materials]:
        me.materials.append(bpy.data.materials[mn])
MI = {m.name: i for i, m in enumerate(me.materials)}
C, D, DUL, EM = MI['Chrome'], MI['PaintedMetal_Darker'], MI['Metal_Dull'], MI['Emissive']
PC, SM, HO = MI['PaintedMetal_Colorable'], MI['Atlas4_Colorable'], MI['Atlas3_Colorable']
CL, RED = MI['CameraLens'], MI['PaintedMetal_Red']
VD = MI['PaintedMetal_VeryDark']       # the bay, like the top's dark deck (owner, 2026-11-07: "Bay VeryDark too")
bm = bmesh.new(); bm.from_mesh(me)
uv = bm.loops.layers.uv.active

# ---- 0. height cut: remap the base mesh's z (old level -> new); the grooves move whole, the bands between them
# shrink, the top moves down H_CUT. The wall paint keeps its v = 0.27 z, so its texture is not squashed ----
Z_KNOTS = [(0.401, 0.401), (0.58, BODY_Z[0]), (0.61, BODY_Z[0] + 0.03), (4.25, BODY_Z[1] - 0.03), (4.28, BODY_Z[1]),
           (4.45, Z_WALL)]


def zmap(z):
    if z <= Z_KNOTS[0][0]: return z
    for (a0, b0), (a1, b1) in zip(Z_KNOTS, Z_KNOTS[1:]):
        if z <= a1: return b0 + (z - a0) * (b1 - b0) / (a1 - a0)
    return z - H_CUT


old_z = {v: v.co.z for v in bm.verts}
for v in bm.verts: v.co.z = zmap(v.co.z)
for f in bm.faces:
    if f.material_index != MI['PaintedMetal_Colorable']: continue
    for l in f.loops:
        if abs(l[uv].uv.y - 0.27 * old_z[l.vert]) < 1e-3: l[uv].uv.y = 0.27 * l.vert.co.z


def islands(b):
    b.faces.ensure_lookup_table(); seen = set(); out = []
    for f in b.faces:
        if f.index in seen: continue
        st = [f]; fs = []; seen.add(f.index)
        while st:
            g = st.pop(); fs.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen: seen.add(h.index); st.append(h)
        out.append(fs)
    return out


def face(vs, want, mat, b=None):
    f = (b or bm).faces.new(vs); f.normal_update()
    if f.normal.dot(Vector(want)) < 0: f.normal_flip()
    f.material_index = mat; return f


def boxuv(faces, k):
    for f in faces:
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            c = l.vert.co
            l[uv].uv = (c.y * k, c.z * k) if ax == 0 else ((c.x * k, c.z * k) if ax == 1 else (c.x * k, c.y * k))


def ang(co): return math.atan2(co.x, co.y)


XB = [R * math.sin(math.radians(k * SEG)) for k in range(17)]


def surf(x, z, h):
    """Point on the faceted wall at front-on x, height z, offset h along the facet normal."""
    s = 1 if x >= 0 else -1; ax = abs(x)
    k = next(k for k in range(16) if ax <= XB[k + 1] + 1e-9)
    t = (ax - XB[k]) / (XB[k + 1] - XB[k])
    if t < 1e-6 or t > 1 - 1e-6:
        a = math.radians((k if t < 0.5 else k + 1) * SEG); rr = R + h / math.cos(HALF)
        return Vector((s * rr * math.sin(a), rr * math.cos(a), z))
    a0 = math.radians(k * SEG); a1 = math.radians((k + 1) * SEG); am = (a0 + a1) / 2
    p = Vector((s * R * math.sin(a0), R * math.cos(a0), z)).lerp(Vector((s * R * math.sin(a1), R * math.cos(a1), z)), t)
    return p + Vector((s * math.sin(am), math.cos(am), 0)) * h


# ---- 1. remove old kiosk and old stripes ----
dead = set()
for fs in islands(bm):
    vs = {v for f in fs for v in f.verts}
    xs = [abs(v.co.x) for v in vs]; ys = [v.co.y for v in vs]
    mats = {me.materials[f.material_index].name for f in fs}
    rs = [math.hypot(v.co.x, v.co.y) for v in vs]
    if (min(ys) > 0.9 and max(xs) < 0.6) or (len(fs) == 16 and min(xs) > 0.7 and max(xs) < 1.11 and mats == {'PaintedMetal_Darker'}):
        dead |= vs
    elif mats == {'PaintedMetal_Colorable'} and min(rs) > 1.1215 and max(rs) < 1.1235 and max(v.co.z for v in vs) < BODY_Z[0]:
        dead |= vs     # a loose painted band 2.5 mm off the wall under the bay, joined to nothing (round 7 seam audit)
bmesh.ops.delete(bm, geom=list(dead), context='VERTS')

# ---- 1b. fill the ring grooves outside the bay: flat wall, seam decals instead (step 5b) ----
def kpos(v):
    d = math.degrees(ang(v.co)) / SEG; k = round(d)
    return k % 64 if abs(d - k) < 1e-4 else None


def in_ring(z, j): return RING_Z[j][0] - 1e-4 <= z <= RING_Z[j][1] + 1e-4


OUTM = range(BAY_K, 64 - BAY_K + 1)          # facet vertex indices (0-63) on or outside the bay edges
for j in (0, 1):
    old_f = [f for f in bm.faces if all(in_ring(v.co.z, j) and kpos(v) in OUTM for v in f.verts)
             and math.hypot(*f.calc_center_median().xy) > 1.10]
    print('groove', j, 'faces', len(old_f))
    bmesh.ops.delete(bm, geom=old_f, context='FACES')
    col_v = {}
    for v in bm.verts:
        if not in_ring(v.co.z, j) or kpos(v) not in OUTM: continue
        r = math.hypot(v.co.x, v.co.y)
        if r < 1.10: continue
        if kpos(v) in (BAY_K, 64 - BAY_K):
            if abs(r - R) > 1e-3: continue          # bay corner floor verts stay at the floor
        elif abs(r - R) > 1e-4:
            v.co.x *= R / r; v.co.y *= R / r
        col_v.setdefault(kpos(v), []).append(v)
    zr = RING_Z[j][1] if j == 0 else RING_Z[j][0]        # the wall edge on the long side of the ring
    for m in range(BAY_K, 64 - BAY_K):
        a_, b_ = sorted(col_v[m], key=lambda v: v.co.z), sorted(col_v[m + 1], key=lambda v: -v.co.z)
        am = math.radians((m + 0.5) * SEG)
        f = face(a_ + b_, (math.sin(am), math.cos(am), 0), PC)
        # UVs: the wall face beyond the ring on this facet, carried on at its own rate in z
        g = bm.edges.get((a_[-1], b_[0]) if j == 0 else (a_[0], b_[-1]))
        wall = next(h for h in g.link_faces if h is not f); f.smooth = wall.smooth
        for l in f.loops:
            side = [k for k in wall.loops if kpos(k.vert) == kpos(l.vert)]
            near = min(side, key=lambda k: abs(k.vert.co.z - zr)); far = max(side, key=lambda k: abs(k.vert.co.z - zr))
            rate = (far[uv].uv[1] - near[uv].uv[1]) / (far.vert.co.z - near.vert.co.z)
            l[uv].uv = (near[uv].uv[0], near[uv].uv[1] + (l.vert.co.z - near.vert.co.z) * rate)

# ---- 2. bay: 1 cm recess between the groove bottoms ----
TH = math.radians(BAY_K * SEG)
cut = [f for f in bm.faces if math.hypot(*f.calc_center_median().xy) > 1.10 and abs(ang(f.calc_center_median())) < TH
       and GZB0 < f.calc_center_median().z < GZB1]
bmesh.ops.delete(bm, geom=cut, context='FACES')
inner = {}; outer = {}
for v in bm.verts:
    r = math.hypot(v.co.x, v.co.y); k = round(math.degrees(ang(v.co)) / SEG)
    if not v.link_faces: continue
    if abs(math.degrees(ang(v.co)) - k * SEG) > 1e-3 or abs(k) > BAY_K: continue
    if abs(r - (R - BAY_DEPTH)) < 0.002: inner[(k, round(v.co.z, 3))] = v
    elif abs(r - R) < 0.002: outer.setdefault(k, []).append(v)
for k in (BAY_K, -BAY_K):   # the floor's corner verts went with the filled grooves; put them back for its side edges
    for z in FL_CZ:
        if (k, z) not in inner:
            c = inner[(k, GZB0)].co; inner[(k, z)] = bm.verts.new((c.x, c.y, z))
bayf = []
for k in range(-BAY_K, BAY_K):
    am = math.radians((k + 0.5) * SEG); want = (math.sin(am), math.cos(am), 0)
    vs = [inner[(k, GZB0)], inner[(k + 1, GZB0)]]
    if k + 1 == BAY_K: vs += [inner[(k + 1, FL_CZ[0])], inner[(k + 1, FL_CZ[1])]]
    vs += [inner[(k + 1, GZB1)], inner[(k, GZB1)]]
    if k == -BAY_K: vs += [inner[(k, FL_CZ[1])], inner[(k, FL_CZ[0])]]
    bayf.append(face(vs, want, VD))
for k, sgn in ((BAY_K, -1), (-BAY_K, 1)):
    # side step from the bay's bottom edge to its top edge (the grooves outside are filled, step 1b)
    col = sorted([v for v in outer[k] if BODY_Z[0] - 1e-4 <= v.co.z <= BODY_Z[1] + 1e-4], key=lambda v: v.co.z)
    a = math.radians(k * SEG)
    bayf.append(face([inner[(k, GZB0)]] + col + [inner[(k, GZB1)], inner[(k, FL_CZ[1])], inner[(k, FL_CZ[0])]],
                     (sgn * math.cos(a), -sgn * math.sin(a), 0), VD))
boxuv(bayf, 0.35)
for f in bayf: f.smooth = True               # its facets follow the wall; the object's Smooth by Angle splits the sides
for f in bm.faces:   # the bay's ends, the old grooves' outer chamfers kept from the base mesh, go dark with it
    c = f.calc_center_median()
    if (1.10 < math.hypot(c.x, c.y) < 1.125 and abs(ang(c)) < TH and abs(f.normal.z) > 0.8
            and (BODY_Z[0] - 0.01 < c.z < GZB0 or GZB1 < c.z < BODY_Z[1] + 0.01)):
        f.material_index = VD

# ---- 3. beam surround: truncated pyramid ----
def rrect(cx, cz, hx, hz, r, n):
    pts = []
    for ox, oz, a0 in ((cx + hx - r, cz + hz - r, 0), (cx - hx + r, cz + hz - r, 90), (cx - hx + r, cz - hz + r, 180), (cx + hx - r, cz - hz + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((ox + r * math.cos(a), oz + r * math.sin(a)))
    return pts


#   Built as a sharp solid with a flat base at the plinth top's centre depth, its 4 slope corners rounded and its
#   front rim bevelled, the glow slot cut, the front face dipped, then the base verts dropped onto the plinth top
#   and the plinth's walls run from its outline to the floor.
RF = R - BAY_DEPTH / math.cos(HALF)                    # floor radius at the facet lines


def off_y(x, rr):
    """y of the wall offset along its facet normals (rr: that surface's radius at the facet lines), at front-on x."""
    ax = abs(x); fk = [rr * math.sin(math.radians(k * SEG)) for k in range(17)]
    k = next(k for k in range(16) if ax <= fk[k + 1] + 1e-9)
    t = (ax - fk[k]) / (fk[k + 1] - fk[k]); a0 = math.radians(k * SEG); a1 = math.radians((k + 1) * SEG)
    return rr * (math.cos(a0) + t * (math.cos(a1) - math.cos(a0)))


# plinth (owner, 2026-11-08: "add that same thickness to the back of the beam surround, then the pyramid angles start
# level with the side plates"): from the bay floor to SH_FRONT, its walls along the facet normals like the plates'
# sides and at P_BX on the wall, so the gap to the plates stays GAP; the pyramid stands on its top
RT = R + SH_FRONT / math.cos(HALF)
FT = [RT * math.sin(math.radians(k * SEG)) for k in range(17)]
def top_y(x): return off_y(x, RT)


PBT = surf(P_BX, 0, SH_FRONT).x   # the plinth top's front-on half-width
Y0 = top_y(PBT)           # the plinth top under the side edges, so the side slopes are exact and stay flat
pb = bmesh.new(); soft = pb.faces.layers.int.new('soft')   # 1 the pyramid's rounded corners, 2 the plinth's
qb = [pb.verts.new((sx * PBT, Y0, z)) for sx, z in ((-1, P_BZ[0]), (1, P_BZ[0]), (1, P_BZ[1]), (-1, P_BZ[1]))]
qt = [pb.verts.new((sx * P_FX, P_FY, z)) for sx, z in ((-1, P_FZ[0]), (1, P_FZ[0]), (1, P_FZ[1]), (-1, P_FZ[1]))]
face([qb[0], qb[3], qb[2], qb[1]], (0, -1, 0), C, pb); face(qt, (0, 1, 0), C, pb)
face([qb[0], qb[1], qt[1], qt[0]], (0, 0.5, -1), C, pb); face([qb[2], qb[3], qt[3], qt[2]], (0, 0.5, 1), C, pb)
face([qb[1], qb[2], qt[2], qt[1]], (1, 0.5, 0), C, pb); face([qb[3], qb[0], qt[0], qt[3]], (-1, 0.5, 0), C, pb)
rc = bmesh.ops.bevel(pb, geom=[pb.edges.get((qb[i], qt[i])) for i in range(4)], offset=P_CR, offset_type='OFFSET',
                     segments=6, profile=0.5, affect='EDGES', clamp_overlap=True, material=C)
for f in rc['faces']: f[soft] = 1
pb.normal_update()


def front_face(): return next(f for f in pb.faces if f.normal.y > 0.999 and f.calc_center_median().y > P_FY - 1e-6)


bmesh.ops.bevel(pb, geom=list(front_face().edges), offset=P_BEV, offset_type='OFFSET', segments=2, profile=0.5,
                affect='EDGES', clamp_overlap=True, material=C)
pb.normal_update()
fr = front_face(); A = [l.vert for l in fr.loops]
bmesh.ops.delete(pb, geom=[fr] + [f for f in pb.faces if f.normal.y < -0.999], context='FACES_ONLY')
ZC = (GZ0 + GZ1) / 2; hh = (GZ1 - GZ0) / 2
Ci = rrect(0, ZC, GW + G_CH, hh + G_CH, GR + G_CH, 6); Dg = rrect(0, ZC, GW, hh, GR, 6)
Cv = [pb.verts.new((x, P_FY, z)) for x, z in Ci]
Ev = [pb.verts.new((x, P_FY - G_CH, z)) for x, z in Dg]
Dv = [pb.verts.new((x, P_FY - G_DEPTH, z)) for x, z in Dg]


FRONT_OUT = [(v.co.x, v.co.z) for v in A]   # the flat front face's outer edge, for the seam round it (step 6e)


def an(v, hx, hz): return math.atan2((v.co.z - ZC) / hz, v.co.x / hx)


# each loop's angle on its own half-width and half-height, so their corners line up: on plain angles round the glow
# centre the tall narrow glow's corners came out of step and a front triangle covered a glow corner (owner, 2026-11-08)
hxA, hzA = max(abs(v.co.x) for v in A), max(abs(v.co.z - ZC) for v in A); hxB, hzB = GW + G_CH, hh + G_CH
As = sorted(A, key=lambda v: an(v, hxA, hzA)); Bs = sorted(Cv, key=lambda v: an(v, hxB, hzB))
aA = [an(v, hxA, hzA) for v in As]; aA.append(aA[0] + 2 * math.pi)
aB = [an(v, hxB, hzB) for v in Bs]; aB.append(aB[0] + 2 * math.pi)
i = j = 0; na, nb = len(As), len(Bs)
while i < na or j < nb:     # front face: zip the rim loop to the glow lip by angle round the glow centre
    if j == nb or (i < na and aA[i + 1] <= aB[j + 1]):
        face([As[i], As[(i + 1) % na], Bs[j % nb]], (0, 1, 0), C, pb); i += 1
    else:
        face([As[i % na], Bs[j], Bs[(j + 1) % nb]], (0, 1, 0), C, pb); j += 1
for k in range(len(Cv)):    # slot: chamfered edge, then straight walls down to the flat glow
    m = (k + 1) % len(Cv)
    face([Cv[k], Cv[m], Ev[m], Ev[k]], (0, 1, 0), C, pb)
    face([Ev[k], Ev[m], Dv[m], Dv[k]], (-(Dg[m][1] - Dg[k][1]), 0, Dg[m][0] - Dg[k][0]), C, pb)
face(Dv, (0, 1, 0), EM, pb)
# dip: the front face sinks DIP over its middle third, as if milled across; the rim slides down the side slopes,
# the glow stays flat (owner, 2026-11-07)
za, zb = P_FZ[0] + (P_FZ[1] - P_FZ[0]) / 3, P_FZ[1] - (P_FZ[1] - P_FZ[0]) / 3
for zc in (za, za + DIP, zb - DIP, zb):
    bmesh.ops.bisect_plane(pb, geom=pb.verts[:] + pb.edges[:] + pb.faces[:], plane_co=(0, 0, zc), plane_no=(0, 0, 1))
KS = (PBT - P_FX) / (P_FY - Y0)           # side slope: x out per y down
for t in range(1, G_TILES):   # glow cut where each tile of the scan lines starts again
    gl = [f for f in pb.faces if f.material_index == EM]
    bmesh.ops.bisect_plane(pb, geom=list({x for f in gl for x in list(f.verts) + list(f.edges)}) + gl,
                           plane_co=(0, 0, GZ0 + t * G_LT), plane_no=(0, 0, 1))
for v in pb.verts:
    d = min(max(min(v.co.z - za, zb - v.co.z), 0.0), DIP)
    if d <= 0 or v.co.y < P_FY - 0.02: continue
    if abs(v.co.x) > GW + G_CH + 0.01: v.co.x += math.copysign(d * KS, v.co.x)
    v.co.y -= d
# base: split its edges at the floor's facet lines, then drop it onto the floor
def is_base(v): return abs(v.co.y - Y0) < 1e-5


for c in [0.0] + [s * FT[1] for s in (-1, 1)]:   # end slopes in strips along the plinth top's facets, so each twists evenly
    pb.normal_update()
    ends = [f for f in pb.faces if abs(f.normal.z) > 0.3 and not P_FZ[0] < f.calc_center_median().z < P_FZ[1]]
    bmesh.ops.bisect_plane(pb, geom=list({x for f in ends for x in list(f.verts) + list(f.edges)}) + ends,
                           plane_co=(c, 0, 0), plane_no=(1, 0, 0))
for c in [0.0] + [s * FT[k] for s in (-1, 1) for k in range(1, 4)]:
    for e in [e for e in pb.edges if is_base(e.verts[0]) and is_base(e.verts[1])]:
        v0, v1 = e.verts
        if (v0.co.x - c) * (v1.co.x - c) < 0 and min(abs(v0.co.x - c), abs(v1.co.x - c)) > 1e-5:
            ne, nv = bmesh.utils.edge_split(e, v0, (c - v0.co.x) / (v1.co.x - v0.co.x)); nv.co.x = c; nv.co.y = Y0
base = [v for v in pb.verts if is_base(v)]
for v in base: v.co.y = top_y(v.co.x)
bmesh.ops.remove_doubles(pb, verts=pb.verts[:], dist=1e-5)
pb.normal_update()


def foot(co):
    """The plinth's foot under a point on its top: along its facet's normal to the bay floor, radially on a facet
    line (the mitre), as surf() offsets the plates."""
    a = math.degrees(math.atan2(abs(co.x), co.y)); k = round(a / SEG)
    if abs(a - k * SEG) < 1e-4: return Vector((co.x * RF / RT, co.y * RF / RT, co.z))
    am = math.radians((math.floor(a / SEG) + 0.5) * SEG)
    return co - Vector((math.copysign(math.sin(am), co.x), math.cos(am), 0)) * (SH_FRONT - SH_BACK)


ft = {}
for e in [e for e in pb.edges if e.is_boundary and all(v.is_valid and v in base for v in e.verts)]:
    v1, v2 = e.verts; lf = e.link_faces[0]
    for v in (v1, v2):
        if v not in ft: ft[v] = pb.verts.new(foot(v.co))
    mid = (v1.co + v2.co) / 2; am = math.atan2(abs(mid.x), mid.y)
    w_ = Vector((math.copysign(math.sin(am), mid.x), math.cos(am), 0))
    pf = face([v1, v2, ft[v2], ft[v1]], lf.normal - w_ * lf.normal.dot(w_), C, pb)
    pf[soft] = 2 if lf[soft] else 0
pb.normal_update()
print('plinth faces', len(ft))


def bent(f):
    c = f.calc_center_median(); n_ = f.normal
    return any(abs((v.co - c).dot(n_)) > 2e-5 for v in f.verts)


bmesh.ops.triangulate(pb, faces=[f for f in pb.faces if len(f.verts) > 3 and bent(f)], quad_method='BEAUTY', ngon_method='BEAUTY')
pm = {v: bm.verts.new(v.co) for v in pb.verts}
soft_kind = {}; sur_faces = []      # sur_faces: the surround's faces, the hosts for its decals (step 6e)
for f in pb.faces:
    nf = bm.faces.new([pm[v] for v in f.verts]); nf.material_index = f.material_index; sur_faces.append(nf)
    if f[soft]: soft_kind[nf] = f[soft]
    if f.material_index == EM:
        tile = math.floor((f.calc_center_median().z - GZ0) / G_LT)
        for l in nf.loops:
            c = l.vert.co; l[uv].uv = (G_U0 + G_UPM * (c.x + GW),0.5 + G_VPM * (c.z - GZ0 - tile * G_LT))
pb.free()


# ---- 4. side plates and modules: built flat (y = offset), cut at the facet lines, wrapped onto the wall ----
def area2(pts): return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))) / 2


def fillet(pts, idxs, r, nseg):
    out = []; Np = len(pts)
    for i, p in enumerate(pts):
        if i not in idxs: out.append(p); continue
        a = Vector(pts[i - 1]); b = Vector(p); c = Vector(pts[(i + 1) % Np])
        u = (a - b).normalized(); w = (c - b).normalized()
        th = math.acos(max(-1.0, min(1.0, u.dot(w))))
        t = r / math.tan(th / 2); p1 = b + u * t; p2 = b + w * t
        ctr = b + (u + w).normalized() * (r / math.sin(th / 2))
        a1 = math.atan2(p1.y - ctr.y, p1.x - ctr.x); a2 = math.atan2(p2.y - ctr.y, p2.x - ctr.x)
        d = a2 - a1
        while d > math.pi: d -= 2 * math.pi
        while d < -math.pi: d += 2 * math.pi
        for k in range(nseg + 1):
            aa = a1 + d * k / nseg; out.append((ctr.x + r * math.cos(aa), ctr.y + r * math.sin(aa)))
    return out


tb = bmesh.new()


def flat_prism(outline):
    if area2(outline) < 0: outline = outline[::-1]
    F = [tb.verts.new((x, SH_FRONT, z)) for x, z in outline]
    Bk = [tb.verts.new((x, SH_BACK, z)) for x, z in outline]
    fr = face(F, (0, 1, 0), C, tb); edges = []
    for k in range(len(F)):
        m = (k + 1) % len(F); x1, z1 = outline[k]; x2, z2 = outline[m]
        face([F[k], F[m], Bk[m], Bk[k]], (z2 - z1, 0, -(x2 - x1)), C, tb)
        edges.append(tb.edges.get((F[k], F[m])))
    return fr, edges


for s in (1, -1):
    xc = s * (XI + XO) / 2
    for z0, z1 in MOD:
        fr, edges = flat_prism(rrect(xc, (z0 + z1) / 2, (XO - XI) / 2, (z1 - z0) / 2, MOD_R, 4))
        bmesh.ops.bevel(tb, geom=edges, offset=SH_BEV, offset_type='OFFSET', segments=2, profile=0.5, affect='EDGES', clamp_overlap=True, material=C)
    # the plate between them: full width like the modules (owner, 2026-11-08: "make them full width with the corner
    # plates"; it had a waisted I outline, 0.06 / 0.05 m set in with 45 degree steps)
    z0, z1 = PL_Z
    fr, edges = flat_prism(rrect(xc, (z0 + z1) / 2, (XO - XI) / 2, (z1 - z0) / 2, MOD_R, 4))
    bmesh.ops.bevel(tb, geom=edges, offset=SH_BEV, offset_type='OFFSET', segments=2, profile=0.5, affect='EDGES', clamp_overlap=True, material=C)
for f in [f for f in tb.faces if f.normal.y > 0.999 and len(f.verts) > 4]:
    bmesh.ops.triangulate(tb, faces=[f], quad_method='BEAUTY', ngon_method='EAR_CLIP')
for s in (1, -1):
    for k in range(1, 16):
        if XI - 0.01 < XB[k] < XO + 0.01:
            g = tb.verts[:] + tb.edges[:] + tb.faces[:]
            bmesh.ops.bisect_plane(tb, geom=g, plane_co=(s * XB[k], 0, 0), plane_no=(1, 0, 0))
bmesh.ops.remove_doubles(tb, verts=tb.verts[:], dist=1e-5)   # a cut landing on a fillet point leaves a sliver
vmap = {v: bm.verts.new(surf(v.co.x, v.co.z, v.co.y)) for v in tb.verts}
plate_front = []   # their front faces, for the custom normals after step 7
for f in tb.faces:
    nf = bm.faces.new([vmap[v] for v in f.verts]); nf.material_index = C
    if all(abs(v.co.y - SH_FRONT) < 1e-6 for v in f.verts): plate_front.append(nf)
tb.free()

# ---- 5. side slot decals: upper and its mirror, each side ----
def wallpt(s, thd, z, off):
    k = math.floor(thd / SEG + 1e-9); t = thd / SEG - k
    if t < 1e-6 or t > 1 - 1e-6:
        a = math.radians(round(thd / SEG) * SEG); rr = R + off / math.cos(HALF)
        return Vector((s * rr * math.sin(a), rr * math.cos(a), z))
    a0 = math.radians(k * SEG); a1 = math.radians((k + 1) * SEG); am = (a0 + a1) / 2
    p = Vector((s * R * math.sin(a0), R * math.cos(a0), z)).lerp(Vector((s * R * math.sin(a1), R * math.cos(a1), z)), t)
    return p + Vector((s * math.sin(am), math.cos(am), 0)) * off


def clip(poly, t0, t1):
    for lo_, sgn in ((t0, 1), (t1, -1)):
        out = []
        for k in range(len(poly)):
            p, q = poly[k], poly[(k + 1) % len(poly)]
            ip, iq = sgn * (p[0] - lo_) >= -1e-9, sgn * (q[0] - lo_) >= -1e-9
            if ip: out.append(p)
            if ip != iq:
                t = (lo_ - p[0]) / (q[0] - p[0]); out.append((lo_, p[1] + t * (q[1] - p[1])))
        poly = out
    return poly




def slot(s, ac, zc, d):
    """One slot decal at 45 degrees, centre (arc ac, z zc), long axis d, cut at the facet edges so each piece lies
    flat. UVs: the piece's long axis along V; across runs with the left normal on the +x side and against it on
    the -x side, so (U, V, normal) stays right-handed on both."""
    d = (d[0] / math.sqrt(2), d[1] / math.sqrt(2)); n = (-d[1], d[0]); hl, hw = HO_L / 2, HO_W / 2
    quad = [(ac + d[0] * a_ + n[0] * c_, zc + d[1] * a_ + n[1] * c_) for a_, c_ in ((-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw))]
    poly = [(math.degrees(a / R), z) for a, z in quad]
    if area2(poly) < 0: poly = poly[::-1]
    vd = {}; fs = []; lo, hi = min(p[0] for p in poly), max(p[0] for p in poly)
    for m in range(int(lo // SEG), int(hi // SEG) + 1):
        piece = clip(poly, max(lo, m * SEG), min(hi, (m + 1) * SEG))
        if len(piece) < 3 or abs(area2(piece)) < 1e-9: continue
        vs = []; pos = {}
        for p in piece:
            key = (round(p[0], 6), round(p[1], 6))
            if key not in vd: vd[key] = bm.verts.new(wallpt(s, p[0], p[1], HO_OFF))
            if vd[key] not in pos: vs.append(vd[key]); pos[vd[key]] = p
        if len(vs) < 3: continue
        am = math.radians((m + 0.5) * SEG)
        f = face(vs, (s * math.sin(am), math.cos(am), 0), HO); f.smooth = True
        for l in f.loops:
            p = pos[l.vert]; ra, rz = math.radians(p[0]) * R - ac, p[1] - zc
            along, across = ra * d[0] + rz * d[1], (ra * n[0] + rz * n[1]) * s
            l[uv].uv = (HO_BOX[0] + (0.5 + across / HO_W) * (HO_BOX[2] - HO_BOX[0]),
                        HO_BOX[1] + (0.5 + along / HO_L) * (HO_BOX[3] - HO_BOX[1]))
        fs.append(f)
    return fs


slot_faces = []
for s in (1, -1):
    slot_faces += slot(s, R * math.radians(ST_C[0]), ST_C[1], (1, 1))              # upper, rising away from the bay
    slot_faces += slot(s, R * math.radians(ST_C[0]), 2 * ZMID - ST_C[1], (1, -1))  # lower, its mirror


# ---- 5b. panel seam decals (Atlas4 piece 3), worked on the unrolled wall in (arc length, z) ----
def band(P, w, half=0):
    """Mitred band round the centre polyline P: per segment its quad, start point, direction, left normal (the V1
    side) and the length along the line at its start. half +1 keeps only the left half (V mid to V1), -1 the right."""
    D_ = []; N_ = []
    for i in range(len(P) - 1):
        da, dz = P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]; L = math.hypot(da, dz)
        D_.append((da / L, dz / L)); N_.append((-dz / L, da / L))
    side = []
    for j in range(len(P)):
        if j in (0, len(P) - 1):
            m = N_[min(j, len(N_) - 1)]; h = w / 2
        else:
            m = (N_[j - 1][0] + N_[j][0], N_[j - 1][1] + N_[j][1]); l = math.hypot(*m); m = (m[0] / l, m[1] / l)
            h = w / 2 / (m[0] * N_[j][0] + m[1] * N_[j][1])
        side.append(((P[j][0] + m[0] * h, P[j][1] + m[1] * h), (P[j][0] - m[0] * h, P[j][1] - m[1] * h)))
    out = []; U = 0
    for i in range(len(P) - 1):
        lo_, hi_ = (side[i][1], side[i + 1][1]) if half <= 0 else (P[i], P[i + 1])
        up_, dn_ = (side[i + 1][0], side[i][0]) if half >= 0 else (P[i + 1], P[i])
        out.append(([lo_, hi_, up_, dn_], P[i], D_[i], N_[i], U))
        U += math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1])
    return out, U


def emit(s, segs, total, off, vd, us=SM_US):
    """Seam faces cut at the facet edges, so each lies flat on its facet. On the -x side U runs the other way
    (total - u), so U, V and the normal keep one handedness all round; us is U per metre."""
    fs = []
    for quad, P0, d, nn, U0 in segs:
        poly = [(math.degrees(a / R), z) for a, z in quad]
        if area2(poly) < 0: poly = poly[::-1]
        lo, hi = min(p[0] for p in poly), max(p[0] for p in poly)
        for m in range(int(lo // SEG), int(hi // SEG) + 1):
            piece = clip(poly, max(lo, m * SEG), min(hi, (m + 1) * SEG))
            if len(piece) < 3 or abs(area2(piece)) * R * math.pi / 180 < 1e-6: continue    # under 1 sq mm: a facet edge just past a step corner
            vs = []; pos = {}
            for p in piece:
                key = (round(p[0], 6), round(p[1], 6))
                if key not in vd: vd[key] = bm.verts.new(wallpt(s, p[0], p[1], off))
                if vd[key] not in pos: vs.append(vd[key]); pos[vd[key]] = p
            if len(vs) < 3: continue
            am = math.radians((m + 0.5) * SEG)
            f = face(vs, (s * math.sin(am), math.cos(am), 0), SM); f.smooth = True
            for l in f.loops:
                p = pos[l.vert]; ra, rz = math.radians(p[0]) * R - P0[0], p[1] - P0[1]
                u = U0 + ra * d[0] + rz * d[1]; u = u if s > 0 else total - u
                l[uv].uv = (u * us, (SM_V[0] + SM_V[1]) / 2 + (ra * nn[0] + rz * nn[1]) / SM_W * (SM_V[1] - SM_V[0]))
            fs.append(f)
    return fs


A_BAY, A_BACK, A_END = (R * math.radians(t) for t in (BAY_K * SEG, TH_BACK, 180))
def ring_pts(j, a0):
    """Ring j's centre line from arc a0 to the back centre, stepping up SM_STEP over the side panel's middle."""
    ze, di, H = SM_Z[j], SM_IN[j], SM_STEP
    return [(a0, ze), (A_BAY + di, ze), (A_BAY + di + H, ze + H), (A_BACK - di - H, ze + H), (A_BACK - di, ze), (A_END, ze)]


# Each ring splits at the bay's corners (owner, 2026-11-08: "half of it followed the perimeter of the cutout"): its
# outer half runs on across the bay's bottom (top) edge, its inner half turns along the bay's side edge into the
# other ring, so a half seam outlines the bay and the rings are whole from its corners to the back. Three half bands
# a side: the bottom ring's V1 stays up; the top ring is the mirror, V1 down, so the side half runs on unbroken with
# V1 away from the bay. U per metre is trimmed so each band's U matches where the two sides meet
seam_faces = []
for s in (1, -1):
    vd = {}
    for P, hf in ((ring_pts(0, 0.0), -1),                                # bay's bottom edge, then the bottom ring's lower half
                  (ring_pts(1, 0.0)[::-1], -1),                          # the top ring's upper half, then the bay's top edge
                  (ring_pts(1, A_BAY)[::-1] + ring_pts(0, A_BAY), 1)):   # top ring's lower half, down the bay's side, bottom ring's upper half
        segs, L = band(P, SM_W, hf)
        seam_faces += emit(s, segs, 2 * L, SM_OFF, vd, round(2 * L * SM_US) / (2 * L))
for s in (1, -1):
    vd = {}                           # back seams, drawn after the rings: top to bottom, V1 towards the back
    zt, zb, h = SM_Z[1], SM_Z[0], SM_W / 2
    segs, L = band([(A_BACK, zt - h), (A_BACK, zb + h)], SM_W)
    tip = [([(A_BACK - h, zt - h), (A_BACK + h, zt - h), (A_BACK, zt)], (A_BACK, zt - h), (0, -1), (1, 0), 0),
           ([(A_BACK + h, zb + h), (A_BACK - h, zb + h), (A_BACK, zb)], (A_BACK, zb + h), (0, -1), (1, 0), L)]
    seam_faces += emit(s, segs + tip, L, SM_STEM_OFF, vd)
sv = list({v for f in seam_faces for v in f.verts})
bmesh.ops.remove_doubles(bm, verts=sv, dist=1e-6)   # the two ring halves meet at the back centre
seam_faces = [f for f in seam_faces if f.is_valid]

# ---- 5c. top: lip, deck, raised ring, hub ----
# Lip with a rounded outer edge, 2 cm above a flat dark deck. On the deck one full chrome ring, as tall and bevelled as
# the side plates (owner, 2026-11-08: the four quarter plates "just be 1 full ring ... It should mimic the shiny metal
# plates on the front next to the beam surround in height, and bevel"), with the dome and the antenna standing on it
# (owner: "Stand on the ring"); a painted hub ring and a domed lens in the middle. The dome and the antenna sit on the
# left-right axis (DOME_C, ANT_C); the antenna has a round base the dome's size, a painted sleeve, a black rubber whip
# (owner, 2026-11-07: A of art/whip-options.png) and a red cap. Heights below are as on the full-height canister (wall
# top loop 4.45, lip 4.62); TS moves them down by the height cut
TS = -H_CUT
TOP_CUT = Z_WALL + 0.005              # faces above this are rebuilt; the wall's top loop is at Z_WALL
T_PLATE = 4.60 + TS                   # the deck's level: 2 cm below the lip
DOME_SRC = Vector((-0.48, -0.30))     # where the base mesh has the dome
# the dome and the antenna on the left-right axis, the antenna on +x, the left seen from the front (owner, 2026-11-08:
# "the antenna on the canister's left and the dome on the right rather than how they are rotated around at an angle")
DOME_C, ANT_C = Vector((-0.61, 0.0)), Vector((0.61, 0.0))
T_BASE_R = 0.165                      # the dome's base radius (the antenna's base matches it): r 0.445 to 0.775
# the ring: the plates' height and bevel (SH_FRONT, SH_BEV in 2 segments, every edge sharp as the object's 35 degree
# Smooth by Angle leaves them); its flat top, r 0.433 to 0.787, holds both bases and the open halves of their foot
# seams, T_FOOT_W wide so they fit (the deck's are SM_W). 45 mm of dark deck each side of it, out to the lip's foot
# (r 0.84) and in to the hub (r 0.38), each with a half seam on both its feet (owner, 2026-11-08: the inner ring "needs
# to have the same black metal gap from the shiny metal ring to the outside"; layout C of art/hub-gap-options.png)
T_RING_R, T_RING_H, T_RING_BEV, T_FOOT_W = (0.425, 0.795), SH_FRONT, SH_BEV, 0.015
# ring top decals, Atlas3_Chrome so they follow the chrome, 1.5 mm up, long side radial, the art's top towards the
# axis: C32 of art/latch-sheet-4.png at the front and the back, and the side panels' slot vent (piece 20) at the four
# 45-degree angles (owner, 2026-11-08: "do C32 front and back, then a slot vent at the 4 45 degree angles")
T_DEC_R = 0.61                                                       # centred across the ring's flat top
# C32: angles, box (236 x 368 px), width, length; as long as the flat top allows, 12 mm in from its inner edge and its
# outer corners 5 mm in (owner, 2026-11-08: "The C32 decals should be larger"; they were 0.16 x 0.25)
T_LATCH = ((0, 180), (0.5049, 0.2534, 0.6201, 0.4331), 0.33 * 236 / 368, 0.33)
T_VENT = ((45, 135, 225, 315), HO_BOX, 0.056, 0.25)                 # 110 x 491 px
T_HUB_UPM = 0.40                       # the painted hub's texture scale, Keen's for PaintedMetal (UV per metre)
# seam lines, Atlas4 piece 3 at the barrel's UV scale, each centred on the foot it marks with only its open half laid
# (owner, 2026-11-07: ring 1 "centered on the interface between the dark grey and the outer rim border"; "the same
# seam border treatment around the dome and antenna foot"): ring 1 on the lip's foot and a ring on the raised ring's
# outer foot, on the deck in Atlas4_VeryDark; round the dome's and the antenna's feet on the ring in Atlas4_Chrome.
# V1 towards the raised part
# the dark deck is BlackMetal (owner, 2026-11-08: "I want the very dark metal on the top to be darker, I guess metal
# black"; it was PaintedMetal_VeryDark); its lines stay Atlas4_VeryDark, the darkest Atlas4 sheet
T_VD, T_LVD = 'BlackMetal', 'Atlas4_VeryDark'                        # the dark deck and the lines on it
T_BASE_MAT = 'PaintedMetal_VeryDark'   # the dome's and the antenna's round bases (owner, 2026-11-08: "very dark metal"; were chrome)
T_HUB_BEV = 0.02                       # 45-degree bevel on the bore step's inner edge (owner, 2026-11-08: "a bevel on the inside")
T_ANT = [(r, z + TS) for r, z in ((0.165, 4.60), (0.165, 4.65), (0.14, 4.66), (0.055, 4.66), (0.055, 4.71), (0.05, 4.715),
         (0.032, 4.715), (0.032, 5.40), (0.022, 5.41), (0.022, 7.38))]   # antenna base, boss, sleeve, whip (on the deck; raised T_RING_H)
T_CAP = [(r, z + TS) for r, z in ((0.022, 7.38), (0.036, 7.38), (0.036, 7.614), (0.031, 7.632), (0.018, 7.645), (0.0, 7.65))]


def t_lip_profile():
    # lip: a 45 degree bevel 0.10 m across and 0.10 m high on its outer edge, measured on concept 2 (owner,
    # 2026-11-07: "isn't the top of the canister supposed to have a big beveled edge?"), with 4 cm rounds where it
    # meets the wall and the top so it shades as one soft shoulder; flat to r 0.85, 1 cm round down to the deck
    rho, t = 0.04, 0.04 * math.tan(math.radians(22.5))       # fillet radius; its tangent distance from each corner
    P = [(1.12, 4.45, None), (1.12, 4.52 - t, PC)]
    P += [(1.12 - rho + rho * math.cos(math.radians(a)), 4.52 - t + rho * math.sin(math.radians(a)), PC) for a in (15, 30, 45)]
    P += [(1.02 - t + rho * math.cos(math.radians(a)), 4.62 - rho + rho * math.sin(math.radians(a)), PC) for a in (45, 60, 75, 90)]
    P += [(0.85, 4.62, PC)]
    P += [(0.85 + 0.01 * math.cos(math.radians(a)), 4.61 + 0.01 * math.sin(math.radians(a)), PC) for a in (120, 150, 180)]
    P += [(0.84, 4.60, PC)]
    return [(r, z + TS, m) for r, z, m in P]


def t_ring_profile():
    """From the lip's foot over the deck, up the ring's outer wall, over its bevels and top, down its inner wall and
    over the deck to the hub's foot (true heights). The deck strips are T_VD, the ring chrome."""
    (ri, ro), b, top = T_RING_R, T_RING_BEV, T_PLATE + T_RING_H
    c = b * math.cos(math.radians(45))                                    # the bevel's middle point, as bmesh's profile 0.5
    return [(0.84, T_PLATE, None), (ro, T_PLATE, MI[T_VD]), (ro, top - b, C), (ro - b + c, top - b + c, C), (ro - b, top, C),
            (ri + b, top, C), (ri + b - c, top - b + c, C), (ri, top - b, C), (ri, T_PLATE, C), (0.38, T_PLATE, MI[T_VD])]


def t_hub_profile():
    # from the deck: the hub ring flush with the lip with a 2.5 cm bezel on its inner edge, in the block's paint (owner,
    # 2026-11-08: "The inner ring should be paint matched"), then the chrome bore step (its inner edge bevelled
    # T_HUB_BEV at 45 degrees) and a domed lens
    P = [(0.38, 4.60, None), (0.38, 4.616, PC), (0.376, 4.62, PC), (0.305, 4.62, PC), (0.28, 4.595, PC),
         (0.28, 4.53, PC), (0.17 + T_HUB_BEV, 4.53, C), (0.17, 4.53 - T_HUB_BEV, C), (0.17, 4.495, C), (0.13, 4.5077, CL), (0.085, 4.5177, CL),
         (0.04, 4.5234, CL), (0.0, 4.525, CL)]
    return [(r, z + TS, m) for r, z, m in P]


def t_lathe(cxy, prof, angs, ring0=None, sign=1):
    """Revolve prof [(r, z, mat)] round cxy at the plan angles angs (radians from +y toward +x); ring0 replaces the
    first ring. The faces face out for a profile that climbs and turns in (sign -1 for one that drops and turns in).
    Returns [(face, segment index, angle index)] and {vert: (ring index, angle index)}."""
    rings = [ring0] if ring0 is not None else []
    for r, z, _ in prof[len(rings):]:
        rings.append(bm.verts.new((cxy.x, cxy.y, z)) if r < 1e-6 else
                     [bm.verts.new((cxy.x + r * math.sin(a), cxy.y + r * math.cos(a), z)) for a in angs])
    vmap = {}
    for j, rg in enumerate(rings):
        if isinstance(rg, list):
            for k, v in enumerate(rg): vmap[v] = (j, k)
    out = []; n = len(angs)
    for j in range(len(prof) - 1):
        (r0, z0, _), (r1, z1, m) = prof[j], prof[j + 1]
        A, B = rings[j], rings[j + 1]
        for k in range(n):
            k1 = (k + 1) % n
            rad = (Vector((math.sin(angs[k]), math.cos(angs[k]), 0)) + Vector((math.sin(angs[k1]), math.cos(angs[k1]), 0))).normalized()
            want = sign * (rad * (z1 - z0) + Vector((0, 0, -(r1 - r0))))
            if isinstance(A, list) and isinstance(B, list): vs = [A[k], A[k1], B[k1], B[k]]
            elif isinstance(B, list): vs = [A, B[k1], B[k]]
            else: vs = [A[k], A[k1], B]
            out.append((face(vs, want, m), j, k))
    return out, vmap


def t_pol(a, r): return Vector((r * math.sin(math.radians(a)), r * math.cos(math.radians(a))))


def t_band(P, w, closed=False):
    """band() for the deck in plan; closed mitres the last point to the first too."""
    if not closed: return band([(p.x, p.y) for p in P], w)
    n = len(P); D_, N_, L_ = [], [], []
    for i in range(n):
        d = P[(i + 1) % n] - P[i]; L = d.length; D_.append((d.x / L, d.y / L)); N_.append((-d.y / L, d.x / L)); L_.append(L)
    side = []
    for j in range(n):
        m = Vector((N_[j - 1][0] + N_[j][0], N_[j - 1][1] + N_[j][1])).normalized(); h = w / 2 / (m.x * N_[j][0] + m.y * N_[j][1])
        side.append(((P[j].x + m.x * h, P[j].y + m.y * h), (P[j].x - m.x * h, P[j].y - m.y * h)))
    out = []; U = 0
    for i in range(n):
        j = (i + 1) % n; out.append(([side[i][1], side[j][1], side[j][0], side[i][0]], (P[i].x, P[i].y), D_[i], N_[i], U)); U += L_[i]
    return out, U


def t_emit(segs, off, mat, z0=None, w=SM_W):
    """Flat seam faces w wide on the deck (or at height z0), off above it; U along the line, V across Atlas4 piece 3,
    V1 on the left."""
    fs = []; vd = {}; z = (T_PLATE if z0 is None else z0) + off
    for quad, P0, d, nn, U0 in segs:
        vs = []
        for p in quad:
            key = (round(p[0], 6), round(p[1], 6))
            if key not in vd: vd[key] = bm.verts.new((p[0], p[1], z))
            if vd[key] not in vs: vs.append(vd[key])
        if len(vs) < 3: continue
        f = face(vs, (0, 0, 1), mat)
        for l in f.loops:
            ra, rb = l.vert.co.x - P0[0], l.vert.co.y - P0[1]
            l[uv].uv = ((U0 + ra * d[0] + rb * d[1]) * SM_US, (SM_V[0] + SM_V[1]) / 2 + (ra * nn[0] + rb * nn[1]) / w * (SM_V[1] - SM_V[0]))
        fs.append(f)
    return fs


def t_foot_seam(P, w=SM_W):
    """The open half of a seam w wide round the closed foot P of a raised part, the part on P's left (V1 towards it):
    centre line on the foot, the half on the right."""
    n = len(P); out = []
    for k, (quad, P0, d, nn, U0) in enumerate(t_band(P, w, closed=True)[0]):
        j = (k + 1) % n
        out.append(([quad[0], quad[1], (P[j].x, P[j].y), (P[k].x, P[k].y)], P0, d, nn, U0))
    return out


def t_seams(lip_foot, ring_foot, parts):
    """lip_foot: the lip's foot, clockwise (the lip on its left); ring_foot: the raised ring's outer foot,
    counter-clockwise (the ring on its left); parts: the dome's and the antenna's feet on the ring, counter-clockwise
    round their centres."""
    fs = t_emit(t_foot_seam(lip_foot), SM_OFF, MI[T_LVD])                  # ring 1, on the lip's 64 points
    fs += t_emit(t_foot_seam(ring_foot), SM_OFF, MI[T_LVD])
    for P in parts:                                                         # on the parts' own 24 points
        fs += t_emit(t_foot_seam(P, T_FOOT_W), SM_OFF, MI['Atlas4_Chrome'], T_PLATE + T_RING_H, T_FOOT_W)
    return fs


def build_top():
    # keep the dome (hemisphere and base ring); remove everything else above the wall's top loop
    dome = [f for f in bm.faces if all((v.co.xy - DOME_SRC).length < T_BASE_R + 1e-3 and v.co.z > T_PLATE - 0.001 for v in f.verts)]
    ds = set(dome)
    loop = sorted((v for v in bm.verts if abs(v.co.z - Z_WALL) < 1e-4 and abs(v.co.xy.length - R) < 2e-3), key=lambda v: ang(v.co))
    assert len(loop) == 64, len(loop)
    # the paint band below carries its UVs on: u per facet from its top verts, v at its rate up the profile
    band_uv = {}; rate = None
    for k in range(64):
        a, b = loop[k], loop[(k + 1) % 64]
        fb = next(f for f in a.link_faces if b in f.verts and f.calc_center_median().z < Z_WALL)
        band_uv[k] = (next(l[uv].uv.copy() for l in fb.loops if l.vert is a), next(l[uv].uv.copy() for l in fb.loops if l.vert is b))
        if rate is None:
            zs = sorted((l.vert.co.z, l[uv].uv.y) for l in fb.loops); rate = (zs[-1][1] - zs[0][1]) / (zs[-1][0] - zs[0][0])
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z > TOP_CUT and f not in ds], context='FACES')
    angs = [ang(v.co) for v in loop]                                        # clockwise from +y, seen from above
    def ring_of(m, jj): return [v for v, (j, k) in sorted(m.items(), key=lambda it: it[1][1]) if j == jj]
    prof = t_lip_profile(); rprof = t_ring_profile()
    lip, vmap = t_lathe(Vector((0, 0)), prof, angs, ring0=loop)
    ring, rmap = t_lathe(Vector((0, 0)), rprof, angs, ring0=ring_of(vmap, len(prof) - 1))
    hub, hmap = t_lathe(Vector((0, 0)), t_hub_profile(), angs, ring0=ring_of(rmap, len(rprof) - 1))
    s = [0.0]
    for j in range(1, len(prof)): s.append(s[-1] + math.hypot(prof[j][0] - prof[j - 1][0], prof[j][1] - prof[j - 1][1]))
    hp = t_hub_profile(); sh = [0.0]
    for j in range(1, len(hp)): sh.append(sh[-1] + math.hypot(hp[j][0] - hp[j - 1][0], hp[j][1] - hp[j - 1][1]))
    chrome, lens = [], []
    lathed = lip + ring + hub; hub_set = {f for f, _, _ in hub}
    for f, j, k in lathed:
        if f in hub_set and f.material_index == PC:
            # the painted hub: one texture width round (0.42 to 0.57 UV per metre at r 0.38 to 0.28), so it meets
            # itself, and Keen's scale up the profile
            for l in f.loops:
                jj, kk = hmap[l.vert]
                l[uv].uv = ((k if kk == k else k + 1) / len(angs), T_HUB_UPM * sh[jj])
        elif f.material_index in (PC, D):
            for l in f.loops:
                jj, kk = vmap[l.vert]
                u = band_uv[k][0].x if kk == k else band_uv[k][1].x
                l[uv].uv = (u, band_uv[k][0].y + rate * s[jj])
        elif f.material_index == CL: lens.append(f)
        else: chrome.append(f)
    # dome: moved from DOME_SRC to DOME_C; its base ring reaches down to the deck and the whole dome stands T_RING_H up
    # on the ring, T_BASE_MAT like the antenna's matching base
    mv = DOME_C - DOME_SRC
    for v in {v for f in dome for v in f.verts}:
        if v.co.z < T_PLATE + 0.0005: v.co.z = T_PLATE
        v.co.z += T_RING_H; v.co.x += mv.x; v.co.y += mv.y
    for f in dome:
        if f.material_index == D: f.material_index = MI[T_BASE_MAT]; chrome.append(f)
    # antenna: base (its wall, chamfer and top, profile points 1 to 3) in T_BASE_MAT; boss, sleeve and shoulder in the
    # block's paint (owner, 2026-11-08: "Make the shiny metal segment of the antenna be paint colored"); red cap
    a24 = [2 * math.pi * i / 24 for i in range(24)]
    ant, _ = t_lathe(ANT_C, [(r, z + T_RING_H, MI['Rubber'] if k == len(T_ANT) - 1 else (MI[T_BASE_MAT] if k in (1, 2, 3) else PC))
                             for k, (r, z) in enumerate(T_ANT)], a24)
    cap, _ = t_lathe(ANT_C, [(r, z + T_RING_H, RED) for r, z in T_CAP], a24)
    def ccw(c, P): return sorted(P, key=lambda p: math.atan2(p.y - c.y, p.x - c.x))
    zr = T_PLATE + T_RING_H
    dome_foot = ccw(DOME_C, [v.co.xy.copy() for v in {v for f in dome for v in f.verts}
                             if abs(v.co.z - zr) < 1e-5 and abs((v.co.xy - DOME_C).length - T_BASE_R) < 1e-3])
    ant_foot = ccw(ANT_C, [ANT_C + T_ANT[0][0] * Vector((math.sin(a), math.cos(a))) for a in a24])
    assert len(dome_foot) == len(ant_foot) == 24, (len(dome_foot), len(ant_foot))
    seams = t_seams([v.co.xy.copy() for v in ring_of(vmap, len(prof) - 1)],
                    [v.co.xy.copy() for v in ring_of(rmap, 1)][::-1], (dome_foot, ant_foot))
    # the bore step's half seam (owner, 2026-11-08: "a half very dark seam around the outer edge where it intersects
    # with the 3D edge extruding out of it"): centre line on the hub wall's foot, only the half on the step laid, like
    # ring 1 on the lip's foot; the ring runs clockwise, the wall on its left
    hz = 4.53 + TS
    hj = next(j for j, (r, z, _) in enumerate(hp) if abs(r - 0.28) < 1e-6 and abs(z - hz) < 1e-6)
    hub_seam = t_emit(t_foot_seam([v.co.xy.copy() for v in ring_of(hmap, hj)]), SM_OFF, MI[T_LVD], z0=hz)
    seams += hub_seam
    print('bore step half seam faces', len(hub_seam))
    # the inner gap's half seams, as the outer gap's: on the ring's inner foot (clockwise, the ring on its left) and on
    # the hub's foot (counter-clockwise, the hub on its left)
    gap_seam = t_emit(t_foot_seam([v.co.xy.copy() for v in ring_of(rmap, len(rprof) - 2)]), SM_OFF, MI[T_LVD])
    gap_seam += t_emit(t_foot_seam([v.co.xy.copy() for v in ring_of(rmap, len(rprof) - 1)][::-1]), SM_OFF, MI[T_LVD])
    seams += gap_seam
    # the ring top's latches and vents (T_LATCH, T_VENT): U against the clockwise tangent, V towards the axis, so
    # U x V is up and the art is not mirrored
    zt = T_PLATE + T_RING_H + SM_OFF; ring_dec = []
    for angs_, box, w, L in (T_LATCH, T_VENT):
        for a in angs_:
            rd = t_pol(a, 1.0); td = Vector((rd.y, -rd.x)); c = rd * T_DEC_R
            vs, loc = [], {}
            for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = c - td * (i * w / 2) - rd * (j * L / 2)
                v_ = bm.verts.new((p.x, p.y, zt)); vs.append(v_); loc[v_] = (i, j)
            f = face(vs, (0, 0, 1), MI['Atlas3_Chrome'])
            for l in f.loops:
                i, j = loc[l.vert]
                l[uv].uv = (box[0] + (i + 1) / 2 * (box[2] - box[0]), box[1] + (j + 1) / 2 * (box[3] - box[1]))
            ring_dec.append(f)
    seams += ring_dec
    print('inner gap half seam faces', len(gap_seam), 'ring top decals', len(ring_dec))
    chrome += [f for f, _, _ in ant]
    bm.normal_update()
    boxuv(chrome + [f for f, _, _ in cap], 0.45)
    for f in lens:
        for l in f.loops: l[uv].uv = (0.5 + l.vert.co.x / 0.34, 0.5 + l.vert.co.y / 0.34)
    new = [f for f, _, _ in lathed] + dome + [f for f, _, _ in ant] + [f for f, _, _ in cap] + seams
    for f in new: f.smooth = True
    for e in {e for f in new for e in f.edges}:
        lf = e.link_faces
        if len(lf) == 2 and lf[0].normal.angle(lf[1].normal, 0) > math.radians(35): e.smooth = False
    # every edge round the ring sharp, as on the plates: its bevel meets the top and the wall at 22.5 degrees, and
    # smooth there it bent the top's normals up to 12 degrees, which warps the chrome's reflection
    for e in {e for f, _, _ in ring for e in f.edges}:
        a, b = rmap.get(e.verts[0]), rmap.get(e.verts[1])
        if a and b and a[0] == b[0] and 1 <= a[0] <= len(rprof) - 2: e.smooth = False
    print('top seam faces', len(seams))
    return new


top_faces = build_top()
print('top faces', len(top_faces))

# ---- 6. normals, materials, UVs and sharp edges for the kiosk pieces ----
bm.normal_update(); nk = 0
for fs in islands(bm):
    vs = {v for f in fs for v in f.verts}
    if max(abs(v.co.x) for v in vs) < 0.75 and min(math.hypot(v.co.x, v.co.y) for v in vs) > 1.09 and min(v.co.y for v in vs) > 0.8:
        nk += 1
        for f in fs: f.smooth = True          # smooth shaded, split only at the sharp edges below (smooth pass, 2026-11-07)
        ch = [f for f in fs if f.material_index != EM]
        for f in ch: f.material_index = C
        boxuv(ch, 0.45)
        for e in {e for f in fs for e in f.edges}:
            lf = e.link_faces
            if len(lf) == 2 and soft_kind.get(lf[0]) and soft_kind.get(lf[0]) == soft_kind.get(lf[1]): continue   # rounded corners stay smooth
            # sharp where a big face meets a bevel; below 8 degrees (facet steps, floor-following twist) stays smooth
            if len(lf) == 2 and lf[0].normal.angle(lf[1].normal, 0) > math.radians(8) and max(lf[0].calc_area(), lf[1].calc_area()) > 0.001:
                e.smooth = False

# ---- 6b. bolt decals: Atlas3_Colorable piece 14, the owner's pick of art/bolt-sheet.png (2026-11-07) ----
# After step 6, whose kiosk test would catch the bay bolts. One square quad per head, turned at random.
B_BOX = (0.9399, 0.752, 0.999, 0.8105)                   # round sunken head, 121 x 120 px
B_W = 0.040; B_H = B_W * 120 / 121                        # Keen's large-grid panel heads: 40-50 mm
B_LIP_R, B_LIP_A = 0.93, [45 * k for k in range(8)]       # centred across the lip's flat top (r 0.85 to 1.00), every 45 degrees from the front (owner, 2026-11-08: "radially aligned with the front of the block")
B_BAY_A = BAY_K * SEG + math.degrees(B_W / R)             # one head out from the bay edge
B_BAY_Z = ((MOD[1][0] + MOD[1][1]) / 2, ZMID, (MOD[0][0] + MOD[0][1]) / 2)   # upper module, plate, lower module centres
rng = random.Random(14)                                   # fixed seed, so a rebuild turns each head the same way


def bolt_face(vs, want, local):
    f = face(vs, want, HO); f.smooth = True
    for l in f.loops:
        p, q = local[l.vert]
        l[uv].uv = (B_BOX[0] + (0.5 + p / B_W) * (B_BOX[2] - B_BOX[0]), B_BOX[1] + (0.5 + q / B_H) * (B_BOX[3] - B_BOX[1]))
    return f


CORNERS = ((-1, -1), (1, -1), (1, 1), (-1, 1))
bolt_faces = []
for a in B_LIP_A:                                         # lip: U x V = +z, the face normal
    c = t_pol(a, B_LIP_R); phi = rng.uniform(0, 2 * math.pi)
    U = Vector((math.cos(phi), math.sin(phi))); V = Vector((-math.sin(phi), math.cos(phi)))
    vs = [bm.verts.new((*(c + U * (i * B_W / 2) + V * (j * B_H / 2)), 4.62 + TS + HO_OFF)) for i, j in CORNERS]
    bolt_faces.append(bolt_face(vs, (0, 0, 1), {v: (i * B_W / 2, j * B_H / 2) for v, (i, j) in zip(vs, CORNERS)}))
for s in (1, -1):                                         # bay sides, in (arc, z): U runs against the arc on +x, with it on -x
    for zc in B_BAY_Z:
        phi = rng.uniform(0, 2 * math.pi); ac = R * math.radians(B_BAY_A)
        U = (-s * math.cos(phi), -s * math.sin(phi)); V = (-math.sin(phi), math.cos(phi))
        pts = [(math.degrees((ac + U[0] * i * B_W / 2 + V[0] * j * B_H / 2) / R), zc + U[1] * i * B_W / 2 + V[1] * j * B_H / 2)
               for i, j in CORNERS]
        m = int(pts[0][0] // SEG); assert all(m * SEG < p[0] < (m + 1) * SEG for p in pts), pts   # one facet, so it lies flat
        vs = [bm.verts.new(wallpt(s, p[0], p[1], HO_OFF)) for p in pts]
        am = math.radians((m + 0.5) * SEG)
        bolt_faces.append(bolt_face(vs, (s * math.sin(am), math.cos(am), 0), {v: (i * B_W / 2, j * B_H / 2) for v, (i, j) in zip(vs, CORNERS)}))


# ---- 6c. signs: the owner's pick of art/sign-sheet.png (2026-11-07: "A1 B3 C1 D1"), in concept 2's spots ----
# Sized and placed as measured on concept 2, text upright (owner, 2026-11-07: Keen's 120-150 mm plates were
# "microscopic, and dont align with the concept art"): plates 0.30 m, the triangle 0.15 m, the label 0.28 m.
def wall_quad(s, deg, zc, w, h, box, mat, off=HO_OFF, phi=0.0):
    """Decal rectangle w x h centred deg round from the front on side s at height zc, turned phi, off the wall (or
    a part that follows it) by off, cut at the facet edges so each piece lies flat. Upright at phi 0: U runs to the
    viewer's right (against the arc on +x, with it on -x), so it is unmirrored on both sides."""
    ac = R * math.radians(deg)
    U = (-s * math.cos(phi), -s * math.sin(phi)); V = (-math.sin(phi), math.cos(phi))
    poly = [(math.degrees((ac + U[0] * i * w / 2 + V[0] * j * h / 2) / R), zc + U[1] * i * w / 2 + V[1] * j * h / 2)
            for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    if area2(poly) < 0: poly = poly[::-1]
    vd = {}; fs = []; lo, hi = min(p[0] for p in poly), max(p[0] for p in poly)
    for m in range(int(lo // SEG), int(hi // SEG) + 1):
        piece = clip(poly, max(lo, m * SEG), min(hi, (m + 1) * SEG))
        if len(piece) < 3 or abs(area2(piece)) < 1e-9: continue
        vs = []; pos = {}
        for p in piece:
            key = (round(p[0], 6), round(p[1], 6))
            if key not in vd: vd[key] = bm.verts.new(wallpt(s, p[0], p[1], off))
            if vd[key] not in pos: vs.append(vd[key]); pos[vd[key]] = p
        am = math.radians((m + 0.5) * SEG)
        f = face(vs, (s * math.sin(am), math.cos(am), 0), MI[mat]); f.smooth = True
        for l in f.loops:
            p = pos[l.vert]; da, dz = R * math.radians(p[0]) - ac, p[1] - zc
            u = 0.5 + (da * U[0] + dz * U[1]) / w; v = 0.5 + (da * V[0] + dz * V[1]) / h
            l[uv].uv = (box[0] + u * (box[2] - box[0]), box[1] + v * (box[3] - box[1]))
        fs.append(f)
    return fs


def wall_sign(s, deg, zb, w, box, px, mat):
    """Upright sign w wide, its height from the piece's px ratio, bottom at zb."""
    h = w * px[1] / px[0]
    return wall_quad(s, deg, zb + h / 2, w, h, box, mat), h


S_GAP, S_PAIR = 0.025, 0.012                    # inset from a seam; gap between the plate and the triangle under it
S_ANG = 96.0                                    # concept 2: the side panel's signs about 96 degrees round on +x
S_PL, S_TRI, S_LBL = 0.30, 0.15, 0.28           # widths measured on concept 2: side plates, triangle, the label over the bay
ring_lo = SM_Z[0] + SM_STEP + SM_W / 2          # the bottom ring's upper edge over the side panel's middle
ring_hi = SM_Z[1] + SM_STEP - SM_W / 2          # the top ring's lower edge there
sign_faces = []
for s in (1, -1):   # the same spots on both sides, text upright (owner, 2026-11-08: "mirrored on the other side")
    fs, _ = wall_sign(s, S_ANG, ring_hi - S_GAP - S_PL * 258 / 461, S_PL, (0, 0.687, 0.2251, 0.813), (461, 258), 'Atlas2')  # A1 DANGER STRONG MAGNETIC FIELD
    sign_faces += fs
    fs, hc = wall_sign(s, S_ANG, ring_lo + S_GAP, S_TRI, (0.0034, 0.3125, 0.1846, 0.4648), (371, 312), 'Decals')            # C1 high-voltage triangle
    sign_faces += fs
    fs, _ = wall_sign(s, S_ANG, ring_lo + S_GAP + hc + S_PAIR, S_PL, (0.6245, 0.875, 0.8516, 1), (465, 256), 'Atlas2')     # B3 WARNING TIP OVER HAZARD
    sign_faces += fs
fs, _ = wall_sign(-1, 2.0, SM_Z[1] + SM_W / 2 + 0.015, S_LBL, (0.6074, 0.8179, 0.8604, 0.8677), (518, 102), 'Atlas2')            # D1 Remote Operated System, over the beam housing
sign_faces += fs
print('sign faces', len(sign_faces))

# ---- 6d. chrome module details: the owner's pick of art/module-sheet.png (2026-11-07: "M1 + M5") ----
# On each module's face (SH_FRONT off the wall), in Atlas3_Chrome so they follow the chrome: a bolt head in each
# corner, one head in from the ends and the sides (owner, 2026-11-08: "a rivet in all 4 corners"; it had two at its
# outer end), and Atlas3 piece 38, the wide frame with a dark slot, centred.
M_A = (math.degrees(math.asin(XI / R)), math.degrees(math.asin(XO / R)))   # the modules' inner and outer edges
M_IN = B_W                                                                  # bolt centres one head in
SL_BOX, SL_W = (0.6274, 0.1274, 0.8726, 0.2476), 0.26; SL_H = SL_W * 246 / 502
module_faces = []
for s in (1, -1):
    for z0, z1 in MOD:
        for zb in (z0 + M_IN, z1 - M_IN):
            for a in (M_A[0] + math.degrees(M_IN / R), M_A[1] - math.degrees(M_IN / R)):
                module_faces += wall_quad(s, a, zb, B_W, B_H, B_BOX, 'Atlas3_Chrome', SH_FRONT + HO_OFF, rng.uniform(0, 2 * math.pi))
        module_faces += wall_quad(s, (M_A[0] + M_A[1]) / 2, (z0 + z1) / 2, SL_W, SL_H, SL_BOX, 'Atlas3_Chrome', SH_FRONT + HO_OFF)
print('module detail faces', len(module_faces))

# ---- 6f. middle plates: a bolt head in each corner, as on the modules, and no other detail (owner, 2026-11-08,
# after a cooling-unit layout, an X with dimples inside and an X between perforated fields: "leave the panel blank
# except for the rivets") ----
PL_C = (M_A[0] + M_A[1]) / 2; PL_HW = R * math.radians(M_A[1] - M_A[0]) / 2
PL_BX, PL_BY = PL_HW - M_IN, (PL_Z[1] - PL_Z[0]) / 2 - M_IN          # corner bolt centres, as on the modules
plate_faces = []
for s in (1, -1):
    for sx in (1, -1):
        for sy in (1, -1):
            plate_faces += wall_quad(s, PL_C + sx * math.degrees(PL_BX / R), ZMID + sy * PL_BY, B_W, B_H, B_BOX, 'Atlas3_Chrome', SH_FRONT + HO_OFF, rng.uniform(0, 2 * math.pi))
print('plate detail faces', len(plate_faces))

# ---- 6e. beam surround seams and bolts: the owner's markup of the top-end render (2026-11-08) ----
# A small seam round the front face; segment seams level with the plate joins, from the plinth's foot up to it with
# pointed T-ends; on each sloped end an open U seam whose sides run over the crease and down the plinth, with two bolt
# heads inside it. Atlas4_Chrome piece 3 and Atlas3_Chrome piece 14, so they follow the chrome.
SR_W = 0.015                                                # "a small seam", under the wall's 20 mm
SR_XC = (P_FX - P_BEV + GW + G_CH) / 2                      # front seam centre line: midway across the rim
SR_ZI = (P_FX - P_BEV) - SR_XC                              # the same distance in from the face's top and bottom edges
SR_CR = 0.02                                                # its corner radius
SR_Z = (MOD[0][1] + GAP / 2, MOD[1][0] - GAP / 2)           # the plate joins' centre lines
SU_IN, SU_B, SU_BIN = 0.07, 0.30, 0.03                      # U: sides in from the end's edges; bottom line up the end; bolts in
hosts_all = [f for f in sur_faces if f.is_valid and f.material_index == C]


def clip_cv(subj, cl):
    """Sutherland-Hodgman: subj clipped to the convex anticlockwise polygon cl."""
    out = subj
    for i in range(len(cl)):
        if not out: break
        a, b = cl[i], cl[(i + 1) % len(cl)]; ex, ez = b[0] - a[0], b[1] - a[1]
        sd = [ex * (p[1] - a[1]) - ez * (p[0] - a[0]) for p in out]; inp = out; out = []
        for j in range(len(inp)):
            k = (j + 1) % len(inp)
            if sd[j] >= 0: out.append(inp[j])
            if (sd[j] >= 0) != (sd[k] >= 0):
                t = sd[j] / (sd[j] - sd[k]); out.append((inp[j][0] + t * (inp[k][0] - inp[j][0]), inp[j][1] + t * (inp[k][1] - inp[j][1])))
    return out


def in_tri(p, t, eps=1e-9):
    return all((t[(i + 1) % 3][0] - t[i][0]) * (p[1] - t[i][1]) - (t[(i + 1) % 3][1] - t[i][1]) * (p[0] - t[i][0]) >= -eps for i in range(3))


def frame(O, Eb, Dp):
    """Right-handed decal frame: origin, up axis b, out axis; a = b x out, so anticlockwise in (a, b) faces out."""
    return O, Eb.cross(Dp).normalized(), Eb, Dp


def host_tris(fr, faces):
    O, Ea, Eb, Dp = fr; out = []
    for f in faces:
        if f.normal.dot(Dp) < 0.2: continue
        vs = [v.co.copy() for v in f.verts]
        for i in range(1, len(vs) - 1):   # the hosts are convex
            t2 = [((p - O).dot(Ea), (p - O).dot(Eb)) for p in (vs[0], vs[i], vs[i + 1])]
            if abs(area2(t2)) < 1e-10: continue
            out.append((t2 if area2(t2) > 0 else t2[::-1], vs[0], f.normal.copy()))
    return out


def drape(fr, poly, hosts, off, mat, uvf, vd):
    """Decal polygon in frame fr, projected along its out axis onto the host faces, cut where they meet, each piece
    off its face by off (mitred where faces meet, so the pieces join)."""
    O, Ea, Eb, Dp = fr
    if area2(poly) < 0: poly = poly[::-1]
    fs = []
    for t2, T0, n in hosts:
        piece = clip_cv(poly, t2)
        if len(piece) < 3 or abs(area2(piece)) < 1e-6: continue   # slivers under 1 mm2 where a cut meets a mitre: no tangent frame
        vs = []; pos = {}
        for p in piece:
            key = (round(p[0], 6), round(p[1], 6))
            if key not in vd:
                q = O + Ea * p[0] + Eb * p[1]; q = q + Dp * (n.dot(T0 - q) / n.dot(Dp))
                ns = []
                for t2b, _, nb in hosts:
                    if in_tri(p, t2b) and all(nb.angle(m, 0) > 1e-3 for m in ns): ns.append(nb)
                m = sum(ns, Vector()).normalized() if ns else n
                vd[key] = bm.verts.new(q + m * (off / min([m.dot(nb) for nb in ns] or [1.0])))
            if vd[key] not in pos: vs.append(vd[key]); pos[vd[key]] = p
        if len(vs) < 3: continue
        f = face(vs, n, MI[mat]); f.smooth = True
        for l in f.loops: l[uv].uv = uvf(pos[l.vert])
        fs.append(f)
    return fs


def drape_band(fr, P, w, hosts, off, mat, vd):
    """Seam band round the polyline P in frame fr; V1 on its left (band())."""
    segs, total = band(P, w); fs = []
    for quad, P0, d, nn, U0 in segs:
        def uvf(p, P0=P0, d=d, nn=nn, U0=U0):
            ra, rb = p[0] - P0[0], p[1] - P0[1]
            return ((U0 + ra * d[0] + rb * d[1]) * SM_US, (SM_V[0] + SM_V[1]) / 2 + (ra * nn[0] + rb * nn[1]) / w * (SM_V[1] - SM_V[0]))
        fs += drape(fr, quad, hosts, off, mat, uvf, vd)
    return fs


surround_faces = []
# front seam, V1 inwards (towards the panel it outlines, as on the top deck); its long sides follow the dip, which
# slides the rim out by KS x the depth while the glow edge stays put, so they keep to the rim's middle
fr_f = frame(Vector(), Vector((0, 0, 1)), Vector((0, 1, 0)))
hf = host_tris(fr_f, [f for f in hosts_all if P_FZ[0] - 0.01 < f.calc_center_median().z < P_FZ[1] + 0.01 and f.normal.y > 0.6])


def arc(cx, cz, a0, a1, n=4):
    return [(cx + SR_CR * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cz + SR_CR * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


XC, ZT, ZB = SR_XC, P_FZ[1] - P_BEV - SR_ZI, P_FZ[0] + P_BEV + SR_ZI
SH_D = KS * DIP / 2
DZA, DZB = P_FZ[0] + (P_FZ[1] - P_FZ[0]) / 3, P_FZ[1] - (P_FZ[1] - P_FZ[0]) / 3
loop = ([(0, ZB)] + arc(XC - SR_CR, ZB + SR_CR, -90, 0) + [(XC, DZA), (XC + SH_D, DZA + DIP), (XC + SH_D, DZB - DIP), (XC, DZB)]
        + arc(XC - SR_CR, ZT - SR_CR, 0, 90) + arc(-XC + SR_CR, ZT - SR_CR, 90, 180)
        + [(-XC, DZB), (-XC - SH_D, DZB - DIP), (-XC - SH_D, DZA + DIP), (-XC, DZA)] + arc(-XC + SR_CR, ZB + SR_CR, 180, 270) + [(0, ZB)])
P = [(-x, z) for x, z in loop]          # frame a = -x
if area2(P[:-1]) < 0: P = P[::-1]
surround_faces += drape_band(fr_f, P, SR_W, hf, SM_OFF, 'Atlas4_Chrome', {})


# segment seams: the surround's cross-section at each plate join, from the plinth's foot over the plinth top, the side
# slope and the rim bevel to the front seam, ending in a point on its centre line; V1 up like the wall rings, 1 mm
# higher than the front seam so the points draw over it (as the wall's stems do)
def chain(z0, s):
    segs = []
    for f in hosts_all:
        if abs(f.normal.z) > 0.05: continue
        pts = []
        for e in f.edges:
            a, b = e.verts[0].co, e.verts[1].co
            if (a.z - z0) * (b.z - z0) < 0:
                p = a.lerp(b, (z0 - a.z) / (b.z - a.z)); pts.append((round(p.x, 6), round(p.y, 6)))
        if len(pts) == 2 and s * (pts[0][0] + pts[1][0]) > 0: segs.append(pts)
    adj = {}
    for p, q in segs:
        adj.setdefault(p, []).append(q); adj.setdefault(q, []).append(p)
    cur = max((k for k, v in adj.items() if len(v) == 1), key=lambda k: abs(k[0]))   # the plinth's foot
    out = [cur]; prev = None
    while len(out) < 400:
        nxt = [q for q in adj[cur] if q != prev]
        if not nxt: break
        prev, cur = cur, nxt[0]; out.append(cur)
    return out


xe = SR_XC + SR_W / 2
for z0 in SR_Z:
    for s in (1, -1):
        pts = chain(z0, s); Q = None
        for j in range(1, len(pts)):
            p, q = pts[j - 1], pts[j]
            if abs(p[1] - P_FY) < 1e-4 and abs(q[1] - P_FY) < 1e-4 and (abs(p[0]) - xe) * (abs(q[0]) - xe) <= 0:
                Q = pts[:j] + [(s * xe, P_FY)]; break
        assert Q, (z0, s, pts[-3:])
        d0 = Vector((Q[1][0] - Q[0][0], Q[1][1] - Q[0][1])).normalized(); Q[0] = (Q[0][0] + d0.x * 0.001, Q[0][1] + d0.y * 0.001)
        Q = [Q[0]] + [Q[j] for j in range(1, len(Q)) if math.dist(Q[j], Q[j - 1]) > 1e-5]
        ns = []
        for j in range(len(Q) - 1):
            dx, dy = Q[j + 1][0] - Q[j][0], Q[j + 1][1] - Q[j][1]; l = math.hypot(dx, dy); ns.append((s * dy / l, -s * dx / l))
        us = [0.0]
        for j in range(1, len(Q)): us.append(us[-1] + math.dist(Q[j], Q[j - 1]))
        T = us[-1] + SR_W / 2
        lo, hi = [], []
        for j, p in enumerate(Q):
            if 0 < j < len(Q) - 1:
                m = Vector(ns[j - 1]) + Vector(ns[j]); m.normalize(); h = SM_STEM_OFF / m.dot(Vector(ns[j]))
            else:
                m = Vector(ns[min(j, len(ns) - 1)]); h = SM_STEM_OFF
            lo.append(bm.verts.new((p[0] + m.x * h, p[1] + m.y * h, z0 - SR_W / 2)))
            hi.append(bm.verts.new((p[0] + m.x * h, p[1] + m.y * h, z0 + SR_W / 2)))
        uu = (lambda u: u) if s > 0 else (lambda u: T - u)
        for j in range(len(Q) - 1):
            f = face([lo[j], lo[j + 1], hi[j + 1], hi[j]], (ns[j][0], ns[j][1], 0), MI['Atlas4_Chrome']); f.smooth = True
            for l in f.loops:
                k = (lo + hi).index(l.vert); jj = k % len(Q)
                l[uv].uv = (uu(us[jj]) * SM_US, SM_V[1] if k >= len(Q) else SM_V[0])
            surround_faces.append(f)
        tip = bm.verts.new((s * SR_XC, P_FY + SM_STEM_OFF, z0))
        f = face([lo[-1], tip, hi[-1]], (0, 1, 0), MI['Atlas4_Chrome']); f.smooth = True
        for l in f.loops:
            l[uv].uv = (uu(T) * SM_US, (SM_V[0] + SM_V[1]) / 2) if l.vert == tip else (uu(us[-1]) * SM_US, SM_V[1] if l.vert == hi[-1] else SM_V[0])
        surround_faces.append(f)

# sloped ends: an open U, V1 inwards, its sides parallel to the end's side edges and run on over the crease and down
# the plinth to the floor; a bolt head inside each bottom corner. Worked in a frame on the end's plane, a = across
for e_, zf, zbe in ((1, P_FZ[1], P_BZ[1]), (-1, P_FZ[0], P_BZ[0])):
    Et = Vector((0, top_y(0) - P_FY, zbe - zf)); Lr = Et.length; Et.normalize()
    fr_e = frame(Vector((0, P_FY, zf)), Et, Vector((0, abs(Et.z), -e_ * Et.y)))
    he = host_tris(fr_e, [f for f in hosts_all if (f.calc_center_median().z - zf) * e_ > -0.005])
    def xs(b): return P_FX + (PBT - P_FX) * b / Lr - SU_IN
    bl, bf = SU_B * Lr, Lr + 0.08
    U_P = fillet([(-xs(bf), bf), (-xs(bl), bl), (xs(bl), bl), (xs(bf), bf)], {1, 2}, SR_CR, 4)   # corners rounded like the front seam's (owner, 2026-11-08)
    surround_faces += drape_band(fr_e, U_P, SR_W, he, SM_OFF, 'Atlas4_Chrome', {})
    bb = bl + SU_BIN
    for sa in (-1, 1):
        c = (sa * (xs(bb) - SU_BIN), bb); phi = rng.uniform(0, 2 * math.pi)
        Ub, Vb = (math.cos(phi), math.sin(phi)), (-math.sin(phi), math.cos(phi))
        poly = [(c[0] + Ub[0] * i * B_W / 2 + Vb[0] * j * B_H / 2, c[1] + Ub[1] * i * B_W / 2 + Vb[1] * j * B_H / 2) for i, j in CORNERS]
        def uvf(p, c=c, Ub=Ub, Vb=Vb):
            dx, dy = p[0] - c[0], p[1] - c[1]
            return (B_BOX[0] + (0.5 + (dx * Ub[0] + dy * Ub[1]) / B_W) * (B_BOX[2] - B_BOX[0]),
                    B_BOX[1] + (0.5 + (dx * Vb[0] + dy * Vb[1]) / B_H) * (B_BOX[3] - B_BOX[1]))
        surround_faces += drape(fr_e, poly, he, HO_OFF, 'Atlas3_Chrome', uvf, {})
# dark notches in the rim beside the glow, one each side at the surround's middle height (owner, 2026-11-08: "add the
# notches but at the center height of the beam surround"; concept 2 has them at the glow's edge): Atlas3_Chrome piece
# 20, the tall dark slot of the side panels, upright, 1 mm out from the slot's chamfer, on the dipped face
N_W = 0.014; N_H = N_W * 491 / 110
for s in (1, -1):
    c = (-s * (GW + G_CH + 0.001 + N_W / 2), ZC)          # frame a = -x
    poly = [(c[0] + i * N_W / 2, c[1] + j * N_H / 2) for i, j in CORNERS]
    def uvf(p, c=c):
        return (HO_BOX[0] + (0.5 + (p[0] - c[0]) / N_W) * (HO_BOX[2] - HO_BOX[0]), HO_BOX[1] + (0.5 + (p[1] - c[1]) / N_H) * (HO_BOX[3] - HO_BOX[1]))
    surround_faces += drape(fr_f, poly, hf, HO_OFF, 'Atlas3_Chrome', uvf, {})
tiny =[f for f in surround_faces if f.calc_area() < 1e-6]   # a sliver's crease point, mitred off both faces, folds it
bmesh.ops.delete(bm, geom=tiny, context='FACES')
surround_faces = [f for f in surround_faces if f.is_valid]
print('surround decal faces', len(surround_faces), 'slivers dropped', len(tiny))
print('kiosk islands', nk, 'slot faces', len(slot_faces), 'seam faces', len(seam_faces), 'bolt faces', len(bolt_faces))

# ---- 6g. half seam round the glow (owner, 2026-11-08: "a half very dark seam decal all the way around the emissive
# where it intersects with the beam surround inside. This will help it blend in better than the hard physical edge"):
# like the deck's half seams round the dome and antenna feet, Atlas4_VeryDark piece 3, its centre line on the slot
# walls' foot and only the half on the glow laid (10 mm), V1 towards the wall ----
GS_Y = P_FY - G_DEPTH + SM_OFF
g_out = [Vector((x, 0.0, z)) for x, z in Dg]
g_c, g_n = Vector((0.0, 0.0, ZC)), Vector((0.0, 1.0, 0.0))
if (g_out[1] - g_out[0]).cross(g_out[0] - g_c).dot(g_n) < 0: g_out.reverse()   # along U x out to the wall = the glow's normal: unmirrored
ng = len(g_out)


def g_inward(k):
    w = g_n.cross((g_out[(k + 1) % ng] - g_out[k]).normalized())
    return w if w.dot(g_c - g_out[k]) > 0 else -w


g_in = []
for k in range(ng):
    a_, b_ = g_inward(k - 1), g_inward(k); m_ = (a_ + b_).normalized()
    g_in.append(g_out[k] + m_ * (SM_W / 2 / max(m_.dot(b_), 0.3)))
g_s, glow_seam, g_vm = 0.0, [], (SM_V[0] + SM_V[1]) / 2
for k in range(ng):
    j = (k + 1) % ng; g_l = (g_out[j] - g_out[k]).length
    vs_ = [bm.verts.new((p.x, GS_Y, p.z)) for p in (g_out[k], g_out[j], g_in[j], g_in[k])]
    uvs_ = dict(zip(vs_, ((g_s * SM_US, g_vm), ((g_s + g_l) * SM_US, g_vm), ((g_s + g_l) * SM_US, SM_V[0]), (g_s * SM_US, SM_V[0]))))
    f_ = face(vs_, (0, 1, 0), MI['Atlas4_VeryDark'])
    for l in f_.loops: l[uv].uv = uvs_[l.vert]
    glow_seam.append(f_); g_s += g_l
print('glow half seam faces', len(glow_seam), 'perimeter', round(g_s, 3))

# ---- 7. foot: the lip's bevel upside down, then flat underneath in to a dark painted shaft that stands in the base's
# trim ring, built by base_ring_build.py (owner, 2026-11-08: "The bottom of the canister should copy the same bevel that
# is at the top, then be flat on the bottom until it reaches the shaft"). It replaces the base mesh's dark collar, taper
# and ledge below the collar's top loop, all in the paint like the lip; the paint's UVs carry on down from the wall ----
NK_R, NK_FOOT_Z, NK_LOOP_Z, NK_BTM_Z = 0.80, 0.17, 0.40, -0.04   # shaft radius; underside; the collar's top loop; shaft bottom


def nk_r(v): return math.hypot(v.co.x, v.co.y)


def nk_profile():
    """t_lip_profile's bevel and rounds mirrored onto the underside at NK_FOOT_Z, from the collar's top loop down."""
    rho, t, zf = 0.04, 0.04 * math.tan(math.radians(22.5)), NK_FOOT_Z
    P = [(R, NK_LOOP_Z, None), (R, zf + 0.10 + t, PC)]
    P += [(R - rho + rho * math.cos(math.radians(a)), zf + 0.10 + t - rho * math.sin(math.radians(a)), PC) for a in (15, 30, 45)]
    P += [(1.02 - t + rho * math.cos(math.radians(a)), zf + rho - rho * math.sin(math.radians(a)), PC) for a in (45, 60, 75, 90)]
    return P + [(NK_R, zf, PC), (NK_R, NK_BTM_Z, D), (0.0, NK_BTM_Z, D)]   # the shaft dark paint, as the trim ring (owner, 2026-11-08: "it should be a dark metal")


nk_lo = sorted((v for v in bm.verts if abs(v.co.z - NK_LOOP_Z) < 1e-4 and abs(nk_r(v) - R) < 2e-3), key=lambda v: ang(v.co))
assert len(nk_lo) == 64, len(nk_lo)
nk_uv = {}; nk_rate = None                 # each facet's u at its two corners and v at the loop, from the paint band above
for k in range(64):
    a, b = nk_lo[k], nk_lo[(k + 1) % 64]
    fa = next(f for f in a.link_faces if b in f.verts and f.calc_center_median().z > NK_LOOP_Z)
    nk_uv[k] = (next(l[uv].uv.copy() for l in fa.loops if l.vert is a), next(l[uv].uv.copy() for l in fa.loops if l.vert is b))
    if nk_rate is None:
        zs = sorted((l.vert.co.z, l[uv].uv.y) for l in fa.loops); nk_rate = (zs[-1][1] - zs[0][1]) / (zs[-1][0] - zs[0][0])
    e = bm.edges.get((a, b)); e.smooth = True
nk_old = [f for f in bm.faces if f.calc_center_median().z < NK_LOOP_Z - 1e-4 and all(v.co.z < NK_LOOP_Z + 1e-4 for v in f.verts)]
bmesh.ops.delete(bm, geom=nk_old, context='FACES')
nkp = nk_profile()
nk_faces, nk_map = t_lathe(Vector((0, 0)), nkp, [ang(v.co) for v in nk_lo], ring0=nk_lo, sign=-1)
nk_s = [0.0]
for j in range(1, len(nkp)): nk_s.append(nk_s[-1] + math.hypot(nkp[j][0] - nkp[j - 1][0], nkp[j][1] - nkp[j - 1][1]))
nk_bare = []
for f, j, k in nk_faces:
    f.smooth = True
    if f.material_index != PC:
        if nkp[j + 1][0] < 1e-6: nk_bare.append(f); continue
        for l in f.loops:   # the shaft: wrapped round it at Keen's paint scale
            jj, kk = nk_map[l.vert]
            l[uv].uv = ((k if kk == k else k + 1) / 64 * 2 * math.pi * NK_R * T_HUB_UPM, l.vert.co.z * T_HUB_UPM)
        continue
    for l in f.loops:
        jj, kk = nk_map[l.vert]
        l[uv].uv = (nk_uv[k][0].x if kk == k else nk_uv[k][1].x, nk_uv[k][0].y - nk_rate * nk_s[jj])
bm.normal_update(); boxuv(nk_bare, T_HUB_UPM)
for e in {e for f, _, _ in nk_faces for e in f.edges}:
    lf = e.link_faces
    if len(lf) == 2 and lf[0].normal.angle(lf[1].normal, 0) > math.radians(35): e.smooth = False
print('foot: removed', len(nk_old), 'faces, built', len(nk_faces), '; paint v rate %.3f' % nk_rate)
# warning triangle under the beam (owner, 2026-11-08: "a red triangle or something on the canister body", "Front, under
# the beam"): Atlas2 piece 54, the red outline with "!", 15 cm, centred between the bay's bottom half seam and the
# foot's bevel; after step 6, whose kiosk test would turn it chrome
TRI_BOX, TRI_W = (0.4648, 0.354, 0.5342, 0.4141), 0.15     # 142 x 123 px
tri_faces = wall_quad(1, 0.0, (SM_Z[0] - SM_W / 2 + nkp[1][1]) / 2, TRI_W, TRI_W * 123 / 142, TRI_BOX, 'Atlas2')
print('warning triangle faces', len(tri_faces))
# ---- 8. the plates' and modules' fronts shade as the cylinder they wrap (owner, 2026-11-08: "some warping in the
# reflections"): their ear-clipped fronts have long thin triangles, and the angle-weighted normals at the facet cuts
# came out uneven. Each front is split sharp from its bevel, and every corner on it gets the exact radial normal ----
pf_set = set(plate_front)
for f in plate_front:
    for e in f.edges:
        if any(g not in pf_set for g in e.link_faces): e.smooth = False
bm.faces.index_update(); pf_idx = {f.index for f in plate_front}
bm.to_mesh(me); bm.free()
cn = [(0.0, 0.0, 0.0)] * len(me.loops)   # zero keeps a corner's own normal
for p in me.polygons:
    if p.index in pf_idx:
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co; cn[li] = Vector((co.x, co.y, 0)).normalized()[:]
me.normals_split_custom_set(cn)
print('plate front faces with radial normals', len(pf_idx))
# the bare metal parts are Metal_Shiny, built as the slot 'Chrome' (owner, 2026-11-08: "Metal_Shiny" of
# art/material-options.png; Chrome's gloss is 38%, Metal_Shiny's 87%); their decals stay the _Chrome sheets
me.materials[C] = next(m for m in bpy.data.materials if m.name == 'Metal_Shiny' and m.library)
old = obj.data; obj.data = me
if 'AZ_kiosk_v1' not in bpy.data.meshes:
    old.name = 'AZ_kiosk_v1'; old.use_fake_user = True
elif old.name not in ('AZ_base_nokiosk', 'AZ_kiosk_v1'):
    bpy.data.meshes.remove(old)
me.name = 'GVK_SalvagerTurret_Azimuth_Visual_Mesh'
print('faces', len(me.polygons), 'max r', round(max(math.hypot(v.co.x, v.co.y) for v in me.vertices), 4))
