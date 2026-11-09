"""Salvage Beam Turret build stages BS1 to BS3, built from low-poly proxies of the finished model (se-dev-seut
block-scenes.md, "Designing the stages").

Run inside GVK_SalvagerTurret.blend. Every stage fills the whole outline (crate, trim ring, canister and antenna) and
only the detail grows, since every stage uses Main's collision; nothing floats, so each stage carries its load path:
crate -> beams under its top -> shaft -> spokes under the canister -> column -> spokes under the top -> dome, boss and
antenna. A framed part is its proxy with every face inset STRIP, the face removed and the strips solidified THICK
inwards; a solid part is the proxy as it is.

- BS1: strip frames over the crate, the ring, the canister wall, its foot, lip and beam surround; solid core pieces:
  the beams, the shaft, the spokes, the column, the antenna boss and rod.
- BS2: the crate's panels fill its frame and its five ports appear, and the ring turns solid; inside the still-framed
  canister wall the mechanisms appear as plain solids: the bay's lower and upper modules, the beam emitter, the drive
  boxes, the dome.
- BS3: the keypads; the canister wall solid apart from three panels on each side and the top, which stay open frame so
  the inside shows; the bay's plate and the solid beam surround added.

The canister is built in its own frame (z 0 at the crate top) and turned 180 degrees about Z into block space, as
SEUT shows it under subpart_Azimuth, so the beam surround faces -Y. One mesh per stage, `Construction` only, flat
shaded, box UVs offset from the origin.
"""
import bpy, bmesh, math
from mathutils import Matrix, Vector

SUB = 'GVK_SalvagerTurret'
STRIP, THICK = 0.07, 0.02
N = 16
ROT = math.radians(78.75)          # wall posts at 78.75 + k * 22.5 degrees: two on the beam surround's sides (79, 101)
CAN = Matrix.Translation((0, 0, -1.25)) @ Matrix.Rotation(math.pi, 4, 'Z')
UV = 0.5                           # UV per metre


def ring(n, r, rot=0.0, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(rot + 2 * math.pi * i / n), cy + r * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]


def loft(rings):
    """A closed solid through (points, z) rings of one count, CCW points; side faces per band, capped."""
    bm = bmesh.new(); vs = [[bm.verts.new((x, y, z)) for x, y in pts] for pts, z in rings]; n = len(vs[0])
    for a, b in zip(vs, vs[1:]):
        for i in range(n): bm.faces.new([a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]])
    bm.faces.new(list(reversed(vs[0]))); bm.faces.new(vs[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def prism(pts, *zs): return loft([(pts, z) for z in zs])


def box(x0, x1, y0, y1, z0, z1): return prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def beam(p0, p1, w, z0, z1):
    a, b = Vector(p0), Vector(p1); d = (b - a).normalized(); n = Vector((-d.y, d.x)) * w / 2
    return prism([tuple(a - n), tuple(b - n), tuple(b + n), tuple(a + n)], z0, z1)


def arc_block(a0, a1, r0, r1, *zs, k=4):
    """A block between two radii and two angles (degrees), its outside a k-segment arc."""
    out = [(r1 * math.cos(math.radians(a0 + (a1 - a0) * i / k)), r1 * math.sin(math.radians(a0 + (a1 - a0) * i / k))) for i in range(k + 1)]
    inn = [(r0 * math.cos(math.radians(a)), r0 * math.sin(math.radians(a))) for a in (a1, a0)]
    return prism(out + inn, *zs)


def annulus(n, r0, r1, z0, z1, rot=0.0):
    bm = bmesh.new(); o0, o1, i0, i1 = [[bm.verts.new((x, y, z)) for x, y in ring(n, r, rot)] for r, z in ((r1, z0), (r1, z1), (r0, z0), (r0, z1))]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([o0[i], o0[j], o1[j], o1[i]]); bm.faces.new([i0[j], i0[i], i1[i], i1[j]])
        bm.faces.new([o1[i], o1[j], i1[j], i1[i]]); bm.faces.new([o0[j], o0[i], i0[i], i0[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def framed(bm, cut_if=lambda f: True, strip=STRIP, thick=THICK):
    """Faces cut_if picks become strip frames unless too small for two strips; the rest stay plates; all thick."""
    bm.normal_update()
    cut = [f for f in bm.faces if cut_if(f) and 2 * f.calc_area() / f.calc_perimeter() > 2.4 * strip]
    if cut:
        bmesh.ops.inset_individual(bm, faces=cut, thickness=strip, depth=0.0, use_even_offset=True)
        bmesh.ops.delete(bm, geom=cut, context='FACES_ONLY')
    bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=thick)
    return bm


def merge(dst, src, M=None):
    if M is not None: bmesh.ops.transform(src, matrix=M, verts=src.verts)
    vm = {v: dst.verts.new(v.co) for v in src.verts}
    for f in src.faces:
        try: dst.faces.new([vm[v] for v in f.verts])
        except ValueError: pass
    src.free()


# --- the base, in block space (crate -3.75 to -1.25, trim ring to -1.13) ---
def crate(stage, bm):
    # The crate's frame is heavier than the canister's (12 cm strips, 4 cm deep), as Keen's cargo container stages are.
    merge(bm, framed(prism([(-1.25, -1.25), (1.25, -1.25), (1.25, 1.25), (-1.25, 1.25)], -3.75, -2.5, -1.25), strip=0.12, thick=0.04))
    if stage == 1:
        for a in (0, 45, 90, 135):                    # beams under the top, flush with it: the ring and the shaft sit on them
            c, s = abs(math.cos(math.radians(a))), abs(math.sin(math.radians(a)))
            L = min((1.21 - 0.05 * s) / c if c > 1e-6 else 9, (1.21 - 0.05 * c) / s if s > 1e-6 else 9)   # ends inside the frame
            c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
            merge(bm, beam((-L * c, -L * s), (L * c, L * s), 0.10, -1.31, -1.25))
        return
    merge(bm, box(-1.21, 1.21, -1.21, 1.21, -3.71, -1.25))          # the panels, 4 cm inside the frame; the top flush, under the ring
    P, H, OUT = 0.68, 1.20, 1.286                     # port frames (detector_conveyor_1 to 5): 1.36 m square, 3.6 cm proud
    for sx, sy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        x0, x1 = (sx * H, sx * OUT) if sx else (-P, P); y0, y1 = (sy * H, sy * OUT) if sy else (-P, P)
        merge(bm, box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), -2.5 - P, -2.5 + P))
    merge(bm, box(-P, P, -P, P, -3.786, -3.70))
    if stage < 3: return
    for x, y, w, d in ((0.825, -1.237, 0.2, 0.1), (1.238, 0.825, 0.1, 0.2), (-0.825, 1.238, 0.2, 0.1), (-1.239, -0.825, 0.1, 0.2)):
        merge(bm, box(x - w / 2, x + w / 2, y - d / 2, y + d / 2, -2.65, -2.35))   # keypads (detector_terminal_1 to 4)


def trim_ring(stage, bm):
    for sx in (-1, 1):                                # the ears, x to +-1.246, |y| 0.33
        merge(bm, box(min(sx * 1.10, sx * 1.246), max(sx * 1.10, sx * 1.246), -0.33, 0.33, -1.25, -1.13))
    if stage == 1:
        merge(bm, annulus(N, 1.11, 1.18, -1.25, -1.13)); merge(bm, annulus(N, 0.86, 0.93, -1.25, -1.13))
        for k in range(8):
            a = math.radians(22.5 + 45 * k); merge(bm, beam((0.9 * math.cos(a), 0.9 * math.sin(a)), (1.14 * math.cos(a), 1.14 * math.sin(a)), 0.08, -1.25, -1.15))
        return
    merge(bm, annulus(64 // 4, 0.86, 1.18, -1.25, -1.13))


# --- the canister, in its own frame (z 0 at the crate top; beam surround at +Y before the turn) ---
def canister(stage, bm):
    c = bmesh.new()
    merge(c, loft([(ring(N, 0.80, ROT), 0.0), (ring(N, 0.80, ROT), 0.17)]))           # shaft
    # The body, foot to lip: its bands meet at the bay's plate joins (z 1.366, 2.805); the foot and lip bands are too
    # small for strips, so they stay plates in every stage.
    body = loft([(ring(N, r, ROT), z) for r, z in ((1.02, 0.17), (1.12, 0.287), (1.12, 1.366), (1.12, 2.805), (1.12, 3.80), (1.032, 3.90), (0.95, 3.92))])
    if stage < 3:
        merge(c, framed(body))
    else:
        def opened(f):                                   # the top and the middle band's three side panels round 0 and 180 degrees
            m = f.calc_center_median(); a = math.degrees(math.atan2(m.y, m.x)) % 360
            return f.normal.z > 0.9 or (abs(f.normal.z) < 0.5 and 1.366 < m.z < 2.805 and min(a, 360 - a, abs(a - 180)) < 25)
        merge(c, framed(body, opened))
    merge(c, loft([(ring(12, 0.15), 0.17), (ring(12, 0.15), 3.92)]))                   # column
    for z0, r1 in ((0.17, 1.0), (3.86, 0.92)):                                         # spokes under the canister and the top
        for k in range(8):
            a = math.radians(45 * k); merge(c, beam((0.10 * math.cos(a), 0.10 * math.sin(a)), (r1 * math.cos(a), r1 * math.sin(a)), 0.08, z0, z0 + 0.06))
    sur = arc_block(79, 101, 1.0, 1.249, 0.64, 3.53)                                   # beam surround
    merge(c, sur if stage == 3 else framed(sur))
    merge(c, loft([(ring(12, 0.165, cx=0.61), 3.92), (ring(12, 0.165, cx=0.61), 4.04)]))   # antenna boss
    merge(c, loft([(ring(6, 0.036, cx=0.61), 4.04), (ring(6, 0.036, cx=0.61), 6.97)]))     # antenna rod
    if stage >= 2:
        for a0, a1 in ((48, 78), (102, 132)):                                          # bay modules, each side of the surround
            merge(c, arc_block(a0, a1, 1.06, 1.15, 0.58, 1.346)); merge(c, arc_block(a0, a1, 1.06, 1.15, 2.825, 3.60))
            if stage == 3: merge(c, arc_block(a0, a1, 1.06, 1.15, 1.386, 2.785))         # the plate between them
        merge(c, arc_block(84, 96, 0.55, 1.10, 1.80, 2.37))                            # beam emitter, behind the surround
        for a in (135, 315):                                                           # drive boxes on the bottom spokes
            x, y = 0.55 * math.cos(math.radians(a)), 0.55 * math.sin(math.radians(a))
            merge(c, box(x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0.23, 0.48))
        merge(c, loft([(ring(12, 0.165, cx=-0.61), 3.92), (ring(12, 0.165, cx=-0.61), 4.02), (ring(12, 0.10, cx=-0.61), 4.12), (ring(12, 0.04, cx=-0.61), 4.145)]))  # dome
    merge(bm, c, CAN)


def box_uv(me):
    uv = me.uv_layers.new(name='UVMap') if not me.uv_layers else me.uv_layers[0]
    for p in me.polygons:
        n = p.normal; ax = max(range(3), key=lambda i: abs(n[i])); u, v = [i for i in range(3) if i != ax]
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (co[u] * UV + 0.137, co[v] * UV + 0.291)


def seut_col(sc, t, i):
    for c in bpy.data.collections:
        if c.seut.scene is sc and c.seut.col_type == t and c.seut.type_index == i: return c


sc = bpy.data.scenes[SUB]; mat = bpy.data.materials['Construction']
for stage in (1, 2, 3):
    bm = bmesh.new()
    crate(stage, bm); trim_ring(stage, bm); canister(stage, bm)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    name = '%s_BS%d' % (SUB, stage); col = seut_col(sc, 'bs', stage)
    me = bpy.data.meshes.new(name + '_build'); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = False
    me.materials.append(mat); box_uv(me)
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, me); col.objects.link(ob)
    else:
        old = ob.data; ob.data = me
        if old.users == 0: bpy.data.meshes.remove(old)
    me.name = name
    xs, ys, zs = ([v.co[i] for v in me.vertices] for i in range(3))
    print('%s: %d faces, %d triangles; x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f' % (name, len(me.polygons), sum(len(p.vertices) - 2 for p in me.polygons),
          min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
