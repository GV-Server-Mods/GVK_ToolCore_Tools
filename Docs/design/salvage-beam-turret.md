---
title: Heavy Salvage Beam Turret
covers:
  - ModScripts/GVK_SalvageTurretClearance.cs
  - Content/Data/CubeBlocks_GVK_Tools.sbc
  - Content/Data/GVK_EntityComponents.sbc
---

# Heavy Salvage Beam Turret

The design document for the turret and its anti-bunker clearance rule. The clearance rule was reworked on 2026-11-07 ([GVK-Settings#750](https://github.com/GV-Server-Mods/GVK-Settings/issues/750)): 8 sight lanes around the turret's moving parts and a 5x5x5 sky above them replace the 7x7x4 workspace and 7x7x7 sky, and every grid counts except other factions' (owner, 2026-11-07). The lanes and the sky are measured from the turret's bottom cell, and that cell, the base, is deliberately not checked (see Model Bounding Box).

## 1. Design Intent & Background

In a hardcore desert PvPvE environment like Kharak, high-performance salvage and repair capabilities are critical for mobile rovers and frontline FOBs. The Salvage Beam Turret fills this role by projecting a high-energy directional beam capable of welding blueprints and deconstructing derelict wrecks from up to 250 meters away (150 m until 2026-11-07).

### The Engineering Challenge: "The Bunker Exploit"
In Space Engineers PvP, high-value turrets present a constant temptation for "bunkering":
* Players embed turrets inside recessed armor wells, sunken hull pockets, or beneath overhead armor overhangs to achieve 90%+ armor coverage while shooting through narrow firing slits.
* Traditionally, servers combat this with written server rules (*"Turrets must have open lines of sight"*), resulting in endless admin tickets, subjective screenshot arguments, and refereeing headaches.

### The GVK Governance Philosophy: Zero "Trust Me Bro™" Rules
In accordance with GVK core engineering standards, **we never enforce server balance through honor systems or written rulebooks.** If a mechanical constraint exists, it must be enforced programmatically:
* The turret physically monitors its own surroundings.
* If a player illegally armors or recesses the mount, the turret **instantly shuts down**, explains the exact layer violation in the Control Panel, and renders a holographic wireframe showing the player how to fix their build.

---

## 2. Clearance Governance Architecture: Sight Lanes and a Clear Sky

The turret checks two things, both centred on it and both starting on top of its base, the cargo-container-like bottom cell, which is not checked: 8 sight lanes out to the edge of a $5\times 5$ area around its moving parts, and a $5\times 5\times 5$ sky above them (8 large blocks / 20 meters tall in all):

```
       ▲ +22.5m (Y=8)
       │  ┌───────────────────────┐
       │  │                       │
       │  │   SKY                 │
       │  │    (5x5x5 Blocks)     │
       │  │                       │
       │  │ RULE: 100% CLEAR SKY  │
       │  │ (Zero blocks allowed) │
       │  │                       │
+10.0m │  ├───────────────────────┤  ▲ Boundary (Y=4: top of the 4-block turret)
       │  │ ──── sight lanes ──── │  Y=3
       │  │ ──── 8 directions ─── │  Y=2   RULE: at least 5 of 8 lanes open
       │  │ ──── at 3 heights ─── │  Y=1
 +2.5m │  ├───────────────────────┤  ▲ Top of the base (Y=1)
       │  │  base: not checked    │
  0.0m ┴──┴───────────────────────┴── Deck Surface (Y=0)
          ◄────── 12.5m ────────►
               (5 Blocks)
```

Seen from above, the lanes run from the turret to the edge of the $5\times 5$ area:

```
   FL     F     FR
     ╲    │    ╱
      ╲   │   ╱
  L ───── T ───── R
      ╱   │   ╲
     ╱    │    ╲
   BL     B     BR
```

### The base layer ($Y=0$): not checked
* The turret's bottom cell is its fixed base. The layer it sits in, 5x5 around it at deck level, is left out, so the base can be built into a deck, cab or hull.

### Sight lanes ($Y=1 \dots 3$)
* **Lanes:** 8 directions from the turret, front, back, both sides and the 4 diagonals, each out to the edge of the $5\times 5$ area ($5\text{ m}$ straight, $7.1\text{ m}$ diagonal). "Front" is the block's own front.
* **Rays:** each lane is a physics ray at each of the turret's 3 layers above the base, through the middle of the layer. A lane is open only if all 3 are clear.
* **Rule:** at least **5 of the 8 lanes** must be open.
* **What it allows and stops:**
  * Flat panels, catwalks and floor plates on the deck around the turret sit below the rays and pass (if their collision is thin, see What counts as blocked).
  * A column on each of the turret's 4 faces hides it from the sides and fails. Columns on 2 neighbouring faces also close the diagonal between them (they meet corner to corner), so 3 face columns close 5 lanes and fail; 2 pass.
  * A wall on one side blocks 3 lanes (that side and its 2 diagonals) and passes; walls on 2 sides fail.
  * Conveyors, lights or part of a rover cab beside the turret pass as long as 5 lanes stay open.
* **Doors count as closed:** a door in a cell a ray crosses blocks it, open or shut (owner request that the rule not be exploitable, 2026-11-07). A door raises no event when it opens or shuts, so otherwise a player could shut doors around a working turret and keep it running until the next check.
* **Diagonals:** a diagonal passes exactly through the corner where its 2 side cells meet. A block on one side leaves it open; a block on the diagonal, or 2 blocks meeting corner to corner across it, closes it. The script casts 2 rays a few centimetres either side of the line to get this answer every time.
* **History:** a 5x5x3 workspace (at most 18 of 72 cells blocked) was used for part of 2026-11-07. It counted a thin floor panel as a full block, yet passed 4 columns on the turret's faces (12 cells), so the owner replaced it with these sight lanes (owner, 2026-11-07).

### The Overhead Sky ($Y=4 \dots 8$)
* **Footprint & Height:** $5\times 5$ large grid blocks, 5 blocks tall ($12.5\text{m}$), directly above the lanes.
* **Rule:** **$100\%$ Clear Sky** (0 of its 125 cells blocked), checked cell by cell.
* **Rationale:**
  * Turrets must have an unobstructed line of sight upward.
  * Prevents armored "caps," ceiling overhangs, bridges, blast skirts or bunker roofs over the turret.
* **History:** until 2026-11-07 the workspace was $7\times 7\times 4$ (48 of 193 cells, earlier 12 per layer) with a $7\times 7\times 7$ sky above it. A box tight around the turret passed it, so the owner chose a smaller zone instead (owner, 2026-11-07).

### What counts as blocked (lanes and sky)
* **The turret's own grid:** in the sky, any block in the cell. In a lane, any block whose collision the ray hits; the turret itself and its moving parts never count.
* **Other grids:** the same, for any grid that is a rotor, hinge, piston or suspension subgrid of the turret's grid, or belongs to the turret's owner or a member of the owner's faction (owner, 2026-11-07). Small grids included. So a roof on a hinge, a garage or hangar that is its own grid, or a shell docked by connector or landing gear all count. A grid belongs to its first big owner; an armor-only grid has none, so it belongs to whoever built it (the first block the grid lists, cached per grid).
* **Doors** in a lane count as closed (see Sight lanes); in the sky every block counts anyway.
* **Thin blocks in a lane** [SOFT]: the ray hits a block's collision, not its cell, so a panel the ray passes over does not count. Some decorative blocks may have full-cell collision; the in-game test checks this.
* **Terrain does not count.** A voxel check was tried on 2026-11-07 and removed the same day.
* **Not counted:** grids of players outside the owner's faction, so another faction can't switch a turret off by parking next to it (they could already weld a block onto its grid); NPC grids and grids built by nobody (ships, bases, wrecks, loose debris), since nobody builds a bunker from an NPC grid and a passing NPC ship or a wreck piece in a lane shouldn't switch a turret off (owner, 2026-11-07); and projections. Allies in another faction count as outside. Until 2026-11-07 only the turret's grid and its mechanical subgrids counted, so a separate grid could roof or wall the turret; the owner chose this rule over counting every grid the rays hit, which would let an enemy rover or a passing player switch it off (owner, 2026-11-07).
* **"Up"** is the block's own up. A turret mounted sideways or upside down checks a sideways or downward sky.

### Taller block
The block is $1\times 4\times 1$ since 2026-11-07, so it covers the antenna, which reaches about 10.15 m above the deck (15 cm sticks out into the sky zone; that is the turret's own model, not a block, so it does not count). As $1\times 3\times 1$ the antenna sat in the cell above the block, where a player might have placed a block (owner, 2026-11-07). The script reads the block's height (`Size` Y) and centre cell from its definition: the lanes run at every layer between the base and the sky (3 for this block), and a block taller than 4 pushes the sky up to start right above it. A taller `Size` moves the model up by half a cell per extra cell, so it needs a matching negative `ModelOffset` Y (see Model Bounding Box).

---

## 3. Performance & Sim-Speed Optimization

With hundreds of blocks ticking on a multiplayer server, keeping sim-speed at 60 TPS requires strict performance hygiene:

1. **Zero Garbage Collection (GC) in Sim Ticks:**
   * The 125 sky cell offsets are built once, from the block definition's height, into a static array (`BuildLayout()`).
   * No `new List`, LINQ queries, or closures are allocated during clearance evaluations. The only allocation is the game's own: the ModAPI hands back each ray hit as an `IHitInfo`, a few small objects per ray.
   * The occupancy grid, the ray hit list and the grid/block lists are static and reused by every turret (all checks run on the game thread, as `CastRay` requires).

2. **Event-Driven Checks plus a 60-second Safety Check:**
   * A check runs when something that could change the result happens, and otherwise once a minute (it was every 10 seconds until 2026-11-07; owner, 2026-11-07).
   * **Blocks added to or removed from the turret's grid** (`OnBlockAdded`, `OnBlockRemoved`): a check at the next update (within ~1.7 s) and a second one ~1.7 s later, because a new or removed block's collision can lag behind the event [SOFT].
   * **Split or merge:** a merge moves the turret onto the other grid with a new position and orientation and closes the old grid, whose events stop [HARD] (`MyCubeGrid.MoveBlocksAndClose`). Every update the turret checks whether its grid changed and, if so, hooks the new grid, recomputes its bottom cell and orientation, and re-checks. Before 2026-11-07 a merged turret kept its old position, so its zones could sit in the wrong place.
   * **Grid watch:** subgrids and separate grids raise no events on the turret's grid. Every update (~1.7 s) the turret finds the counted grids reaching into its area (a bounds query and a group lookup) and compares them with what the last check saw: how many, their block count, and their position and facing relative to its grid (a change of more than 10 cm or about 0.6 degrees). A change triggers a check, so a hinged roof, a piston wall or a friendly ship parked over it is caught within ~1.7 s.
   * **Owner change** (a hacked or rewelded turret) is watched the same way. **Switching it on** checks at once (item 4).
   * A turret beside something that keeps moving, such as a spinning rotor or wheels reaching into its area, re-checks every ~1.7 s while it moves.
   * It initializes on spawn (instant evaluation when unhangared, admin-spawned, or loaded from a save), with a second check once the physics has settled.

3. **CPU Cost:**
   * Each check casts 24 to 36 short rays on a client or local game (12 for the straight lanes, 1 or 2 per diagonal layer), reads the sky from the turret's own grid cell by cell (125 lookups) plus 72 lookups for doors. Each counted grid reaching into the area costs whichever is fewer: its own cells inside the area (a few hundred lookups for a large-grid base) or all its blocks (a small subgrid).
   * **A dedicated server needs only the verdict**, since each client works out the Control Panel text and the wireframe itself. It skips the lanes when the sky already fails, stops a lane at its first blocked layer, and stops once 5 lanes are open or 4 blocked: 15 rays for a clear turret. The verdict is the same as with every ray cast.
   * Estimate [SOFT]: about 0.1 to 0.25 ms per check on a client, roughly 10 to 25 times the old cell count (about 10 us), once a minute per idle turret. The game spreads every 100-tick update over 100 frames [HARD] (`MyParallelEntityUpdateOrchestrator`, `MyDistributedTypeUpdater(100)`), so turrets don't check on the same frame.
   * **Timing log** (2026-11-07): `TimingLog` in the script is off in releases. Set it to `true` in a local build and it writes the average and worst time per check and the rays per check to the game log every 20 checks.

4. **Other Factions' Grids Are Ignored:**
   * The turret's grid, its mechanical group (`GridLinkTypeEnum.Mechanical`), and grids of the owner or the owner's faction count.
   * Other factions' grids, NPC grids and grids built by nobody (ships, bases, wrecks, loose debris) do **not** trigger shutdowns. They are left out of the grid watch too, so they cost no checks.
   * An unowned grid's builder is read once per grid by walking its blocks (`IMyCubeGrid.GetBlocks` with a filter that adds nothing; the engine has no early exit [HARD]) and cached, up to 256 grids.

5. **Instant Slap-Back Anti-Bypass (`EnabledChanged`):**
   * If an unscrupulous player binds "Toggle On" to a cockpit hotbar or automated timer block loop inside an illegal bunker, the `EnabledChanged` event catches the state change on **Frame 0**.
   * It evaluates clearance instantly and knocks `Enabled = false` back off before the turret can even charge or fire a single raycast.
   * The script's own switching on and off does not set off a second check in the middle of the first.

---

## 4. Edge Cases & Whitelist Exemptions

* **Projector Immunity:**
  * Projected blueprint ghost blocks have no physics (`block.CubeGrid.Physics == null`) or belong to an active projector (`internalGrid.Projector != null`).
  * Ghost blocks are immediately ignored, preventing blue holographic projections from shutting down active shipyards or repair rigs.
* **NPC Exemption:**
  * A turret owned by an NPC identity (an owner with no Steam ID: `MyAPIGateway.Players.TryGetSteamId(ownerId) == 0`) skips the rule, and its Control Panel says so.
  * This allows world builders and encounter authors to build aesthetic boss grids with deeply recessed armor without code interference.
  * An unowned turret ("Nobody") is **not** exempt, so a player can't dodge the rule by giving the turret away.
  * If a player hacks or rewelds an NPC turret into their own ownership, the owner change is noticed within ~1.7 seconds (or at once when they switch it on) and clearance is enforced.
* **Restart-Safe Auto-Re-Enable:**
  * When the rule switches a turret off, the server writes a flag to the block's mod storage (GUID registered in `Data/GVK_EntityComponents.sbc`). After a restart, clearing the zone still turns it back on. A turret the player switched off themselves stays off.

---

## 5. ToolCore Integration & Engine Workarounds

Modifying and maintaining ToolCore weapons requires defensive engineering around internal framework quirks:

### The Missing Beam State Bug
* **The Bug:** When a ToolCore turret is shut off (`Enabled = false`), ToolCore expires the beam effect (`Trigger.Firing` is stripped from AV state). However, ToolCore's `SessionLogic` forgets to reset `turret.Aligned = false`. When re-enabled, ToolCore only fires `Trigger.Firing` if `aligned != turret.Aligned`. Because the turret is still pointing at the same block, `true != true` evaluates to **false**—leaving the beam invisible while the tool silently damages/welds blocks!
* **The Fix:** When `GVK_SalvageTurretClearance` auto-re-enables the turret after an obstacle is cleared, it schedules a 3-frame (~50ms) pulse on ToolCore's `ToolCore_TrackTargets` property. This flags `TargetsDirty = true`, forcing ToolCore to refresh target alignment and cleanly reignite the visual laser beam.

### Model Bounding Box
* The block is $1\times 4\times 1$ with `<ModelOffset x="0" y="-1.25" z="0" />` in `CubeBlocks_GVK_Tools.sbc` (until 2026-11-07, $1\times 3\times 1$ with offset 0).
* An earlier $1\times 2\times 1$ version lowered the bounding box centre by $1.25\text{ m}$ and sank the model halfway into the deck; it needed a $1.25\text{ m}$ model offset. The sight lanes ignore any hit inside the turret's own cells.
* The model sits at the centre of the block's bounding box, so each extra cell of `Size` Y lifts it by half a cell ($1.25\text{ m}$). A 4-tall block needs `<ModelOffset y="-1.25" />`, a 5-tall one $-2.5$.
* **A block's `Position` is its centre cell, not its bottom one** [HARD]: `MySlimBlock.ComputePositionInGrid` adds the definition's `Center`, which defaults to `(Size - 1) / 2`. For the old 3-tall block that was the middle cell; for the 4-tall block it is the second cell from the bottom. The script used `Position` as the bottom cell until 2026-11-07, so every zone sat one cell too high: the deck layer beside the turret went unchecked, and the cell directly on top of the turret was skipped as part of the turret. It now steps down from `Position` by `Center.Y` cells to the bottom cell, and leaves that base layer out on purpose (owner, 2026-11-07).

### Why "Ray with a Working Volume" Sucked (The Line vs. Sphere Tradeoff)
During early testing, an intuitive design idea was considered: *“Why not shoot a thin ray at the target and create a working sphere/volume at the impact point (`WorkOrigin: Hit` with `EffectShape: Sphere`), so the laser carves out a wider work area?”*

In practice, this approach proved completely disastrous across four critical gameplay and engine metrics:

1. **Wall-Hacking & Armor Bleed-Through (The Phasing Exploit):**
   * When a ray hits an exterior armor plate, the spherical work volume expands equally in all directions from the hit point—including **inward through the hull**.
   * In Grind mode, a 3-meter to 5-meter sphere reaches straight *through* solid heavy armor bulkheads, grinding away interior gyroscopes, jump drives, cockpits, and reactors while leaving the outer armor skin untouched! It effectively gave players wall-penetrating deconstruction lasers.

2. **Chaotic Work Order & The "Trapped Blueprint" Disaster:**
   * A volumetric sphere queries and processes blocks in a cluster rather than along a linear directional vector.
   * **In Weld Mode:** The sphere indiscriminately welds whatever blocks are in the bubble. It would frequently finish outer armor blocks first, completely enclosing unfinished conveyor tubes, thrusters, and batteries inside an armored tomb where players could never reach or finish them.
   * **In Grind Mode:** Instead of peeling a derelict wreck layer-by-layer like an onion, it turned ships into hollowed-out "Swiss cheese" shells, causing unpredictable grid splits, floating voxel collisions, and Havok solver saturation.

3. **Massive Visual & Spatial Disconnect:**
   * The visual laser emitter draws a focused, high-precision beam.
   * When using a hit volume, blocks 3 meters to the left, right, or completely obscured behind walls would randomly smoke, spark, and disintegrate without the beam ever touching them. Players had zero visual clarity on what the turret was actually prioritizing or chewing through.

4. **Entity Pruning Performance Spikes:**
   * Dynamically calculating a moving 3D sphere query against dense, 10,000+ block grids on every tick consumes noticeably more CPU time than a single directed line raycast.

#### Why `EffectShape: Line` + `WorkOrigin: Emitter` is Superior:
* **True Directional Salvage:** Grinding uses `WorkOrder: Forward`. The beam strictly deconstructs the first physical block it contacts along its line of sight. Armor must be stripped before interior components can be touched.
* **Flawless Blueprint Construction:** Welding uses `WorkOrder: Backward`. The beam reaches deep into the projection and welds from the back forward, ensuring internal structural skeletons and conveyors are fully built before the outer hull is sealed.
* **100% Visual Fidelity:** What the beam touches is what gets worked on. Zero ghost damage, zero wall-hacking.

### Self-Cannibalization Protection
* Both Weld and Grind definitions explicitly set `<AffectOwnGrid>false</AffectOwnGrid>`.
* Guarantees that stray beam raycasts or wide emitters never grind away the rover's own armor deck or self-repair internal blocks unintentionally.

---

## 6. Player Experience & Diagnostic Feedback

### Terminal Control Panel
Players receive transparent, actionable feedback directly in the block's Control Panel:

* **When Clear:**
  ```text
  === Mount Clearance Status ===
  Status: [ONLINE - CLEAR]

   • Sight lanes (8 directions out to the 5x5 edge, min 5 open): 6 open [CLEAR]
     Blocked: right, back-right
   • Sky (5x5x5, 100% clear): 0 of 125 cells blocked [CLEAR]
  A lane is open when its line at every height is clear.
  Your and your faction's grids count; other
  factions', NPC grids, terrain and people do not.
  ```

* **When Obstructed:**
  ```text
  === Mount Clearance Status ===
  Status: [OFFLINE - MOUNT OBSTRUCTED]
  Reason: Sight lanes blocked (only 4 of 8 open, min 5)

   • Sight lanes (8 directions out to the 5x5 edge, min 5 open): 4 open [OBSTRUCTED]
     Blocked: front, right, back, left
   • Sky (5x5x5, 100% clear): 0 of 125 cells blocked [CLEAR]
  A lane is open when its line at every height is clear.
  Your and your faction's grids count; other
  factions', NPC grids, terrain and people do not.

  Toggle 'Show Clearance Zone' below to see the holographic guide.
  ```

* **Sky:** `Reason: Sky obstructed (overhead structure or roof detected)`.
* **Both:** `Reason: Sight lanes and Sky are both obstructed`.
* **NPC-owned:** `Status: [NPC - CLEARANCE NOT ENFORCED]`.

### Client-Side Holographic Wireframe
Players can toggle `[Show Clearance Zone: Visible / Hidden]` in the terminal:
* Draws, in world space via `MySimpleObjectDraw`, sized from the block's height:
  * **Sight lanes:** 24 lines, one per lane and layer, from the turret's side to the edge of the 5x5 area. Each is **green** when its ray is clear and **red** when blocked. A lane with any red line is blocked.
  * **Sky:** a $12.5\text{m} \times 12.5\text{m} \times 12.5\text{m}$ wireframe box ($Y=4 \dots 8$), sky blue when open and **red** if even 1 cell is blocked.
* **Camera Culling:** Automatically stops rendering if the player moves further than **50 meters** away, preserving client GPU frametimes.
