---
title: Heavy Salvage Beam Turret
covers:
  - ModScripts/GVK_SalvageTurretClearance.cs
  - Content/Data/CubeBlocks_GVK_Tools.sbc
  - Content/Data/GVK_EntityComponents.sbc
---

# Heavy Salvage Beam Turret

The design document for the turret and its anti-bunker clearance rule. The clearance rule was reworked on 2026-11-07 ([GVK-Settings#750](https://github.com/GV-Server-Mods/GVK-Settings/issues/750)): the workspace limit now counts the whole volume instead of each layer, and terrain and mechanical subgrids count as blocked cells.

## 1. Design Intent & Background

In a hardcore desert PvPvE environment like Kharak, high-performance salvage and repair capabilities are critical for mobile rovers and frontline FOBs. The Salvage Beam Turret fills this role by projecting a high-energy directional beam capable of welding blueprints and deconstructing derelict wrecks from up to 150 meters away.

### The Engineering Challenge: "The Bunker Exploit"
In Space Engineers PvP, high-value turrets present a constant temptation for "bunkering":
* Players embed turrets inside recessed armor wells, sunken hull pockets, or beneath overhead armor overhangs to achieve 90%+ armor coverage while shooting through narrow firing slits.
* Traditionally, servers combat this with written server rules (*"Turrets must have open lines of sight"*), resulting in endless admin tickets, subjective screenshot arguments, and refereeing headaches.

### The GVK Governance Philosophy: Zero "Trust Me Bro™" Rules
In accordance with GVK core engineering standards, **we never enforce server balance through honor systems or written rulebooks.** If a mechanical constraint exists, it must be enforced programmatically:
* The turret physically monitors its own surroundings.
* If a player illegally armors or recesses the mount, the turret **instantly shuts down**, explains the exact layer violation in the Control Panel, and renders a holographic wireframe showing the player how to fix their build.

---

## 2. Clearance Governance Architecture: Dual Stacked Zones

Rather than an unforgiving, arbitrary sphere or a crude box, the turret enforces a **Dual Stacked Envelope** (11 large blocks / 27.5 meters tall total):

```
       ▲ +27.5m (Y=10)
       │  ┌───────────────────────────────┐
       │  │                               │
       │  │    ZONE 2: SKY                │
       │  │       (7x7x7 Blocks)          │
       │  │                               │
       │  │   RULE: 100% CLEAR SKY        │
       │  │   (Zero blocks allowed)       │
       │  │                               │
+10.0m │  ├───────────────────────────────┤  ▲ Boundary (Y=4: 1 block above the 3-block turret)
       │  │    ZONE 1: WORKSPACE          │
       │  │       (7x7x4 Blocks)          │
       │  │   RULE: >= 75% CLEAR OVERALL  │
       │  │   (Max 48 of 193 cells)       │
       │  │              [T]              │
  0.0m ┴──┴───────────────────────────────┴── Deck Surface (Y=0)
          ◄────────── 17.5m ─────────────►
                   (7 Blocks)
```

### Zone 1: The Local Workspace ($Y=0 \dots 3$)
* **Footprint & Height:** $7\times 7$ large grid blocks ($17.5\text{m} \times 17.5\text{m}$), spanning 4 blocks tall ($10\text{m}$) from the turret's own level ($Y=0$, the layer above the deck) to 1 block above the 3-block tall turret ($Y=3$). That is 196 cells, less the turret's own 3: **193 cells**.
* **Rule:** The workspace as a whole must stay **$\ge 75\%$ clear**: at most **48 of the 193 cells** may be blocked, anywhere in the volume.
* **Engineering Tradeoff & Player Realism:**
  * If clearance required 100% clear space at the deck, players couldn't even mount a conveyor tube, antenna mast, or spotlight on their rover roof without disabling the turret.
  * 48 cells is room for a full rover cab or bulkhead behind the turret, catwalks, antennas and lights, in whatever shape the build needs.
  * The most wall it allows is a ring on the workspace's outer edge, two blocks high (24 cells a layer, exactly 48). A third layer of ring fails. The open sky rule is what stops a bunker: nothing may cover the turret.
  * The limit counts **cells**, not blocks: a 3x3 block covers 9 cells.

### What counts as a blocked cell (both zones)
* **The turret's own grid:** any block in the cell.
* **Mechanical subgrids:** any part of a block on a grid joined through rotors, hinges, pistons or suspension, small grid included. A roof on a hinge or a rotor does not get around the rule.
* **Terrain:** a cell that is at least half sand or rock (8 sample points per cell, read at voxel LOD 1). A turret dug into a pit, trench or cave shuts off, and a base turret sitting low on a slope may need the ground cut back.
* **Not counted:** unconnected grids (a ship parked or hovering over the turret, an enemy rover), so nobody can switch a turret off by parking on it. Connector-docked ships are unconnected for this purpose.
* **"Up"** is the block's own up. A turret mounted sideways or upside down checks a sideways or downward sky.

### Zone 2: The Overhead Sky ($Y=4 \dots 10$)
* **Footprint & Height:** $7\times 7$ large grid blocks, extending 7 blocks tall ($17.5\text{m}$) directly above the work zone ($Y=4$) to $Y=10$.
* **Rule:** **$100\%$ Clear Sky** (0 of its 343 cells blocked).
* **Rationale:**
  * Turrets must have an unobstructed line of sight upward.
  * Prevents armored "caps," ceiling overhangs, bridges, blast skirts, terrain overhangs or subterranean bunker roofs over the turret.

---

## 3. Performance & Sim-Speed Optimization

With hundreds of blocks ticking on a multiplayer server, keeping sim-speed at 60 TPS requires strict performance hygiene:

1. **Zero Garbage Collection (GC) in Sim Ticks:**
   * All 536 cell offsets are precomputed once at world load into a static array (`InitializeClearanceOffsets()`).
   * No `new List`, LINQ queries, or closures are allocated during clearance evaluations.
   * The occupancy grid, voxel buffer and grid/block lists are static and reused by every turret (all checks run on the game thread).

2. **Event-Driven Checks plus a 10-second Heartbeat:**
   * The clearance component hooks `grid.OnBlockAdded`, `grid.OnBlockRemoved`, and `grid.OnGridSplit`, and checks at once when one fires.
   * It initializes dirty on spawn (ensuring instant evaluation when unhangared, admin-spawned, or loaded from a save).
   * Subgrid changes, terrain digging and grid merges raise no event on the turret's grid, so every turret also re-checks every ~10 seconds.
   * Each check reads the turret's own grid cell by cell (536 lookups), walks the blocks of any mechanical subgrid whose bounds reach the zone, and reads the zone's terrain in one voxel read at LOD 1 (2 m voxels, a few thousand voxels).

3. **Unconnected Grids Are Ignored:**
   * Only the turret's grid and grids in its mechanical group (`GridLinkTypeEnum.Mechanical`) count.
   * Floating debris, passing rovers and docked ships are separate groups and do **not** trigger shutdowns.

4. **Instant Slap-Back Anti-Bypass (`EnabledChanged`):**
   * If an unscrupulous player binds "Toggle On" to a cockpit hotbar or automated timer block loop inside an illegal bunker, the `EnabledChanged` event catches the state change on **Frame 0**.
   * It evaluates clearance instantly and knocks `Enabled = false` back off before the turret can even charge or fire a single raycast.

---

## 4. Edge Cases & Whitelist Exemptions

* **Projector Immunity:**
  * Projected blueprint ghost blocks have no physics (`block.CubeGrid.Physics == null`) or belong to an active projector (`internalGrid.Projector != null`).
  * Ghost blocks are immediately ignored, preventing blue holographic projections from shutting down active shipyards or repair rigs.
* **NPC Exemption:**
  * A turret owned by an NPC identity (an owner with no Steam ID: `MyAPIGateway.Players.TryGetSteamId(ownerId) == 0`) skips the rule, and its Control Panel says so.
  * This allows world builders and encounter authors to build aesthetic boss grids with deeply recessed armor without code interference.
  * An unowned turret ("Nobody") is **not** exempt, so a player can't dodge the rule by giving the turret away.
  * If a player hacks or rewelds an NPC turret into their own ownership, the next check (at most ~10 seconds, or at once when they switch it on) enforces clearance.
* **Restart-Safe Auto-Re-Enable:**
  * When the rule switches a turret off, the server writes a flag to the block's mod storage (GUID registered in `Data/GVK_EntityComponents.sbc`). After a restart, clearing the zone still turns it back on. A turret the player switched off themselves stays off.

---

## 5. ToolCore Integration & Engine Workarounds

Modifying and maintaining ToolCore weapons requires defensive engineering around internal framework quirks:

### The Missing Beam State Bug
* **The Bug:** When a ToolCore turret is shut off (`Enabled = false`), ToolCore expires the beam effect (`Trigger.Firing` is stripped from AV state). However, ToolCore's `SessionLogic` forgets to reset `turret.Aligned = false`. When re-enabled, ToolCore only fires `Trigger.Firing` if `aligned != turret.Aligned`. Because the turret is still pointing at the same block, `true != true` evaluates to **false**—leaving the beam invisible while the tool silently damages/welds blocks!
* **The Fix:** When `GVK_SalvageTurretClearance` auto-re-enables the turret after an obstacle is cleared, it schedules a 3-frame (~50ms) pulse on ToolCore's `ToolCore_TrackTargets` property. This flags `TargetsDirty = true`, forcing ToolCore to refresh target alignment and cleanly reignite the visual laser beam.

### Model Bounding Box
* The block is $1\times 3\times 1$ with `<ModelOffset x="0" y="0" z="0" />` in `CubeBlocks_GVK_Tools.sbc`.
* An earlier $1\times 2\times 1$ version lowered the bounding box centre by $1.25\text{ m}$ and sank the model halfway into the deck; it needed a $1.25\text{ m}$ model offset. The block went back to 3 tall, and the clearance zone leaves out all 3 of its cells.

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

   • Workspace (7x7x4, min 75% clear): 12 of max 48 cells blocked [CLEAR]
   • Sky (7x7x7, 100% clear): 0 cells blocked [CLEAR]
  Blocks, rotor/hinge/piston parts and terrain all count.
  ```

* **When Obstructed:**
  ```text
  === Mount Clearance Status ===
  Status: [OFFLINE - MOUNT OBSTRUCTED]
  Reason: Sky obstructed (overhead structure, roof or terrain detected)

   • Workspace (7x7x4, min 75% clear): 20 of max 48 cells blocked [CLEAR]
   • Sky (7x7x7, 100% clear): 6 cells blocked [OBSTRUCTED]
   • Terrain fills 6 of those cells
  Blocks, rotor/hinge/piston parts and terrain all count.

  Toggle 'Show Clearance Zone' below to see the holographic guide.
  ```

* **NPC-owned:** `Status: [NPC - CLEARANCE NOT ENFORCED]`.

### Client-Side Holographic Wireframe
Players can toggle `[Show Clearance Zone: Visible / Hidden]` in the terminal:
* Renders two stacked wireframe bounding boxes in world space via `MySimpleObjectDraw`:
  * **Zone 1 (Workspace):** $17.5\text{m} \times 10.0\text{m} \times 17.5\text{m}$ ($Y=0 \dots 3$).
  * **Zone 2 (Sky Chimney):** $17.5\text{m} \times 17.5\text{m} \times 17.5\text{m}$ ($Y=4 \dots 10$).
* **Diagnostic Color Coding:**
  * **Zone 1:** Cyan when legal; turns **Red** if over-bunkered (more than 48 of its 193 cells blocked).
  * **Zone 2:** Sky Blue when open; turns **Red** if even 1 cell of the overhead sky is blocked.
* **Camera Culling:** Automatically stops rendering if the player moves further than **50 meters** away, preserving client GPU frametimes.
