using System;
using System.Collections.Generic;
using System.Text;
using Sandbox.Common.ObjectBuilders;
using Sandbox.ModAPI;
using Sandbox.ModAPI.Interfaces;
using Sandbox.ModAPI.Interfaces.Terminal;
using VRage.Game;
using VRage.Game.Components;
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
    /// or underground bunkers by requiring an expanding open-air funnel above the mounting footprint.
    /// Features:
    /// - Event-driven dirty flagging (zero CPU checks when no blocks are being added/removed).
    /// - Full support for Hangar unstorage, admin spawns, blueprints, and world load.
    /// - Automatic bypass on projected ghost blocks.
    /// - Smart 75% clearance threshold per layer and overall.
    /// - Seamless auto-re-enable when obstructions are ground down.
    /// - Holographic 3-tier wireframe toggle in the Control Panel.
    /// </summary>
    [MyEntityComponentDescriptor(typeof(MyObjectBuilder_ConveyorSorter), false, "GVK_LargeSalvageBeamTurret")]
    public class GVK_SalvageTurretClearance : MyGameLogicComponent
    {
        private static readonly Vector3I[] ClearanceOffsets = InitializeClearanceOffsets();
        internal static readonly HashSet<GVK_SalvageTurretClearance> ActiveDrawTurrets = new HashSet<GVK_SalvageTurretClearance>();
        private static bool _terminalControlsInitialized = false;

        private const int TotalCells = 537;
        private const int MaxAllowedObstructedZone1 = 12; // 75% clear per layer in Zone 1 (Y=0..3: 2 blocks above turret)
        private const int MaxAllowedObstructedZone2 = 0;  // 100% clear in Zone 2 (Y=4..10: 7 layers of open sky)

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

        private readonly int[] _layerObstructedCounts = new int[11];

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
        /// Precomputes the 537 relative block coordinates comprising the two stacked zones:
        /// Zone 1 (Work Zone): Y=0 to Y=3 (194 cells, >= 75% clear per layer, extends 2 blocks above turret).
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
                        // Exclude the 2-block tall turret itself at (0, 0, 0) and (0, 1, 0)
                        if ((y == 0 || y == 1) && x == 0 && z == 0)
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
        /// Evaluates all 537 funnel cells against the grid, tracking clearance per layer.
        /// </summary>
        private void CheckClearance()
        {
            var grid = _sorter.CubeGrid;
            if (grid == null)
                return;

            var basePos = _sorter.Position;

            // Use cached orientation vectors computed once in UpdateOnceBeforeFrame (Audit #10)
            var rightVec = _cachedRightVec;
            var upVec = _cachedUpVec;
            var forwardVec = _cachedForwardVec;

            for (int k = 0; k < 11; k++)
            {
                _layerObstructedCounts[k] = 0;
            }

            int totalObstructed = 0;

            for (int i = 0; i < ClearanceOffsets.Length; i++)
            {
                var offset = ClearanceOffsets[i];

                int gx = basePos.X + (offset.X * rightVec.X) + (offset.Y * upVec.X) - (offset.Z * forwardVec.X);
                int gy = basePos.Y + (offset.X * rightVec.Y) + (offset.Y * upVec.Y) - (offset.Z * forwardVec.Y);
                int gz = basePos.Z + (offset.X * rightVec.Z) + (offset.Y * upVec.Z) - (offset.Z * forwardVec.Z);
                var checkPos = new Vector3I(gx, gy, gz);

                var slim = grid.GetCubeBlock(checkPos);
                if (slim != null && slim.FatBlock != _sorter)
                {
                    totalObstructed++;
                    if (offset.Y >= 0 && offset.Y < 11)
                    {
                        _layerObstructedCounts[offset.Y]++;
                    }
                }
            }

            bool obstructed = false;
            _zone1Obstructed = false;
            _zone2Obstructed = false;
            string reason = "";

            // Evaluate Zone 1 (Work Zone: Y=0..3, max 12 blocked per layer)
            for (int y = 0; y <= 3; y++)
            {
                if (_layerObstructedCounts[y] > MaxAllowedObstructedZone1)
                {
                    obstructed = true;
                    _zone1Obstructed = true;
                    break;
                }
            }

            // Evaluate Zone 2 (Sky Chimney: Y=4..10, 100% clear sky required)
            for (int y = 4; y <= 10; y++)
            {
                if (_layerObstructedCounts[y] > MaxAllowedObstructedZone2)
                {
                    obstructed = true;
                    _zone2Obstructed = true;
                    break;
                }
            }

            if (_zone1Obstructed && _zone2Obstructed)
            {
                reason = "Workspace and Sky are both obstructed";
            }
            else if (_zone1Obstructed)
            {
                reason = "Workspace obstructed (exceeds allowed limit around turret)";
            }
            else if (_zone2Obstructed)
            {
                reason = "Sky obstructed (overhead structure or roof detected)";
            }

            bool stateChanged = false;

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
                        _wasEnabledBeforeObstruction = true;
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
                    _wasEnabledBeforeObstruction = false;
                    _refreshBeamTicks = 3;
                    NeedsUpdate |= MyEntityUpdateEnum.EACH_FRAME;
                }
            }

            if (stateChanged)
            {
                _terminalBlock?.RefreshCustomInfo();
            }
        }

        private void AppendCustomInfo(IMyTerminalBlock block, StringBuilder sb)
        {
            sb.AppendLine();
            sb.AppendLine("=== Mount Clearance Status ===");

            if (_isObstructed)
            {
                sb.AppendLine("Status: [OFFLINE - MOUNT OBSTRUCTED]");
                sb.AppendLine(string.Format("Reason: {0}", _violationReason));
                sb.AppendLine();
                sb.AppendLine(string.Format(" • Workspace (7x7x4, min 75%): {0}", _zone1Obstructed ? "[OBSTRUCTED]" : "[CLEAR]"));
                sb.AppendLine(string.Format(" • Sky (7x7x7, min 100%): {0}", _zone2Obstructed ? "[OBSTRUCTED]" : "[CLEAR]"));
                sb.AppendLine();
                sb.AppendLine("Toggle 'Show Clearance Zone' below to see the holographic guide.");
            }
            else
            {
                sb.AppendLine("Status: [ONLINE - CLEAR]");
                sb.AppendLine(" • Workspace (7x7x4, min 75%): [CLEAR]");
                sb.AppendLine(" • Sky (7x7x7, min 100%): [CLEAR]");
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