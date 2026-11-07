using System;
using System.Collections.Generic;
using System.Text;
using Sandbox.Common.ObjectBuilders;
using Sandbox.Game.Entities;
using Sandbox.Game.EntityComponents;
using Sandbox.ModAPI;
using Sandbox.ModAPI.Interfaces;
using Sandbox.ModAPI.Interfaces.Terminal;
using VRage.Game;
using VRage.Game.Components;
using VRage.Game.ModAPI;
using VRage.ModAPI;
using VRage.ObjectBuilders;
using VRage.Utils;
using VRage.Voxels;
using VRageMath;

namespace GVK_ToolCore_Tools
{
    /// <summary>
    /// Enforces the clearance rule for the GVK Large Salvage Beam Turret.
    /// Prevents players from sinking long-range beam turrets into armored chimneys, silos,
    /// or underground bunkers by requiring an expanding open-air funnel above the mounting footprint.
    /// Features:
    /// - Two zones: a 7x7x4 workspace (at most 25% of its cells blocked) and a 7x7x7 sky (no cells blocked).
    /// - A cell is blocked by the turret's own grid, its rotor/hinge/piston subgrids, or terrain.
    /// - Re-checks on own-grid block changes and every ~10 s (subgrids and terrain raise no events).
    /// - Skips projected ghost blocks and NPC-owned turrets.
    /// - Auto-re-enables once clear; the flag survives a save and reload.
    /// - Holographic wireframe toggle in the Control Panel.
    /// </summary>
    [MyEntityComponentDescriptor(typeof(MyObjectBuilder_ConveyorSorter), false, "GVK_LargeSalvageBeamTurret")]
    public class GVK_SalvageTurretClearance : MyGameLogicComponent
    {
        private static readonly Vector3I[] ClearanceOffsets = InitializeClearanceOffsets();
        internal static readonly HashSet<GVK_SalvageTurretClearance> ActiveDrawTurrets = new HashSet<GVK_SalvageTurretClearance>();
        private static bool _terminalControlsInitialized = false;

        private const int TotalCells = 536;
        private const int WorkspaceCells = 193;            // Zone 1: 7x7x4 minus the turret's own 3 cells
        private const int MaxAllowedObstructedZone1 = 48;  // 75% of the whole workspace must stay clear (floor of 25% of 193)
        private const int MaxAllowedObstructedZone2 = 0;   // 100% clear in Zone 2 (Y=4..10: 7 layers of open sky)

        // Occupancy grid over the 7 x 11 x 7 zone, indexed by CellIndex(offset).
        private const int ZoneCellCount = 7 * 11 * 7;

        // Terrain: a cell counts as blocked when at least half of its 8 sample points are solid.
        // Read at voxel LOD 1 (2 m voxels) to keep the read to a few thousand voxels per check.
        private const int TerrainLod = 1;
        private const int TerrainSolidSamples = 4;
        private const byte VoxelSolidContent = 127;

        // Mod storage key for the auto-re-enable flag. Registered in Data/GVK_EntityComponents.sbc,
        // otherwise the game drops it on save.
        private static readonly Guid ReEnableStorageGuid = new Guid("AB503EF1-F20D-4F3A-A7EE-E7C67638EC0A");

        // Shared scratch buffers: every clearance check runs on the game thread, one at a time.
        private static MyStorageData _voxelData;
        private static readonly List<MyVoxelBase> _voxelMaps = new List<MyVoxelBase>();
        private static readonly List<MyVoxelBase> _voxelRoots = new List<MyVoxelBase>();
        private static readonly List<IMyCubeGrid> _groupGrids = new List<IMyCubeGrid>();
        private static readonly List<IMySlimBlock> _subgridBlocks = new List<IMySlimBlock>();
        private static readonly bool[] _occupied = new bool[ZoneCellCount];
        private static readonly bool[] _terrainCell = new bool[ZoneCellCount];

        private IMyFunctionalBlock _sorter;
        private IMyTerminalBlock _terminalBlock;
        private IMyCubeGrid _trackedGrid;

        private bool _isObstructed;
        private bool _zone1Obstructed;
        private bool _zone2Obstructed;
        private bool _wasEnabledBeforeObstruction;
        private bool _isDirty = true;
        private bool _initialized;
        private bool _showClearanceWireframe;

        private string _violationReason = "";
        private int _refreshBeamTicks;

        // Heartbeat: forces a full re-evaluation every ~10 seconds regardless of events.
        // Catches grid merges and any other silent grid mutations that bypass
        // OnBlockAdded/OnBlockRemoved events. (Audit #2)
        private const int HeartbeatInterval = 6; // 6 × Update100 (~100 ticks each) ≈ 600 ticks ≈ 10 sec
        private int _heartbeatCounter;

        // Reentrancy guard: prevents infinite EnabledChanged → CheckClearance → Enabled = false → EnabledChanged loop
        // if Keen ever changes event dispatch timing. (Audit #4)
        private bool _processingEnabledChange;

        // Cached block orientation vectors — these never change once the block is placed.
        // Avoids recomputing GetIntVector/GetFlippedDirection on every CheckClearance call. (Audit #10)
        private Vector3I _cachedRightVec;
        private Vector3I _cachedUpVec;
        private Vector3I _cachedForwardVec;

        private int _workspaceBlocked;
        private int _skyBlocked;
        private int _terrainBlocked;
        private bool _npcExempt;

        // Values last shown in the Control Panel, so it refreshes only when they change.
        private int _shownWorkspaceBlocked = -1;
        private int _shownSkyBlocked = -1;
        private int _shownTerrainBlocked = -1;
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
        public bool Zone1Obstructed { get { return _zone1Obstructed; } }
        public bool Zone2Obstructed { get { return _zone2Obstructed; } }
        public IMyFunctionalBlock Sorter { get { return _sorter; } }

        /// <summary>
        /// Precomputes the 536 relative block coordinates comprising the two stacked zones:
        /// Zone 1 (Work Zone): Y=0 to Y=3 (193 cells, >= 75% clear over the whole zone, extends 1 block above turret).
        /// Zone 2 (Sky Chimney): Y=4 to Y=10 (343 cells, 100% clear sky).
        /// </summary>
        private static Vector3I[] InitializeClearanceOffsets()
        {
            var list = new List<Vector3I>(TotalCells);

            // Levels 0 to 10 (11 layers total)
            for (int y = 0; y <= 10; y++)
            {
                for (int x = -3; x <= 3; x++)
                {
                    for (int z = -3; z <= 3; z++)
                    {
                        // Exclude the 3-block tall turret itself at (0, 0, 0), (0, 1, 0), and (0, 2, 0)
                        if ((y == 0 || y == 1 || y == 2) && x == 0 && z == 0)
                            continue;

                        list.Add(new Vector3I(x, y, z));
                    }
                }
            }

            return list.ToArray();
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

            _trackedGrid = _sorter.CubeGrid;
            _trackedGrid.OnBlockAdded += OnGridModified;
            _trackedGrid.OnBlockRemoved += OnGridModified;
            _trackedGrid.OnGridSplit += OnGridSplit;
            _sorter.EnabledChanged += OnEnabledChanged;

            if (_terminalBlock != null)
            {
                _terminalBlock.AppendingCustomInfo += AppendCustomInfo;
            }

            // Cache block orientation vectors — these are fixed once the block is placed
            // and never change, so computing them once avoids repeated lookups in CheckClearance. (Audit #10)
            var orientation = _sorter.Orientation;
            var rightDir = Base6Directions.GetFlippedDirection(orientation.Left);
            _cachedRightVec = Base6Directions.GetIntVector(rightDir);
            _cachedUpVec = Base6Directions.GetIntVector(orientation.Up);
            _cachedForwardVec = Base6Directions.GetIntVector(orientation.Forward);

            CreateTerminalControls();

            // Restore the auto-re-enable flag saved before the last restart.
            string stored;
            if (Entity.Storage != null && Entity.Storage.TryGetValue(ReEnableStorageGuid, out stored))
            {
                _wasEnabledBeforeObstruction = stored == "1";
            }

            NeedsUpdate = MyEntityUpdateEnum.EACH_100TH_FRAME;
            _initialized = true;
            _isDirty = true;

            // Immediate initial clearance check upon spawn / load / unhangar
            CheckClearance();
        }

        private void OnGridModified(IMySlimBlock slim)
        {
            _isDirty = true;
        }

        private void OnGridSplit(IMyCubeGrid grid1, IMyCubeGrid grid2)
        {
            _isDirty = true;

            // After a split, _trackedGrid may point at the orphaned half that no longer
            // contains the turret. Rebind events to the turret's actual grid. (Audit #15)
            if (_sorter == null || _sorter.MarkedForClose)
                return;

            var currentGrid = _sorter.CubeGrid;
            if (currentGrid != null && currentGrid != _trackedGrid)
            {
                _trackedGrid.OnBlockAdded -= OnGridModified;
                _trackedGrid.OnBlockRemoved -= OnGridModified;
                _trackedGrid.OnGridSplit -= OnGridSplit;

                _trackedGrid = currentGrid;
                _trackedGrid.OnBlockAdded += OnGridModified;
                _trackedGrid.OnBlockRemoved += OnGridModified;
                _trackedGrid.OnGridSplit += OnGridSplit;
            }
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

            // Heartbeat: periodically force a full re-evaluation regardless of dirty flag.
            // Catches grid merges and any other silent mutations that bypass
            // OnBlockAdded/OnBlockRemoved events. (Audit #2)
            _heartbeatCounter++;
            if (_heartbeatCounter >= HeartbeatInterval)
            {
                _heartbeatCounter = 0;
                _isDirty = true;
            }

            // Event-Driven: Only evaluate if the grid has been modified (or heartbeat fired)
            if (!_isDirty)
                return;

            _isDirty = false;
            CheckClearance();
        }

        /// <summary>
        /// Evaluates all 536 zone cells against the turret's grid, its mechanical subgrids and terrain,
        /// then applies the whole-workspace and sky limits.
        /// </summary>
        private void CheckClearance()
        {
            var grid = _sorter.CubeGrid;
            if (grid == null)
                return;

            _workspaceBlocked = 0;
            _skyBlocked = 0;
            _terrainBlocked = 0;
            _zone1Obstructed = false;
            _zone2Obstructed = false;

            // NPC turrets (owner has no Steam ID) skip the rule. "Nobody" ownership does not.
            long ownerId = _sorter.OwnerId;
            _npcExempt = ownerId != 0 && MyAPIGateway.Players.TryGetSteamId(ownerId) == 0;

            if (!_npcExempt)
            {
                Array.Clear(_occupied, 0, ZoneCellCount);
                Array.Clear(_terrainCell, 0, ZoneCellCount);
                ComputeWorldAxes(grid);

                MarkOwnGrid(grid);
                MarkMechanicalSubgrids(grid);
                MarkTerrain();

                for (int i = 0; i < ClearanceOffsets.Length; i++)
                {
                    int idx = CellIndex(ClearanceOffsets[i]);
                    if (!_occupied[idx])
                        continue;

                    if (ClearanceOffsets[i].Y <= 3)
                        _workspaceBlocked++;
                    else
                        _skyBlocked++;

                    if (_terrainCell[idx])
                        _terrainBlocked++;
                }

                _zone1Obstructed = _workspaceBlocked > MaxAllowedObstructedZone1;
                _zone2Obstructed = _skyBlocked > MaxAllowedObstructedZone2;
            }

            bool obstructed = _zone1Obstructed || _zone2Obstructed;
            string reason = "";

            if (_zone1Obstructed && _zone2Obstructed)
            {
                reason = "Workspace and Sky are both obstructed";
            }
            else if (_zone1Obstructed)
            {
                reason = string.Format("Workspace obstructed (more than {0} of {1} cells blocked)", MaxAllowedObstructedZone1, WorkspaceCells);
            }
            else if (_zone2Obstructed)
            {
                reason = "Sky obstructed (overhead structure, roof or terrain detected)";
            }

            // Refresh the Control Panel whenever the counts it shows change.
            bool stateChanged = _workspaceBlocked != _shownWorkspaceBlocked || _skyBlocked != _shownSkyBlocked
                || _terrainBlocked != _shownTerrainBlocked || _npcExempt != _shownNpcExempt;
            _shownWorkspaceBlocked = _workspaceBlocked;
            _shownSkyBlocked = _skyBlocked;
            _shownTerrainBlocked = _terrainBlocked;
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
                        _sorter.Enabled = false;
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
                        _sorter.Enabled = true;
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
        }

        private static int CellIndex(int x, int y, int z)
        {
            return ((y * 7) + (x + 3)) * 7 + (z + 3);
        }

        private static int CellIndex(Vector3I offset)
        {
            return CellIndex(offset.X, offset.Y, offset.Z);
        }

        /// <summary>
        /// Computes the world-space cell axes of the turret and the world AABB of both zones.
        /// Offset (x, y, z) maps to grid cell basePos + x*right + y*up - z*forward.
        /// </summary>
        private void ComputeWorldAxes(IMyCubeGrid grid)
        {
            MatrixD wm = grid.WorldMatrix;
            double gs = grid.GridSize;

            _wOrigin = grid.GridIntegerToWorld(_sorter.Position);
            _wRight = Vector3D.TransformNormal(new Vector3D(_cachedRightVec.X, _cachedRightVec.Y, _cachedRightVec.Z), wm) * gs;
            _wUp = Vector3D.TransformNormal(new Vector3D(_cachedUpVec.X, _cachedUpVec.Y, _cachedUpVec.Z), wm) * gs;
            _wBack = Vector3D.TransformNormal(new Vector3D(-_cachedForwardVec.X, -_cachedForwardVec.Y, -_cachedForwardVec.Z), wm) * gs;
            _cellSizeSq = gs * gs;
            _zoneBox = ZoneBounds(_wOrigin, _wRight, _wUp, _wBack);
        }

        /// <summary>
        /// Axis-aligned bounds of the full 7 x 11 x 7 zone, given its base cell centre and cell axes
        /// in any coordinate space.
        /// </summary>
        private static BoundingBoxD ZoneBounds(Vector3D origin, Vector3D right, Vector3D up, Vector3D back)
        {
            var min = new Vector3D(double.MaxValue);
            var max = new Vector3D(double.MinValue);

            for (int c = 0; c < 8; c++)
            {
                double sx = (c & 1) == 0 ? -3.5 : 3.5;
                double sy = (c & 2) == 0 ? -0.5 : 10.5;
                double sz = (c & 4) == 0 ? -3.5 : 3.5;
                var p = origin + right * sx + up * sy + back * sz;
                min = Vector3D.Min(min, p);
                max = Vector3D.Max(max, p);
            }

            return new BoundingBoxD(min, max);
        }

        private void MarkOwnGrid(IMyCubeGrid grid)
        {
            var basePos = _sorter.Position;
            var rightVec = _cachedRightVec;
            var upVec = _cachedUpVec;
            var forwardVec = _cachedForwardVec;

            for (int i = 0; i < ClearanceOffsets.Length; i++)
            {
                var offset = ClearanceOffsets[i];

                int gx = basePos.X + (offset.X * rightVec.X) + (offset.Y * upVec.X) - (offset.Z * forwardVec.X);
                int gy = basePos.Y + (offset.X * rightVec.Y) + (offset.Y * upVec.Y) - (offset.Z * forwardVec.Y);
                int gz = basePos.Z + (offset.X * rightVec.Z) + (offset.Y * upVec.Z) - (offset.Z * forwardVec.Z);

                var slim = grid.GetCubeBlock(new Vector3I(gx, gy, gz));
                if (slim != null && slim.FatBlock != _sorter)
                {
                    _occupied[CellIndex(offset)] = true;
                }
            }
        }

        /// <summary>
        /// Marks cells holding any block of a grid joined to the turret's grid by rotors, hinges,
        /// pistons or suspension. Any part of a block in a cell blocks it, small grid included.
        /// Unconnected grids never count, so nobody can switch the turret off by parking over it.
        /// </summary>
        private void MarkMechanicalSubgrids(IMyCubeGrid grid)
        {
            _groupGrids.Clear();
            MyAPIGateway.GridGroups.GetGroup(grid, GridLinkTypeEnum.Mechanical, _groupGrids);

            for (int g = 0; g < _groupGrids.Count; g++)
            {
                var sub = _groupGrids[g];
                if (sub == grid || sub.MarkedForClose || sub.Physics == null)
                    continue;

                if (!_zoneBox.Intersects(sub.WorldAABB))
                    continue;

                _subgridBlocks.Clear();
                sub.GetBlocks(_subgridBlocks);

                for (int b = 0; b < _subgridBlocks.Count; b++)
                {
                    var slim = _subgridBlocks[b];
                    var min = slim.Min;
                    var max = slim.Max;

                    for (int x = min.X; x <= max.X; x++)
                        for (int y = min.Y; y <= max.Y; y++)
                            for (int z = min.Z; z <= max.Z; z++)
                                MarkWorldPoint(sub.GridIntegerToWorld(new Vector3I(x, y, z)));
                }
            }

            _subgridBlocks.Clear();
            _groupGrids.Clear();
        }

        private void MarkWorldPoint(Vector3D world)
        {
            var d = world - _wOrigin;
            int x = (int)Math.Floor(Vector3D.Dot(d, _wRight) / _cellSizeSq + 0.5);
            int y = (int)Math.Floor(Vector3D.Dot(d, _wUp) / _cellSizeSq + 0.5);
            int z = (int)Math.Floor(Vector3D.Dot(d, _wBack) / _cellSizeSq + 0.5);

            if (x < -3 || x > 3 || y < 0 || y > 10 || z < -3 || z > 3)
                return;

            _occupied[CellIndex(x, y, z)] = true;
        }

        /// <summary>
        /// Marks cells that are mostly terrain: a pit, trench, cave or overhang around the turret.
        /// </summary>
        private void MarkTerrain()
        {
            _voxelMaps.Clear();
            _voxelRoots.Clear();
            var box = _zoneBox;
            MyGamePruningStructure.GetAllVoxelMapsInBox(ref box, _voxelMaps);

            for (int i = 0; i < _voxelMaps.Count; i++)
            {
                var voxel = _voxelMaps[i];
                if (voxel == null || voxel.MarkedForClose)
                    continue;

                // A planet's physics sections share its storage; read each storage once, from its root.
                var root = voxel.RootVoxel;
                if (root != null && !root.MarkedForClose && !_voxelRoots.Contains(root))
                    _voxelRoots.Add(root);
            }

            for (int i = 0; i < _voxelRoots.Count; i++)
            {
                MarkTerrainFrom(_voxelRoots[i]);
            }

            _voxelMaps.Clear();
            _voxelRoots.Clear();
        }

        private void MarkTerrainFrom(MyVoxelBase root)
        {
            var storage = ((IMyVoxelBase)root).Storage;
            if (storage == null)
                return;

            // Storage coordinates (LOD 0, 1 m voxels) of world point p: Transform(p, inv) + half size + StorageMin.
            MatrixD inv = MatrixD.Invert(root.WorldMatrix);
            Vector3D shift = new Vector3D(root.SizeInMetresHalf) + new Vector3D(root.StorageMin.X, root.StorageMin.Y, root.StorageMin.Z);

            var sOrigin = Vector3D.Transform(_wOrigin, inv) + shift;
            var sRight = Vector3D.TransformNormal(_wRight, inv);
            var sUp = Vector3D.TransformNormal(_wUp, inv);
            var sBack = Vector3D.TransformNormal(_wBack, inv);

            var bounds = ZoneBounds(sOrigin, sRight, sUp, sBack);
            var lo = Vector3I.Max(Vector3I.Floor(bounds.Min) - 1, Vector3I.Zero);
            var hi = Vector3I.Min(Vector3I.Ceiling(bounds.Max) + 1, storage.Size - 1);
            if (lo.X > hi.X || lo.Y > hi.Y || lo.Z > hi.Z)
                return;

            var loLod = lo >> TerrainLod;
            var hiLod = hi >> TerrainLod;

            if (_voxelData == null)
                _voxelData = new MyStorageData(MyStorageDataTypeFlags.Content);

            _voxelData.Resize(loLod, hiLod);
            storage.ReadRange(_voxelData, MyStorageDataTypeFlags.Content, TerrainLod, loLod, hiLod);

            var size = _voxelData.Size3D;
            double lodScale = 1.0 / (1 << TerrainLod);

            for (int i = 0; i < ClearanceOffsets.Length; i++)
            {
                var offset = ClearanceOffsets[i];
                int idx = CellIndex(offset);
                if (_occupied[idx])
                    continue;

                var centre = sOrigin + sRight * offset.X + sUp * offset.Y + sBack * offset.Z;
                int solid = 0;

                // 8 sample points, one at the centre of each octant of the cell.
                for (int s = 0; s < 8; s++)
                {
                    double dx = (s & 1) == 0 ? -0.25 : 0.25;
                    double dy = (s & 2) == 0 ? -0.25 : 0.25;
                    double dz = (s & 4) == 0 ? -0.25 : 0.25;
                    var p = (centre + sRight * dx + sUp * dy + sBack * dz) * lodScale;

                    var v = new Vector3I(
                        (int)Math.Floor(p.X + 0.5) - loLod.X,
                        (int)Math.Floor(p.Y + 0.5) - loLod.Y,
                        (int)Math.Floor(p.Z + 0.5) - loLod.Z);

                    if (v.X < 0 || v.Y < 0 || v.Z < 0 || v.X >= size.X || v.Y >= size.Y || v.Z >= size.Z)
                        continue;

                    if (_voxelData.Content(ref v) > VoxelSolidContent)
                        solid++;
                }

                if (solid >= TerrainSolidSamples)
                {
                    _occupied[idx] = true;
                    _terrainCell[idx] = true;
                }
            }
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
            sb.AppendLine(string.Format(" • Workspace (7x7x4, min 75% clear): {0} of max {1} cells blocked {2}",
                _workspaceBlocked, MaxAllowedObstructedZone1, _zone1Obstructed ? "[OBSTRUCTED]" : "[CLEAR]"));
            sb.AppendLine(string.Format(" • Sky (7x7x7, 100% clear): {0} cells blocked {1}",
                _skyBlocked, _zone2Obstructed ? "[OBSTRUCTED]" : "[CLEAR]"));
            if (_terrainBlocked > 0)
                sb.AppendLine(string.Format(" • Terrain fills {0} of those cells", _terrainBlocked));
            sb.AppendLine("Blocks, rotor/hinge/piston parts and terrain all count.");

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
            toggle.Tooltip = MyStringId.GetOrCompute("Displays a holographic wireframe of the required 7x7 mounting clearance column.");
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
            _voxelData = null;
            _voxelMaps.Clear();
            _voxelRoots.Clear();
            _groupGrids.Clear();
            _subgridBlocks.Clear();
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

        // Snapshot buffer: reused each frame to avoid iterating the live HashSet from
        // the render thread while the sim thread may be modifying it. (Audit #12)
        private readonly List<GVK_SalvageTurretClearance> _drawSnapshot = new List<GVK_SalvageTurretClearance>();

        // Zone 1 (Work Zone): 7x7x4 from Y=0 to Y=3 (17.5m wide, 10m tall, 17.5m deep, from Y=-1.25m to Y=+8.75m)
        private static readonly BoundingBoxD BoxZone1 = new BoundingBoxD(
            new Vector3D(-8.75, -1.25, -8.75),
            new Vector3D(8.75, 8.75, 8.75));

        // Zone 2 (Sky Chimney): 7x7x7 from Y=4 to Y=10 (17.5m wide, 17.5m tall, 17.5m deep, from Y=+8.75m to Y=+26.25m)
        private static readonly BoundingBoxD BoxZone2 = new BoundingBoxD(
            new Vector3D(-8.75, 8.75, -8.75),
            new Vector3D(8.75, 26.25, 8.75));

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
                var basePos = turret.Sorter.Position;
                var baseWorldPos = grid.GridIntegerToWorld(basePos);

                // Cull wireframe if camera is further than 50m
                if (Vector3D.DistanceSquared(cameraPos, baseWorldPos) > 2500.0)
                    continue;

                // Build world transformation aligned to turret orientation centered on base cell
                MatrixD turretWorld = turret.Sorter.WorldMatrix;
                turretWorld.Translation = baseWorldPos;

                Color colorZone1 = turret.Zone1Obstructed ? new Color(255, 50, 50, 180) : new Color(50, 220, 255, 180);
                Color colorZone2 = turret.Zone2Obstructed ? new Color(255, 50, 50, 180) : new Color(100, 180, 255, 160);

                var box1 = BoxZone1;
                var box2 = BoxZone2;

                // Render Zone 1 (Work Zone) and Zone 2 (Sky Chimney)
                MySimpleObjectDraw.DrawTransparentBox(ref turretWorld, ref box1, ref colorZone1, MySimpleObjectRasterizer.Wireframe, 1, 0.04f, null, WireframeMaterial, false);
                MySimpleObjectDraw.DrawTransparentBox(ref turretWorld, ref box2, ref colorZone2, MySimpleObjectRasterizer.Wireframe, 1, 0.04f, null, WireframeMaterial, false);
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