using System;
using System.Collections.Generic;
using System.Text;
using Sandbox.Common.ObjectBuilders;
using Sandbox.Definitions;
using Sandbox.Game.Entities;
using Sandbox.Game.EntityComponents;
using Sandbox.ModAPI;
using Sandbox.ModAPI.Interfaces;
using Sandbox.ModAPI.Interfaces.Terminal;
using VRage.Game;
using VRage.Game.Components;
using VRage.Game.Entity;
using VRage.Game.ModAPI;
using VRage.ModAPI;
using VRage.ObjectBuilders;
using VRage.Utils;
using VRageMath;

namespace GVK_ToolCore_Tools
{
    /// <summary>
    /// Enforces the clearance rule for the GVK Large Salvage Beam Turret.
    /// Prevents players from sinking long-range beam turrets into armored chimneys, silos,
    /// or underground bunkers by requiring open sight lines around the turret and open sky above it.
    /// Features:
    /// - 8 sight lanes (front, back, sides, diagonals) out to the edge of a 5x5 area, each a physics ray
    ///   at every layer of the turret above its base. At least 5 lanes must be open.
    /// - A 5x5x5 sky above that, checked cell by cell, with no cells blocked.
    /// - The base layer (the turret's bottom cell) is not checked. Offsets are measured from the bottom cell.
    /// - Blocks count on the turret's grid, its rotor/hinge/piston subgrids, and any other grid owned by nobody,
    ///   an NPC, the turret's owner or the owner's faction. Other factions' grids, terrain and people do not.
    /// - Re-checks when a block is added to or removed from the turret's grid, when the turret changes grid
    ///   (merge), when a nearby counted grid moves or changes, when the owner changes, and every ~60 s as a safety net.
    /// - Doors in the lanes count as closed: opening or shutting one raises no event.
    /// - Skips projected ghost blocks and NPC-owned turrets.
    /// - Auto-re-enables once clear; the flag survives a save and reload.
    /// - Holographic wireframe toggle in the Control Panel.
    /// </summary>
    [MyEntityComponentDescriptor(typeof(MyObjectBuilder_ConveyorSorter), false, "GVK_LargeSalvageBeamTurret")]
    public class GVK_SalvageTurretClearance : MyGameLogicComponent
    {
        internal static readonly HashSet<GVK_SalvageTurretClearance> ActiveDrawTurrets = new HashSet<GVK_SalvageTurretClearance>();
        private static bool _terminalControlsInitialized = false;

        // Zone layout, built once from the block's height in cells (Size Y in the SBC) by BuildLayout().
        // Offsets are measured from the turret's bottom cell (its base, Y=0, which is not checked), X and Z
        // from -2 to 2, -Z being the turret's front. The sight lanes run at the 3 layers above the base; the
        // sky is the 5 layers above them (or right above a turret taller than 4).
        private const int HalfWidth = 2;                   // 5x5 zones
        private const int Width = 2 * HalfWidth + 1;
        private const int WorkspaceBottom = 1;             // the layer above the base
        private const int WorkspaceLayers = 3;
        private const int SkyLayers = 5;
        private const int MaxAllowedObstructedZone2 = 0;   // 100% clear sky
        private static int _turretHeight;
        private static int _skyBottom;                     // 4, or the top of a taller turret
        private static int _skyTop;                        // _skyBottom + 4
        private static Vector3I[] ClearanceOffsets;        // the sky cells
        private static int _skyCells;                      // 5x5x5 = 125

        // Sight lanes, clockwise from the front as (x, z) steps. Each casts one ray per layer (two for a
        // diagonal, see CastLane) from inside the turret's own cell to just inside the 5x5 edge.
        internal const int LaneCount = 8;
        private const int MinOpenLanes = 5;
        internal static readonly int[] LaneX = { 0, 1, 1, 1, 0, -1, -1, -1 };
        internal static readonly int[] LaneZ = { -1, -1, 0, 1, 1, 1, 0, -1 };
        private static readonly string[] LaneNames = { "front", "front-right", "right", "back-right", "back", "back-left", "left", "front-left" };
        private const double RayStart = 0.3;               // cells from the turret's axis: inside its own cell
        internal const double RayEnd = HalfWidth + 0.45;   // short of the 5x5 edge, so blocks outside it never count
        private const double DiagonalShift = 0.08;         // see CastLane
        private const int RaycastLayer = 24;               // MyPhysics.CollisionLayers.ObjectDetectionCollisionLayer
        internal static int LaneHeights;                   // the turret's layers above its base: 3

        // Mod storage key for the auto-re-enable flag. Registered in Data/GVK_EntityComponents.sbc,
        // otherwise the game drops it on save.
        private static readonly Guid ReEnableStorageGuid = new Guid("AB503EF1-F20D-4F3A-A7EE-E7C67638EC0A");

        // Shared scratch buffers: every clearance check runs on the game thread, one at a time.
        private static readonly List<IMyCubeGrid> _groupGrids = new List<IMyCubeGrid>();
        private static readonly List<MyEntity> _nearEntities = new List<MyEntity>();
        private static readonly List<IMyCubeGrid> _countedGrids = new List<IMyCubeGrid>();   // see CollectCountedGrids
        private static readonly List<IMySlimBlock> _subgridBlocks = new List<IMySlimBlock>();
        private static readonly List<IHitInfo> _hits = new List<IHitInfo>();

        // Who built each unowned grid seen near a turret (see GridBuilder), by grid entity id.
        private const int MaxCachedBuilders = 256;
        private static readonly Dictionary<long, long> _gridBuilders = new Dictionary<long, long>();
        private static readonly Func<IMySlimBlock, bool> _sampleBuilder = SampleBuilder;
        private static long _sampledBuilder;
        private static bool _builderSampled;
        private static bool[] _occupied;                   // Sky occupancy, indexed by CellIndex(offset)
        private static bool[] _doorCells;                  // Doors in the lane layers, indexed by DoorIndex(x, layer, z)
        private static bool _anyDoor;

        // Watch tolerances: Havok jitters subgrids a little even when nothing moves them.
        private const double WatchMoveSq = 0.1 * 0.1;      // metres
        private const double WatchTurnSq = 0.01 * 0.01;    // about 0.6 degrees

        // Timing log for performance tests (2026-11-07), off in releases. Set to true in a local build to
        // write a line to the game log every TimingLogEvery checks.
        private static readonly bool TimingLog = false;
        private const int TimingLogEvery = 20;
        private static readonly System.Diagnostics.Stopwatch _timer = new System.Diagnostics.Stopwatch();
        private static int _timedChecks;
        private static long _timedTicks;
        private static long _timedMaxTicks;
        private static int _timedRays;

        private IMyFunctionalBlock _sorter;
        private IMyTerminalBlock _terminalBlock;
        private IMyCubeGrid _trackedGrid;

        private bool _isObstructed;
        private bool _lanesObstructed;
        private bool _skyObstructed;
        private bool _wasEnabledBeforeObstruction;
        private bool _initialized;
        private bool _showClearanceWireframe;

        private string _violationReason = "";
        private int _refreshBeamTicks;

        // Safety re-check every ~60 s. Changes are normally caught sooner: block events on the turret's grid,
        // the grid-change and subgrid watch in UpdateBeforeSimulation100, and switching the turret on.
        private const int HeartbeatInterval = 36; // 36 x Update100 (~100 ticks each) = 3600 ticks = 60 s
        private int _heartbeatCounter;

        // Checks still owed, run one per Update100. A block event owes 2: a new or removed block's
        // collision can lag behind the event, so the second check confirms the first.
        private int _pendingChecks;

        // What the last check saw, for the watch: owner, and the counted grids reaching into the area.
        private long _checkedOwnerId;
        private NearGridState _watch;

        private struct NearGridState
        {
            public int Near;       // counted grids, other than the turret's own, whose bounds reach into the area
            public int Blocks;     // their block count
            public Vector3D Pos;   // sums of their position, forward and up, in the turret grid's frame
            public Vector3D Fwd;
            public Vector3D Up;
        }

        // Reentrancy guard: prevents infinite EnabledChanged → CheckClearance → Enabled = false → EnabledChanged loop
        // if Keen ever changes event dispatch timing. (Audit #4)
        private bool _processingEnabledChange;

        // Cached block orientation vectors in the turret's grid, set by BindGrid. They change only when a
        // merge moves the turret onto another grid. (Audit #10)
        private Vector3I _cachedRightVec;
        private Vector3I _cachedUpVec;
        private Vector3I _cachedForwardVec;

        // The turret's bottom cell. The block's Position is its centre cell (Size-1)/2, not its bottom.
        private Vector3I _basePos;
        private int _centreY;

        private int _openLanes = LaneCount;
        private int _blockedLaneMask;                      // one bit per lane
        private bool[] _rayBlocked;                        // per layer of each lane: lane * LaneHeights + layer
        private int _skyBlocked;
        private bool _npcExempt;

        // Values last shown in the Control Panel, so it refreshes only when they change.
        private int _shownBlockedLaneMask = -1;
        private int _shownSkyBlocked = -1;
        private bool _shownNpcExempt;

        // World-space step for one cell along the turret's right, up and back axes, plus the
        // turret's base cell centre. Recomputed each check (the grid moves).
        private Vector3D _wOrigin;
        private Vector3D _wRight;
        private Vector3D _wUp;
        private Vector3D _wBack;
        private double _cellSizeSq;
        private BoundingBoxD _zoneBox;

        /// <summary>
        /// Gets or sets whether the client holographic wireframe is visible for this turret.
        /// </summary>
        public bool ShowClearanceWireframe
        {
            get { return _showClearanceWireframe; }
            set
            {
                _showClearanceWireframe = value;
                if (value)
                {
                    ActiveDrawTurrets.Add(this);
                }
                else
                {
                    ActiveDrawTurrets.Remove(this);
                }
            }
        }

        public bool IsObstructed { get { return _isObstructed; } }
        public bool SkyObstructed { get { return _skyObstructed; } }
        public IMyFunctionalBlock Sorter { get { return _sorter; } }
        public Vector3I BasePos { get { return _basePos; } }
        internal static int WorkspaceBottomLayer { get { return WorkspaceBottom; } }
        internal static int SkyBottom { get { return _skyBottom; } }
        internal static int SkyTop { get { return _skyTop; } }

        /// <summary>
        /// Whether the ray of a lane at one layer above the base (0 = the lowest) was blocked in the last check.
        /// </summary>
        internal bool RayBlockedAt(int lane, int layer)
        {
            return _rayBlocked != null && _rayBlocked[lane * LaneHeights + layer];
        }

        /// <summary>
        /// Precomputes the layout for a turret H cells tall (offsets from its bottom cell): the sight lanes at
        /// Y=1..3 (above the base), and the sky cells, 5x5, the 5 layers above them (or above a taller turret).
        /// Runs once; the turret has one block definition.
        /// </summary>
        private static void BuildLayout(int height)
        {
            if (ClearanceOffsets != null && _turretHeight == height)
                return;

            _turretHeight = height;
            _skyBottom = Math.Max(WorkspaceBottom + WorkspaceLayers, height);
            _skyTop = _skyBottom + SkyLayers - 1;
            LaneHeights = _skyBottom - WorkspaceBottom;

            var list = new List<Vector3I>();
            for (int y = _skyBottom; y <= _skyTop; y++)
                for (int x = -HalfWidth; x <= HalfWidth; x++)
                    for (int z = -HalfWidth; z <= HalfWidth; z++)
                        list.Add(new Vector3I(x, y, z));

            ClearanceOffsets = list.ToArray();
            _occupied = new bool[Width * SkyLayers * Width];
            _doorCells = new bool[Width * LaneHeights * Width];
            _skyCells = list.Count;
        }

        public override void Init(MyObjectBuilder_EntityBase objectBuilder)
        {
            base.Init(objectBuilder);
            NeedsUpdate = MyEntityUpdateEnum.BEFORE_NEXT_FRAME;
        }

        public override void UpdateOnceBeforeFrame()
        {
            base.UpdateOnceBeforeFrame();

            _sorter = Entity as IMyFunctionalBlock;
            _terminalBlock = Entity as IMyTerminalBlock;

            if (_sorter == null || _sorter.CubeGrid == null)
                return;

            // Strict Projector Check: Do NOT execute on projected / hologram ghost blocks
            if (IsProjected(_sorter))
                return;

            _sorter.EnabledChanged += OnEnabledChanged;

            if (_terminalBlock != null)
            {
                _terminalBlock.AppendingCustomInfo += AppendCustomInfo;
            }

            // Height and centre cell come from the block definition, so a taller block in the SBC
            // resizes the zones with it.
            var def = MyDefinitionManager.Static.GetCubeBlockDefinition(_sorter.BlockDefinition);
            int height = def != null ? def.Size.Y : 3;
            _centreY = def != null ? def.Center.Y : 1;
            BuildLayout(height);
            _rayBlocked = new bool[LaneCount * LaneHeights];
            BindGrid(_sorter.CubeGrid);

            CreateTerminalControls();

            // Restore the auto-re-enable flag saved before the last restart.
            string stored;
            if (Entity.Storage != null && Entity.Storage.TryGetValue(ReEnableStorageGuid, out stored))
            {
                _wasEnabledBeforeObstruction = stored == "1";
            }

            NeedsUpdate = MyEntityUpdateEnum.EACH_100TH_FRAME;
            _initialized = true;

            // Immediate initial clearance check upon spawn / load / unhangar, confirmed once the
            // grid's physics has settled.
            CheckClearance();
            _pendingChecks = 1;
        }

        /// <summary>
        /// Hooks the turret's current grid and caches its orientation and bottom cell in that grid.
        /// Runs at start, after a split, and after a merge, which moves the turret onto the other grid
        /// with a new position and orientation ([HARD] MyCubeGrid.MoveBlocksAndClose).
        /// </summary>
        private void BindGrid(IMyCubeGrid grid)
        {
            if (_trackedGrid != null)
            {
                _trackedGrid.OnBlockAdded -= OnGridModified;
                _trackedGrid.OnBlockRemoved -= OnGridModified;
                _trackedGrid.OnGridSplit -= OnGridSplit;
            }

            _trackedGrid = grid;
            _trackedGrid.OnBlockAdded += OnGridModified;
            _trackedGrid.OnBlockRemoved += OnGridModified;
            _trackedGrid.OnGridSplit += OnGridSplit;

            var orientation = _sorter.Orientation;
            _cachedRightVec = Base6Directions.GetIntVector(Base6Directions.GetFlippedDirection(orientation.Left));
            _cachedUpVec = Base6Directions.GetIntVector(orientation.Up);
            _cachedForwardVec = Base6Directions.GetIntVector(orientation.Forward);
            _basePos = _sorter.Position - _cachedUpVec * _centreY;
            _pendingChecks = 2;
        }

        private void OnGridModified(IMySlimBlock slim)
        {
            _pendingChecks = 2;
        }

        private void OnGridSplit(IMyCubeGrid grid1, IMyCubeGrid grid2)
        {
            _pendingChecks = 2;

            // After a split, _trackedGrid may point at the orphaned half that no longer
            // contains the turret. Rebind events to the turret's actual grid. (Audit #15)
            if (_sorter == null || _sorter.MarkedForClose)
                return;

            var currentGrid = _sorter.CubeGrid;
            if (currentGrid != null && currentGrid != _trackedGrid)
                BindGrid(currentGrid);
        }

        private void OnEnabledChanged(IMyTerminalBlock block)
        {
            // Reentrancy guard: CheckClearance() may set Enabled = false, which fires
            // this event again. Guard prevents stack recursion. (Audit #4)
            if (_processingEnabledChange)
                return;

            if (_sorter == null || _sorter.MarkedForClose)
                return;

            if (IsProjected(_sorter))
                return;

            // When toggled ON, run an immediate clearance evaluation to prevent bypass
            if (_sorter.Enabled)
            {
                _processingEnabledChange = true;
                try
                {
                    CheckClearance();
                }
                finally
                {
                    _processingEnabledChange = false;
                }
            }
        }

        /// <summary>
        /// Determines whether the block belongs to a projected ghost blueprint grid.
        /// </summary>
        private static bool IsProjected(IMyCubeBlock block)
        {
            if (block?.CubeGrid == null) return false;
            if (block.CubeGrid.Physics == null) return true;
            var internalGrid = block.CubeGrid as Sandbox.Game.Entities.MyCubeGrid;
            return internalGrid != null && internalGrid.Projector != null;
        }

        public override void UpdateBeforeSimulation()
        {
            base.UpdateBeforeSimulation();

            if (_refreshBeamTicks > 0)
            {
                _refreshBeamTicks--;
                if (_refreshBeamTicks == 0)
                {
                    NeedsUpdate &= ~MyEntityUpdateEnum.EACH_FRAME;
                    RefreshToolCoreBeam();
                }
            }
        }

        /// <summary>
        /// Pulses ToolCore target tracking after an auto-re-enable event.
        /// Fixes a ToolCore quirk where re-enabling an aligned turret leaves the visual beam
        /// dormant because ToolCore only fires Trigger.Firing on state transitions.
        /// </summary>
        private void RefreshToolCoreBeam()
        {
            try
            {
                if (_terminalBlock == null || _terminalBlock.MarkedForClose)
                    return;

                var trackProp = _terminalBlock.GetProperty("ToolCore_TrackTargets");
                if (trackProp != null)
                {
                    bool current = _terminalBlock.GetValueBool("ToolCore_TrackTargets");
                    _terminalBlock.SetValueBool("ToolCore_TrackTargets", !current);
                    _terminalBlock.SetValueBool("ToolCore_TrackTargets", current);
                }
            }
            catch (Exception ex)
            {
                MyLog.Default.WriteLineAndConsole(string.Format("[GVK_SalvageTurretClearance] Error refreshing ToolCore beam: {0}", ex.Message));
            }
        }

        public override void UpdateBeforeSimulation100()
        {
            base.UpdateBeforeSimulation100();

            if (!_initialized || _sorter == null || _sorter.MarkedForClose || _sorter.CubeGrid == null)
                return;

            // IsProjected() check removed here — projected blocks return early from
            // UpdateOnceBeforeFrame() without setting _initialized = true, so they
            // can never reach this point. (Audit #9: dead code removal)

            // A merge moves the turret onto the other grid and closes the old one, whose events then stop.
            var grid = _sorter.CubeGrid;
            if (grid != _trackedGrid)
                BindGrid(grid);

            _heartbeatCounter++;
            if (_heartbeatCounter >= HeartbeatInterval)
            {
                _heartbeatCounter = 0;
                if (_pendingChecks == 0)
                    _pendingChecks = 1;
            }
            else if (_pendingChecks == 0 && (_sorter.OwnerId != _checkedOwnerId || (!_npcExempt && NearGridsChanged(grid))))
            {
                _pendingChecks = 1;
            }

            if (_pendingChecks == 0)
                return;

            _pendingChecks--;
            CheckClearance();
        }

        /// <summary>
        /// Whether the counted grids reaching into the area moved or turned relative to the turret's grid,
        /// gained or lost blocks, came or went since the last check. Subgrids and separate grids raise no
        /// events on the turret's grid, so this is how a hinged roof, a piston wall or a ship parked over the
        /// turret gets noticed. Costs a group lookup and a bounds query when nothing is near.
        /// </summary>
        private bool NearGridsChanged(IMyCubeGrid grid)
        {
            ComputeWorldAxes(grid);
            CollectCountedGrids(grid);

            bool changed;
            if (_countedGrids.Count == 0 && _watch.Near == 0)
            {
                changed = false;
            }
            else
            {
                var now = ReadNearState(grid);
                changed = now.Near != _watch.Near || now.Blocks != _watch.Blocks
                    || Vector3D.DistanceSquared(now.Pos, _watch.Pos) > WatchMoveSq
                    || Vector3D.DistanceSquared(now.Fwd, _watch.Fwd) > WatchTurnSq
                    || Vector3D.DistanceSquared(now.Up, _watch.Up) > WatchTurnSq;
            }

            _countedGrids.Clear();
            return changed;
        }

        /// <summary>
        /// Fills _countedGrids with the grids, other than the turret's own, whose bounds reach into the area
        /// (_zoneBox) and whose blocks count: the turret's rotor/hinge/piston subgrids, and separate grids that
        /// pass CountsSeparateGrid. Projections (no physics) never count.
        /// </summary>
        private void CollectCountedGrids(IMyCubeGrid grid)
        {
            _countedGrids.Clear();
            _groupGrids.Clear();
            MyAPIGateway.GridGroups.GetGroup(grid, GridLinkTypeEnum.Mechanical, _groupGrids);

            _nearEntities.Clear();
            MyGamePruningStructure.GetTopMostEntitiesInBox(ref _zoneBox, _nearEntities);

            long owner = _sorter.OwnerId;
            IMyFaction faction = owner != 0 ? MyAPIGateway.Session.Factions.TryGetPlayerFaction(owner) : null;

            for (int i = 0; i < _nearEntities.Count; i++)
            {
                var other = _nearEntities[i] as IMyCubeGrid;
                if (other == null || other == grid || other.MarkedForClose || other.Physics == null)
                    continue;

                if (_groupGrids.Contains(other) || CountsSeparateGrid(other, owner, faction))
                    _countedGrids.Add(other);
            }

            _nearEntities.Clear();
            _groupGrids.Clear();
        }

        /// <summary>
        /// Whether a separate grid counts (owner, 2026-11-07), judged by its owner (first big owner) or, when
        /// it has none, by who built it (GridBuilder). Only the turret's owner and members of the owner's
        /// faction count. Other factions' grids never count, so nobody outside the faction can switch the
        /// turret off by parking next to it, and NPC grids and grids built by nobody (ships, bases, wrecks,
        /// debris) never count either.
        /// </summary>
        private static bool CountsSeparateGrid(IMyCubeGrid other, long owner, IMyFaction faction)
        {
            var owners = other.BigOwners;
            long id = owners != null && owners.Count > 0 ? owners[0] : GridBuilder(other);
            if (id == 0)
                return false;
            if (id == owner)
                return true;

            return faction != null && MyAPIGateway.Session.Factions.TryGetPlayerFaction(id) == faction;
        }

        /// <summary>
        /// Who built an unowned grid (an armor-only shell, debris or a wreck), read from the first block the grid
        /// lists (BuiltBy; 0 for nobody). Reading it walks the grid's blocks, so it is cached per grid. A grid
        /// built by several players is judged by that first block [SOFT].
        /// </summary>
        private static long GridBuilder(IMyCubeGrid grid)
        {
            long builder;
            if (_gridBuilders.TryGetValue(grid.EntityId, out builder))
                return builder;

            _builderSampled = false;
            _sampledBuilder = 0;
            grid.GetBlocks(_subgridBlocks, _sampleBuilder);   // adds nothing, see SampleBuilder
            if (_gridBuilders.Count >= MaxCachedBuilders)
                _gridBuilders.Clear();
            _gridBuilders[grid.EntityId] = _sampledBuilder;
            return _sampledBuilder;
        }

        private static bool SampleBuilder(IMySlimBlock block)
        {
            if (!_builderSampled)
            {
                _sampledBuilder = block.BuiltBy;
                _builderSampled = true;
            }
            return false;
        }

        /// <summary>
        /// Sums up the grids in _countedGrids: how many, their blocks, and their position and facing in the
        /// turret grid's frame.
        /// </summary>
        private NearGridState ReadNearState(IMyCubeGrid grid)
        {
            var state = new NearGridState();
            MatrixD gm = grid.WorldMatrix;

            for (int g = 0; g < _countedGrids.Count; g++)
            {
                var other = _countedGrids[g];
                state.Near++;
                var cube = other as Sandbox.Game.Entities.MyCubeGrid;
                if (cube != null)
                    state.Blocks += cube.BlocksCount;

                MatrixD sm = other.WorldMatrix;
                Vector3D d = sm.Translation - gm.Translation;
                state.Pos += new Vector3D(d.Dot(gm.Right), d.Dot(gm.Up), d.Dot(gm.Backward));
                state.Fwd += new Vector3D(sm.Forward.Dot(gm.Right), sm.Forward.Dot(gm.Up), sm.Forward.Dot(gm.Backward));
                state.Up += new Vector3D(sm.Up.Dot(gm.Right), sm.Up.Dot(gm.Up), sm.Up.Dot(gm.Backward));
            }

            return state;
        }

        /// <summary>
        /// Casts the sight lanes and checks the sky cells against the turret's grid and the other counted
        /// grids near it, then applies the lane and sky limits.
        /// </summary>
        private void CheckClearance()
        {
            var grid = _sorter.CubeGrid;
            if (grid == null)
                return;

            // Switching the turret on right after a merge can get here before UpdateBeforeSimulation100 does.
            if (grid != _trackedGrid)
                BindGrid(grid);

            if (TimingLog)
                _timer.Restart();

            // A dedicated server needs only the verdict: the Control Panel text and the wireframe are worked
            // out by each client itself. So it stops casting once the result is settled; the result is the same.
            bool detail = !MyAPIGateway.Utilities.IsDedicated;

            _openLanes = LaneCount;
            _blockedLaneMask = 0;
            _skyBlocked = 0;
            _lanesObstructed = false;
            _skyObstructed = false;
            Array.Clear(_rayBlocked, 0, _rayBlocked.Length);

            // NPC turrets (owner has no Steam ID) skip the rule. "Nobody" ownership does not.
            long ownerId = _sorter.OwnerId;
            _checkedOwnerId = ownerId;
            _npcExempt = ownerId != 0 && MyAPIGateway.Players.TryGetSteamId(ownerId) == 0;

            if (!_npcExempt)
            {
                Array.Clear(_occupied, 0, _occupied.Length);
                Array.Clear(_doorCells, 0, _doorCells.Length);
                _anyDoor = false;
                ComputeWorldAxes(grid);

                CollectCountedGrids(grid);
                _watch = ReadNearState(grid);

                MarkOwnGrid(grid);
                for (int g = 0; g < _countedGrids.Count; g++)
                    MarkGrid(_countedGrids[g]);

                for (int i = 0; i < ClearanceOffsets.Length; i++)
                {
                    if (_occupied[CellIndex(ClearanceOffsets[i])])
                        _skyBlocked++;
                }

                _skyObstructed = _skyBlocked > MaxAllowedObstructedZone2;

                // Without detail: no lanes once the sky fails, and stop once 5 lanes are open or 4 blocked.
                if (detail || !_skyObstructed)
                {
                    int open = 0;
                    int blocked = 0;
                    for (int lane = 0; lane < LaneCount; lane++)
                    {
                        if (!detail && (open >= MinOpenLanes || blocked > LaneCount - MinOpenLanes))
                            break;

                        if (CastLane(lane, detail))
                        {
                            open++;
                        }
                        else
                        {
                            blocked++;
                            _blockedLaneMask |= 1 << lane;
                        }
                    }

                    _openLanes = LaneCount - blocked;
                    _lanesObstructed = blocked > LaneCount - MinOpenLanes;
                }

                _hits.Clear();
                _subgridBlocks.Clear();
                _countedGrids.Clear();
            }

            bool obstructed = _lanesObstructed || _skyObstructed;
            string reason = "";

            if (_lanesObstructed && _skyObstructed)
                reason = "Sight lanes and Sky are both obstructed";
            else if (_lanesObstructed)
                reason = string.Format("Sight lanes blocked (only {0} of {1} open, min {2})", _openLanes, LaneCount, MinOpenLanes);
            else if (_skyObstructed)
                reason = "Sky obstructed (overhead structure or roof detected)";

            // Refresh the Control Panel whenever what it shows changes.
            bool stateChanged = _blockedLaneMask != _shownBlockedLaneMask || _skyBlocked != _shownSkyBlocked
                || _npcExempt != _shownNpcExempt;
            _shownBlockedLaneMask = _blockedLaneMask;
            _shownSkyBlocked = _skyBlocked;
            _shownNpcExempt = _npcExempt;

            if (obstructed)
            {
                if (!_isObstructed || _violationReason != reason)
                {
                    stateChanged = true;
                }

                _isObstructed = true;
                _violationReason = reason;

                if (MyAPIGateway.Session != null && MyAPIGateway.Session.IsServer)
                {
                    if (_sorter.Enabled)
                    {
                        SetReEnableFlag(true);
                        SetEnabled(false);
                    }
                }
            }
            else
            {
                if (_isObstructed)
                {
                    stateChanged = true;
                }

                _isObstructed = false;
                _violationReason = "";

                // Seamless Auto-Re-Enable
                if (_wasEnabledBeforeObstruction)
                {
                    if (MyAPIGateway.Session != null && MyAPIGateway.Session.IsServer)
                    {
                        SetEnabled(true);
                    }
                    SetReEnableFlag(false);
                    _refreshBeamTicks = 3;
                    NeedsUpdate |= MyEntityUpdateEnum.EACH_FRAME;
                }
            }

            if (stateChanged)
            {
                _terminalBlock?.RefreshCustomInfo();
            }

            if (TimingLog)
                LogTiming();
        }

        /// <summary>
        /// Switches the turret without OnEnabledChanged running a second check in the middle of this one.
        /// </summary>
        private void SetEnabled(bool value)
        {
            bool wasProcessing = _processingEnabledChange;
            _processingEnabledChange = true;
            try
            {
                _sorter.Enabled = value;
            }
            finally
            {
                _processingEnabledChange = wasProcessing;
            }
        }

        /// <summary>
        /// When TimingLog is on: every TimingLogEvery checks, writes their average and worst time and
        /// the average rays per check to the game log, then starts over.
        /// </summary>
        private static void LogTiming()
        {
            long ticks = _timer.ElapsedTicks;
            _timedChecks++;
            _timedTicks += ticks;
            if (ticks > _timedMaxTicks)
                _timedMaxTicks = ticks;

            if (_timedChecks < TimingLogEvery)
                return;

            double usPerTick = 1000000.0 / System.Diagnostics.Stopwatch.Frequency;
            MyLog.Default.WriteLineAndConsole(string.Format(
                "[GVK_SalvageTurretClearance] Timing: {0} checks, average {1:0} us, worst {2:0} us, {3:0.0} rays per check ({4})",
                _timedChecks, _timedTicks * usPerTick / _timedChecks, _timedMaxTicks * usPerTick, (double)_timedRays / _timedChecks,
                MyAPIGateway.Utilities.IsDedicated ? "dedicated server" : "client or local game"));

            _timedChecks = 0;
            _timedTicks = 0;
            _timedMaxTicks = 0;
            _timedRays = 0;
        }

        private static int CellIndex(int x, int y, int z)
        {
            return (((y - _skyBottom) * Width) + (x + HalfWidth)) * Width + (z + HalfWidth);
        }

        private static int CellIndex(Vector3I offset)
        {
            return CellIndex(offset.X, offset.Y, offset.Z);
        }

        private static int DoorIndex(int x, int layer, int z)
        {
            return ((layer * Width) + (x + HalfWidth)) * Width + (z + HalfWidth);
        }

        private static bool DoorAt(int x, int layer, int z)
        {
            return _anyDoor && _doorCells[DoorIndex(x, layer, z)];
        }

        /// <summary>
        /// Grid cell of offset (x, y, z): basePos + x*right + y*up - z*forward.
        /// </summary>
        private Vector3I GridCell(int x, int y, int z)
        {
            return _basePos + _cachedRightVec * x + _cachedUpVec * y - _cachedForwardVec * z;
        }

        /// <summary>
        /// Computes the world-space cell axes of the turret and the world AABB of the area (lanes and sky).
        /// Offset (x, y, z) maps to grid cell basePos + x*right + y*up - z*forward.
        /// </summary>
        private void ComputeWorldAxes(IMyCubeGrid grid)
        {
            MatrixD wm = grid.WorldMatrix;
            double gs = grid.GridSize;

            _wOrigin = grid.GridIntegerToWorld(_basePos);
            _wRight = Vector3D.TransformNormal(new Vector3D(_cachedRightVec.X, _cachedRightVec.Y, _cachedRightVec.Z), wm) * gs;
            _wUp = Vector3D.TransformNormal(new Vector3D(_cachedUpVec.X, _cachedUpVec.Y, _cachedUpVec.Z), wm) * gs;
            _wBack = Vector3D.TransformNormal(new Vector3D(-_cachedForwardVec.X, -_cachedForwardVec.Y, -_cachedForwardVec.Z), wm) * gs;
            _cellSizeSq = gs * gs;
            _zoneBox = ZoneBounds(_wOrigin, _wRight, _wUp, _wBack);
        }

        /// <summary>
        /// Axis-aligned bounds of the area, the lane layers and the sky, given the base cell centre and
        /// cell axes in any coordinate space.
        /// </summary>
        private static BoundingBoxD ZoneBounds(Vector3D origin, Vector3D right, Vector3D up, Vector3D back)
        {
            var min = new Vector3D(double.MaxValue);
            var max = new Vector3D(double.MinValue);

            for (int c = 0; c < 8; c++)
            {
                double sx = (c & 1) == 0 ? -(HalfWidth + 0.5) : HalfWidth + 0.5;
                double sy = (c & 2) == 0 ? WorkspaceBottom - 0.5 : _skyTop + 0.5;
                double sz = (c & 4) == 0 ? -(HalfWidth + 0.5) : HalfWidth + 0.5;
                var p = origin + right * sx + up * sy + back * sz;
                min = Vector3D.Min(min, p);
                max = Vector3D.Max(max, p);
            }

            return new BoundingBoxD(min, max);
        }

        private void MarkOwnGrid(IMyCubeGrid grid)
        {
            for (int i = 0; i < ClearanceOffsets.Length; i++)
            {
                var offset = ClearanceOffsets[i];
                var slim = grid.GetCubeBlock(GridCell(offset.X, offset.Y, offset.Z));
                if (slim != null && slim.FatBlock != _sorter)
                {
                    _occupied[CellIndex(offset)] = true;
                }
            }

            // Doors in the lane layers, which CastLane counts as closed.
            for (int h = 0; h < LaneHeights; h++)
            {
                for (int x = -HalfWidth; x <= HalfWidth; x++)
                {
                    for (int z = -HalfWidth; z <= HalfWidth; z++)
                    {
                        if (x == 0 && z == 0)
                            continue;

                        var slim = grid.GetCubeBlock(GridCell(x, WorkspaceBottom + h, z));
                        if (slim != null && slim.FatBlock is IMyDoor)
                        {
                            _doorCells[DoorIndex(x, h, z)] = true;
                            _anyDoor = true;
                        }
                    }
                }
            }
        }

        /// <summary>
        /// Marks the sky cells, and the lane cells holding a door, that a counted grid's blocks fill. Any part
        /// of the grid in a cell counts, small grid included. It reads whichever is fewer: the grid's own
        /// cells inside the area, or all its blocks. So a big base beside the turret costs a few hundred
        /// lookups, and a small subgrid only its own blocks.
        /// </summary>
        private void MarkGrid(IMyCubeGrid other)
        {
            // The area's corners in the other grid's cell coordinates.
            MatrixD inv = other.WorldMatrixNormalizedInv;
            double gs = other.GridSize;
            var lo = new Vector3D(double.MaxValue);
            var hi = new Vector3D(double.MinValue);

            for (int c = 0; c < 8; c++)
            {
                double sx = (c & 1) == 0 ? -(HalfWidth + 0.5) : HalfWidth + 0.5;
                double sy = (c & 2) == 0 ? WorkspaceBottom - 0.5 : _skyTop + 0.5;
                double sz = (c & 4) == 0 ? -(HalfWidth + 0.5) : HalfWidth + 0.5;
                Vector3D corner = _wOrigin + _wRight * sx + _wUp * sy + _wBack * sz;
                Vector3D local;
                Vector3D.Transform(ref corner, ref inv, out local);
                lo = Vector3D.Min(lo, local);
                hi = Vector3D.Max(hi, local);
            }

            var min = Vector3I.Max(new Vector3I((int)Math.Floor(lo.X / gs + 0.5), (int)Math.Floor(lo.Y / gs + 0.5), (int)Math.Floor(lo.Z / gs + 0.5)), other.Min);
            var max = Vector3I.Min(new Vector3I((int)Math.Floor(hi.X / gs + 0.5), (int)Math.Floor(hi.Y / gs + 0.5), (int)Math.Floor(hi.Z / gs + 0.5)), other.Max);
            if (min.X > max.X || min.Y > max.Y || min.Z > max.Z)
                return;

            long cells = (long)(max.X - min.X + 1) * (max.Y - min.Y + 1) * (max.Z - min.Z + 1);
            var cube = other as Sandbox.Game.Entities.MyCubeGrid;
            long blocks = cube != null ? cube.BlocksCount : long.MaxValue;

            if (cells <= blocks)
            {
                for (int x = min.X; x <= max.X; x++)
                {
                    for (int y = min.Y; y <= max.Y; y++)
                    {
                        for (int z = min.Z; z <= max.Z; z++)
                        {
                            var cell = new Vector3I(x, y, z);
                            var slim = other.GetCubeBlock(cell);
                            if (slim != null)
                                MarkWorldPoint(other.GridIntegerToWorld(cell), slim.FatBlock is IMyDoor);
                        }
                    }
                }

                return;
            }

            _subgridBlocks.Clear();
            other.GetBlocks(_subgridBlocks);

            for (int b = 0; b < _subgridBlocks.Count; b++)
            {
                var slim = _subgridBlocks[b];
                var bmin = slim.Min;
                var bmax = slim.Max;
                bool door = slim.FatBlock is IMyDoor;

                for (int x = bmin.X; x <= bmax.X; x++)
                    for (int y = bmin.Y; y <= bmax.Y; y++)
                        for (int z = bmin.Z; z <= bmax.Z; z++)
                            MarkWorldPoint(other.GridIntegerToWorld(new Vector3I(x, y, z)), door);
            }

            _subgridBlocks.Clear();
        }

        private void MarkWorldPoint(Vector3D world, bool door)
        {
            var d = world - _wOrigin;
            int x = (int)Math.Floor(Vector3D.Dot(d, _wRight) / _cellSizeSq + 0.5);
            int y = (int)Math.Floor(Vector3D.Dot(d, _wUp) / _cellSizeSq + 0.5);
            int z = (int)Math.Floor(Vector3D.Dot(d, _wBack) / _cellSizeSq + 0.5);

            if (x < -HalfWidth || x > HalfWidth || z < -HalfWidth || z > HalfWidth)
                return;

            if (y >= _skyBottom && y <= _skyTop)
            {
                _occupied[CellIndex(x, y, z)] = true;
            }
            else if (door && y >= WorkspaceBottom && y < _skyBottom && (x != 0 || z != 0))
            {
                _doorCells[DoorIndex(x, y - WorkspaceBottom, z)] = true;
                _anyDoor = true;
            }
        }

        /// <summary>
        /// Casts a lane's rays, one per layer, into _rayBlocked. Returns true if all are clear. Without
        /// detail (dedicated server) it stops at the first blocked layer.
        /// A diagonal passes exactly through the corner where its two side cells meet, where a ray could
        /// graze either block or neither. So it casts two rays shifted a little to either side of the line,
        /// and a layer is blocked only if both are: by a block on the line, or by two blocks meeting corner
        /// to corner across it. A block on one side only leaves the diagonal open.
        /// A door in a cell a ray crosses blocks it, open or shut: a door raises no event when it moves,
        /// so an open door would otherwise hide a shut one until the next check.
        /// </summary>
        private bool CastLane(int lane, bool detail)
        {
            int dx = LaneX[lane];
            int dz = LaneZ[lane];
            bool open = true;

            for (int h = 0; h < LaneHeights; h++)
            {
                double y = WorkspaceBottom + h;
                bool blocked;

                if (dx != 0 && dz != 0)
                {
                    // Ray A runs on the X side of the diagonal, ray B on the Z side; each crosses 4 cells.
                    blocked = (DoorAt(dx, h, 0) || DoorAt(dx, h, dz) || DoorAt(2 * dx, h, dz) || DoorAt(2 * dx, h, 2 * dz)
                            || RayBlocked(dx * (RayStart + DiagonalShift), y, dz * RayStart, dx * RayEnd, dz * (RayEnd - DiagonalShift)))
                        && (DoorAt(0, h, dz) || DoorAt(dx, h, dz) || DoorAt(dx, h, 2 * dz) || DoorAt(2 * dx, h, 2 * dz)
                            || RayBlocked(dx * RayStart, y, dz * (RayStart + DiagonalShift), dx * (RayEnd - DiagonalShift), dz * RayEnd));
                }
                else
                {
                    blocked = DoorAt(dx, h, dz) || DoorAt(2 * dx, h, 2 * dz)
                        || RayBlocked(dx * RayStart, y, dz * RayStart, dx * RayEnd, dz * RayEnd);
                }

                _rayBlocked[lane * LaneHeights + h] = blocked;
                if (blocked)
                {
                    open = false;
                    if (!detail)
                        break;
                }
            }

            return open;
        }

        /// <summary>
        /// Casts one physics ray between two points given in cells in the turret's frame, at layer y.
        /// Blocked by any block of the turret's grid or a counted grid (_countedGrids), except the turret
        /// itself and its moving parts. Terrain, characters, loose items and grids that don't count are ignored.
        /// </summary>
        private bool RayBlocked(double x0, double y, double z0, double x1, double z1)
        {
            Vector3D from = _wOrigin + _wRight * x0 + _wUp * y + _wBack * z0;
            Vector3D to = _wOrigin + _wRight * x1 + _wUp * y + _wBack * z1;
            MyAPIGateway.Physics.CastRay(from, to, _hits, RaycastLayer);
            if (TimingLog)
                _timedRays++;

            for (int i = 0; i < _hits.Count; i++)
            {
                var hit = _hits[i];
                IMyCubeGrid hitGrid = null;

                // Subparts lead up to their block, blocks to their grid. Stop at the turret's own parts.
                for (var e = hit.HitEntity; e != null && e != _sorter; e = e.Parent)
                {
                    hitGrid = e as IMyCubeGrid;
                    if (hitGrid != null)
                        break;
                }

                if (hitGrid == null || (hitGrid != _trackedGrid && !_countedGrids.Contains(hitGrid)))
                    continue;

                // A hit inside the turret's own cell is the turret: no other block can be there.
                var d = hit.Position - _wOrigin;
                if (Math.Abs(Vector3D.Dot(d, _wRight)) < 0.5 * _cellSizeSq && Math.Abs(Vector3D.Dot(d, _wBack)) < 0.5 * _cellSizeSq)
                    continue;

                return true;
            }

            return false;
        }

        /// <summary>
        /// Sets the auto-re-enable flag and, on the server, keeps it in the block's mod storage
        /// so a turret the rule switched off still comes back on after a restart.
        /// </summary>
        private void SetReEnableFlag(bool value)
        {
            _wasEnabledBeforeObstruction = value;

            if (MyAPIGateway.Session == null || !MyAPIGateway.Session.IsServer || Entity == null)
                return;

            if (value)
            {
                if (Entity.Storage == null)
                    Entity.Storage = new MyModStorageComponent();

                Entity.Storage.SetValue(ReEnableStorageGuid, "1");
            }
            else if (Entity.Storage != null)
            {
                Entity.Storage.RemoveValue(ReEnableStorageGuid);
            }
        }

        private void AppendCustomInfo(IMyTerminalBlock block, StringBuilder sb)
        {
            sb.AppendLine();
            sb.AppendLine("=== Mount Clearance Status ===");

            if (_npcExempt)
            {
                sb.AppendLine("Status: [NPC - CLEARANCE NOT ENFORCED]");
                sb.AppendLine();
                return;
            }

            if (_isObstructed)
            {
                sb.AppendLine("Status: [OFFLINE - MOUNT OBSTRUCTED]");
                sb.AppendLine(string.Format("Reason: {0}", _violationReason));
            }
            else
            {
                sb.AppendLine("Status: [ONLINE - CLEAR]");
            }

            sb.AppendLine();
            sb.AppendLine(string.Format(" • Sight lanes ({0} directions out to the 5x5 edge, min {1} open): {2} open {3}",
                LaneCount, MinOpenLanes, _openLanes, _lanesObstructed ? "[OBSTRUCTED]" : "[CLEAR]"));
            if (_blockedLaneMask != 0)
            {
                sb.Append("   Blocked: ");
                bool first = true;
                for (int lane = 0; lane < LaneCount; lane++)
                {
                    if ((_blockedLaneMask & (1 << lane)) == 0)
                        continue;
                    if (!first)
                        sb.Append(", ");
                    sb.Append(LaneNames[lane]);
                    first = false;
                }
                sb.AppendLine();
            }
            sb.AppendLine(string.Format(" • Sky ({0}x{0}x{1}, 100% clear): {2} of {3} cells blocked {4}",
                Width, SkyLayers, _skyBlocked, _skyCells, _skyObstructed ? "[OBSTRUCTED]" : "[CLEAR]"));
            sb.AppendLine("A lane is open when its line at every height is clear.");
            sb.AppendLine("Your and your faction's grids count; other");
            sb.AppendLine("factions', NPC grids, terrain and people do not.");

            if (_isObstructed)
            {
                sb.AppendLine();
                sb.AppendLine("Toggle 'Show Clearance Zone' below to see the holographic guide.");
            }

            sb.AppendLine();
        }

        private static void CreateTerminalControls()
        {
            if (_terminalControlsInitialized)
                return;

            _terminalControlsInitialized = true;

            var toggle = MyAPIGateway.TerminalControls.CreateControl<IMyTerminalControlOnOffSwitch, IMyConveyorSorter>("GVK_ShowClearanceZone");
            toggle.Title = MyStringId.GetOrCompute("Show Clearance Zone");
            toggle.Tooltip = MyStringId.GetOrCompute("Displays a holographic wireframe of the turret's clearance zones.");
            toggle.OnText = MyStringId.GetOrCompute("Visible");
            toggle.OffText = MyStringId.GetOrCompute("Hidden");
            toggle.Getter = (b) =>
            {
                var logic = b.GameLogic?.GetAs<GVK_SalvageTurretClearance>();
                return logic != null && logic.ShowClearanceWireframe;
            };
            toggle.Setter = (b, v) =>
            {
                var logic = b.GameLogic?.GetAs<GVK_SalvageTurretClearance>();
                if (logic != null) logic.ShowClearanceWireframe = v;
            };
            toggle.Visible = (b) => b.BlockDefinition.SubtypeId == "GVK_LargeSalvageBeamTurret";

            MyAPIGateway.TerminalControls.AddControl<IMyConveyorSorter>(toggle);
        }

        public override void Close()
        {
            ActiveDrawTurrets.Remove(this);

            if (_trackedGrid != null)
            {
                _trackedGrid.OnBlockAdded -= OnGridModified;
                _trackedGrid.OnBlockRemoved -= OnGridModified;
                _trackedGrid.OnGridSplit -= OnGridSplit;
                _trackedGrid = null;
            }

            if (_terminalBlock != null)
            {
                _terminalBlock.AppendingCustomInfo -= AppendCustomInfo;
            }

            if (_sorter != null)
            {
                _sorter.EnabledChanged -= OnEnabledChanged;
            }

            _sorter = null;
            _terminalBlock = null;
            _initialized = false;

            base.Close();
        }

        /// <summary>
        /// Clears all static state between session loads. Must be called from the session
        /// component's UnloadData() to prevent stale entries in ActiveDrawTurrets (which
        /// would reference disposed entities) and to allow terminal controls to re-register
        /// on the next world load. (Audit #5, #6)
        /// </summary>
        internal static void ResetSessionState()
        {
            ActiveDrawTurrets.Clear();
            _terminalControlsInitialized = false;
            _groupGrids.Clear();
            _subgridBlocks.Clear();
            _hits.Clear();
            _nearEntities.Clear();
            _countedGrids.Clear();
            _gridBuilders.Clear();
        }
    }

    /// <summary>
    /// Client-side session component that renders the holographic clearance wireframe
    /// for any turrets that have the terminal toggle enabled.
    /// Also responsible for cleaning up static state on session unload. (Audit #5, #6)
    /// </summary>
    [MySessionComponentDescriptor(MyUpdateOrder.NoUpdate)]
    public class GVK_ClearanceDrawSession : MySessionComponentBase
    {
        private static readonly MyStringId WireframeMaterial = MyStringId.GetOrCompute("GizmoDrawLine");
        private static readonly Vector4 LaneClearColor = new Color(60, 230, 90, 200).ToVector4();
        private static readonly Vector4 LaneBlockedColor = new Color(255, 50, 50, 200).ToVector4();

        // Snapshot buffer: reused each frame to avoid iterating the live HashSet from
        // the render thread while the sim thread may be modifying it. (Audit #12)
        private readonly List<GVK_SalvageTurretClearance> _drawSnapshot = new List<GVK_SalvageTurretClearance>();


        public override void Draw()
        {
            base.Draw();

            if (MyAPIGateway.Session == null || GVK_SalvageTurretClearance.ActiveDrawTurrets.Count == 0)
                return;

            var cameraPos = MyAPIGateway.Session.Camera?.Position ?? Vector3D.Zero;

            // Snapshot the set to avoid iterating a live collection from the render thread
            // while the sim thread may be adding/removing entries via ShowClearanceWireframe
            // or Close(). The list is reused (no allocation after first frame). (Audit #12)
            _drawSnapshot.Clear();
            _drawSnapshot.AddRange(GVK_SalvageTurretClearance.ActiveDrawTurrets);

            for (int i = 0; i < _drawSnapshot.Count; i++)
            {
                var turret = _drawSnapshot[i];
                if (turret.Sorter == null || turret.Sorter.MarkedForClose || turret.Sorter.CubeGrid == null)
                    continue;

                var grid = turret.Sorter.CubeGrid;
                var baseWorldPos = grid.GridIntegerToWorld(turret.BasePos);

                // Cull wireframe if camera is further than 50m
                if (Vector3D.DistanceSquared(cameraPos, baseWorldPos) > 2500.0)
                    continue;

                // Build world transformation aligned to turret orientation centered on base cell
                MatrixD turretWorld = turret.Sorter.WorldMatrix;
                turretWorld.Translation = baseWorldPos;

                // Sight lanes: one line per layer, from the turret's side to the 5x5 edge, green if clear.
                double gs = grid.GridSize;
                Vector3D up = turretWorld.Up * gs;
                Vector3D right = turretWorld.Right * gs;
                Vector3D back = turretWorld.Backward * gs;
                for (int lane = 0; lane < GVK_SalvageTurretClearance.LaneCount; lane++)
                {
                    Vector3D dir = right * GVK_SalvageTurretClearance.LaneX[lane] + back * GVK_SalvageTurretClearance.LaneZ[lane];
                    for (int h = 0; h < GVK_SalvageTurretClearance.LaneHeights; h++)
                    {
                        Vector3D level = baseWorldPos + up * (GVK_SalvageTurretClearance.WorkspaceBottomLayer + h);
                        Vector4 color = turret.RayBlockedAt(lane, h) ? LaneBlockedColor : LaneClearColor;
                        MySimpleObjectDraw.DrawLine(level + dir * 0.5, level + dir * GVK_SalvageTurretClearance.RayEnd, WireframeMaterial, ref color, 0.05f);
                    }
                }

                // Sky box in the turret's frame, centred on its bottom cell.
                Color colorSky = turret.SkyObstructed ? new Color(255, 50, 50, 180) : new Color(100, 180, 255, 160);
                double half = 2.5 * gs;
                var sky = new BoundingBoxD(new Vector3D(-half, (GVK_SalvageTurretClearance.SkyBottom - 0.5) * gs, -half),
                    new Vector3D(half, (GVK_SalvageTurretClearance.SkyTop + 0.5) * gs, half));
                MySimpleObjectDraw.DrawTransparentBox(ref turretWorld, ref sky, ref colorSky, MySimpleObjectRasterizer.Wireframe, 1, 0.04f, null, WireframeMaterial, false);
            }
        }

        /// <summary>
        /// Clears all static state when the world unloads. Prevents stale ActiveDrawTurrets
        /// entries from referencing disposed entities and ensures terminal controls re-register
        /// properly when a new world loads in the same game process. (Audit #5, #6)
        /// </summary>
        protected override void UnloadData()
        {
            GVK_SalvageTurretClearance.ResetSessionState();
            _drawSnapshot.Clear();
            base.UnloadData();
        }
    }
}