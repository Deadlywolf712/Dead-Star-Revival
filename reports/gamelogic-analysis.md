# Dead Star Game Logic Analysis

**Source**: `GameComponentsNeedle_Steam_Release.dll` (PE32+ x86-64, built 2016-07-19)
**Build path**: `E:\rel\Needle_Release\`
**Strings extracted**: 49,694

---

## 1. Match Lifecycle

### Match States [CONFIRMED]

The game controller uses `NNeedleGameControllerCommon::kMatchState_*` enum values. From strings and error messages:

- **kMatchState_Started** - Active gameplay (`GetMatchState() == NNeedleGameControllerCommon::kMatchState_Started`)
- Additional states implied by flow: Creating, Loading, Lobby, Playing, Finished

### Match Flow [CONFIRMED]

From `CComponentNeedleGameControllerDefault` and log strings:

1. **Matchmaking** - `CCPLdrNeedleNetworkClientMatchMaker` handles queue
   - States: `LobbyState_Matchmaking`, `LobbyState_NeedleEscape_Matchmaking`
   - Matchmaker sends request with: `Mode, ReqType, Type, Size, Contract, Party, Count, Crossplay, region(Default, Custom)`
   - Response: `Matchmaker: Request complete. Server address: %s:%d.`
2. **Lobby** - `CCPLdrNeedleUILobbyHelper`, `CCPLdrNeedleUILobbyPlayerEntry`
   - `DisplayLobby`, `~LOBBY_NEEDLE_LOBBY_TITLE~`
   - Reservation system: `CNeedleServerReservationService`
   - Region voting: `Vote_Choice1`, `Vote_Choice2`, `Vote_Random`
3. **Auto-Start/Balance** - `GameController::UpdateMatchAutoStart`
   - `enough connected - starting countdown`
   - `not enough connected - drifters=%d scavengers=%d minconnected=%d`
   - `starting auto-balance countdown`
   - `committing auto-balance...`
   - `canceling auto-balance`
4. **Loading** - `CCPLdrNeedleUILoadingScreenDisplay`, `AssetsLoading`
   - `~LOADING_MATCH_CONQUEST~`, `~LOADING_MATCH_HUNT~`, `~LOADING_MATCH_RECON~`, etc.
   - Mode-specific tips: `LOADING_CONQUEST_TIP_`, `LOADING_HUNT_TIP_`, etc.
5. **Galaxy Creation** - `CCPLdrNeedleGalaxyGenerator` (server-side)
   - `ERROR: StartGalaxyCreation() can't be called more than once.`
6. **Playing** - Match runs with ticket system, spawning, etc.
   - `needle_MatchStartCountdown` controls pre-start countdown
7. **Match End** - Multiple end conditions trigger `OnEnteredStateFinished`
   - `CComponentNeedleGameControllerDefault::OnEnteredStateFinished - WriteMatchStats failed.`
   - `FinishedMatch`, `MatchEnded`
8. **After Action** - `CCPLdrNeedleUIAfterActionController`, `CCPLdrNeedleUIAfterActionAvailableSwitch`
   - Match stats written: `WriteMatchStats`, `needle_publishMatchStats`
9. **Restart** - `needle_MatchFinishedRestartTime`, `needle_ReturnToLobby`

### Key Match Config Vars [CONFIRMED]

| Variable | Purpose |
|----------|---------|
| `needle_MatchAutoStart` | Auto-start when enough players |
| `needle_MatchBalanceTime` | Time for auto-balance |
| `needle_MatchCountdownTime` | Pre-match countdown |
| `needle_MatchStartCountdown` | Start countdown |
| `needle_MatchReadyTime` | Time to ready up |
| `needle_MatchSize` | Small/Medium/Large |
| `needle_MatchType` | Which game mode |
| `needle_MatchFinishedRestartTime` | Delay before restart |
| `needle_MatchFinishedCameraFade` | End-of-match camera fade |
| `needle_MatchObjectCreationTimeWindow` | Object creation window |
| `needle_MaxMatchJoinWaitTime` | Max wait for late joiners |
| `needle_EndMatchAndShowResults` | Force end match |
| `needle_MatchDebug` | Debug mode |
| `needle_MatchDebugAutoBalance` | Debug auto-balance |
| `needle_MatchDebugCountPlayers` | Debug player count |

---

## 2. Scoring System

### Ticket System [CONFIRMED]

Core component: `CCPLdrNeedleDataTickets`

**Conquest Tickets:**
| Variable | Purpose |
|----------|---------|
| `needle_ConquestTicketsStartBase` | Base starting tickets |
| `needle_ConquestTicketsStartPerSector` | Additional tickets per sector held |
| `needle_ConquestTicketRateMultiplier` | Ticket drain rate multiplier |
| `needle_UseTickets` | Enable/disable ticket system |
| `needle_TicketGoalForMatch` | Ticket threshold for match end |
| `needle_MatchTicketsNeededForCapitalShip` | Tickets needed to summon capital ship |

**Recon Tickets (size-dependent):**
| Variable | Purpose |
|----------|---------|
| `needle_ReconTicketsStartLarge` | Starting tickets (10v10) |
| `needle_ReconTicketsStartMedium` | Starting tickets (medium) |
| `needle_ReconTicketsStartSmall` | Starting tickets (5v5) |

**Ticket Events:**
- `HunterCriticalTickets`, `NeedleCriticalTickets` - Low ticket warning
- `HunterLowOnTickets`, `NeedleLowOnTickets` - Approaching critical
- `HunterRanOutOfTickets`, `NeedleRanOutOfTickets` - Team eliminated
- `HunterTicketRateChanged`, `NeedleTicketRateChanged` - Rate change notification
- `DrifterTicketsRemaining`, `ScavengerTicketsRemaining` - Hunt mode team tickets

### Victory/Defeat Conditions [CONFIRMED]

**Conquest:**
- `MatchEnded_HunterCapturedBases` / `MatchEnded_NeedleCapturedBases` - All bases captured
- `OnMatchEndEvent_HunterRanOutOfTickets` / `OnMatchEndEvent_NeedleRanOutOfTickets` - Tickets depleted
- `TimeOutHunterWon` / `TimeOutNeedleWon` - Time-based victory
- Summary strings: `MATCH_SUMMARY_CONQUEST_BASE_WIN/LOSE`, `MATCH_SUMMARY_CONQUEST_TICKET_WIN/LOSE`

**NeedleEscape (PvE):**
- `MatchEnd_Escaped` / `MatchEnd_EscapedGalaxy` - Successfully escaped
- `MatchEnd_Survived` - Survived
- `MatchEnd_Failure` - Failed
- `OnNeedleEscaped` - Escape event
- Summary strings: `MATCH_SUMMARY_NEEDLE_WIN/LOSE/SURVIVED`

**Victory Types:**
- **Decisive Victory** - `needle_FameRateForDecisiveWin`, `~LEADERBOARD_DECISIVE_VICTORY~`
- **Strategic Victory** - `needle_FameRateForStrategicWin`, `~LEADERBOARD_STRATEGIC_VICTORY~`
- **Loss** - `needle_FameRateForLoss`
- **Capital Ship Escape** - `needle_FameRateForCapitalShipEscape`

### Fame/XP System [CONFIRMED]

| Variable | Purpose |
|----------|---------|
| `needle_ServerFameGainMultiplier` | Server-side fame multiplier |
| `needle_ServerXpGainMultiplier` | Server-side XP multiplier |
| `needle_ExperienceLevel1` through `needle_ExperienceLevel9` | XP thresholds per level |
| `needle_ExperienceAssistMultiplier` | Assist XP multiplier |
| `needle_ExperienceAssistRadius` | Assist credit radius |
| `needle_ExperiencePercentageToOtherShipTypes` | XP spillover to other ships |
| `needle_ExperiencePerCrystalUpgradingStructure` | XP for crystal spending |
| `needle_ExperiencePerOreUpgradingStructure` | XP for ore spending |
| `needle_ExperienceAdjustMinimum` | Min XP adjustment |
| `needle_ExperienceAdjustPercentagePerCategory` | Per-category XP adjust |
| `needle_ExperienceAdjustPercentagePerLevel` | Per-level XP adjust |

### Match Stats Categories [CONFIRMED]

From `GetMatchStats` calls:
- `AcePilotEvents` - Top performer awards
- `ActionEvents` - Tactical actions
- `AIEvents` - AI-related events
- `DeathEvents` - Death tracking
- `PlayerEvents` - Player actions
- `Match` - Overall match data
- `Players` - Per-player stats

---

## 3. Galaxy/Sector System

### Galaxy Generation [CONFIRMED]

Core classes:
- `CCPLdrNeedleGalaxyGenerator` - Main generator
- `CCPLdrNeedleGalaxySector` - Individual sector
- `CCPLdrNeedleGalaxyRegion` - Region container
- `CCPLdrNeedleGalaxyBorderControl` - Border management
- `CCPLdrNeedleGalaxySectorConnectionSwitch` - Sector connections
- `CCPLdrNeedleGalaxySectorInhabitant` - Entities in sectors
- `CCPLdrNeedleGalaxyBackground` - Visual backdrop

Source files:
- `GameObjects\NeedleGalaxy\CNeedleGalaxy.cpp`
- `GameObjects\NeedleGalaxy\CNeedleGalaxyDefinition.cpp`
- `GameObjects\NeedleGalaxy\CNeedleGalaxyClient.cpp`
- `GameObjects\NeedleGalaxy\NNeedleGalaxy.cpp`
- `GameObjects\NeedleGalaxy\CComponentNeedleGalaxySector.cpp`
- `GameObjects\NeedleGalaxy\CComponentNeedleGalaxyRegion.cpp`
- `GameObjects\NeedleGalaxy\CComponentNeedleGalaxyBackground.cpp`

### Sector Types [CONFIRMED]

- `SectorType_Default` - Normal gameplay sector
- `SectorType_NeedleWarpIn` - Capital ship warp-in sector
- `SectorType_NeedleWarpInSupport` - Support for warp-in

### Sector Connections [CONFIRMED]

Sectors connect via clock positions (hexagonal grid):
- `ConnectionAt2`, `ConnectionAt4`, `ConnectionAt6`, `ConnectionAt8`, `ConnectionAt10`, `ConnectionAt12`

This confirms a **hexagonal sector layout** with up to 6 connections per sector.

### Sector Tags [CONFIRMED]

- `CPOLdrNeedleSectorTags` - Tag-based filtering for sector selection
- `Out-of-range SectorTags bit` - Bit-flag based tag system
- `ERROR: Failed to find a valid sector for included tags %X %s, required tags %X %s and excluded tags %X %s`

### Galaxy Config [CONFIRMED]

| Variable | Purpose |
|----------|---------|
| `needle_MakeGalaxy` | Trigger galaxy creation |
| `needle_ForceSector` | Force specific sector |
| `needle_DebugGalaxySectors` | Debug sector display |
| `needle_HideGalaxyMenu` | Hide galaxy menu |
| `needle_Theme` | Visual theme |
| `needle_Backdrop` | Background setting |
| `needle_RandomThemeFirstValid` | Theme range start |
| `needle_RandomThemeLastValid` | Theme range end |
| `needle_ExposeBaseWithOnlyOneAdjacentSector` | Home base vulnerability |
| `needle_OutOfSectorTime` | Time allowed out of sector |
| `needle_IgnoreOutOfSectorCheck` | Disable OOS check |

### Quadrant System [CONFIRMED]

Galaxy is divided into quadrants with row/column layout:
- `mQuadrantColumnCount <= gkUint8Max`
- `mQuadrantRowCount <= gkUint8Max`
- `needle_ShowQuadrantScoresForTeam` - Display quadrant scores

### Region System [CONFIRMED]

Regions affect galaxy appearance and events:
- `CCPLdrNeedlePackageRegionMasterList` - Master region list
- `CCPLdrNeedleGalaxyRegion` - Region component
- `CPOLdrNeedleRegionMasterListEntry`, `CPOLdrNeedleRegionTags`
- `region.deadstarservices.com` - Region lookup endpoint
- `needle_RegionLookupUrl`, `needle_CurrentRegionCode`, `needle_StartRegion`
- Region voting before match: `Vote_Choice1`, `Vote_Choice2`, `Vote_Random`

### Nebula System [CONFIRMED]

Nebulae are generated within sectors with gameplay effects:

**Nebula Types:**
- `NEBULA_CLOAK` - Cloaking effect
- `NEBULA_CORROSIVE` - Damage over time
- `NEBULA_EMP` - EMP effect
- `NEBULA_FIERY` - Fire/burn damage
- `NEBULA_ICY` - Frozen/slow effect

**Nebula Components:**
- `CCPLdrNebulaDefault`, `CCPLdrNebula2Default` - Core nebula
- `CCPLdrNebulaArchetypeCloud`, `CCPLdrNebulaArchetypePlasma` - Visual types
- `CCPLdrNebulaShapePolygon` - Shape definition
- `CCPLdrNebulaSpawnerGeneric` - Spawning
- `CCPLdrNeedleAreaEffectNebula` - Gameplay effects
- `CCPLdrNeedleGeneralGenerateWithinNebula` - Object spawning in nebula
- `needle_NebulaOptions` - Nebula config

---

## 4. Ship Data

### Ship Classes [CONFIRMED]

Three main categories:
- **Scout** - `~CATEGORY_SCOUT_NAME~`, `OnScout`
- **Raider** - `~CATEGORY_RAIDER_NAME~`, `OnRaider`
- **Frigate** - `~CATEGORY_FRIGATE_NAME~`, `OnFrigate`

### Ship Subtypes (Specialists) [CONFIRMED]

Four specialists per class:
- `ShipType_Combat` - Combat specialist
- `ShipType_Mining` - Mining/resource specialist
- `ShipType_Production` - Production/building specialist
- `ShipType_Research` - Research/tech specialist

Spawn events confirm subtypes: `OnShipReadyToWarpIn_Combat`, `OnShipReadyToWarpIn_Mining`, `OnShipReadyToWarpIn_Production`, `OnShipReadyToWarpIn_Research`

This gives **12 total ship types** (3 classes x 4 specialists).

### Ship Systems (5 slots) [CONFIRMED]

Each ship has a core + 4 system slots:
- **Core** (slot 0) - `SelectDevice_Core`, `augmentRank_Core`, `canAugment_Core`
- **Slot 1-4** - `SelectDevice_Device0` through `SelectDevice_Device3`
- System range: `NNeedleShipCommon::kSystemUpgrade_FirstValid` to `kSystemUpgrade_LastValid`
- Slot range: `NNeedleShipSystemsCommon::kSlot_FirstValid` to `kSlot_LastValid`

**System Ranks (5 levels per slot):**
- `CoreRankBecame_1` through `CoreRankBecame_5`
- Debug vars: `needle_DebugSystemRankShipCore`, `needle_DebugSystemRankShipSlot1-4`

**System Level Progression:**
- `needle_SecondsForMinimumMatchShipLevel_1` through `_9` - Time-gated minimum levels
- `needle_UseMinimumMatchShipLevel` - Enable time-gated leveling
- `SystemMaxRank`, `SystemNotMaxRank` - Max rank checks

### Loadout System [CONFIRMED]

- **3 loadout slots** per player: `SelectShip_Slot0`, `SelectShip_Slot1`, `SelectShip_Slot2`
- `CurrentShipIndex_0`, `CurrentShipIndex_1`, `CurrentShipIndex_2`
- `Slot_1_ShipType`, `Slot_2_ShipType`, `Slot_3_ShipType`
- `needle_SelectedShipIndex` - Currently selected ship
- `SetSlot_CurrentShip`, `SetSlot_NextShip`, `SetSlot_PreviousShip`
- `ERROR: SetMainLoadoutSlotIndex() - Trying to set the slot to %d.`
- `ERROR: CCoreAccountData::ValidateAndFixup() - Invalid loadout. Using default.`

### Weapons [CONFIRMED]

**Weapon Types:**
- `CCPLdrNeedleGunBeam` - Beam weapons
- `CCPLdrNeedleGunBullet` - Projectile weapons
- `CCPLdrNeedleGunCharge` - Charged weapons
- `CCPLdrNeedlePointFire` - Point-fire weapons

**Shot Types:**
- `CCPLdrNeedleShotBeam` - Beam shots
- `CCPLdrNeedleShotBullet` - Bullet shots

**Fire Control:**
- `CCPLdrNeedleFireControlSimple` - Single weapon/device (current)
- `CCPLdrNeedleFireControlAlternating` - DEPRECATED

**Hardpoints:**
- `CCPLdrNeedleHardpointTurret` - Ship turrets
- `CCPLdrNeedleHardpointAimIndicator` - Aim helper
- 4 turret slots: `UseOriginatorAsTurret_0` through `_3`
- `Notify_Turret_0_Destroyed` through `_3`

### Devices [CONFIRMED]

- `CCPLdrNeedleDeviceCloak` - Cloaking device
- `CCPLdrNeedleDeviceDroneControl` - Drone launcher
- `CCPLdrNeedleDeviceEMP` - EMP device
- `CCPLdrNeedleDeviceGeneratedProbe` - Probe generator
- `CCPLdrNeedleDeviceProbeLauncher` - Probe launcher
- `CCPLdrNeedleDeviceRepairField` - Area repair
- `CCPLdrNeedleDeviceScripted` - Script-driven device
- `CCPLdrNeedleDeviceShiftDrive` - Teleport/shift

**Device Activation:**
- `FIRE_SHIP_DEVICE_0` through `_3`, `FireDevice1` through `3`
- `Enable_Slot_Device_1-3`, `Disable_Slot_Device_1-3`

### Status Effects [CONFIRMED]

Applied via area effects or weapons:
- `CCPLdrNeedleApplyEffectBurn` - Burn DOT
- `CCPLdrNeedleApplyEffectCloak` / `Decloak` - Cloaking
- `CCPLdrNeedleApplyEffectCorrosive` - Corrosive damage
- `CCPLdrNeedleApplyEffectDamage` - Direct damage
- `CCPLdrNeedleApplyEffectDamageInputModifier` - Damage taken modifier
- `CCPLdrNeedleApplyEffectDamageOutputModifier` - Damage dealt modifier
- `CCPLdrNeedleApplyEffectEMP` - EMP disable
- `CCPLdrNeedleApplyEffectFireAt` - Force fire
- `CCPLdrNeedleApplyEffectInvulnerable` - Invulnerability
- `CCPLdrNeedleApplyEffectLeech` - Life steal
- `CCPLdrNeedleApplyEffectLinearVelocityModifier` - Speed mod
- `CCPLdrNeedleApplyEffectAngularVelocityModifier` - Turn rate mod
- `CCPLdrNeedleApplyEffectModifySensorStrength` - Sensor mod
- `CCPLdrNeedleApplyEffectModifySignalStrength` - Signature mod
- `CCPLdrNeedleApplyEffectMutualRepair` - Mutual heal
- `CCPLdrNeedleApplyEffectObliterate` - Instant kill
- `CCPLdrNeedleApplyEffectPush` - Knockback
- `CCPLdrNeedleApplyEffectRepair` - Heal
- `CCPLdrNeedleApplyEffectRepairModifier` - Heal modifier
- `CCPLdrNeedleApplyEffectRevealCloak` - Decloak reveal

### Augment System [CONFIRMED]

Augments are modifiers applied to ship systems:

**Augment Types:**
- `AUGMENT_TYPE_DAMAGE` / `_DAMAGE_INPUT_MODIFIER` / `_DAMAGE_OUTPUT_MODIFIER`
- `AUGMENT_TYPE_HEALTH`
- `AUGMENT_TYPE_REPAIR` / `_REPAIR_MODIFIER`
- `AUGMENT_TYPE_SPEED`
- `AUGMENT_TYPE_COOLDOWN` / `_COOLDOWN_MODIFIER`
- `AUGMENT_TYPE_SENSOR_STRENGTH_MODIFIER`
- `AUGMENT_TYPE_LINEAR_VELOCITY_MODIFIER`
- `AUGMENT_TYPE_ANGULAR_VELOCITY_MODIFIER`

**UI Augment Categories:**
- `~AUGMENT_TYPE_AMPLIFIER~`, `~AUGMENT_TYPE_CREATION~`, `~AUGMENT_TYPE_DAMAGE~`
- `~AUGMENT_TYPE_DATA~`, `~AUGMENT_TYPE_DEFENSE~`, `~AUGMENT_TYPE_ELECTRONICS~`
- `~AUGMENT_TYPE_ENERGY~`, `~AUGMENT_TYPE_LOGIC~`, `~AUGMENT_TYPE_PROPULSION~`
- `~AUGMENT_TYPE_UNIVERSAL~`, `~AUGMENT_TYPE_EMPTY~`

**Augment Origins (Races A-H):**
- `~AUGMENT_ORIGIN_RACEA~` through `~AUGMENT_ORIGIN_RACEH~`
- `~AUGMENT_ORIGIN_NONE~`

**Augment Placement:**
- Per-slot: `augmentRank_Core`, `augmentRank_Slot1-4`, `canAugment_Core/Ship/Slot1-4`
- `needle_AugmentLevel`, `needle_AugmentEffectMultplier`
- Reconstruction: `CCPLdrNeedleUIReconstructionMenuController`

### Ship Master Lists [CONFIRMED]

- `CCPLdrNeedlePackageShipMasterList` - All ships
- `CCPLdrNeedlePackageSkinMasterList` - All skins
- `CCPLdrNeedlePackageAugmentMasterList` - All augments
- `CCPLdrNeedlePackagePilotLevelMasterList` - Pilot progression
- `CCPLdrNeedlePackagePopulationMasterList` - Population/faction data

### Ship Config Vars [CONFIRMED]

| Variable | Purpose |
|----------|---------|
| `needle_ShipCategory` | Current ship class (Scout/Raider/Frigate) |
| `needle_ShipType` | Current ship type (Combat/Mining/Production/Research) |
| `needle_ShipRace` | Ship faction/race |
| `needle_ShipSkinIndex` | Equipped skin |
| `needle_ShipBoostPlayerScanner` | Scanner boost |
| `needle_ShipCloakPlayer` | Cloak state |
| `needle_PlayersCanUseAllShipsForTesting` | Debug: unlock all ships |
| `needle_PlayersCanUseAllSkinsForTesting` | Debug: unlock all skins |

---

## 5. Server-Side Controllers

### Core Class Hierarchy [CONFIRMED]

**Engine Layer** (from GameCore_Steam_Release.dll):
- `CBaseGameManager` - Base game manager
- `CGameManager` - Main game manager (extends CBaseGameManager)
- `CGameObjectComponentGameController` - Base controller component
- `CServerNetworkScene` - Server networking
- `CClientNetworkScene` - Client networking
- `CNetPropertiesManager` - Network property sync

**Game Layer** (from GameComponentsNeedle_Steam_Release.dll):
- `CCPLdrNeedleGameControllerDefault` - **Main server game controller**
- `CCPLdrNeedleGameControllerClient` - Client-side controller
- `CCPLdrNeedleGeneralGameControllerProxy` - Controller proxy

Source files:
- `GameObjects\NeedleGameController\CComponentNeedleGameController.cpp`
- `GameObjects\NeedleGameController\CComponentNeedleGameControllerDefault.cpp`
- `GameObjects\NeedleGameController\CNeedlePlayerData.cpp`
- `GameObjects\NeedleGameController\CNeedleShipData.cpp`
- `GameObjects\NeedleGameController\NNeedleGameUtils.cpp`

### Network Components [CONFIRMED]

- `CCPLdrNeedleNetSyncClientObjectHost` - Client object sync
- `CCPLdrNeedleNetSyncServerObjectHost` - Server object sync
- `CCPLdrNeedleNetworkClientMatchMaker` - Matchmaker client
- `CCPLdrNeedleNetworkClientAccountDataHelper` - Account data
- `CCPLdrNeedleNetworkLoginClientLoginManager` - Login

### Player Info Management [CONFIRMED]

- `CNeedleMatchPlayerInfoManagerClient` - Tracks connected players
- `CNeedlePlayerData` - Per-player data
- `CNeedleShipData` - Per-ship data
- Player connection: `CComponentNeedleGameControllerDefault: Player %d connected.`
- Player disconnect: `Player %d (%s) disconnected: level=%d team=%d`

### Data Services [CONFIRMED]

- `CNeedleServerCapitalShipDataService` - Server-side capital ship tracking
- `CNeedleClientCapitalShipDataService` - Client-side capital ship display
- `CNeedleAccountService` - Authentication/account management
- `CNeedleServerReservationService` - Player slot reservations
- `CNeedleServerStatusCommunicator` - Server health reporting
- `CNeedleTicketValidator` - Connection ticket validation

---

## 6. AI/Bot System

### AI Components [CONFIRMED]

- `CCPLdrNeedleControllerAI` - AI ship controller
- `CCPLdrNeedleControllerPlayer` - Player ship controller
- `CCPLdrNeedleAIManagerSquad` - AI squad management (for drones)
- `CCPLdrNeedleWaypointPatrolPoint` - Patrol waypoints
- `CCPLdrNeedleWaypointPathPoint` - Path following
- `CCPLdrNeedleWaypointGuardPoint` - Guard positions

### AI Config [CONFIRMED]

| Variable | Purpose |
|----------|---------|
| `needle_AiGodMode` | AI invincibility |
| `needle_AILevelMultiplierWhenKilled` | AI respawn level scaling |
| `needle_AILookAheadFrameCount` | AI prediction frames |
| `needle_DisableAIDevices` | Disable AI device usage |
| `needle_DisableAIWeapons` | Disable AI weapon usage |
| `needle_ObserverModeSkipAI` | Skip AI in observer |

### AI Avoidance Weights [CONFIRMED]

| Variable | Purpose |
|----------|---------|
| `needle_WeightDesiredDirection` | Pathfinding weight |
| `needle_WeightInactiveMineAvoidance` | Mine avoidance |
| `needle_WeightObjectAvoidance` | Object avoidance |
| `needle_WeightPhysicsWeaponAvoidance` | Physics weapon dodge |
| `needle_WeightRaycastWeaponAvoidance` | Raycast weapon dodge |
| `needle_WeightShipAvoidance` | Ship collision avoidance |
| `needle_WeightStrafeDirection` | Strafe weighting |

### OldEmpire/NPC System [CONFIRMED]

- `CapturedByTeam_OldEmpire`, `ForceCaptureByTeam_OldEmpire` - OldEmpire captures
- `SetTeam_OldEmpire`, `TeamChangedTo_OldEmpire`, `TriggeredOldEmpireTeam`
- `SetLightBarColorToTeamOldEmpire`
- `needle_OldEmpireStartLevel` - Starting level for OldEmpire enemies
- `OldEmpire_BlockedFromSpawning` - Spawn blocking

### Neutral Entities [CONFIRMED]

- `CapturedByTeam_Neutral`, `ForceCaptureByTeam_Neutral`
- `SetTeam_Neutral`, `TeamChangedTo_Neutral`

---

## 7. Config Vars (Complete List)

### Total needle_* vars found: **~380 unique**

Categorized below (gameplay-affecting vars only, excluding debug/UI-only):

#### Match Settings
| Variable | Purpose |
|----------|---------|
| `needle_MatchAutoStart` | Auto-start matches |
| `needle_MatchBalanceTime` | Team balance timer |
| `needle_MatchCountdownTime` | Pre-match countdown |
| `needle_MatchMaxLevelDifference` | Max level diff for balance |
| `needle_MatchMaxPlayersDifference` | Max player diff for balance |
| `needle_MatchMinPlayersPerTeamLarge` | Min players (10v10) |
| `needle_MatchMinPlayersPerTeamMedium` | Min players (medium) |
| `needle_MatchMinPlayersPerTeamSmall` | Min players (5v5) |
| `needle_MatchSize` | Small/Medium/Large |
| `needle_MatchType` | Game mode |
| `needle_MatchStartCountdown` | Final countdown |
| `needle_MatchReadyTime` | Ready phase duration |
| `needle_IsSinglePlayer` | Single player mode |
| `needle_MaxSquadSize` | Max party/squad size |
| `needle_EnableTeamShuffle` | Allow team shuffling |
| `needle_AllowPlayerTeamChange` | Allow manual team change |
| `needle_AllowClientRequestTeam` | Client team request |
| `needle_EnableClientReadyMatchStartClient` | Client ready system |
| `needle_EnableClientReadyMatchStartServer` | Server ready system |

#### Scoring/Tickets
| Variable | Purpose |
|----------|---------|
| `needle_ConquestTicketsStartBase` | Conquest base tickets |
| `needle_ConquestTicketsStartPerSector` | Conquest per-sector tickets |
| `needle_ConquestTicketRateMultiplier` | Ticket drain speed |
| `needle_ReconTicketsStartLarge/Medium/Small` | Recon starting tickets |
| `needle_UseTickets` | Enable ticket system |
| `needle_TicketGoalForMatch` | Ticket target |
| `needle_FirstTeamCaptureBonus` | First capture bonus |

#### Capital Ship (NeedleEscape)
| Variable | Purpose |
|----------|---------|
| `needle_CapitalShipRunJumpCount` | Number of jumps to escape |
| `needle_CapitalShipOverride` | Override capital ship |
| `needle_CurrentCapitalShipJumpNumber` | Current jump number |
| `needle_MatchTicketsNeededForCapitalShip` | Tickets for capital ship |
| `needle_MatchTimeBeforeRequestingCapitalShip` | Time before capital ship |
| `needle_CapitalShipCenterLevel/Specialist` | Center node config |
| `needle_CapitalShipFrontLevel/Specialist` | Front node config |
| `needle_CapitalShipLeftLevel/Specialist` | Left node config |
| `needle_CapitalShipRightLevel/Specialist` | Right node config |
| `needle_CapitalShipWarpCoreSpecialist` | Warp core specialist |
| `needle_capitalShipDefenseRespawnTime` | Defense respawn timer |
| `needle_PersistCapitalShipPodState` | Persist pod state between jumps |
| `needle_ContractMaxJumps` | Max jumps per contract |

#### Experience/Progression
| Variable | Purpose |
|----------|---------|
| `needle_ExperienceLevel1-9` | XP thresholds |
| `needle_ExperienceAssistMultiplier` | Assist XP scaling |
| `needle_ExperienceAssistRadius` | Assist credit range |
| `needle_ServerFameGainMultiplier` | Fame gain rate |
| `needle_ServerXpGainMultiplier` | XP gain rate |
| `needle_StructureLevelForXp` | Structure level for XP |
| `needle_StructureLevelOverride` | Override structure level |
| `needle_StructureMaxLevelLarge/Medium/Small` | Max structure level by size |

#### Spawning/Respawn
| Variable | Purpose |
|----------|---------|
| `needle_PlayerDespawnTime` | Despawn timer after death |
| `needle_LongDistanceRespawn` | Long-range spawn |
| `needle_structureDefenseRespawnTime` | Structure defense respawn |
| `needle_WaveTimerUpdateMultiplier` | Wave timer scaling |
| `needle_WaveTimerUpdatedMultiplierEnabled` | Enable wave timer mod |

#### Network/Server
| Variable | Purpose |
|----------|---------|
| `needle_ServerName` (via `00...99needle_ServerName`) | Server name |
| `needle_publicip` | Public IP address |
| `needle_useMatchmaker` | Use matchmaker service |
| `needle_IdleTimeoutTime` | Idle kick timer |
| `needle_IdleTimeoutTimeWarning` | Idle kick warning |
| `needle_PingTooHighDropTime` | High ping kick timer |
| `needle_PingTooHighThreshold` | Ping threshold |
| `needle_unhealthyServerKickTime` | Unhealthy server kick |
| `needle_unhealthyServerKillTimeAfterKickTime` | Kill after kick |
| `needle_ResetServerOnNoConnections` | Reset on empty |
| `needle_NetworkSyncSleepTime` | Sync tick rate |
| `needle_UpdateFrequencyHighSeconds` | High-priority update rate |
| `needle_UpdateFrequencyLowSeconds` | Low-priority update rate |
| `needle_NetworkRatingUpdatePeriod` | Network rating update |

#### Events
| Variable | Purpose |
|----------|---------|
| `needle_EventChanceOverride` | Override event chance |
| `needle_EventOptions` | Event configuration |
| `needle_EventWeightOverride_CometIce` | Ice comet weight |
| `needle_EventWeightOverride_CometMolten` | Molten comet weight |
| `needle_EventWeightOverride_CometPlasma` | Plasma comet weight |
| `needle_EventWeightOverride_MaximizeUpgrades` | Upgrade event weight |
| `needle_EventWeightOverride_Pirates` | Pirate attack weight |
| `needle_EventWeightOverride_Misc_0-4` | Miscellaneous events |

---

## 8. Game Mode Specifics

### Conquest [CONFIRMED]

**Match Type**: `MatchType_Conquest`
**Sizes**: Large (10v10 "Fleet"), Small (5v5 "Crew")
**Teams**: Hunter vs Needle
**Matchmaking**: `StartMatchmaking_Conquest_Any`, `_Large`, `_Small`

**Mechanics:**
- Capture outposts to drain enemy tickets
- Home bases become vulnerable: `BecameVulnerableConquestHomeBase`, `BecameInvulnerableConquestHomeBase`
- `ConquestHomeInvulnerable_Hunter/Needle`, `ConquestHomeVulnerable_Hunter/Needle`
- `needle_ExposeBaseWithOnlyOneAdjacentSector` - Base vulnerability with only 1 adjacent sector
- One home base per team: `ERROR: Adding more than one conquest home base for a given team`

**Victory Conditions:**
1. Capture all enemy bases (`MatchEnded_HunterCapturedBases`)
2. Deplete enemy tickets (`OnMatchEndEvent_HunterRanOutOfTickets`)
3. Timeout (`TimeOutHunterWon/TimeOutNeedleWon`)

**Leaderboards**: `ShowConquestLeaderboard`, `~XP_CONQUEST~`

### Recon [CONFIRMED]

**Match Type**: `MatchType_Recon`
**Sizes**: Large (10v10), Small (5v5)
**Matchmaking**: `StartMatchmaking_Recon_Large`, `_Small`

**Mechanics:**
- Ticket-based with size-dependent starting tickets
- `GiveReconMatchActions` - Match-specific tactical actions
- `ShowReconLeaderboard`

### Hunt [CONFIRMED]

**Match Type**: `MatchType_Hunt`
**Sizes**: Large, Small
**Teams**: **Drifters** vs **Scavengers** (NOT Hunter/Needle)
**Matchmaking**: `StartMatchmaking_Hunt_Large`, `_Small`

**Key Strings:**
- `LocalPlayerTeam_Drifter/Drifters`, `LocalPlayerTeam_Scavenger/Scavengers`
- `Team_Drifters`, `Team_Scavengers`
- `DrifterCount`, `ScavengerCount`
- `DrifterTicketsRemaining`, `ScavengerTicketsRemaining`
- Balance: `imbalanced players - drifters=%d scavengers=%d difference=%d maxdifference=%d`
- Level balance: `imbalanced levels - drifters=%d scavengers=%d difference=%d maxdifference=%d`
- `drifters=%d scavengers=%d total=%d`

**Events:**
- `EVENT_GUARDIANS` - Guardian NPC spawn
- `Event_Pirates`, `Force Pirates` - Pirate NPC spawn

### Freeplay [CONFIRMED]

**Match Type**: `MatchType_Freeplay`
**No matchmaking** - accessed via menu: `SetEntryPoint_FreePlayMenu`, `Triggered_FreePlayMenu`
- Loading tips: `LOADING_FREEPLAY_TIP_`

### Tutorial [CONFIRMED]

**Match Type**: `MatchType_Tutorial`
**No matchmaking** - accessed via menu: `SetEntryPoint_TutorialMenu`, `Triggered_TutorialMenu`
- `CCPLdrNeedleGeneralTutorialHelper`, `CCPLdrNeedleUITutorialDisplay`
- `ShowTutorialText`, `HideTutorialText`
- `TUTORIAL_MESSAGE_` prefix for tutorial text
- Progress tracking: `tutorial_complete_01/02/03`, `tutorial_hasShownPrompt`
- `OUTPOST_TUTORIAL`, `Force Outpost Tutorial`

### NeedleEscape (PvE) [CONFIRMED]

**Match Type**: `MatchType_NeedleEscape`
**Matchmaking**: `StartMatchmaking_NeedleEscape`
**Lobby**: `LobbyState_NeedleEscape_Game`, `LobbyState_NeedleEscape_Matchmaking`

**Capital Ship Contract System:**
- Players accept contracts to escort a capital ship through multiple jumps
- `needle_CapitalShipRunJumpCount` - Total jumps required
- `needle_CurrentCapitalShipJumpNumber` - Current jump number
- `~CONTRACT_JUMP~: %d/%d` - Jump progress display
- Contract states: `~CONTRACT_STATE_UNUSED~`, `~CONTRACT_STATE_IN_PROGRESS~`, `~CONTRACT_STATE_SUCCESS~`, `~CONTRACT_STATE_FAILURE~`
- Contract selection: `ContractSelected_InProgress`, `ContractSelected_NotStarted`
- `DeleteSelectedContract`, `DeleteContractParams`

**Capital Ship Nodes (5 positions):**
- Center: `~CAPITAL_SHIP_CENTER_NAME~` (needle_CapitalShipCenterLevel/Specialist)
- Front: `~CAPITAL_SHIP_FRONT_NAME~` (needle_CapitalShipFrontLevel/Specialist)
- Left: `~CAPITAL_SHIP_LEFT_NAME~` (needle_CapitalShipLeftLevel/Specialist)
- Right: `~CAPITAL_SHIP_RIGHT_NAME~` (needle_CapitalShipRightLevel/Specialist)
- Warp Core: (needle_CapitalShipWarpCoreSpecialist)

**Capital Ship Specialist Types:**
- `~CAPITAL_SHIP_COMBAT_NAME~`
- `~CAPITAL_SHIP_MINING_NAME~`
- `~CAPITAL_SHIP_PRODUCTION_NAME~`
- `~CAPITAL_SHIP_RESEARCH_NAME~`

**Resource Pods:**
- `CCPLdrNeedleCapitalShipResourcePodSetup`, `ResourcePodSpawner`, `ResourcePodStatus`
- 4 pods per node: `_Pod_0_Destroyed` through `_Pod_3_Destroyed`
- `needle_PersistCapitalShipPodState` - Pods persist between jumps

**Match End:**
- `OnNeedleEscaped`, `MatchEnd_EscapedGalaxy` - Successful escape
- `MatchEnd_Survived` - Survived but didn't escape
- `MatchEnd_Failure` - Capital ship destroyed
- `FinalJumpCompleted` - Last jump done
- Rewards: `EscapeRunRewards`, `HasContractReward_0-4`

### Match Size Definitions [CONFIRMED]

- `MatchSize_Large` - Fleet (10v10)
- `MatchSize_Medium` - [UNCERTAIN] (may not be fully implemented)
- `MatchSize_Small` - Crew (5v5)
- Lobby text: `~LOBBY_MODE_SIZE_CREW~`, `~LOBBY_MODE_SIZE_FLEET~`

---

## 9. Cut Content

### NeedleCrisis [CONFIRMED - CUT]

- `MatchType_NeedleCrisis` - Defined as match type
- `OnMatchType_NeedleCrisis` - Has match type handler
- `~LOADING_MATCH_NEEDLE_CRISIS~` - Has loading screen
- `LOADING_NEEDLE_CRISIS_TIP_` - Has loading tips
- **No matchmaking entry** (no `StartMatchmaking_NeedleCrisis`)
- **No unique game logic strings** beyond these references

### NeedleDiscovery [CONFIRMED - CUT]

- `MatchType_NeedleDiscovery` - Defined as match type
- `OnMatchType_NeedleDiscovery` - Has match type handler
- `~LOADING_MATCH_NEEDLE_DISCOVERY~` - Has loading screen
- `LOADING_NEEDLE_DISCOVERY_TIP_` - Has loading tips
- **No matchmaking entry**
- **No unique game logic strings** beyond these references

### NeedleExploration [CONFIRMED - CUT]

- `MatchType_NeedleExploration` - Defined as match type
- `OnMatchType_NeedleExploration` - Has match type handler
- `~LOADING_MATCH_NEEDLE_EXPLORATION~` - Has loading screen
- `LOADING_NEEDLE_EXPLORATION_TIP_` - Has loading tips
- **No matchmaking entry**
- **No unique game logic strings** beyond these references

**Assessment**: All three cut modes have match type enums, event handlers, and loading screen infrastructure, but no dedicated game logic (no unique config vars, scoring, or win conditions). They were likely planned modes that never made it past the skeleton stage. They share the same Needle escape/PvE summary strings, suggesting they may have been variants of NeedleEscape.

---

## 10. Data File References

### .csif Files [CONFIRMED]

Only one .csif reference found:
- `$/needle/ui/common/****/default_ship_values.csif` - Default ship balance values

The `****` wildcard in the path suggests these files are loaded from asset packages with variable identifiers.

### Master List Components (Data-Driven Assets) [CONFIRMED]

These components define the game's data-driven content:

| Component | Purpose |
|-----------|---------|
| `CCPLdrNeedlePackageShipMasterList` | Ship definitions |
| `CCPLdrNeedlePackageSkinMasterList` | Skin definitions |
| `CCPLdrNeedlePackageAugmentMasterList` | Augment definitions |
| `CCPLdrNeedlePackagePilotLevelMasterList` | Pilot level progression |
| `CCPLdrNeedlePackagePopulationMasterList` | Population/faction data |
| `CCPLdrNeedlePackagePortraitMasterList` | Player portraits |
| `CCPLdrNeedlePackageBackgroundMasterList` | Galaxy backgrounds |
| `CCPLdrNeedlePackageRegionMasterList` | Region definitions |
| `CCPLdrNeedlePackageSectorMasterList` | Sector templates |
| `CCPLdrNeedlePackageNebulaMasterList` | Nebula types |
| `CCPLdrNeedlePackageEventMasterList` | In-match events |
| `CCPLdrNeedlePackageDlcMasterList` | DLC content |
| `CCPLdrNeedlePackageGeneratedObjectMasterList` | Generated objects |
| `CCPLdrNeedlePackageGeneratedObjectDefinition` | Object definitions |

### Structure Upgrade UI Textures [CONFIRMED]

Structure types visible from UI textures:
- `structure_image_combatbeam.ctxr` - Beam turret structure
- `structure_image_combatbullet.ctxr` - Bullet turret structure
- `structure_image_combatemp.ctxr` - EMP structure
- `structure_image_combatmissile.ctxr` - Missile structure
- `structure_image_construction.ctxr` - Construction/production
- `structure_image_mining.ctxr` - Mining structure
- `structure_image_research.ctxr` - Research structure
- `structure_image_sensor.ctxr` - Sensor array
- `structure_image_needlefront/left/middle/right.ctxr` - Capital ship positions

### Area Effect Types [CONFIRMED]

- `CCPLdrNeedleAreaEffectCapsule` - Capsule-shaped
- `CCPLdrNeedleAreaEffectCone` - Cone-shaped
- `CCPLdrNeedleAreaEffectJump` - Jump/warp
- `CCPLdrNeedleAreaEffectNebula` - Nebula
- `CCPLdrNeedleAreaEffectRadial` - Radial/sphere
- `CCPLdrNeedleAreaEffectRegion` - Region-wide
- `CCPLdrNeedleAreaEffectSector` - Sector-wide
- `CCPLdrNeedleAreaEffectTouchSensor` - Touch/proximity
- `CCPLdrNeedleAreaEffectTrail` - Trail behind moving objects

---

## Appendix A: Teams

| Team | Context | Notes |
|------|---------|-------|
| **Hunter** | Conquest, Recon | Default PvP team 1 |
| **Needle** | Conquest, Recon | Default PvP team 2 |
| **Drifters** | Hunt | Hunt mode team 1 |
| **Scavengers** | Hunt | Hunt mode team 2 |
| **OldEmpire** | NeedleEscape PvE | AI enemy faction |
| **Neutral** | All modes | Unaffiliated NPCs |
| **NoTeam** | System | No team assigned |

## Appendix B: Tactical Actions (Awards)

| Variable | Award |
|----------|-------|
| `needle_TacticalActionAwardForAfterlife` | Kill after death |
| `needle_TacticalActionAwardForAssault` | Assault |
| `needle_TacticalActionAwardForAvenger` | Avenge teammate |
| `needle_TacticalActionAwardForBloodthirsty` | Kill streak |
| `needle_TacticalActionAwardForCapitalCritical` | Critical capital damage |
| `needle_TacticalActionAwardForCapitalDamage` | Capital ship damage |
| `needle_TacticalActionAwardForCapitalDestruction` | Destroy capital ship |
| `needle_TacticalActionAwardForComeback` | Comeback kill |
| `needle_TacticalActionAwardForConquest` | Conquest |
| `needle_TacticalActionAwardForDefense` | Defense |
| `needle_TacticalActionAwardForDomination` | Multi-kill |
| `needle_TacticalActionAwardForGuardianHunter` | Kill guardian |
| `needle_TacticalActionAwardForHijacker` | Hijack |
| `needle_TacticalActionAwardForMerciless` | Kill streak |
| `needle_TacticalAction_AwardForRecapture` | Recapture point |
| `needle_TacticalActionAwardForRevenge` | Revenge kill |
| `needle_TacticalActionAwardForRuthless` | Kill streak |
| `needle_TacticalActionAwardForShutDown` | Shut down streak |
| `needle_TacticalActionAwardForUnstoppable` | Kill streak |

**Streak Thresholds:**
- Bloodthirsty: `needle_TacticalAction_StreakForBloodthirsty`
- Merciless: `needle_TacticalAction_StreakForMerciless`
- Ruthless: `needle_TacticalAction_StreakForRuthless`
- Unstoppable: `needle_TacticalAction_StreakForUnstoppable`
- Domination: `needle_TacticalAction_KillsForDomination`
- Comeback: `needle_TacticalAction_DeathsForComeback`
- Avenger: `needle_TacticalAction_MaxTimeForAvenger`
- Near Outpost: `needle_TacticalAction_NearOutpostDistance`

## Appendix C: Ace Pilot Categories

| Variable | Category |
|----------|----------|
| `needle_AcePilotAwardForAceKiller` | Most kills |
| `needle_AcePilotAwardForDeadEye` | Accuracy |
| `needle_AcePilotAwardForHighestStreak` | Longest streak |
| `needle_AcePilotAwardForTopAssists` | Most assists |
| `needle_AcePilotAwardForTopAttacker` | Most damage |
| `needle_AcePilotAwardForTopCapture` | Most captures |
| `needle_AcePilotAwardForTopDefender` | Most defenses |
| `needle_AcePilotAwardForTopUpgrader` | Most upgrades |

## Appendix D: Trophy/Achievement Thresholds

| Variable | Trophy |
|----------|--------|
| `needle_TrophyBaseCapturesForControlFreak` | Control Freak |
| `needle_TrophyDecisiveVictoriesForSoulEater` | Soul Eater |
| `needle_TrophyFlightTimeForCertifiedPilot` | Certified Pilot |
| `needle_TrophyKillStreakForEnFuego` | En Fuego |
| `needle_TrophyKillStreakForUntouchable` | Untouchable |
| `needle_TrophyOreSpentForClaimJumper` | Claim Jumper |
| `needle_TrophyPlayerAssistsForAccomplice` | Accomplice |
| `needle_TrophyPlayerKillsForBloodGod` | Blood God |
| `needle_TrophyPlayerKillsForReaper` | Reaper |
| `needle_TrophyVictoriesForBiggestFish` | Biggest Fish |

## Appendix E: Network Error Codes

| Error | Meaning |
|-------|---------|
| `NET_APP_ERROR_CAPITAL_SHIP_DATA_ERROR` | Capital ship data failure |
| `NET_APP_ERROR_CAPITAL_SHIP_MATCH_FINISHED` | Capital ship match ended |
| `NET_APP_ERROR_IDLE_TIMEOUT` | Player idle too long |
| `NET_APP_ERROR_NETWORKDEVICEDISCONNECTED` | Network device lost |
| `NET_APP_ERROR_PING_TOO_HIGH` | Ping exceeds threshold |
| `NET_APP_ERROR_SERVERCONNECTIONTIMEOUT` | Server connection timeout |
| `NET_APP_ERROR_STATSREADFAILURE` | Stats read failure |
| `NET_APP_ERROR_UNHEALTHY_SERVER_KICKOUT` | Unhealthy server |

## Appendix F: Matchmaking Regions

- `matchmaking_location_useast`
- `matchmaking_location_uswest`
- `matchmaking_location_europe`
- `matchmaking_location_asia`
- `matchmaking_location_oceania`
- `matchmaking_location_southamerica`
- `matchmaking_allow_crossplay`

## Appendix G: Player Communication (Comms Wheel)

From UI texture references:
- Attack Here (`attack_here_icon`)
- Defend Here (`defend_here_icon`)
- Enemy Spotted (`enemy_spotted_icon`)
- Follow Me (`follow_me_icon`)
- Need Repair (`need_repair_icon`)
- Yes (`yes_icon`)
- No (`no_icon`)
- Sorry (`sorry_icon`)
- Thanks (`thanks_icon`)

Config: `needle_PlayerCommBubbleLifetime`, `needle_PlayerCommWaypointLifetime`

## Appendix H: Source File Map

All source paths found (relative to `Needle_Release\Source\Game\GameComponentsNeedle\`):

- `GameObjects\NeedleGameController\CComponentNeedleGameController.cpp`
- `GameObjects\NeedleGameController\CComponentNeedleGameControllerDefault.cpp`
- `GameObjects\NeedleGameController\CNeedlePlayerData.cpp`
- `GameObjects\NeedleGameController\CNeedleShipData.cpp`
- `GameObjects\NeedleGameController\NNeedleGameUtils.cpp`
- `GameObjects\NeedleGalaxy\CNeedleGalaxy.cpp`
- `GameObjects\NeedleGalaxy\CNeedleGalaxyDefinition.cpp`
- `GameObjects\NeedleGalaxy\CNeedleGalaxyClient.cpp`
- `GameObjects\NeedleGalaxy\NNeedleGalaxy.cpp`
- `GameObjects\NeedleGalaxy\CComponentNeedleGalaxySector.cpp`
- `GameObjects\NeedleGalaxy\CComponentNeedleGalaxyRegion.cpp`
- `GameObjects\NeedleGalaxy\CComponentNeedleGalaxyBackground.cpp`
- `GameObjects\NeedleCapitalShip\CNeedleCapitalShipManager.cpp`
- `GameObjects\NeedleCapitalShip\CNeedleClientCapitalShipDataService.cpp`
- `GameObjects\NeedleCapitalShip\CNeedleServerCapitalShipDataService.cpp`
- `GameObjects\NeedleDevice\CComponentNeedleDevice.cpp`
- `GameObjects\NeedleDevice\CComponentNeedleDeviceDroneControl.cpp`
- `GameObjects\NeedleShip\CComponentNeedleShipGeneric.cpp`
- `GameObjects\NeedleShip\CNetNeedleShipMetadataProvider.cpp`
- `GameObjects\NeedleShot\CComponentNeedleShotBeam.cpp`
- `GameObjects\NeedleShot\CComponentNeedleShotBullet.cpp`
- `GameObjects\NeedlePackage\CNeedleShipMasterListManager.cpp`
- `GameObjects\NeedleRespawn\CNeedleRespawnManager.cpp`
- `GameObjects\NeedleAreaEffect\CComponentNeedleAreaEffectJump.cpp`
- `GameObjects\NeedleNetwork\CComponentNeedleNetworkClientMatchMaker.cpp`
- `GameObjects\NeedleUI\CComponentNeedleUIAfterActionController.cpp`
- `GameObjects\NeedleUI\CComponentNeedleUIReconstructionMenuController.cpp`
- `GameObjects\NeedleUI\CComponentNeedleUIShipAugmentMenuController.cpp`
- `GameObjects\NeedleUI\CComponentNeedleUIShipSystemValues.cpp`
- `GameObjects\NeedleUI\CComponentNeedleUIRegionDisplay.cpp`
- `GameObjects\NebulaArchetype\NNebulaArchetypeCommon.cpp`
- `Services\CNeedleTicketValidator.cpp`
- `Services\CNeedleServerReservationService.cpp`

Engine paths:
- `Engine/Network/CNetStream.h`
- `Engine/Resource/CResourceManager.h`
