"""Salvage Beam Turret LODs: LOD1 and LOD2 of the base and of the canister, rebuilt from their Main models.

Run inside GVK_SalvagerTurret.blend after kiosk_build.py and base_ring_build.py, so the LODs follow every change to
Main. Each LOD is one object in its scene's LODn collection: every mesh in Main (the base's crate, ring, ports and
keypads; the canister) evaluated with its modifiers and merged, its opaque faces decimated (Decimate Collapse), the
glow, screens and the smallest accent materials kept whole, and its decals laid back on unchanged. LOD2 keeps only
decals at least DEC_MIN across, so seams, bolts and text go and the signs, vents and plates stay; LOD3, the turret
about 10 px tall, has no decals. Decals left hanging by the decimation are dropped, and the ones the shell rose up
under are lifted, so the export decal snap starts from a clear gap. Shading: Main's own normals (radial plate fronts, the ring's weighted normals) carried
through the decimation as a corner attribute and set as custom normals, edges over 30 degrees sharp. LOD1 and LOD2 at
the base's old distances; LOD3 as far out as the vanilla turrets' (150 m) for a block 4 cells tall.
"""
import bpy, bmesh, math
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree

DEC = {"DECAL", "DECAL_NOPREMULT", "DECAL_CUTOUT"}
SCENES = ['GVK_SalvagerTurret', 'GVK_SalvagerTurret_Azimuth']
LODS = [(1, 30, 0.5, 0.0), (2, 80, 0.2, 0.06), (3, 200, 0.1, 99.0)]   # (LOD, distance m, share of opaque faces kept, DEC_MIN m)
KEEP_NAMES = {'Terminal', 'Conveyor'}                # never decimated, with the emissive materials and any under KEEP_N
KEEP_N = 60
SHARP = math.radians(30)
PROTECT, HELD_W = 1.0, 0.6                           # vertex group factor and weight for a material the first pass lost


def seut_col(sc, col_type, index=0, ref=None):
    for c in bpy.data.collections:
        if c.seut.scene is sc and c.seut.col_type == col_type and c.seut.type_index == index and (ref is None or c.seut.ref_col == ref):
            return c


def tech(m): return getattr(m.seut, 'technique', '') if m else ''


def merged(sc, main):
    """Main's meshes as exported (modifiers applied), in one bmesh with one material list and one UV layer."""
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap'); cn = bm.loops.layers.float_vector.new('cn'); mats = []
    for o in sorted((o for o in main.all_objects if o.type == 'MESH' and not o.name.endswith('(L)')), key=lambda o: o.name):
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        M = o.matrix_world; N = M.to_3x3().inverted().transposed(); src_uv = me.uv_layers.active; cns = me.corner_normals
        mi = []
        for m in me.materials:
            if m not in mats: mats.append(m)
            mi.append(mats.index(m))
        vs = [bm.verts.new(M @ v.co) for v in me.vertices]
        for p in me.polygons:
            try: f = bm.faces.new([vs[i] for i in p.vertices])
            except ValueError: continue
            f.material_index = mi[p.material_index] if p.material_index < len(mi) else 0
            for l, li in zip(f.loops, p.loop_indices): l[uv].uv = src_uv.data[li].uv; l[cn] = (N @ cns[li].vector).normalized()
        bpy.data.meshes.remove(me)
    return bm, mats


def islands(faces):
    """Decal faces grouped by shared vertices."""
    left = set(faces); out = []
    while left:
        st = [left.pop()]; g = [st[0]]
        while st:
            f = st.pop()
            for v in f.verts:
                for h in v.link_faces:
                    if h in left: left.discard(h); st.append(h); g.append(h)
        out.append(g)
    return out


def across(g):
    """An island's width, twice its area over its outline's length: a seam strip's width, about 0.11 m for a
    300 x 168 mm sign, 0.07 for a 150 mm triangle, 0.02 for a bolt."""
    s = set(g); P = sum(e.calc_length() for f in g for e in f.edges if sum(h in s for h in e.link_faces) == 1)
    return 2 * sum(f.calc_area() for f in g) / max(P, 1e-6)


def to_mesh(bm, mats, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    for m in mats: me.materials.append(m)
    return me


def decimate(me, ratio, sc, protect=()):
    """Decimate Collapse through a temporary object in the scene the window shows (the depsgraph's). The faces of the
    materials in protect cost more to collapse (a weight-0 vertex group), so a material the first pass wiped out
    survives the second (se-dev-seut: never let a decimate pass delete accent faces)."""
    ob = bpy.data.objects.new('TMP_lod', me); sc.collection.objects.link(ob)
    md = ob.modifiers.new('dec', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = ratio
    if protect:
        held = {vi for p in me.polygons if p.material_index in protect for vi in p.vertices}
        vg = ob.vertex_groups.new(name='decimate')
        vg.add([v.index for v in me.vertices if v.index not in held], 1.0, 'REPLACE'); vg.add(list(held), HELD_W, 'REPLACE')
        md.vertex_group = 'decimate'; md.vertex_group_factor = PROTECT
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    out = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)
    return out


def host_bvh(bm, dec_i):
    host = bmesh.new(); vm = {}
    for f in bm.faces:
        if f.material_index in dec_i: continue
        vs = [vm[v] if v in vm else vm.setdefault(v, host.verts.new(v.co)) for v in f.verts]
        try: host.faces.new(vs)
        except ValueError: pass
    bvh = BVHTree.FromBMesh(host); host.free(); bm.normal_update()
    return bvh


def samples(f):
    """The centre, each corner pulled 1 mm in and each edge's middle pulled 1 mm in."""
    c = f.calc_center_median(); pull = lambda p: p.lerp(c, min(1.0, 0.001 / max((p - c).length, 1e-9)))
    return [c] + [pull(v.co) for v in f.verts] + [pull((e.verts[0].co + e.verts[1].co) / 2) for e in f.edges]


def drop_stranded(bm, dec_i):
    """Decal faces the decimation stranded: a corner (1 mm in) or the centre with no surface within 2 cm under it, or
    one with a surface just over it. Floating ones stay (at 30 m and out a few mm of float does not show)."""
    bvh = host_bvh(bm, dec_i); kill = []
    for f in bm.faces:
        if f.material_index not in dec_i: continue
        n = f.normal
        for p in samples(f):
            if bvh.ray_cast(p + n * 1e-4, -n, 0.02)[0] is None or bvh.ray_cast(p - n * 1e-4, n, 0.004)[0] is not None:
                kill.append(f); break
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    return len(kill)


def lift_low(bm, dec_i, lo=0.001, to=0.0015, passes=3):
    """Decal faces the decimated shell rose up under (lowest sample under lo) lifted to `to` along their normal, so
    the export snap starts from a clear gap; a shared corner takes the largest lift its faces ask for."""
    bvh = host_bvh(bm, dec_i); total = set()
    for _ in range(passes):
        up = {}
        for f in bm.faces:
            if f.material_index not in dec_i: continue
            n = f.normal; gs = [h[3] - 0.004 for h in (bvh.ray_cast(p + n * 0.004, -n, 0.024) for p in samples(f)) if h[0] is not None]
            if gs and min(gs) < lo:
                total.add(f)
                for v in f.verts: up[v] = max(up.get(v, 0.0), to - min(gs))
        if not up: break
        for v, d in up.items():
            n = sum((f.normal for f in v.link_faces if f.material_index in dec_i), Vector()).normalized()
            v.co += n * d
        bm.normal_update()
    return len(total)


def build(sc):
    main = seut_col(sc, 'main'); sub = sc.seut.subtypeId
    bm, mats = merged(sc, main)
    cnt = Counter(f.material_index for f in bm.faces)
    keep = {i for i, m in enumerate(mats) if tech(m) in DEC or (m and (m.name in KEEP_NAMES or 'Emissive' in m.name)) or cnt[i] < KEEP_N}
    dec_i = {i for i, m in enumerate(mats) if tech(m) in DEC}
    main_cnt = {mats[i].name: n for i, n in cnt.items()}
    for n, dist, ratio, dmin in LODS:
        col = seut_col(sc, 'lod', n, main); col.seut.lod_distance = dist
        shell, whole = bm.copy(), bm.copy()
        bmesh.ops.delete(shell, geom=[f for f in shell.faces if f.material_index in keep], context='FACES')
        drop = [f for f in whole.faces if f.material_index not in keep]
        if dmin:
            drop += [f for g in islands([f for f in whole.faces if f.material_index in dec_i]) if across(g) < dmin for f in g]
        bmesh.ops.delete(whole, geom=drop, context='FACES')
        nshell = len(shell.faces); had = {f.material_index for f in shell.faces}
        me = decimate(to_mesh(shell, mats, 'TMP_shell'), ratio, sc)
        gone = had - {p.material_index for p in me.polygons}
        if gone:                                         # a material wiped out: decimate again with it protected
            bpy.data.meshes.remove(me); me = decimate(to_mesh(shell, mats, 'TMP_shell'), ratio, sc, gone)
            print('  LOD%d: protected %s' % (n, [mats[i].name for i in gone]))
        shell.free(); nshell_out = len(me.polygons)
        out = bmesh.new(); out.from_mesh(me); bpy.data.meshes.remove(me)
        tmp = to_mesh(whole, mats, 'TMP_whole'); whole.free(); out.from_mesh(tmp); bpy.data.meshes.remove(tmp)
        nlost = drop_stranded(out, dec_i); nlift = lift_low(out, dec_i)
        for f in out.faces: f.smooth = True
        for e in out.edges:
            if len(e.link_faces) != 2 or e.calc_face_angle(0.0) > SHARP: e.smooth = False
        name = '%s_LOD%d' % (sub, n)
        old = bpy.data.objects.get(name)
        if old is not None:
            om = old.data; bpy.data.objects.remove(old)
            if om.users == 0: bpy.data.meshes.remove(om)
        me = to_mesh(out, mats, name); out.free()
        a = me.attributes['cn']; fl = [0.0] * (3 * len(me.loops)); a.data.foreach_get('vector', fl); ns = [None] * len(me.loops); bad = 0
        for p in me.polygons:                  # Main's shading normals, carried through the decimation
            for li in p.loop_indices:
                v = Vector(fl[3 * li:3 * li + 3])
                if v.length < 0.5 or v.normalized().dot(p.normal) < 0.2: v = p.normal.copy(); bad += 1
                ns[li] = v.normalized()
        me.attributes.remove(a); me.normals_split_custom_set(ns)
        ob = bpy.data.objects.new(name, me); col.objects.link(ob)
        got = Counter(me.materials[p.material_index].name for p in me.polygons)
        lost = [k for k in main_cnt if k not in got and not (dmin and tech(bpy.data.materials.get(k)) in DEC)]
        print('%s LOD%d at %d m: %d faces (decimated %d -> %d), stranded decal faces dropped %d, lifted %d, materials missing: %s, normals off Main %d of %d' % (
              sub, n, dist, len(me.polygons), nshell, nshell_out, nlost, nlift, lost or 'none', bad, len(ns)))
    bm.free()


win = bpy.context.window_manager.windows[0]; s0 = win.scene
try:
    for sn in SCENES:
        win.scene = bpy.data.scenes[sn]
        with bpy.context.temp_override(window=win, scene=win.scene, view_layer=win.scene.view_layers[0]):
            build(win.scene)
finally:
    win.scene = s0
