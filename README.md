# GVK ToolCore Tools: Salvage Beam Turret

An advanced, automated utility mod for **GV: Deserts of Kharak (GVK)**, featuring the **Heavy Salvage Beam Turret** (`GVK_LargeSalvageBeamTurret`) powered by ToolCore and governed by programmatic clearance enforcement.

---

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
+10.0m │  ├───────────────────────────────┤  ▲ Boundary (Y=4: 2 blocks above turret)
       │  │    ZONE 1: WORKSPACE          │
       │  │       (7x7x4 Blocks)          │
       │  │   RULE: >= 75% CLEAR / LAYER  │
       │  │   (Max 12 blocks / layer)     │
       │  │              [T]              │
  0.0m ┴──┴───────────────────────────────┴── Deck Surface (Y=0)
          ◄────────── 17.5m ─────────────►
                   (7 Blocks)
```

### Zone 1: The Local Workspace ($Y=0 \dots 3$)
* **Footprint & Height:** $7\times 7$ large grid blocks ($17.5\text{m} \times 17.5\text{m}$), spanning 4 blocks tall ($10\text{m}$) from the deck surface ($Y=0$) to exactly 2 blocks above the 2-block tall turret ($Y=3$).
* **Rule:** Every single layer must remain **$\ge 75\%$ unobstructed** (a maximum of **12 blocks** occupied per layer).
* **Engineering Tradeoff & Player Realism:**
  * If clearance required 100% clear space at the deck, players couldn't even mount a conveyor tube, antenna mast, or spotlight on their rover roof without disabling the turret.
  * At 12 blocks allowed per layer, players can comfortably mount a full **7-block-wide rover cab/bulkhead** directly behind the turret, run catwalks, and install antennas/lights without tripping false alarms.
  * However, building a sunken trench (14 blocks), 3-sided armored pocket (21 blocks), or enclosed bunker pillbox (24 blocks) is mechanically impossible.

### Zone 2: The Overhead Sky ($Y=4 \dots 10$)
* **Footprint & Height:** $7\times 7$ large grid blocks, extending 7 blocks tall ($17.5\text{m}$) directly above the work zone ($Y=4$) to $Y=10$.
* **Rule:** **$100\%$ Clear Sky** (0 blocks allowed).
* **Rationale:**
  * Turrets must have an unobstructed line of sight upward.
  * Prevents armored "caps," ceiling overhangs, bridges, blast skirts, or subterranean bunker roofs over the turret.

---

## 3. Performance & Sim-Speed Optimization

With hundreds of blocks ticking on a multiplayer server, keeping sim-speed at 60 TPS requires strict performance hygiene:

1. **Zero Garbage Collection (GC) in Sim Ticks:**
   * All 537 grid offsets are precomputed once at world load into a static array (`InitializeClearanceOffsets()`).
   * No `new List`, LINQ queries, or closures are allocated during clearance evaluations.
   * Internal layer counts are tracked using a pre-allocated reusable integer buffer.

2. **Event-Driven Sleep (0.000 ms Idle CPU Time):**
   * The clearance component hooks `grid.OnBlockAdded`, `grid.OnBlockRemoved`, and `grid.OnGridSplit`.
   * It initializes dirty on spawn (ensuring instant evaluation when unhangared, admin-spawned, or loaded from a save).
   * Once validated clear, **the component goes completely dormant**, consuming **0.000 ms of CPU time** until a player physically places or grinds a block on that grid.

3. **Subgrid & Neighbor Entity Separation:**
   * Clearance checks use `_sorter.CubeGrid.GetCubeBlock(checkPos)`.
   * Subgrids (rotors, hinges, suspensions), floating debris, and passing rovers are separate entities in Havok physics and do **not** trigger false-positive shutdowns.

4. **Instant Slap-Back Anti-Bypass (`EnabledChanged`):**
   * If an unscrupulous player binds "Toggle On" to a cockpit hotbar or automated timer block loop inside an illegal bunker, the `EnabledChanged` event catches the state change on **Frame 0**.
   * It evaluates clearance instantly and knocks `Enabled = false` back off before the turret can even charge or fire a single raycast.

---

## 4. Edge Cases & Whitelist Exemptions

* **Projector Immunity:**
  * Projected blueprint ghost blocks have no physics (`block.CubeGrid.Physics == null`) or belong to an active projector (`internalGrid.Projector != null`).
  * Ghost blocks are immediately ignored, preventing blue holographic projections from shutting down active shipyards or repair rigs.
* **NPC & Relic Exemption:**
  * NPC encounters (MES drones, Gaalsien convoys, ancient derelict wrecks) bypass clearance enforcement entirely.
  * Verified via Steam ID (`MyAPIGateway.Players.TryGetSteamId(ownerId) == 0`) and faction checks (`IsEveryoneNpc()`, `GAALSIEN`, `DERELICT`, `SPRT`, `KOTH`).
  * This allows world builders and encounter authors to build aesthetic boss grids with deeply recessed armor without code interference.
  * If a player hacks or rewelds an NPC turret into human ownership, the script detects the human Steam ID and immediately enforces clearance!

---

## 5. ToolCore Integration & Engine Workarounds

Modifying and maintaining ToolCore weapons requires defensive engineering around internal framework quirks:

### The Missing Beam State Bug
* **The Bug:** When a ToolCore turret is shut off (`Enabled = false`), ToolCore expires the beam effect (`Trigger.Firing` is stripped from AV state). However, ToolCore's `SessionLogic` forgets to reset `turret.Aligned = false`. When re-enabled, ToolCore only fires `Trigger.Firing` if `aligned != turret.Aligned`. Because the turret is still pointing at the same block, `true != true` evaluates to **false**—leaving the beam invisible while the tool silently damages/welds blocks!
* **The Fix:** When `GVK_SalvageTurretClearance` auto-re-enables the turret after an obstacle is cleared, it schedules a 3-frame (~50ms) pulse on ToolCore's `ToolCore_TrackTargets` property. This flags `TargetsDirty = true`, forcing ToolCore to refresh target alignment and cleanly reignite the visual laser beam.

### Model Bounding Box & Sinking Fix
* Resizing the block from $1\times 3\times 1$ to $1\times 2\times 1$ lowered the geometric center of the large grid bounding box by exactly $1.25\text{ meters}$ ($0.5 \times 2.5\text{m}$).
* Without compensation, the 3D model sank halfway into the mounting deck.
* Fixed in `CubeBlocks_GVK_Tools.sbc` via `<ModelOffset x="0" y="1.25" z="0" />`, restoring flush mounting on large grid decks.

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
   • Workspace (7x7x4, min 75%): [CLEAR]
   • Sky (7x7x7, min 100%): [CLEAR]
  ```

* **When Obstructed:**
  ```text
  === Mount Clearance Status ===
  Status: [OFFLINE - MOUNT OBSTRUCTED]
  Reason: Sky obstructed (overhead structure or roof detected)

   • Workspace (7x7x4, min 75%): [CLEAR]
   • Sky (7x7x7, min 100%): [OBSTRUCTED]

  Toggle 'Show Clearance Zone' below to see the holographic guide.
  ```

### Client-Side Holographic Wireframe
Players can toggle `[Show Clearance Zone: Visible / Hidden]` in the terminal:
* Renders two stacked wireframe bounding boxes in world space via `MySimpleObjectDraw`:
  * **Zone 1 (Workspace):** $17.5\text{m} \times 10.0\text{m} \times 17.5\text{m}$ ($Y=0 \dots 3$).
  * **Zone 2 (Sky Chimney):** $17.5\text{m} \times 17.5\text{m} \times 17.5\text{m}$ ($Y=4 \dots 10$).
* **Diagnostic Color Coding:**
  * **Zone 1:** Cyan when legal; turns **Red** if over-bunkered ($\ge 13$ blocks on any layer).
  * **Zone 2:** Sky Blue when open; turns **Red** if even 1 block breaches the overhead sky.
* **Camera Culling:** Automatically stops rendering if the player moves further than **50 meters** away, preserving client GPU frametimes.