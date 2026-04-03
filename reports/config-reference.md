# Dead Star Config Variable Reference

Extracted from binary analysis of GameComponentsNeedle_Steam_Release.dll and GameCore_Steam_Release.dll.
Default values recovered from x64 disassembly of variable registration functions.

**Legend:**
- `[binary]` = Default extracted from DLL registration code
- `[override]` = Value set in gamescriptvars.txt (overrides binary default)
- `[computed]` = Default is -1 (sentinel); actual value computed at runtime
- `???` = Default could not be determined from static analysis

---

## 1. Server Core Configuration

| Variable | Type | Default | Max | Description |
|----------|------|---------|-----|-------------|
| needle_useMatchmaker | int | 0 | - | Enable matchmaker integration (override: true) |
| needle_DemoMode | int | 0 | - | Demo/tutorial mode |
| needle_IsSinglePlayer | int | 0 | - | Single player mode flag |
| needle_ResetServerOnNoConnections | bool | true | - | Reset server when all players disconnect |
| needle_ServerDrawMainView | int | 0 | - | Render game view on dedicated server |
| needle_ServerBroadcast | int | 0 | - | Server broadcast flag |
| needle_ServerOptions | int | 0 | - | Server option flags |
| needle_publishMatchStats | bool | true | - | Publish match statistics to backend |
| needle_publicip | string | ??? | - | Public IP address override |
| needle_publicServiceUrlOverride | string | ??? | - | Public service API URL override |
| needle_privateServiceUrlOverride | string | ??? | - | Private service API URL override |
| needle_serviceApiVersion | string | ??? | - | Service API version string |
| needle_CaptureMouseWhilePlaying | bool | true | - | Capture mouse in windowed mode |
| needle_WriteDebugFiles | int | 0 | - | Write debug log files |

## 2. Network Configuration

| Variable | Type | Default | Max | Description |
|----------|------|---------|-----|-------------|
| network_ServerAddress | string | ??? | - | Server listen address |
| network_ServerListenPort | int | 27500 | 65535 | Server listen port |
| network_AllowCrossPlatformPlay | bool | true | - | Allow cross-platform play |
| network_BlendTransform | float | 10.0 | - | Network transform interpolation blend |
| network_BlendVelocity | ??? | ??? | - | Network velocity interpolation |
| network_ThrottleLimit | ??? | ??? | - | Network throttle limit |
| network_ThrottleStep | int | 500 | - | Network throttle step size |
| network_ThrottleThreshold | int | 500 | - | Network throttle activation threshold |
| network_serverSceneCulling | bool | true | - | Server-side scene culling |
| network_LocalPlayerId | ??? | ??? | - | Local player network ID |
| network_PlayerName | string | ??? | - | Player display name |
| network_DebugBounds | int | 0 | - | Debug network object bounds |
| network_DebugConnection | int | 0 | - | Debug network connections |
| network_ShowObjectBandwidth | int | 0 | - | Show per-object bandwidth |
| network_ShowObjectCount | int | 0 | - | Show network object count |
| network_printHierarchy | int | 0 | - | Print network hierarchy |
| network_WarnAboutServerObjectsOnClient | bool | true | - | Warn about server objects on client |
| serverUpdateHz | int | 20 | - | Server tick rate (Hz) |
| needle_NetworkSyncSleepTime | float | 5.0 | - | Network sync sleep time (s) |
| needle_NetworkRatingUpdatePeriod | float | 1.0 | - | Network quality rating update period (s) |

## 3. Match Configuration

### Match Type & Size

| Variable | Type | Default | Max | Description |
|----------|------|---------|-----|-------------|
| needle_MatchType | int | 0 | 7 | Match type: 0=Conquest, 1=Recon, 2=Hunt |
| needle_MatchSize | int | 0 | 2 | Match size: 0=Small, 1=Medium, 2=Large |
| needle_StartRegion | int | 0 | 1 | Starting region index |
| needle_ForceSector | int | 0 | 1 | Force specific sector |
| needle_Theme | int | 0 | - | Map theme index |
| needle_Backdrop | int | 0 | 1 | Background/skybox selection |
| needle_NebulaOptions | int | 0 | 6 | Nebula visual options |
| needle_RandomThemeFirstValid | int | 0 | - | Random theme range start |
| needle_RandomThemeLastValid | int | 4 | - | Random theme range end |

### Match Timing

| Variable | Type | Default | Max | Description |
|----------|------|---------|-----|-------------|
| needle_MatchAutoStart | bool | true | - | Auto-start match when players ready |
| needle_MatchCountdownTime | float | 90.0 | - | Pre-match countdown timer (s) |
| needle_MatchStartCountdown | float | 3.0 | - | Final start countdown (s) |
| needle_MatchReadyTime | float | 5.0 | - | Time to ready up (s) |
| needle_MatchBalanceTime | float | 10.0 | - | Team balance/rebalance time (s) |
| needle_MatchFinishedRestartTime | float | 2.0 | - | Delay after match ends before restart (s) |
| needle_MatchFinishedCameraFade | float | 0.45 | - | Camera fade duration at match end (s) |
| needle_MaxMatchJoinWaitTime | float | 20.0 | - | Max wait time for joining a match (s) |
| needle_WaitForAccountDataReadyTime | float | 5.0 | - | Wait for account data to load (s) |
| needle_ClientLoadAssetTimeAllowance | float | 20.0 | - | Client asset loading allowance (s) |

### Match Player Requirements

| Variable | Type | Default | Max | Description |
|----------|------|---------|-----|-------------|
| needle_MatchMinPlayersPerTeamSmall | int | 3 | - | Min players/team for Small matches |
| needle_MatchMinPlayersPerTeamMedium | int | 4 | - | Min players/team for Medium matches |
| needle_MatchMinPlayersPerTeamLarge | int | 5 | - | Min players/team for Large matches |
| needle_MatchMaxPlayersDifference | int | 1 | - | Max player count difference between teams |
| needle_MatchMaxLevelDifference | int | 5 | - | Max average level difference between teams |
| needle_MaxSquadSize | int | 10 | 10 | Maximum squad/party size (min=1) |

### Connection Quality

| Variable | Type | Default | Max | Description |
|----------|------|---------|-----|-------------|
| needle_PingTooHighThreshold | int | 500 | 2147483647 | Ping threshold to consider too high (ms) |
| needle_PingTooHighDropTime | float | 5.0 | - | Time over threshold before kick (s) |
| needle_HighPingValue | int | 200 | - | Ping value displayed as "high" (ms) |
| needle_LowPingValue | int | 75 | - | Ping value displayed as "low" (ms) |
| needle_IdleTimeoutTime | float | 180.0 | - | Idle timeout before kick (s) |
| needle_IdleTimeoutTimeWarning | float | 150.0 | - | Idle timeout warning (s) |
| needle_unhealthyServerKickTime | float | 180.0 | - | Unhealthy server kick time (s) |
| needle_unhealthyServerKillTimeAfterKickTime | float | 5.0 | - | Time after kick before kill (s) |
| needle_OutOfSectorTime | float | 5.0 | - | Time allowed out of sector (s) |

## 4. Ticket System (Conquest & Recon)

| Variable | Type | Default | Max | Description |
|----------|------|---------|-----|-------------|
| needle_UseTickets | bool | true | - | Enable ticket system |
| needle_TicketGoalForMatch | int | 0 | - | Ticket goal to win (0 = use default) |
| needle_ConquestTicketsStartBase | int | -1 (computed) | - | Base starting tickets for Conquest |
| needle_ConquestTicketsStartPerSector | int | -1 (computed) | - | Additional tickets per sector in Conquest |
| needle_ConquestTicketRateMultiplier | float | 1.0 | - | Conquest ticket drain rate multiplier |
| needle_ReconTicketsStartSmall | int | -1 (computed) | - | Recon starting tickets (Small) |
| needle_ReconTicketsStartMedium | int | -1 (computed) | - | Recon starting tickets (Medium) |
| needle_ReconTicketsStartLarge | int | -1 (computed) | - | Recon starting tickets (Large) |

## 5. Capital Ship System

| Variable | Type | Default | Max | Description |
|----------|------|---------|-----|-------------|
| needle_MatchTicketsNeededForCapitalShip | int | 30 | - | Ticket threshold to request capital ship |
| needle_MatchTimeBeforeRequestingCapitalShip | int | 120 | - | Min match time before capital ship request (s) |
| needle_CapitalShipRunJumpCount | int | 6 | - | Number of jumps in capital ship run |
| needle_capitalShipDefenseRespawnTime | float | 120.0 | - | Capital ship defense respawn time (s) |
| needle_PersistCapitalShipPodState | int | 0 | - | Persist pod destruction state |
| needle_CapitalShipOverride | int | 0 | - | Override capital ship settings |

## 6. Structure/Outpost Configuration

| Variable | Type | Default | Max | Description |
|----------|------|---------|-----|-------------|
| needle_structureDefenseRespawnTime | float | 120.0 | - | Structure defense respawn time (s) |
| needle_StructureLevelForXp | int | 5 | - | Structure level for XP calculation |
| needle_StructureLevelOverride | int | ??? | - | Override structure levels |
| needle_StructureMaxLevelSmall | int | -1 (computed) | 4 | Max structure level (Small match) |
| needle_StructureMaxLevelMedium | int | -1 (computed) | 4 | Max structure level (Medium match) |
| needle_StructureMaxLevelLarge | int | -1 (computed) | 4 | Max structure level (Large match) |
| needle_StructureOverride | int | 0 | - | Structure override flag |
| needle_StructureUpgradeResourceTest | int | 0 | 1 | Test structure upgrade resources |
| needle_ExposeBaseWithOnlyOneAdjacentSector | int | 0 | - | Expose base with single adjacent sector |
| needle_FirstTeamCaptureBonus | int | 0 | - | Bonus for first team capture |

## 7. Experience & Leveling

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_ExperienceLevel1 | int | 150 | XP required for level 1 |
| needle_ExperienceLevel2 | int | 450 | XP required for level 2 |
| needle_ExperienceLevel3 | int | 900 | XP required for level 3 |
| needle_ExperienceLevel4 | int | 1350 | XP required for level 4 |
| needle_ExperienceLevel5 | int | 1850 | XP required for level 5 |
| needle_ExperienceLevel6 | int | 2350 | XP required for level 6 |
| needle_ExperienceLevel7 | int | 2900 | XP required for level 7 |
| needle_ExperienceLevel8 | int | 3450 | XP required for level 8 |
| needle_ExperienceLevel9 | int | 4000 | XP required for level 9 |
| needle_ExperienceAdjustMinimum | int | 10 | Minimum XP adjustment |
| needle_ExperienceAssistMultiplier | float | 0.5 | Assist XP multiplier |
| needle_ExperienceAssistRadius | float | 300.0 | Assist credit radius |
| needle_ExperiencePerCrystalUpgradingStructure | int | 2 | XP per crystal spent upgrading |
| needle_ExperiencePerOreUpgradingStructure | int | 2 | XP per ore spent upgrading |
| needle_ServerXpGainMultiplier | float | 1.0 | Server-wide XP multiplier |
| needle_UseMinimumMatchShipLevel | int | 0 | Enable minimum ship level per time |
| needle_SecondsForMinimumMatchShipLevel_1 | float | 120.0 | Time for min ship level 1 (s) |
| needle_UpgradeLevel | int | 0 | Starting upgrade level (max=6) |

## 8. Fame & Rewards

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_FameRateForCapitalShipEscape | float | 2.0 | Fame multiplier for capital ship escape |
| needle_FameRateForDecisiveWin | float | 2.0 | Fame multiplier for decisive victory |
| needle_FameRateForStrategicWin | float | 1.0 | Fame multiplier for strategic victory |
| needle_FameRateForLoss | float | 0.5 | Fame multiplier for loss |
| needle_ServerFameGainMultiplier | float | 1.0 | Server-wide fame gain multiplier |
| needle_IgnoreDatabaseFameCaps | int | 0 | Ignore database fame caps |

## 9. Tactical Action Awards (XP per action)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_TacticalActionAwardForAfterlife | int | 50 | Afterlife kill award |
| needle_TacticalActionAwardForAssault | int | 50 | Assault award |
| needle_TacticalActionAwardForAvenger | int | 50 | Avenger kill award |
| needle_TacticalActionAwardForBloodthirsty | int | 200 | 5-kill streak |
| needle_TacticalActionAwardForCapitalCritical | int | 200 | Capital ship critical hit |
| needle_TacticalActionAwardForCapitalDamage | int | 100 | Capital ship damage |
| needle_TacticalActionAwardForCapitalDestruction | int | 800 | Capital ship destruction |
| needle_TacticalActionAwardForComeback | int | 50 | Comeback after 3 deaths |
| needle_TacticalActionAwardForConquest | int | 150 | Base capture |
| needle_TacticalActionAwardForDefense | int | 50 | Base defense |
| needle_TacticalActionAwardForGuardianHunter | int | 25 | Guardian kill |
| needle_TacticalActionAwardForHijacker | int | 50 | Hijack award |
| needle_TacticalActionAwardForMerciless | int | 250 | 10-kill streak |
| needle_TacticalActionAwardForRevenge | int | 50 | Revenge kill |
| needle_TacticalActionAwardForRuthless | int | 300 | 15-kill streak |
| needle_TacticalActionAwardForShutDown | int | 75 | Shut down streak |
| needle_TacticalActionAwardForUnstoppable | int | 350 | 20-kill streak |
| needle_TacticalAction_AwardForRecapture | int | 0 | Recapture award |

### Tactical Action Thresholds

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_TacticalAction_DeathsForComeback | int | 3 | Deaths needed for comeback |
| needle_TacticalAction_KillsForDomination | int | 3 | Kills for domination |
| needle_TacticalAction_MaxTimeForAvenger | float | 3.0 | Max time for avenger (s) |
| needle_TacticalAction_NearOutpostDistance | float | 400.0 | Distance for near-outpost actions |
| needle_TacticalAction_StreakForBloodthirsty | int | 5 | Kill streak for Bloodthirsty |
| needle_TacticalAction_StreakForMerciless | int | 10 | Kill streak for Merciless |
| needle_TacticalAction_StreakForRuthless | int | 15 | Kill streak for Ruthless |
| needle_TacticalAction_StreakForUnstoppable | int | 20 | Kill streak for Unstoppable |

## 10. Ace Pilot Awards (XP per category)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_AcePilotAwardForAceKiller | int | 500 | Ace killer award |
| needle_AcePilotAwardForDeadEye | int | 500 | Dead eye award |
| needle_AcePilotAwardForHighestStreak | int | 500 | Highest streak award |
| needle_AcePilotAwardForTopAssists | int | 500 | Top assists award |
| needle_AcePilotAwardForTopAttacker | int | 500 | Top attacker award |
| needle_AcePilotAwardForTopCapture | int | 500 | Top capture award |
| needle_AcePilotAwardForTopDefender | int | 500 | Top defender award |
| needle_AcePilotAwardForTopUpgrader | int | 500 | Top upgrader award |

## 11. Trophy/Achievement Thresholds

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_TrophyBaseCapturesForControlFreak | int | 50 | Base captures for Control Freak |
| needle_TrophyDecisiveVictoriesForSoulEater | int | 10 | Decisive wins for Soul Eater |
| needle_TrophyFlightTimeForCertifiedPilot | int | 36000 | Flight time for Certified Pilot (s = 10 hrs) |
| needle_TrophyKillStreakForEnFuego | int | 5 | Kill streak for En Fuego |
| needle_TrophyKillStreakForUntouchable | int | 10 | Kill streak for Untouchable |
| needle_TrophyOreSpentForClaimJumper | int | 10000 | Ore spent for Claim Jumper |
| needle_TrophyPlayerAssistsForAccomplice | int | 100 | Assists for Accomplice |
| needle_TrophyPlayerKillsForBloodGod | int | 500 | Kills for Blood God |
| needle_TrophyPlayerKillsForReaper | int | 100 | Kills for Reaper |
| needle_TrophyShipPlayerKills | int | 100 | Ship-specific player kills |
| needle_TrophyVictoriesForBiggestFish | int | 50 | Victories for Biggest Fish |

## 12. AI Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_AiGodMode | int | 0 | AI invincibility |
| needle_AILevelMultiplierWhenKilled | float | 2.0 | AI level multiplier on kill |
| needle_AILookAheadFrameCount | int | 1 | AI look-ahead frames |
| needle_DisableAIDevices | int | 0 | Disable AI devices |
| needle_DisableAIWeapons | int | 0 | Disable AI weapons |
| needle_WeightDesiredDirection | float | 6.0 | AI pathfinding weight |
| needle_WeightInactiveMineAvoidance | float | 3.0 | AI mine avoidance weight |
| needle_WeightObjectAvoidance | float | 3.0 | AI obstacle avoidance weight |
| needle_WeightPhysicsWeaponAvoidance | float | 6.0 | AI physics weapon avoidance |
| needle_WeightRaycastWeaponAvoidance | float | 5.0 | AI raycast weapon avoidance |
| needle_WeightShipAvoidance | float | 2.0 | AI ship avoidance weight |
| needle_WeightStrafeDirection | float | 1.0 | AI strafe weight |
| needle_MaxStressTestLifetime | float | 120.0 | AI stress test max lifetime (s) |
| needle_MinStressTestLifetime | float | 30.0 | AI stress test min lifetime (s) |

## 13. Matchmaking Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| matchmaking_allow_crossplay | bool | true | Allow crossplay matchmaking |
| matchmaking_location_asia | bool | true | Enable Asia region |
| matchmaking_location_europe | bool | true | Enable Europe region |
| matchmaking_location_oceania | bool | true | Enable Oceania region |
| matchmaking_location_southamerica | bool | true | Enable South America region |
| matchmaking_location_useast | bool | true | Enable US East region |
| matchmaking_location_uswest | bool | true | Enable US West region |
| needle_requestUpdateBase | float | ??? | Matchmaker poll base interval |
| needle_requestUpdateIncreaseRate | float | ??? | Matchmaker poll increase rate |
| needle_requestUpdateMax | float | ??? | Matchmaker poll max interval |
| needle_squadPollBase | float | ??? | Squad poll base interval |
| needle_squadPollIncreaseRate | float | ??? | Squad poll increase rate |
| needle_squadPollMax | float | ??? | Squad poll max interval |
| needle_DelayFollowSquadTime | float | 8.0 | Delay before following squad (s) |
| needle_UpdateFrequencyHighSeconds | int | 5 | High-priority update frequency (s) |
| needle_UpdateFrequencyLowSeconds | int | 5 | Low-priority update frequency (s) |

## 14. Player/Ship Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_ShipType | int | 0 | Ship type index |
| needle_ShipRace | int | 0 | Ship race (0=default) |
| needle_ShipCategory | int | 0 | Ship category |
| needle_ShipSkinIndex | int | 0 | Ship skin index |
| needle_SelectedShipIndex | int | 0 | Selected ship index |
| needle_PlayerDespawnTime | float | 2.0 | Player despawn time after death (s) |
| needle_LongDistanceRespawn | int | 0 | Enable long distance respawn |
| needle_GodMode | int | 0 | Player invincibility |
| needle_HasInfiniteOre | int | 0 | Infinite ore cheat |
| needle_AllowPlayerTeamChange | int | 0 | Allow team switching |
| needle_AllowClientRequestTeam | int | 0 | Allow client team requests |
| needle_PlayersCanUseAllShipsForTesting | int | 0 | Unlock all ships |
| needle_PlayersCanUseAllSkinsForTesting | int | 0 | Unlock all skins |
| needle_ContractMaxJumps | int | 6 | Max contract jumps |

## 15. HUD & UI Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_ShowHUD | bool | true | Show HUD |
| needle_ShowDamageNumbers | bool | true | Show damage numbers |
| needle_ShowXPNumbers | bool | true | Show XP numbers |
| needle_ShowLockOnCone | bool | true | Show lock-on cone |
| needle_HUDPlayerNameTrimLength | int | 16 | Max player name display length |
| needle_HUDLayoutIndex | int | 0 | HUD layout (max=10) |
| needle_DamageFlashTime | float | 0.5 | Damage flash duration (s) |
| needle_DamageTextSize | int | 0 | Damage text size (max=2) |
| needle_AdjustUIWidth | float | 90.0 | UI width percentage |
| needle_AdjustUIHeight | float | 90.0 | UI height percentage |
| needle_AdjustUIOffsetX | float | -5.0 | UI X offset |
| needle_AdjustUIOffsetY | float | -5.0 | UI Y offset |
| needle_AdjustUIResolutionRatio | float | 100.0 | UI resolution ratio |
| needle_PlayerCommBubbleLifetime | float | 3.0 | Chat bubble display time (s) |
| needle_PlayerCommWaypointLifetime | float | 15.0 | Waypoint marker lifetime (s) |
| hud_BannersHide | int | 0 | Hide banners |
| hud_CapitalShipStatusHide | int | 0 | Hide capital ship status |
| hud_CargoHoldBarHide | int | 0 | Hide cargo hold bar |
| hud_GameStatusHide | int | 0 | Hide game status |
| hud_GameTipsHide | int | 0 | Hide game tips |
| hud_HealthBarsHide | int | 0 | Hide health bars |
| hud_InteractionPromptsHide | int | 0 | Hide interaction prompts |
| hud_LevelUpIndicatorHide | int | 0 | Hide level up indicator |
| hud_OutOfSectorWarningHide | int | 0 | Hide out-of-sector warning |
| hud_ScannerHide | int | 0 | Hide scanner |
| hud_ScoreboardHide | int | 0 | Hide scoreboard |
| hud_ShipSystemStatusHide | int | 0 | Hide ship system status |
| hud_SystemStatusHide | int | 0 | Hide system status |
| hud_TargetingSymbolsHide | int | 0 | Hide targeting symbols |
| hud_TextBoxHide | int | 0 | Hide text box |
| hud_XPBarHide | int | 0 | Hide XP bar |

## 16. Scanner Display Toggles

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_ScannerShowBarrierGenerators | bool | true | Show barrier generators |
| needle_ScannerShowCapitalShipNodes | bool | true | Show capital ship nodes |
| needle_ScannerShowComets | bool | true | Show comets |
| needle_ScannerShowComms | bool | true | Show comm markers |
| needle_ScannerShowContainers | bool | true | Show containers |
| needle_ScannerShowDamage | bool | true | Show damage indicators |
| needle_ScannerShowMines | bool | true | Show mines |
| needle_ScannerShowShips | bool | true | Show ships |
| needle_ScannerShowStructures | bool | true | Show structures |
| needle_ScannerShowTerrain | bool | true | Show terrain |
| needle_ScannerShowTurrets | bool | true | Show turrets |

## 17. Audio

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_MasterVolume | ??? | ??? | Master volume |
| needle_MusicVolume | ??? | ??? | Music volume |
| needle_SfxVolume | ??? | ??? | SFX volume |
| needle_VoiceChatSpeakerVolume | float | 100.0 | Voice chat volume |
| needle_VoiceChatPushToTalkMode | int | 0 | Push-to-talk mode (max=2) |
| needle_VoiceChatDebug | int | 0 | Voice chat debug |
| needle_VoiceChatLoopback | int | 0 | Voice chat loopback test |

## 18. Rendering Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| r_renderer | string | ??? | Renderer name (override: "needle") |
| r_brightness | float | 50.0 | Screen brightness |
| r_fullscreen | bool | true | Fullscreen mode |
| r_screenHeight | int | 1080 | Screen height |
| r_vsync | bool | true | Vertical sync |
| r_fxaaEnable | bool | true | FXAA anti-aliasing |
| r_fxaaQuality | int | 0 | FXAA quality level |
| r_maxParticleCount | int | 10000 | Maximum particle count |
| r_multithreaded | bool | true | Multithreaded rendering |
| r_drawOpaque | bool | true | Draw opaque objects |
| r_drawTranslucent | bool | true | Draw translucent objects |
| r_halfresLightbuffers | int | 0 | Half-res light buffers |
| r_narrowFramebuffers | int | 0 | Narrow framebuffers |
| r_camLight | int | 0 | Camera light |
| r_device | int | 0 | Render device |
| r_fps | int | 0 | FPS display |
| r_vendor | int | 0 | GPU vendor index |
| renderConsoleMessages | bool | true | Render console messages |
| renderConsoleOutput | bool | true | Render console output |
| renderConsoleTopLines | bool | true | Render console top lines |
| gameSpeed | float | 1.0 | Game speed multiplier |

## 19. Shadow Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_ShadowCascadeSize0 | float | 400.0 | Shadow cascade 0 size |
| needle_ShadowCascadeSize1 | float | 900.0 | Shadow cascade 1 size |
| needle_ShadowCascadeSize2 | float | 1200.0 | Shadow cascade 2 size |
| needle_ShadowCascadeBias0 | float | 0.0009 | Shadow cascade 0 bias |
| needle_ShadowCascadeBias1 | float | 0.0009 | Shadow cascade 1 bias |
| needle_ShadowCascadeBias2 | float | 0.0009 | Shadow cascade 2 bias |
| needle_ShadowCull | bool | true | Shadow culling |
| needle_ShadowDebug | int | 0 | Shadow debug mode |
| needle_ShadowFreeze | int | 0 | Freeze shadows |
| needle_ShadowMapEnableWorldSnap | int | 0 | Shadow map world snap |
| needle_ShadowMapVisualizeCascades | int | 0 | Visualize shadow cascades (max=2) |

## 20. Event Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_EventChanceOverride | float | -1.0 | Override event chance (-1=default) |
| needle_EventOptions | int | 0 | Event option flags (max=10) |
| needle_EventWeightOverride_CometIce | float | -1.0 | Ice comet weight (-1=default) |
| needle_EventWeightOverride_CometMolten | float | -1.0 | Molten comet weight (-1=default) |
| needle_EventWeightOverride_CometPlasma | float | -1.0 | Plasma comet weight (-1=default) |
| needle_EventWeightOverride_MaximizeUpgrades | float | -1.0 | Maximize upgrades weight (-1=default) |
| needle_EventWeightOverride_Misc_0 | float | -1.0 | Misc event 0 weight (-1=default) |
| needle_EventWeightOverride_Misc_1 | float | -1.0 | Misc event 1 weight (-1=default) |
| needle_EventWeightOverride_Misc_2 | float | -1.0 | Misc event 2 weight (-1=default) |
| needle_EventWeightOverride_Misc_3 | float | -1.0 | Misc event 3 weight (-1=default) |
| needle_EventWeightOverride_Misc_4 | float | -1.0 | Misc event 4 weight (-1=default) |
| needle_EventWeightOverride_Pirates | float | -1.0 | Pirates weight (-1=default) |
| needle_WaveTimerUpdateMultiplier | float | 0.5 | Wave timer multiplier |
| needle_WaveTimerUpdatedMultiplierEnabled | int | 0 | Enable wave timer multiplier |

## 21. Observer/Spectator Mode

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_EnableObserverMode | int | 0 | Enable observer mode |
| needle_EnableDebugObserver | int | 0 | Enable debug observer |
| needle_ObserverModeSkipAI | bool | true | Skip AI in observer mode |
| needle_ObserverModeTeam | int | 0 | Observer team (max=3) |
| needle_AreObserversOmniscient | bool | true | Observers see all |
| needle_EnableClientReadyMatchStartClient | bool | true | Client ready match start (client) |
| needle_EnableClientReadyMatchStartServer | bool | true | Client ready match start (server) |
| needle_EnableTeamShuffle | bool | true | Enable team shuffle |

## 22. Indicator/Attention System

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| needle_IndicatorAttentionOnCreate | bool | true | Attention on create |
| needle_IndicatorAttentionOnCreate_Large | int | 0 | Large attention on create |
| needle_IndicatorAttentionOnNewTarget | bool | true | Attention on new target |
| needle_IndicatorAttentionOnNewTarget_Large | int | 0 | Large attention on new target |
| needle_IndicatorAttentionOnSpawning | bool | true | Attention on spawning |
| needle_IndicatorAttentionOnSpawning_Large | int | 0 | Large attention on spawning |
| needle_IndicatorAttentionOnCapitalShipAppear | bool | true | Attention on capital ship |
| needle_IndicatorAttentionOnCapitalShipAppear_Large | int | 0 | Large attention on capital ship |
| needle_IndicatorAttention_LargeAnimStartScale | float | 0.3 | Large anim start scale |
| needle_IndicatorAttention_LargeAnimTime | float | 0.7 | Large anim time (s) |
| needle_IndicatorAttention_SmallAnimStartScale | float | 0.7 | Small anim start scale |
| needle_IndicatorAttention_SmallAnimTime | float | 0.3 | Small anim time (s) |
| needle_IndicatorAttention_NewTargetLockoutTime | float | 5.0 | New target lockout (s) |
| needle_IndicatorAttention_NewTargetLockoutTime_Large | float | 5.0 | Large target lockout (s) |
| needle_Indicator_StructureDistanceToHide | float | 50.0 | Structure indicator hide distance |
| needle_Indicator_StructureDistanceToShow | float | 125.0 | Structure indicator show distance |

## Enum Reference

### MatchType (needle_MatchType)
| Value | Name | Description |
|-------|------|-------------|
| 0 | Conquest | Capture and hold sectors, drain enemy tickets |
| 1 | Recon | Reconnaissance-focused mode |
| 2 | Hunt | Hunting/elimination mode |
| 3-7 | Reserved | Additional mode slots (unused in retail) |

### MatchSize (needle_MatchSize)
| Value | Name | Typical Players |
|-------|------|----------------|
| 0 | Small | Up to 5v5 |
| 1 | Medium | Up to 8v8 |
| 2 | Large | 10v10 |

### Ship Categories
| Value | Name |
|-------|------|
| 0 | Scout |
| 1 | Raider |
| 2 | Frigate |
| 3 | (max for DebugContract_ShipType) |

---

*Generated 2026-04-03 from Dead Star build 1234898 (Depot 366401)*
*Binary analysis via x64 disassembly of config variable registration functions*
