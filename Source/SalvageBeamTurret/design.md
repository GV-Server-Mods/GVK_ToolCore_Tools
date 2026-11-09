# Salvage Beam Turret model: design document

Status: style pass, revision 3, agreed with the owner (2026-11-07); being built. Checkpoint 2 (the kiosk) was
refined over three critic rounds at the owner's request (2026-11-07: "keep making it closer to the concept
art"); its as-built sizes are in "Kiosk as built" below. Checkpoint 3 (the top) was built from a sketched layout
the owner picked, with one critic round (2026-11-07), then its latch pads were formed round latch decals and its
grooves became seam lines on chrome plates with darker grey gaps (checkpoints 3b to 3e, 2026-11-07); see "Top as
built". Checkpoint 5 (2026-11-08) gave the base a trim ring with two ears round the canister's foot and
reworked the crate-top corners; see "Base ring and crate top as built". Round 5b (2026-11-08, after the owner's
first in-game look) replaced the four quarter plates and their latch pads with one full raised ring, put the side
signs on both sides, painted the antenna sleeve and evened out the side plates' reflections; see "Top as built".
Round 6 (2026-11-08) put the dome and the antenna on the left-right axis, laid latches and vents on the ring, painted
the hub with a dark gap like the outer one, lined the lip bolts up with the front, gave the foot the lip's bevel and
made the base trim ring plain dark grey.
Source: `GVK_SalvagerTurret.blend` in this folder.

## References (`art/`)

| File | What it is | Used for |
|---|---|---|
| `game-ref-lowres-1.png`, `game-ref-lowres-2.png` | The Deserts of Kharak canister in game (owner, 2026-11-07: "better artwork") | The look to match |
| `concept-detail-2.png` | Owner's second AI concept | The top design and the side decals (owner, 2026-11-07). It lacks the small dome on top, which stays |
| `concept-detail.png` | Owner's first AI concept made from the game art | The chrome angled beam kiosk, the chrome modules and the seams that wrap round the barrel (owner, 2026-11-07). Not its exposed wires and gears ("a few too many wires and gears") |
| `concept-sheet.png` | Owner's earlier concept sheet (front, side, top, 3/4) | Overall layout only |
| `game-ref-far.png`, `game-ref-near.png` | Earlier in-game shots | Overall layout only |
| `style-board-1-overall.png`, `style-board-2-details.png` | Revision 1 comparison boards (concept sheet beside the model) | History |
| `checkpoint-1.png`, `checkpoint-2.png`, `checkpoint-2b.png`, `checkpoint-2c.png`, `checkpoint-2d.png` | Checkpoint renders; 2b is the kiosk after the critic rounds, 2c the thin curved version, 2d the rounded, dipped surround with even gaps, each beside concept 2 | History |
| `seam-proposal-side.png`, `top-proposal.png`, `top-proposal-2.png`, `groove-sketch-top.png`, `panel-sketch-top.png` | Layouts sketched over the model for the owner's pick: the seams, the first top layout (turned down), the two even top layouts (A picked), the top's grooves as seam lines (built as sketched), and three panel shapes round the dome and the antenna (B picked, then A) | History |
| `latch-sheet.png`, `latch-sheet-2.png` | Contact sheets of latch decals for the top's pads | History |
| `latch-sheet-3.png`, `latch-sheet-4.png` | Latch decals that could sit flat on the ring top: six `Atlas3_Chrome` pieces beside the old `Decals` 28 buckle, then 25 (owner, 2026-11-08: "show me more options"): nine more `Atlas3_Chrome` pieces, the six again, and dark versions (`Atlas3_Darker`, `PanelingDarker`, `ButtonsAtlas_Darker`) for contrast on the chrome | C32 of sheet 4, built front and back on the ring (owner, 2026-11-08) |
| `hub-gap-options.png` | Three plan layouts for a dark gap between the ring and the painted hub | C picked: the ring moves out, 45 mm gaps both sides (owner, 2026-11-08) |
| `checkpoint-4e.png`, `material-options.png`, `checkpoint-4f.png`, `checkpoint-4f-top.png` | The canister after the height cut; the chrome parts in `Chrome`, `Metal_Shiny` and `BlackMetal` (owner, 2026-11-08: "Metal_Shiny"); the canister in `Metal_Shiny`, from the front and from above. Blender's grey backdrop gives the metals nothing to reflect, so gloss barely shows | History |
| `checkpoint-4g.png` | Round 4g: modules with a rivet in each corner, and full-width middle plates left blank but for their corner rivets | History |
| `checkpoint-5.png` | Checkpoint 5 as built: the trim ring and ears, the crate-top corners, the neck, the black deck, the dark dome and antenna bases, the bore step's bevel and half seam, the glow's half seam | History; the crate-top corners are still as shown |
| `checkpoint-5b.png` | Round 5b: the full ring with the dome and the antenna standing on it and the painted sleeve, the signs on both sides, the side plates' even reflections | History |
| `checkpoint-6.png` | Round 6: the top from above and from the front, the new foot, the plain trim ring | Current for the top and the trim ring |
| `checkpoint-7.png` | Round 7: the crate's bevels before and after, a name plate, the seam split at the bay's corners, the red triangle and the dark shaft | Current for the crate, the bay seams and the foot |
| `foot-proposal.png`, `height-mock.png` | The canister foot as built (F0, kept) beside two mock-ups under concept 2's foot; two ways to make the canister about 15% shorter (owner, 2026-11-08), mocked by squashing a copy, so their decals look squashed | History |
| `checkpoint-2e.png` to `checkpoint-2g.png`, `checkpoint-3.png`, `checkpoint-3b.png` to `checkpoint-3i.png`, `whip-options.png` | Later kiosk rounds; the top as built beside concept 2's top, with its latch decals, with the deck and seam lines, with the strip panels, with straight ends and darker gaps, and with darker lines centred on the plate edges and seams round the latch pads, with the deck darker again and the ring on the lip's foot, and with seams round the dome and antenna feet and the bay dark too; four antenna whip colourings, and the black whip as built | History |

## Block

| Item | Value |
|---|---|
| Grid and size | Large, 1 x 4 x 1 cells, `ModelOffset` Y -1.25 |
| Base (main scene) | Bottom cell: kitbashed vanilla one-cell cargo container frame, 5 conveyor ports (4 sides and the bottom), a keypad beside each; a trim ring with two ears on its top, round the canister's foot (child object `GVK_SalvagerTurret_Ring`) |
| Azimuth subpart | The canister: 2.24 m wide, 3.97 m tall above the base, antenna up to 6.95 m, 0.55 m inside the block's top (4.67 m and 7.65 m before the height cut, 2026-11-08) |
| Elevation subpart | 1 cm placeholder 2.085 m up the canister (2.43 before the height cut), at the glow strip's centre, carries the beam emitter 1.25 m forward of the axis |

Owner: keep the dimensions and the 5 ports, and make the fine details match the art. The canister was later made
0.70 m shorter (owner, 2026-11-08: "shorten the height of the canister about 15%"); the block stays 4 cells. The emissive strip is
not blue in game, which is fine (owner, 2026-11-07). The game colours the `Emissive` material by block state.

The beam starts on the front face and moves up and down the front centre line as the turret elevates (1.46 to
3.34 m up; 1.8 to 3.7 m before the height cut), so the glow strip stays centred on the front: the beam comes out of it.

## Surface by surface

Heights are measured from the canister's foot (the top of the base cell). "Paint" is `PaintedMetal_Colorable`
(takes the player's colour and skin), "dark" is `PaintedMetal_VeryDark` (it was `PaintedMetal_Darker` until 2026-11-07), "chrome" is `Metal_Shiny` (owner, 2026-11-08: "Metal_Shiny" of `art/material-options.png`; it was `Chrome`, whose
gloss is 38% against `Metal_Shiny`'s 87%, so it read as satin metal). Seams are
`PanelingColorable` decals.

| Surface | Now | Proposal |
|---|---|---|
| Seams | 3 raised dark scratched strips (left, right, back, full height) | Delete the 3 strips. Seam decals: a ring round the barrel under the top lip, one above the foot, and the kiosk bay outline, which steps out with 45 degree corners near its top and bottom (concept 2), joined to the rings with mitred joins |
| Diagonal stripes | 8 raised dark plates, 4 on the front face (2 high, 2 low, either side of the kiosk) and 4 on the back, each with 2 round end caps | Keep only the 4 on the front face (owner, 2026-11-07); delete the 4 on the back and all 16 caps. Set flush into the wall, light grey (`Metal_Dull`) with angled ends, as in the art |
| Beam kiosk | Dark slab 1.12 m wide (0.54 to 4.32 m) with a light metal plate stuck on it, glow strip 0.11 m wide in a 0.22 m dark frame | A bay cut into the wall where the slab is. In it a chrome housing whose top and bottom ends angle back into the wall, its frame split into segments, a small plate on the angled top (concept 2). Glow strip about 0.15 m wide in a bevelled chrome frame, same height, centred |
| Chrome modules | None | 4: a high one and a low one on each side of the housing, each about 0.25 x 0.3 m with a dark slot, and a chrome plate between each pair (owner, 2026-11-07) |
| Side box | Box on the back left: high-voltage sign, red button, yellow frame, metal plate | Delete. It has no detector, so nothing in game uses it |
| Signs | None on the canister | As in concept 2, at Keen's sizes: a small text warning plate high on the left of the bay, an orange warning plate low on the left with a triangle sign under it, and a small plate high on the right of the bay. Picked from a contact sheet |
| Bolts | None on the canister | Bolt decals beside the bay edge, high, middle and low on each side (concept 2) |
| Top lip | Scratched band under a plain edge | Thick painted lip with a rounded edge, the upper ring seam under it, 8 bolts round its top |
| Top inside | Dark disc with a light metal vent disc cut by 12 radial slots | Concept 2's top: a recessed chrome plate with a ring groove at its edge, 4 raised quarter plates with gaps between them and a small latch block on each, a raised central ring and a bore with a dark lens in the middle. Modelled, since the art shows real steps |
| Dome | Painted dome r 0.165 m | Keep where it is (owner, 2026-11-07: "I want to keep that dome on top") |
| Antenna | Dark mast on a dark pad with a yellow hex collar | Keep its position. Chrome mast from a small chrome boss on the plate, red cap (`PaintedMetal_Red`) on the tip (concept 2) |
| Canister foot | Dark collar to 0.40 m, then a yellow band 0.44 to 0.52 m | Yellow band to paint, with the lower ring seam above it. The tapered dark collar stays (owner, 2026-11-08: "F0" of `art/foot-proposal.png`, over a straight wall on the base's ring and a short dark chamfer) |
| Base frame | Vanilla cargo container frame, vanilla finish | Keep |
| Name plates | "SALVAGER TURRET" plates above each port, 3.6 cm out of the cell | Keep, proud of the cell as Keen's keypad frames are, reading "SALVAGE BEAM TURRET" (owner, 2026-11-08: "I kinda liked that panel with the text on it"; "Proud, like vanilla"). Deleted in round 5, back in round 7 |
| Keypads | 5, one beside each port, stuck on the face, 2.3 cm out of the cell | Keep (they hold the terminal detectors), each set flat into a fitted pocket so it sits inside the cell |

Not taken from the art: the exposed wires and the gear ring (owner), the round base plate (the cargo base and
its 5 ports stay), and revision 1's red indicator lamp (the old concept sheet only).

### Kiosk as built (checkpoint 2, after the critic rounds)

Replaces the sizes in the kiosk, module and stripe rows above. Built by `kiosk_build.py` in this folder (run
inside the open .blend; it rebuilds the canister from the kept `AZ_base_nokiosk` mesh), so any size changes in
its parameter block. x is across the front, measured from the front centre line. Heights are after the height
cut (round 4e): `H_CUT` and `BODY_Z` set it, and step 0 remaps the base mesh.

| Part | Size |
|---|---|
| Bay | 39.375 degrees each side of the front (x ±0.71), edges at z 0.55 and 3.62; a recess 1 cm deep that follows the barrel's facets, its top and bottom ends the old grooves' 5 mm chamfers, its sides square steps; `PaintedMetal_VeryDark`, both end chamfers included (owner, 2026-11-07: "Bay VeryDark too"; the top chamfer had been the wall's paint, the rest `PaintedMetal_Darker`). The base mesh's cut ring grooves are filled outside the bay (owner, 2026-11-07: "better as decal grooves"); seam decals mark the rings |
| Seams | `Atlas4_Colorable` piece 3 (Keen's newer panel line), 20 mm wide, 1.5 mm off the wall, cut at the facet edges so each piece lies flat. A ring at each old groove, its centre line on the bay's bottom and top edges (z 0.55 and 3.62), split at the bay's corners (owner, 2026-11-08: "half of it followed the perimeter of the cutout for the kiosk"): the half away from the bay runs on across the bay's edge, the half towards it turns along the bay's side edge into the other ring, so a half seam outlines the bay and each ring is whole from the bay's corners round the back (round 7; before, the band edges were level with the bay's ends, centre lines z 0.56 and 3.61); over the middle of each side panel it steps up 7 cm at 45 degrees, the top ring 0.15 m and the bottom ring 0.30 m in from each panel end. A vertical seam each side at 140.6 degrees (as far from the back as the bay edge is from the front), between the rings, with pointed T-ends 2.5 mm off the wall. Laid out from the concept side view (owner's pick of `art/seam-proposal-side.png`, 2026-11-07). Groove sides: the bottom ring V1 up, the top ring V1 down (its mirror, so the side half runs on unbroken with V1 away from the bay), vertical seams V1 towards the back. Pieces under 1 sq mm, where a facet edge falls just past a step corner, are dropped. A loose painted band 2.5 mm off the wall under the bay, joined to nothing, is removed in step 1 (round 7 audit) |
| Gaps | One gap, 27 mm measured along the surface, between the bay edge and every part and between the parts (owner, 2026-11-07: equal gaps, then a third smaller than the first 4 cm). The bay's top and bottom edges are at z 0.55 and 3.62 |
| Beam surround | Chrome truncated pyramid on a plinth, top and bottom level with the modules (owner, 2026-11-07). The plinth is as thick as the plates, bay floor to 25 mm proud of the wall, its walls along the facet normals 0.48 m apart on the wall (so the gap to the plates stays 27 mm), z 0.577 to 3.593; the pyramid's slopes start on its top, level with the plate faces (owner, 2026-11-08: "add that same thickness to the back of the beam surround, then the pyramid angles start level with the side plates"). Front face 0.39 m wide (55 mm of rim round the glow), z 0.777 to 3.393, 1.232 m from the axis (0.112 m proud of the wall; front corners at r 1.247, the most the 1.25 m cell edge allows); side slopes 24 degrees off the wall normal, ends 0.20 m tall at 23.5 degrees to the wall (owner, 2026-11-07: "look a little thicker"; it was 0.35 m and 1.22 m, with 29 degree ends from the bay floor). Slope corners rounded (30 mm bevel, 6 segments), front rim bevelled 3 mm. The front face dips 30 mm over its middle third (z 1.649 to 2.521) with 45 degree ramps, as if milled across; the side slopes stay one flat plane |
| Glow strip | 0.28 m wide, z 0.887 to 3.283, rounded corners r 0.05; one flat face 75 mm behind the outer face (45 mm behind the dipped part), so it does not follow the dip (owner, 2026-11-07: flat, then a few cm deeper), in a straight-walled slot with a 5 mm chamfer at its edge. UVs on the scan-line panel in the atlas's top half (owner's pick, 2026-11-07), lines running across the strip: the panel's full height (v 0.5 to 1.0) twice over the strip, joined at z 2.085, so 128 lines about 19 mm apart (24 mm before the height cut squeezed the strip 17% along its length) (owner, 2026-11-07: "maximize the height of the atlas and make it look more dense"); u 0.085 to 0.27, 677 pixels per metre across and 855 along (an even 677 both ways before the height cut). The panel's line breaks stand in three columns (u 0.12, 0.18 and 0.23); this range puts the middle one on the strip's centre line (owner, 2026-11-08: "moved over a little so the breaks in the white lines are centered"; it was u 0.02 to 0.205, the breaks 9 cm to the left). The front face round the slot is zipped from its rim to the slot's lip by each loop's angle on its own half-width and half-height; plain angles round the glow centre had left a front triangle over each top corner of the glow (owner, 2026-11-08: the "messed up texture error"). The atlas is 1024 x 2048, so u per metre is twice v, as vanilla maps `Emissive` (Beacon about 305, Conveyor Sorter about 450 px/m, read from the SDK models). The panel's first and last rows match, so the join does not show; the first squeeze onto a small patch looked stretched (owner, 2026-11-07). A half seam runs round the glow where the slot walls meet it (owner, 2026-11-08: "a half very dark seam decal all the way around the emissive ... help it blend in better than the hard physical edge"): `Atlas4_VeryDark` piece 3, centred on the walls' foot with only its 10 mm on the glow laid, 1.5 mm off it, V1 towards the wall (step 6g of `kiosk_build.py`). Whether the game draws the glow through the decal is not yet seen in game |
| Modules | 2 per side, chrome shells 35 mm thick that follow the barrel's curve (back on the bay floor, front 25 mm proud of the wall; owner, 2026-11-07: "look a little thicker", they were 12 mm and 2 mm proud), x 0.266 to 0.689, z 0.577 to 1.352 and 2.818 to 3.593, rounded corners r 0.03, plain faces (the earlier 3 mm face inset was removed, owner, 2026-11-07), edges bevelled 8 mm (was 3) |
| Plates | 1 per side between the modules, same 35 mm curved shell, z 1.379 to 2.791, full width (x 0.266 to 0.689) with the modules' r 0.03 corners (owner, 2026-11-08: "I'm not loving their shape. Maybe we make them full width with the corner plates"; they were waisted I shapes) |
| Slots | 4 decals of `Atlas3_Colorable` piece 20, the tall dark slot (owner's pick, 2026-11-07: "atlast 3 20"), in place of the raised stripes. Each 0.78 x 0.175 m at 45 degrees, 1.5 mm off the wall, cut at the facet edges. Centres 64.6 degrees round from the front, at z 3.155 (upper, falling toward the bay) and z 1.015 (lower, its mirror image about z 2.085), so they span z 0.68 to 3.49 (the upper's offset from the middle scaled with the bay): each 0.15 m further out than the stripes were (owner, 2026-11-07: "move those decals further apart height-wise"). Upper and lower stay identical (owner, 2026-11-07, although they differ in concept 2) |

The bay, housing and glow grew in rounds 2 and 3: both critics put the concept's bay near 39 degrees each side.
Round 3's deep flat bay with slab-like housing and plates "look like fat slabs" (owner, 2026-11-07), so the bay
became a 1 cm curved recess, the plates thin curved shells with the same front-on outlines, and the housing a
truncated pyramid (`art/checkpoint-2c.png`). The next round rounded the surround's corners, levelled it with the
modules, evened and narrowed the gaps, dipped its front face and made the glow flat (`art/checkpoint-2d.png`).
Round 2e set the glow deeper on the scan-line panel and made the stripes dark with pointed ends
(`art/checkpoint-2e.png`). Round 2f filled the cut ring grooves and laid the seam decals from the concept side
view, sketched over the side ortho first (`art/seam-proposal-side.png`, `art/checkpoint-2f.png`). Round 2g
swapped the stripes for slot decals set further apart and tiled the glow over the scan-line panel's full height
twice (`art/checkpoint-2g.png`).
Round 4c (2026-11-08) thickened the plates and the surround and put the surround on a plinth (`art/checkpoint-4c.png`).
Round 4d (2026-11-08) rounded the end seams' corners and added the dark notches (`art/checkpoint-4d.png`).
Round 4e (2026-11-08) made the canister 0.70 m shorter, every band between the foot's dark collar and the lip
shorter in proportion (owner's pick, A of `art/height-mock.png`), the top moved down unchanged and every decal
kept its size; the elevation pivot moved to the glow's new centre and both upper collision cylinders lost 0.70 m
(`art/checkpoint-4e.png`).
Round 4f (2026-11-08) made every chrome part `Metal_Shiny` (the owner asked for "a more reflective and/or chrome
texture"); their decals stay on the `_Chrome` sheets, so seams and bolts read a little duller than the plate
(`art/checkpoint-4f.png`). Blender's grey backdrop shows little of the gloss; the look needs the in-game test.
Round 4g (2026-11-08) put a rivet in each module corner, made the middle plates full-width rounded rectangles and left
them blank but for their own corner rivets (`art/checkpoint-4g.png`).
Largest radius now 1.247 m (surround front corners), 1.249 m with the seam decals on its rim bevel.

The owner's front and side concept views (2026-11-07, shorter than the block) measure, at the canister's 2.24 m
width: surround base about 0.63 m wide (model 0.48), its chrome frame round the glow about 0.41 m (model front
face 0.35), side plates about 0.30 m (model 0.42), glow about 0.27 m (model 0.28). In side view the surround
stands about 0.23 m proud with near-upright ends; the model keeps 0.10 m and 29 degree ends, since the turret's
sweep must stay inside the 1.25 m cell edge.

### Top as built (round 6)

Replaces the sizes in the top lip, top inside, dome and antenna rows above. Built by step 5c of `kiosk_build.py`.
Layout: the owner's pick of `art/top-proposal-2.png`, variant A (2026-11-07). The owner turned down the first
sketch (`art/top-proposal.png`) because the dome and the antenna were handled differently and "the plates cut
unevenly around the dome looks odd". One critic round followed (checkpoint 3: raised quarter plates over a
`Metal_Dull` plate, a chrome rim ring and a dark groove inside the lip). The owner then had the grooves made
decals (2026-11-07: "I think you can do a lot of those grooves as groove decals"; "Build as sketched" for
`art/groove-sketch-top.png`), so the plates, their gaps, the rim ring and the groove became one flat deck with
seam lines along the old outlines (`art/checkpoint-3c.png`). The owner turned down that version's round curves
round the dome and the antenna ("they don't look like panels") and its 4 cm pads ("The latch pads stick out too
far, and make the other seam lines obvious they are not 3D"), and picked the strip panel, B of
`art/panel-sketch-top.png` (`art/checkpoint-3d.png`). The owner then went back to A with the gaps darker
(2026-11-07: "I regret going with B, should have gone with A and have the gaps around the panels and outer edge be
darker grey metal"; `art/checkpoint-3e.png`). The owner then saw a white edge on the dark side of the lines and
asked for them centred on the plate edge, and for seam lines round the latch pads "to add some separation"
(2026-11-07; `art/checkpoint-3f.png`), then for the dark deck "even darker again" and the ring inside the lip
"centered on the interface between the dark grey and the outer rim border" (2026-11-07; `art/checkpoint-3g.png`), and for "the same
seam border treatment around the dome and antenna foot" (2026-11-07; `art/checkpoint-3h.png`).
After the first in-game look the owner had the four quarter plates made one full ring (2026-11-08: "I think I'd
prefer to have that 4 pie cuts just be 1 full ring ... It should mimic the shiny metal plates on the front next to
the beam surround in height, and bevel"), with the dome and the antenna standing on it ("Stand on the ring"); their
latch pads went with them, and the side latches' `Decals` 28 buckles had "lack[ed] texture" in game
(`art/checkpoint-5b.png`). Round 6 (owner, 2026-11-08: "Put the antenna on the canister's left and the dome on the
right rather than how they are rotated around at an angle"; "do C32 front and back, then a slot vent at the 4 45
degree angles"; "The inner ring should be paint matched, but it also needs to have the same black metal gap from the
shiny metal ring to the outside"; layout C of `art/hub-gap-options.png`) is `art/checkpoint-6.png`. Left and right
are seen from the front (+y). r is the radius from the axis, z the height from the foot.

| Part | Size |
|---|---|
| Lip | Painted. On its outer edge a 45 degree bevel 0.10 m across and 0.10 m high (wall up to z 3.82, top from r 1.02), with 4 cm rounds where it meets the wall and the top, so it shades as one soft shoulder; measured on concept 2 (owner, 2026-11-07: "isn't the top of the canister supposed to have a big beveled edge?"; it was a 5 cm round). Flat top at z 3.92 (4.62 before the height cut) from r 1.00 to 0.85, a 1 cm round at its inner edge down to the deck; its paint UVs carry on from the wall below |
| Deck | Flat at z 3.90 (2 cm below the lip), r 0.84 to 0.38, `BlackMetal` where the ring leaves it showing: two 45 mm gaps, r 0.84 to 0.795 and 0.425 to 0.38 (owner, 2026-11-08: "I want the very dark metal on the top to be darker, I guess metal black"). It was `PaintedMetal_VeryDark` (owner, 2026-11-07: "even darker again" than `PaintedMetal_Darker`), which renders mid grey from above, since it is glossy and partly metallic; the owner first kept it over `BlackMetal` and `BlackMattePlastic` (`art/deck-options.png`, 2026-11-07: "Keep D1"). The kiosk bay stays `PaintedMetal_VeryDark` |
| Ring | One chrome (`Metal_Shiny`) ring on the deck, r 0.425 to 0.795 (moved out 40 mm in round 6 for the inner gap), 25 mm tall (top z 3.925) with an 8 mm bevel in 2 segments on both top edges, the side plates' height and bevel. Every edge round it is sharp, as on the plates: its bevel meets the top and the walls at 22.5 degrees, and smooth there it bent the top's normals up to 12 degrees, which warped the chrome's reflection. Its flat top, r 0.433 to 0.787, holds the dome's and the antenna's bases (r 0.445 to 0.775), the open halves of their foot seams and the ring-top decals |
| Seam lines | Piece 3 of Atlas4, 1.5 mm off their surface, the barrel's UV scale, each centred on the foot it marks with only its open half laid (owner, 2026-11-07: ring 1 "centered on the interface between the dark grey and the outer rim border"). On the deck, 20 mm wide in `Atlas4_VeryDark`, the darkest Atlas4 sheet (its flanks are the 64 grey of `PaintedMetal_VeryDark`, a little lighter than the `BlackMetal` deck; there is no black Atlas4): ring 1 on the lip's foot (r 0.84, on the lip's own 64 points, its inner half laid), and a ring on the raised ring's outer foot (r 0.795, its outer half laid); the inner gap the same way, a ring on the raised ring's inner foot (r 0.425, its inner half laid) and one on the hub's foot (r 0.38, its outer half laid). On the ring top, 15 mm wide in `Atlas4_Chrome` so they fit beside the bevel: a seam round the dome's and the antenna's feet (r 0.165, on their own 24 points; owner, 2026-11-07: "the same seam border treatment around the dome and antenna foot"). Groove sides: V1 towards the raised part. The quarter-plate outlines, T-stems and pad seams went with the plates |
| Ring-top decals | `Atlas3_Chrome`, flat on the ring top 1.5 mm up, centred at r 0.61, long side radial, the art's top towards the axis, unmirrored. Front and back (0 and 180 degrees): C32 of `art/latch-sheet-4.png`, the plate with 4 screws and a slot, 212 x 330 mm, as large as the flat top allows (12 mm in from its inner edge, the outer corners 5 mm in; owner, 2026-11-08: "The C32 decals should be larger", it was 160 x 250). At 45, 135, 225 and 315 degrees: piece 20, the side panels' slot vent, 56 x 250 mm. The latch pads (chrome pads round `Atlas3_Chrome` 18 and `Decals` 28 decals) went with the quarter plates in round 5b |
| Hub | Ring r 0.28 to 0.38 in `PaintedMetal_Colorable`, the block's paint (owner, 2026-11-08: "The inner ring should be paint matched"; it was chrome), one texture width round so it meets itself (0.42 to 0.57 UV per metre) and 0.40 up its profile, top z 3.92 level with the lip, a 2.5 cm bezel at 45 degrees on its inner edge; inside it a chrome step at z 3.83 (r 0.17 to 0.28) with a 2 cm bevel at 45 degrees on its inner edge, and a half seam round its outer edge, where the ring's wall rises from it (owner, 2026-11-08: "a bevel on the inside" and "a half very dark seam around the outer edge"): `Atlas4_VeryDark` piece 3 centred on the wall's foot, only the half on the step laid, V1 towards the wall, like ring 1 on the lip's foot |
| Lens | `CameraLens`, r 0.17, edge at z 3.795, domed 3 cm to z 3.825 |
| Dome | On the right, centred at x -0.61 on the left-right axis (moved from x -0.48, y -0.30 in round 6), raised 25 mm onto the ring: painted hemisphere r 0.14; its base ring (r 0.165) stands on the ring top in `PaintedMetal_VeryDark` (owner, 2026-11-08: "the round base of the antenna and the dome to be very dark metal"; it was chrome) |
| Antenna | On the left, centred at x 0.61 (it was at x 0.48, y 0.30), raised 25 mm onto the ring, tip at z 6.975. A base matching the dome's (r 0.165, on the ring top, top z 3.975) in `PaintedMetal_VeryDark` (owner, 2026-11-08, as the dome's; it was chrome); boss r 0.055 to z 4.04, sleeve r 0.032 to z 4.725 and its shoulder in `PaintedMetal_Colorable`, the block's paint (owner, 2026-11-08: "Make the shiny metal segment of the antenna be paint colored"; they were chrome); whip r 0.022 to z 6.705 in `Rubber` (owner, 2026-11-07: A of `art/whip-options.png`, after the all-chrome whip looked "kinda bland"); `PaintedMetal_Red` cap r 0.036 with a rounded tip |

The critic also asked for a 0.3 m antenna sleeve; measured on concept 2, the sleeve is about a quarter of the
mast, as built, so it stayed. The lens renders mottled in EEVEE although its textures are flat (an even dark
colour map and a flat normal map), so it needs a look in game, as do the seam lines on the chrome and dark deck. The deck and its
lines sit 3.9 m from the model origin, where the game rounds vertices to about 3 mm, so the decal snap at export
is what keeps them visible. The canister is now 5,837 faces, 3,056 of them the top (374 seam and ring-top decal
faces), with 84 bolt, sign and module decal faces, 221 seam, bolt and notch faces on the beam surround and 28 round
the glow; it was 5,319 and 2,922 in round 5b, 5,653 and 3,266 with the quarter plates as decal outlines, and 6,554 and 4,286 with them raised. In the EEVEE renders the dark bases' flat tops read lighter than the
black deck, since `PaintedMetal_VeryDark` is glossy and only partly metallic (`art/checkpoint-5.png`).
Shading (smooth pass, 2026-11-07): every canister face is smooth shaded, split at the edges the build marks sharp
and by the object's Smooth by Angle modifier at 35 degrees; the kiosk pieces and the bay floor had been flat shaded.
The side plates' and modules' fronts have custom normals, each corner the exact radial direction, and are split
sharp from their bevels (owner, 2026-11-08: "some warping in the reflections as I look around it"). Their fronts are
ear-clipped into long thin triangles, and the angle-weighted normals at the facet cuts came out uneven; now they
shade as the cylinder they wrap. The normals survive the Smooth by Angle modifier and the export mesh.
The build stages are flat shaded, as Keen's are ("Build stages", below).

### Base ring and crate top as built (checkpoint 5)

Built by `base_ring_build.py` in this folder: round 5 of the ring mock-ups (owner, 2026-11-08: "lets just continue
with this for now") and round 2 of the crate-top corners (owner, 2026-11-08: "Build both"). Run it inside the open
.blend after `kiosk_build.py`. Its first run keeps the base mesh as it was in `BASE_src` (fake user); every run
rebuilds `GVK_SalvagerTurret_Visual` from it and replaces the child object `GVK_SalvagerTurret_Ring`, so a run
always starts clean. Heights here are from the crate top (block z -1.25), the canister's own frame.

| Part | Size |
|---|---|
| Base cell | The +x grab bar (`Metal_Dull`) and the old ring (`PaintedMetal_Darker`) are gone. The raised top plate (±1.03 m) is flush with the corner brackets (owner, 2026-11-08: "a big square plate on top ... needs to all be blended flat"): each bracket's crown is cut at the plate's edge, the part under the plate removed and the rest levelled to the plate top. The box's worn bevels are plain paint (round 7; owner, 2026-11-08: "lots of ugly scratched metal bevels around it"): the `PaintedMetalScratched_Colorable` chamfers round the panels and keypads are `PaintedMetal_Colorable` with their own UVs (1,580 faces), the `PaintedMetalScratched_Darker` ones `PaintedMetal_Darker` (1,040), and the rounded box edges that sat on the `Doodads` atlas's dark arms with their white wear lines (80% or more of their UV area) `PaintedMetal_Darker` (327), both box mapped at 0.40 per metre. The chrome grab bars and the yellow port frames are unchanged. Keen's keypad decals in the port frames are lifted to 1.5 mm (they sat 0.45 to 0.9 mm off). 8,726 faces with the name plates |
| Name plates | The five plates above the ports from the first model (`C:\SE_Assets\TestMod\GVK_SalvagerTurret.blend`, 2026-10-20), kept in the mesh `NAMEPLATE_src` (fake user), in plain `PaintedMetal_Darker` (their bevels were scratched), box mapped at 0.40 per metre. Their faces are 1.269 m out, 1.9 cm out of the cell, as Keen's keypad frames stand 3.6 cm out (owner, 2026-11-08: "Proud, like vanilla"). "SALVAGE BEAM TURRET" in `TextAtlas` letters 80 mm tall, 8 mm apart and 32 mm between words, 1.074 m long, centred on each plate's flat front 1.5 mm off it; upright on the four sides, and on the bottom plate its top away from the port. 1,580 plate faces, 85 letters |
| Ring and ears | One plate in plan: the 64-gon r 1.18 with an ear each side out to x ±1.246 (\|y\| 0.33), filleted where they meet, inside the cell. All `PaintedMetal_Darker`, Keen's plain dark grey, at 0.40 UV per metre (owner, 2026-11-08: the "scratched texture on top ... needs to follow keen style for that grey metal", and the "main bevel looks like it stretches the grey textures vertically too much"; the face was `PaintedMetalScratched_Darker` and the rim `Doodads`, mapped on the brackets' 21 px rolled-edge strip). Flat top at z 0.12, planar UVs, its inner edge stepping down from r 0.964 to a lip at r 0.86, z 0.02. The outer rim is a rolled edge, unrolled for its UVs (U round the ring, rounded to whole tiles so it meets itself, V up the profile), its foot following the crate top (at most 12 mm down); the ears' tips are flat faces, with blocks under them fitted to the bracket ends. Smooth shaded, sharp over 30 degrees, weighted normals. 1,040 faces, 190 of them decals |
| Ring decals | `Atlas3_Darker`, seams `Atlas4_Darker` piece 3, 1.5 mm off. A groove seam at r 0.995 runs round the ring and out along each ear at \|y\| 0.24, over the rolled edge and down its tip face. Front and back: a vent panel framed by seams over the strap handles' edges (75.5, 104.5, 255.5 and 284.5 degrees) with 45-degree legs into the groove, 9 piece 15 slots and 4 bolts on the pitch circle r 1.06. Piece 4 at the four diagonals, 8 bolts round the inner step (r 0.908), square to the radius so each 40 mm head stays on the 44 mm step (round 7; they were turned at random and overhung its edges). The vent seams down the rim end where it meets the crate top; the foot chamfer below is buried in the plate. Each ear: piece 4 with 2 bolts on top; 9 slots, piece 7 and 2 bolts on its tip face |
| Crate-top corners | One `Atlas3_Colorable` piece 29 vent per white corner, its right angle to the box corner and its long side to the ring, turned, never mirrored; 0.311 m. 3 cm from the ring and from the tip of the grey corner, 6 cm from the sides, since the art's corner chamfer is smaller than the bracket's (owner, 2026-11-08: "equal distance from the ring and the box grey corners, just like 3 or 5 cm gap"). No seam round it (owner: "remove that outer edge seam since the corner vent has its own outline") |
| Canister foot | Step 7 of `kiosk_build.py` (round 6; owner, 2026-11-08: "The bottom of the canister should copy the same bevel that is at the top, then be flat on the bottom until it reaches the shaft"): the lip's profile upside down. The wall runs straight down to z 0.287, then the 45 degree bevel 0.10 m across and high with its 4 cm rounds, a flat underside at z 0.17 from r 1.02 in to r 0.80, and a dark `PaintedMetal_Darker` shaft r 0.80 down to z -0.04 inside the ring, its UVs wrapped round it at 0.40 per metre (owner, 2026-11-08: "it should be a dark metal"; it was `Metal_Shiny`). It replaces the base mesh's dark collar (z 0.34 to 0.40), taper and ledge; all of it is in the paint like the lip, its UVs carried on down from the wall |

Collision (round 7): `Collision_Ring`, a convex hull of the ring and ears' plan (42 points, x ±1.2475, y ±1.18) from
the crate top to the ring top (block z -1.25 to -1.13), beside the crate cube and the upper cylinder (r 1.12), which
the ring's lip and ears stuck 6 to 13 cm out of. The name plates and the visual parts past the cell have no collision;
every collision piece stays inside the cell. The canister's cylinder (r 1.12, z 0 to 3.93) still covers the new foot.

## LODs (round 8)

Built by `lod_build.py` in this folder (owner, 2026-11-08: "Work on LODS"). Run it inside the open .blend after
`kiosk_build.py` and `base_ring_build.py`, so the LODs follow every change to Main; each run replaces the LOD objects,
one per `LODn` collection, in the base and the canister scenes.

| LOD | Distance | Base faces | Canister faces | What it keeps |
|---|---|---|---|---|
| Main | | 13,662 | 5,917 | Everything |
| LOD1 | 30 m | 7,170 | 3,888 | The opaque faces decimated to half; every decal |
| LOD2 | 80 m | 2,902 | 1,523 | Opaque faces to a fifth; decals at least 6 cm across (signs, vents, plates, keypads). Seams, bolts and the name-plate text go |
| LOD3 | 200 m | 1,538 | 828 | Opaque faces to a tenth; no decals |

Distances: the vanilla gatling turret switches at 20, 60 and 150 m; this block is 4 cells tall, so LOD3 waits until
200 m, when it is about 10 px tall. The old base LODs sat at 30 and 80 m.

Method: Main's meshes are merged in block space with their modifiers applied, and their opaque faces go through
Decimate Collapse. The glow and screens (the emissive materials, `Terminal`, `Conveyor`) and every material with
under 60 faces (the antenna, small accents) stay whole, so nothing changes colour. Main's own shading normals (the
plates' radial fronts, the ring's weighted normals) are carried through the decimation and set as custom normals,
edges over 30 degrees sharp, so the chrome reflects as on Main. A decal width is twice its area over its outline.

Decals the decimation left hanging are dropped: any sample (the centre, and the corners and edge middles pulled 1 mm
in) with no surface within 2 cm under it, or one within 4 mm over it (canister LOD1: 126 faces of the dark deck seams;
LOD2: 1). Where the shell rose up under a decal, the decal is lifted to 1.5 mm (canister LOD1: 24 faces; base LOD1:
4). The decal snap at export then runs on the LODs as on Main.

A material the decimation wipes out is decimated again with its faces held back (a vertex group at weight 0.6), as
se-dev-seut says never to let a decimate pass delete accent faces: the base's LOD3 lost all 560 of its
`PaintedMetalScratched_Yellow` port-frame faces at first and now keeps 10. Its port slats still read a shade lighter.
The empty BS1 to BS3 and BS1_LOD1 collections that SEUT's collection rebuild added to the canister scene are removed,
since a subpart scene has no build stages. Review sheet: `art/checkpoint-8.png` (Main, LOD1, LOD2 and LOD3, left to right).

## Build stages (round 9)

Built by `bs_build.py` in this folder (owner, 2026-11-08: "Yes, do BS1–BS3", then "why are the build stages not
following the skill's instructions?"), to se-dev-seut's build-stage brief (`block-scenes.md`, "Designing the stages").
The old stages came with the first model (2026-10-20): BS1 was the crate alone, BS2 stopped half way up the canister,
BS3's canister frame was still the old height (0.7 m above the finished canister), each stage only added frame, and
they kept the old ring. Every stage now fills the whole outline, crate, trim ring, canister and antenna, because every
stage uses Main's collision; only the detail grows, and nothing floats.

| Stage | Build % | Faces | What it shows |
|---|---|---|---|
| BS1 | to 33 | 1,298 | Strip frames over the crate (12 cm strips, heavier, as Keen's cargo container stages), the trim ring, the canister and its beam surround; solid: the beams under the crate top, the shaft, the spokes under the canister and its top, the central column, the antenna boss and rod |
| BS2 | to 66 | 1,293 | The crate's panels fill its frame and its five ports appear; the ring is solid; inside the still-framed canister the bay's lower and upper modules, the beam emitter, two drive boxes and the dome appear as plain solids |
| BS3 | to 100 | 830 | The keypads; the canister wall solid except the top and three panels on each side, left open frame so the inside shows; the bay's plate and the solid beam surround |

The load path in each stage: crate, beams under its top (BS1) or its panels, shaft, spokes, column, spokes under the
top, dome and antenna boss. The canister is built in its own frame and turned 180 degrees into block space as SEUT
shows it under `subpart_Azimuth`, so the beam surround faces -Y; that the stages meet the finished turret at that angle
is not checked in game. Canister strips 7 cm, 2 cm deep; one mesh per stage in `Construction`, box UVs at 0.5 per metre
offset from the origin. Review sheet: `art/checkpoint-9.png`.

## Decals

| Surface | Decal | Status |
|---|---|---|
| Canister wall | Panel seams (`Atlas4_Colorable` piece 3) | Built: two stepped rings split at the bay's corners into a half seam round the bay, and two back seams ("Kiosk as built", Seams). Decal snap at export |
| Canister wall, side panels | Slots (`Atlas3_Colorable` piece 20) | Built: 4 ("Kiosk as built", Slots). Decal snap at export |
| Canister wall | Warning signs | Built: 7, the owner's pick of `art/sign-sheet.png` ("A1 B3 C1 D1", 2026-11-07), A1, B3 and C1 on both sides, and the red warning triangle under the beam (round 7), below |
| Canister wall, beside the bay | Bolts (`Atlas3_Colorable` piece 14) | Built: 3 per side, below |
| Top deck and ring | Panel seams (piece 3 of `Atlas4_VeryDark` on the deck, `Atlas4_Chrome` on the ring) | Built: rings on both feet of both dark gaps, and seams round the dome's and the antenna's feet on the ring ("Top as built", Seam lines). Decal snap at export |
| Top, ring | C32 latches and slot vents (`Atlas3_Chrome`) | Built: C32 front and back, piece 20 vents at the four 45-degree angles ("Top as built", Ring-top decals). Decal snap at export |
| Top, hub | Half seam (`Atlas4_VeryDark` piece 3) | Built: round the bore step's outer edge ("Top as built", Hub). Decal snap at export |
| Glow strip | Half seam (`Atlas4_VeryDark` piece 3) | Built: round the glow at the slot walls' foot ("Kiosk as built", Glow strip). Not yet seen in game over the glow |
| Base ring and ears | Slots, panels, bolts and seams (`Atlas3_Darker`, `Atlas4_Darker`) | Built: 68 decals and 40 seam lines ("Base ring and crate top as built"). Decal snap at export |
| Crate-top corners | Corner vents (`Atlas3_Colorable` piece 29) | Built: 4 ("Base ring and crate top as built") |
| Base, name plates | "SALVAGE BEAM TURRET" (`TextAtlas` letters) | Built: on all 5 plates ("Base ring and crate top as built", Name plates). Decal snap at export |
| Top lip | Bolts (`Atlas3_Colorable` piece 14) | Built: 8 round the lip, below |
| Chrome modules | Bolts and a framed dark slot (`Atlas3_Chrome`) | Built: the owner's pick of `art/module-sheet.png` ("M1 + M5", 2026-11-07), below |
| Beam surround | Panel seams (`Atlas4_Chrome` piece 3), bolts (`Atlas3_Chrome` piece 14) and dark notches (`Atlas3_Chrome` piece 20) | Built from the owner's markup of the top-end render (2026-11-08), below. The sketch's rim bolts (`art/surround-proposal.png`) were left out, and its notches moved from the dip ramps to mid height (owner, 2026-11-08). Decal snap at export |

Bolts, signs, module and surround details as built (checkpoints 4b to 4d, steps 6b to 6e of `kiosk_build.py`),
all 1.5 mm off their surface (the surround's segment seams 2.5 mm), with unmirrored UVs:

| Part | Size and place |
|---|---|
| Bolts | `Atlas3_Colorable` piece 14, the round sunken head (owner's pick of `art/bolt-sheet.png`, 2026-11-07), 40 mm, each turned at random (fixed seed). Lip: 8, centred across its flat top (r 0.93, z 3.92) every 45 degrees from the front (owner, 2026-11-08: "radially aligned with the front of the block"; they started at 13 degrees, in line with the dome and the antenna where they were). Bay: 3 per side on the wall one head out from the bay edge (41.4 degrees), at z 3.206, 2.085 and 0.965, the centres of the upper module, the plate and the lower module |
| Signs | Sized and placed as measured on concept 2, text upright (owner, 2026-11-07: Keen's 120-150 mm plates were "microscopic, and dont align with the concept art"). On each side panel at 96 degrees, the same on both sides with the text upright (owner, 2026-11-08: "mirrored on the other side (but text facing the correct direction)"): `Atlas2` 15 DANGER STRONG MAGNETIC FIELD, 300 x 168 mm, 25 mm under the top ring; `Decals` 38 high-voltage triangle, 150 x 126 mm, 25 mm above the bottom ring, with `Atlas2` 6 WARNING TIP OVER HAZARD, 300 x 165 mm, 12 mm above it. On the wall 20 mm above the bay's top edge, over the beam housing (centre 2 degrees round on -x, as in concept 2): `Atlas2` 14 Remote Operated System, 280 x 55 mm. Under the beam, at the front centre on the wall between the bottom ring and the foot's bevel (centre z 0.413): `Atlas2`'s red warning triangle (u 0.465 to 0.534, v 0.354 to 0.414, 142 x 123 px), 150 x 130 mm (owner, 2026-11-08: "a red triangle or something on the canister body", "Front, under the beam") |
| Module details | `Atlas3_Chrome` on each module's face. Four piece 14 bolt heads, 40 mm, one in each corner, one head in from the ends and sides (owner, 2026-11-08: "a rivet in all 4 corners"; there were two at the outer end); piece 38, the wide frame with a dark slot, 260 x 127 mm, centred |
| Plate details | Four piece 14 bolt heads in `Atlas3_Chrome`, one in each corner as on the modules, and nothing else (owner, 2026-11-08: "leave the panel blank except for the rivets"). Three layouts were built and turned down first: a cooling unit (perforated rails, crossbars, a fan grille, louvres and a drain coupling; the grille and the rails were disliked), Atlas1's X with Atlas3 46's dimples inside it ("dumb as hell with the dots INSIDE the X"), and the X between two perforated fields of those dimples |
| Surround seams | 15 mm wide ("a small seam decal", owner, 2026-11-08), each piece draped onto the face under it and mitred where faces meet. Front seam: round the front face, midway across the rim (centre line 23.5 mm in from the flat face's edge, the same at top and bottom), corners r 0.02, following the dip; V1 inwards, towards the panel it outlines, as on the top deck. Segment seams: level with the plate joins (z 1.366 and 2.805), from the plinth's foot over the plinth top, the side slope and the rim bevel to the front seam, ending in a point on its centre line, 1 mm higher so the point draws over it; V1 up like the wall rings. Ends: an open U on each sloped end, its sides 70 mm in from the end's side edges and parallel to them, run on over the crease and down the plinth to the floor, its bottom line 30% of the way up the end, its bottom corners r 0.02 like the front seam's (owner, 2026-11-08: "round the corners of those seams"); V1 inwards |
| Surround bolts | `Atlas3_Chrome` piece 14, 40 mm, turned at random: two per end, inside the U's bottom corners, 30 mm in from its side and bottom centre lines |
| Surround notches | `Atlas3_Chrome` piece 20, the tall dark slot, 14 x 62 mm, upright: one each side on the rim at the surround's mid height (z 2.085, the dipped face), 1 mm out from the glow slot's chamfer (owner, 2026-11-08: "add the notches but at the center height of the beam surround") |

## Build checkpoints

Each gets renders and the owner's yes before the next.

1. Removals and material changes (strips, back stripes, caps, side box, name plates, yellow and scratched bands).
2. Kiosk bay, chrome housing, glow strip, modules and plates.
3. Top: lip, chrome plate, quarter plates, central ring and lens, antenna boss and tip (built, "Top as built").
4. Decals: seams, stripes, signs, bolts, slots (contact sheets first).
5. Base keypad pockets.

## Options (not in the proposal unless the owner asks)

- **Base corners take skins.** The vanilla corners use `Doodads`, which skins such as Battered skip, so they stay
  flat painted beside skinned faces. Moving their painted part to `PaintedMetal_Colorable` fixes it, as on the
  Hurricane.

## Not changing

- Dimensions apart from the canister's height (0.70 m shorter, owner, 2026-11-08), the 5 ports, the base frame.
- Quality pass finding 4 (beam origin inside the hull above about 40 degrees elevation), by the owner's choice
  (2026-11-07). Finding 10 (the canister swept 3.8 cm past the cell sides) went away with the style changes:
  the largest radius is now 1.249 m (the surround's rim with its seam decals).

## Quality pass (2026-11-07)

Done in the .blend: build-stage collision collections and a test collection removed, azimuth rigid bodies
removed, 17 vanilla materials linked from the SEUT library, unused material slots and loose geometry removed,
zero-area UV faces on BS2 and BS3 re-projected, port lips moved 1.3 cm inward into the cell (with their
detectors), side box decals turned to face out. The .blend moved here from `C:\SE_Assets\TestMod` and exports
straight into `Content/Models/Cubes/large/laser_turret/`.

Found: the shipped base model points its LODs at `Models\Cubes\Large\GVK_SalvagerTurret_LOD1` and `_LOD2`,
but the files sit in `...\large\laser_turret\`, so the game has never loaded the base LODs. Re-exporting from
the new export path fixes it.

Still to do after the style changes: azimuth LOD1 and LOD2, the base's LODs and build stages with the new ring,
the collision check, the decal snap (vertex rounding), export of all three scenes, and a check of the LOD paths and
dummies in the new models. Then the owner's in-game test. On hold until the owner's further canister changes
(2026-11-08).

Preview export (2026-11-08, checkpoint 5, owner: "can I see it in game now?"): all three scenes exported into
`laser_turret` and deployed to the local Mods folder, the decals snapped on temporary export meshes (the .blend keeps
its unsnapped meshes; the snap ran with the normal-only modifiers baked in, since `decal_snap.py` skips objects with
modifiers). The base's LODs and build stages in it still show the old ring and grab bar, and the canister has no LODs.
The LOD paths now point at `laser_turret`. SEUT now embeds the collision in each `.mwm`, so the separate
`GVK_SalvagerTurret_Azimuth.hkt.mwm` is gone. SEUT 1.2.1 crashed on the first try at `prepare_mat_for_export` (a stray
local asset copy of `Metal_Shiny` beside the linked one; the copy is removed). SEUT warns that `PaintedMetal_Red`,
the antenna cap, is a DLC material (W012), which Keen requires to be DLC-locked.

Second preview export (2026-11-08, round 5b): the canister scene only, the same way (its decals snapped, 96 off
the grid before and none after), built and deployed; the deployed `GVK_SalvagerTurret_Azimuth.mwm` matches. The
canister is a subpart, so the game needs a full restart to show it.

Third preview export (2026-11-08, round 6): the base and the canister scenes, the same way (the canister's decals
108 off the grid before and none after, the base's 24 and none; the trim ring's 3 stay off, as in every export, against
6 whose design gap the grid cannot hold), built and deployed; both deployed `.mwm` files match. SEUT links its preview
copy of the canister (`GVK_SalvagerTurret_Azimuth_Visual.001 (L)`, under the base's `subpart_Azimuth`, 1.25 m lower and
turned 180 degrees) into whichever scene is active when it refreshes the instances, so it showed up in the canister
scene as a second canister; it is unlinked there again after each export and is never exported with the canister.

Fourth preview export (2026-11-08, round 7): all three scenes, the same way, after a decal audit of every decal face
on the canister, the base and the ring (a ray cast from each face's centre and corners to the surface under it):
the canister's decals 108 off the grid before the snap and none after, the base's 36 and none, the ring's none (its
inner-step bolts, squared to the radius, no longer overhang). Two canister faces still read 3.5 mm at one end: the
side half seam's centre line lies on the bay's edge by design, so its corner ray grazes the lip. Built and deployed;
all eight deployed `.mwm` files match. The subparts and the new collision piece need a full game restart.

Fifth preview export (2026-11-08, round 8, the LODs): the base and the canister scenes, the same way, now with the
LOD collections in the decal snap (base Main 36 off the grid before and none after, LOD1 29 and none; canister Main
108 and none, LOD1 108 and none; LOD2 none). The Elevation scene did not change and was not exported. Both Main
models read their LODs at 30, 80 and 200 m from `Models\Cubes\large\laser_turret\<name>_LOD1` to `_LOD3`, so the
quality pass's broken base LOD paths are fixed. Built and deployed; all twelve deployed `.mwm` files match. The
canister is a subpart, so a full game restart is needed.

Sixth preview export (2026-11-08, round 9, the build stages): the base scene only, the same way; the new BS1 to BS3
written beside it, and the SBC's three `BuildProgressModels` (to 33, 66 and 100%) already point at them. Built and
deployed; all twelve deployed `.mwm` files match. Seen in game after this export (owner, 2026-11-08: "ok turret
looks great, works great"); a weld-up or grind-down through the stages was not mentioned.
