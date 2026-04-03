# Dead Star -- Hidden Secrets Report
## Console Commands, Debug Menus, Cheat Codes & Developer Tools

Generated: 2026-04-03
Source: `Bin64/*.dll` string analysis

---

## 1. GOD MODE / CHEAT FLAGS [!!!]

These are the most exciting finds -- full cheat variables baked into the shipping binary:

| Variable | Description |
|----------|-------------|
| `needle_GodMode` | **[!!!] Player god mode toggle** |
| `needle_AiGodMode` | AI god mode toggle |
| `needle_HasInfiniteOre` | **[!!!] Unlimited ore resource** |
| `ArmorNoDamage` | Armor takes no damage |
| `ShieldNoDamage` | Shield takes no damage |
| `ShipHit_NoDamage` | Ship takes no damage on hit |
| `needle_SelfDestructPlayer` | Force self-destruct |

**God Mode strings found:** `AI God Mode`, `God Mode`, `Infinite Ore`

---

## 2. OBSERVER / SPECTATOR MODE [!!!]

Full spectator system exists in the game:

| Variable | Description |
|----------|-------------|
| `needle_EnableObserverMode` | **[!!!] Enable spectator mode** |
| `needle_EnableDebugObserver` | **[!!!] Debug observer with extra powers** |
| `needle_AreObserversOmniscient` | **[!!!] See everything (both teams)** |
| `needle_ObserverModeSkipAI` | Observer ignores AI ships |
| `needle_ObserverModeTeam` | Which team observer follows |

Related UI text: `Observer Team (Only valid when starting as an Observer)`

---

## 3. DEBUG CAMERA [!!!]

Full free-flight debug camera system in `GameCore_Steam_Release.dll`:

- `CComponentCameraDebugCamera` -- Full component class
- `ToggleActive` / `SetActive` / `SetInactive` message handlers
- `EnableUserInput` / `DisableUserInput` toggles
- `invertDebugCamera` -- Invert controls flag
- `Debug Camera '%s' auto reactivated.` -- Auto-reactivation system
- `SetDefaultDebugCameraActive` -- Activate default debug cam
- `DisableDefaultDebugCamera` -- Deactivate it

---

## 4. DEBUG MENU SYSTEM [!!!]

A full hierarchical debug menu exists (CDebugMenu):

**Source files referenced:**
- `CDebugMenu.cpp`
- `CDebugConsole.cpp`

**Menu API (from mangled symbols):**
- `CDebugMenu::Enable(bool)` -- **[!!!] Toggle the debug menu on/off**
- `CDebugMenu::IsEnabled()` -- Check if menu is active
- `CDebugMenu::Render()` -- Draw the menu
- `CDebugMenu::Update(CUserInput, float)` -- Process input
- `CDebugMenu::AddMenuItemBool(...)` -- Add bool toggle
- `CDebugMenu::AddMenuItemInt(...)` -- Add integer slider
- `CDebugMenu::AddMenuItemFloat(...)` -- Add float slider
- `CDebugMenu::RemoveFolder(...)` -- Remove menu folder
- `CDebugMenu::RemoveMenuItemByCaption(...)` -- Remove item
- `CDebugMenu::AssignMenuItemFriendlyNames(...)` -- Set display names
- `CDebugMenu::SyncFrameBegin()` -- Frame sync
- `CGameManager::AddDebugMenuItems()` -- **[!!!] Populates the menu**

**Root folder:** `Main Debug Menu`

Error: `Trying to make a debug menu item of type I don't know!`
Error: `Can't add string types to the debug menu`
Error: `Debug folder name too large`

---

## 5. DEBUG CONSOLE SYSTEM

Full in-game console with output rendering:

| Variable | Description |
|----------|-------------|
| `debugConsoleMaxBottomLines` | Max lines at bottom |
| `debugConsoleMaxTopLines` | Max lines at top |
| `debugConsoleStringTimeout` | How long strings stay visible |
| `dumpConsoleOutputToTerminal` | **[!!!] Dump console to stdout** |
| `renderConsoleMessages` | Toggle console message rendering |
| `renderConsoleOutput` | Toggle console output rendering |
| `renderConsoleTopLines` | Toggle top-line rendering |

**Console infrastructure:**
- `bpe_console_printf` -- Print to in-game console
- `bpe_debugger_and_console_printf` -- Print to both debugger + console
- `bpe_set_console_print_hook` -- Hook console output
- `gpConsole` -- Global console pointer (`CConsole*`)
- `PrintToConsole` -- Direct print function
- `CCPLdrNeedleLocalClientConsoleHelper` -- Console helper component

**HUD console message types:**
- `~HUD_CONSOLE_AI~`
- `~HUD_CONSOLE_DIED~`
- `~HUD_CONSOLE_JOINED~`
- `~HUD_CONSOLE_KILLED~`
- `~HUD_CONSOLE_LEFT~`

Console font: `$/enginesupport/fonts/****/console.cfon`

---

## 6. UNLOCK ALL / TESTING FLAGS [!!!]

| Variable | Description |
|----------|-------------|
| `needle_PlayersCanUseAllShipsForTesting` | **[!!!] Unlock all ships** |
| `needle_PlayersCanUseAllSkinsForTesting` | **[!!!] Unlock all skins** |
| `needle_ShowHiddenShips` | **[!!!] Show hidden/cut ships** |
| `needle_ShowHiddenSkins` | **[!!!] Show hidden/cut skins** |
| `needle_ShowHiddenPortraits` | **[!!!] Show hidden portraits** |
| `needle_DebugShowAllAugments` | Show all augments |
| `needle_DebugShowAllTacticalActions` | Show all tactical actions |

Debug log messages confirm these work:
- `DEBUG: Players Can Use All Ships`
- `DEBUG: Players Can Use All Skins`

---

## 7. MATCH CONTROL / SERVER COMMANDS [!!!]

Commands that control match flow and server state:

| Variable | Description |
|----------|-------------|
| `needle_StartGame` | **[!!!] Force start a game** |
| `needle_EndMatchAndShowResults` | **[!!!] Force end match** |
| `needle_MatchAutoStart` | Auto-start matches |
| `needle_MatchStartCountdown` | Set countdown timer |
| `needle_ReturnToLobby` | Return to lobby |
| `needle_SkipToLobby` | Skip directly to lobby |
| `needle_SkipToMain` | Skip to main menu |
| `needle_MakeGalaxy` | **[!!!] Generate galaxy map** |
| `needle_ForceSector` | Force specific sector |
| `needle_ResetServerOnNoConnections` | Auto-reset server |
| `needle_MatchType` | Set match type |
| `needle_MatchSize` | Set match size |
| `needle_MatchBalanceTime` | Team balance timer |
| `needle_MatchCountdownTime` | Countdown duration |
| `needle_MatchReadyTime` | Ready-up timer |
| `needle_MatchFinishedRestartTime` | Post-match restart timer |
| `needle_EnableTeamShuffle` | Enable team shuffling |
| `needle_EnableClientReadyMatchStartClient` | Client ready-up |
| `needle_EnableClientReadyMatchStartServer` | Server ready-up |
| `needle_useMatchmaker` | Toggle matchmaker |
| `needle_publishMatchStats` | Toggle stat publishing |

---

## 8. SHIP CYCLING / TEAM SWITCHING COMMANDS

| Command | Description |
|---------|-------------|
| `AllShips_NextShip` | **[!!!] Cycle to next ship (all ships)** |
| `AllShips_PrevShip` | **[!!!] Cycle to previous ship (all ships)** |
| `Follow_NextShipInTeam` | Follow next teammate |
| `Follow_PrevShipInTeam` | Follow previous teammate |
| `SwitchTeam` | **[!!!] Switch teams** |
| `SetSlot_NextShip` | Change ship slot |
| `NextShipFilter` / `PrevShipFilter` | Filter ships |
| `AnnihilateAllShips` | **[!!!] Destroy all ships** |
| `DestroyAllShips` | Destroy all ships |
| `AnnihilateAllSpawnedHealthComponents` | Destroy all health |
| `DespawnShip` | Despawn a ship |

---

## 9. STRESS TEST / BOT SYSTEM [!!!]

The game has a built-in bot/stress test system:

| Variable | Description |
|----------|-------------|
| `needle_DebugStressTest` | **[!!!] Enable stress test mode** |
| `needle_DebugStressTestDisableTickets` | Disable tickets in stress test |
| `needle_DebugStressTestServices` | Stress test with services |
| `needle_DebugStressTestShip` | Set stress test ship type |
| `needle_DebugStressTestTeam` | Set stress test team |
| `needle_MinStressTestLifetime` | Min bot lifetime |
| `needle_MaxStressTestLifetime` | Max bot lifetime |

Related: `Fake Player %d` -- Fake player naming format
Related: `FakeListenForSinglePlayer` -- Fake listen server for SP

---

## 10. NEEDLE DEBUG VARIABLES -- CONTRACT/STATE INSPECTION

Full contract state inspection system (all `needle_DebugContract_*`):

- `needle_DebugContractId` -- Current contract ID
- `needle_DebugContract_ShipType` -- Ship type in contract
- `needle_DebugContract_PrevJumpNumber` -- Previous jump number
- `needle_DebugContract_Core_SpecialistId` -- Core specialist
- `needle_DebugContract_Node_[0-3]_Level` -- Node levels
- `needle_DebugContract_Node_[0-3]_Ore` -- Node ore amounts
- `needle_DebugContract_Node_[0-3]_EverDestroyed` -- Destruction state
- `needle_DebugContract_Node_[0-3]_SpecialistId` -- Node specialists
- `needle_DebugContract_Node_[0-3]_Pod_[0-3]_Destroyed` -- Pod states
- `needle_UseDebugContract` -- **[!!!] Use debug contract data**

---

## 11. NETWORK/API DEBUG TOGGLES

These toggle visibility of network request/response data:

| Variable | What it shows |
|----------|--------------|
| `needle_ShowClientInfo` | Client info |
| `needle_ShowServerInfo` | Server info |
| `needle_ShowClientPingTimes` | Ping times |
| `needle_ShowAugmentShipRequest/Response` | Augment API |
| `needle_ShowRefreshAccountDataRequest/Response` | Account refresh API |
| `needle_ShowPushPlayerAccountDataChangesRequest/Response` | Account push API |
| `needle_ShowPushRewardsRequest/Response` | Rewards API |
| `needle_ShowPushCapitalShipMatchStatsRequest/Response` | Match stats API |
| `needle_ShowStartRunRequest/Response` | Start run API |
| `needle_ShowDeleteContractRequest/Response` | Delete contract API |
| `needle_ShowReconstructAugmentRequest/Response` | Reconstruct API |
| `needle_ShowLeaderboardResponse` | Leaderboard data |
| `needle_ShowLocalLeaderboardEntryResponse` | Local leaderboard |
| `needle_ShowTrophyDataResponse` | Trophy data |
| `needle_ShowRewardsResponse` | Rewards data |
| `needle_ShowPostReportRequest/Response` | Report API |
| `needle_ShowClientCapitalShipMatchStatusRequestResponse` | Capital ship status |
| `needle_ShowServerCapitalShipMatchStatusRequestResponse` | Server capital ship status |
| `needle_ShowCargo` | Cargo display |
| `needle_ShowStatusEffects` | Status effects |
| `needle_ShowDamageNumbers` | Damage numbers |
| `needle_ShowXPNumbers` | XP gain display |

---

## 12. GAME STATE OVERRIDES

| Variable | Description |
|----------|-------------|
| `needle_IsSinglePlayer` | Force single-player mode |
| `needle_IgnoreDatabaseFameCaps` | **[!!!] Bypass fame caps** |
| `needle_IgnoreDatabaseInvalidLists` | Bypass invalid list checks |
| `needle_IgnoreDatabaseScriptVars` | Bypass DB script vars |
| `needle_IgnoreOutOfSectorCheck` | **[!!!] Bypass out-of-sector check** |
| `needle_ServerFameGainMultiplier` | **[!!!] Multiply fame gain** |
| `needle_ServerXpGainMultiplier` | **[!!!] Multiply XP gain** |
| `needle_ForceAccountDataRefresh` | Force account refresh |
| `needle_ForcePushAccountData` | Force push account data |
| `needle_DebugFakePreviousMatchData` | Fake previous match data |
| `needle_StructureLevelOverride` | Override structure level |
| `needle_StructureOverride` | Override structure type |
| `needle_CapitalShipOverride` | Override capital ship |
| `needle_EventChanceOverride` | Override event chance |

---

## 13. COMMAND-LINE FLAGS

Known launch flags from the binaries:

| Flag | Source | Description |
|------|--------|-------------|
| `-debuggfx` | GameCore | Debug graphics mode |
| `-telemetry` | GameCore | Enable telemetry |
| `-i` | (known) | Instance flag |

Most other `-` prefixed strings in GameCore/Engine are binary noise, not real flags.

---

## 14. RENDERER DEBUG CVARS

| Variable | Description |
|----------|-------------|
| `r_showBounds` | Show object bounding boxes |
| `r_showObjectCount` | Show rendered object count |
| `r_disableEnvmap` | Disable environment maps |
| `r_disableSpecular` | Disable specular lighting |
| `ctr_showLoadingCounts` | Show loading counters |
| `needle_ShadowDebug` | Shadow debug visualization |
| `needle_ShadowFreeze` | Freeze shadow cascades |
| `needle_shadowMapShowTexture` | Show shadow map texture |
| `needle_ShadowMapVisualizeCascades` | Visualize shadow cascades |
| `needle_FreezeFrustum` | **[!!!] Freeze camera frustum** |
| `needle_ServerDrawMainView` | Server-side rendering |
| `needle_RenderFixedSafeFrame` | Fixed safe frame |
| `needle_WriteDebugFiles` | **[!!!] Write debug output files** |

---

## 15. VOICE CHAT DEBUG

| Variable | Description |
|----------|-------------|
| `needle_VoiceChatDebug` | Voice chat debug mode |
| `needle_VoiceChatLoopback` | **[!!!] Loopback test mode** |
| `needle_VoiceChatPushToTalkMode` | PTT mode |
| `needle_VoiceChatSpeakerVolume` | Speaker volume |
| `needle_DebugAnyPlayerTalkingDisplay` | Show who's talking |

---

## 16. CAMERA SYSTEM CONTROLS

| Variable | Description |
|----------|-------------|
| `needle_CameraLookAheadEnable` | Look-ahead toggle |
| `needle_CameraLookAheadAccel` | Look-ahead acceleration |
| `needle_CameraLookAheadAim` | Look-ahead while aiming |
| `needle_CameraLookAheadMove` | Look-ahead while moving |
| `needle_CameraRangeIndex` | Camera range preset |
| `needle_CameraZoomEnable` | Zoom toggle |
| `needle_CameraZoomIn` / `Out` | Zoom limits |
| `needle_CameraZoomInRate` / `OutRate` | Zoom speed |
| `needle_CameraZoomInDelay` / `OutDelay` | Zoom delay |
| `needle_MatchFinishedCameraFade` | Post-match camera fade |
| `needle_ClientReplayMode` | **[!!!] Client replay mode** |

---

## 17. DEVELOPER COMMENTS & FUNNY STRINGS

| String | Source |
|--------|--------|
| `~LEADERBOARD_HACKS~` | **[!!!] Leaderboard hacks category** |
| `NO-MAP-FIXME` | Unfixed map issue |
| `DEPRECATED: CComponentNeedleFireControlAlternating should not be used anymore.` | Deprecated weapon system |
| `Trying to make a debug menu item of type I don't know!` | Confused developer |
| `DEBUG STRING - Please install the license file to play the full version of the game.` | License check placeholder |
| `must only have one console` | Singleton enforcement |
| `gConsolePtr == NULL` | Console null check |
| `Value mismatch while transferring cargo!` | Cargo transfer bug |

---

## 18. MISCELLANEOUS INTERESTING FINDS

| Variable/String | Description |
|-----------------|-------------|
| `needle_DebugShortWarpTimers` | **[!!!] Speed up warp timers** |
| `needle_DebugStartingPoints` | Override starting points |
| `needle_DebugGalaxySectors` | Debug galaxy sectors |
| `needle_DebugLongPlayerNames` | Force long player names |
| `needle_DebugLongPlayerNameOverride` | Override player name |
| `needle_DebugPingValue` | Fake ping value |
| `needle_DebugPortraitId` | Override portrait |
| `needle_DebugShipSnapshots` | Ship snapshot debug |
| `needle_DebugPopupErrorString` | Popup error test |
| `needle_DebugTrophyProgress` | Trophy progress debug |
| `needle_NeverFinishCreating` | **[!!!] Hang in creation state** |
| `needle_NeverFinishLoading` | **[!!!] Hang in loading state** |
| `needle_PrintFocusContextChanges` | Log UI focus changes |
| `needle_PrintScannerListUsage` | Log scanner usage |
| `needle_DebugIsFake` (NeedleCommon) | **[!!!] Fake Amazon metadata flag** |
| `needle_ConquestTicketRateMultiplier` | **[!!!] Control ticket drain speed** |
| `needle_WaveTimerUpdateMultiplier` | Modify wave timers |
| `needle_EventWeightOverride_*` | Override event spawn weights |

---

## 19. COMPLETE NEEDLE_ VARIABLE COUNT

**Total unique `needle_` variables found: 280+**

Categories:
- Debug/Test: ~70 variables
- Match Control: ~30 variables
- Game Tuning: ~80 variables
- UI/HUD: ~40 variables
- Network/API: ~30 variables
- Camera/Rendering: ~20 variables
- Audio: ~5 variables
- Misc: ~15 variables

---

## SUMMARY: TOP 10 MOST INTERESTING FINDS

1. **[!!!] `needle_GodMode`** -- Full god mode, left in shipping binary
2. **[!!!] `needle_EnableObserverMode` + `needle_AreObserversOmniscient`** -- Full spectator with omniscient view
3. **[!!!] `CDebugMenu::Enable()`** -- Complete hierarchical debug menu system
4. **[!!!] `needle_PlayersCanUseAllShipsForTesting`** -- Unlock all ships
5. **[!!!] `needle_ShowHiddenShips/Skins/Portraits`** -- Access cut/hidden content
6. **[!!!] `needle_DebugStressTest`** -- Built-in bot system for filling matches
7. **[!!!] `CComponentCameraDebugCamera`** -- Free-flight debug camera
8. **[!!!] `needle_ServerXpGainMultiplier` / `needle_ServerFameGainMultiplier`** -- XP/Fame multipliers
9. **[!!!] `~LEADERBOARD_HACKS~`** -- Leaderboard hacks category string
10. **[!!!] `needle_ClientReplayMode`** -- Replay system exists

---

## NOTES FOR REVIVAL

- The debug menu and console systems are fully present in the release DLLs. These were compiled in but likely gated behind a flag check.
- The `needle_*` variables appear to be CVar-style script variables that can be set at runtime. Finding how to set them (likely through the debug console or config files) would unlock all of this functionality.
- The stress test / bot system (`needle_DebugStressTest`) could be invaluable for testing the revival server with fake players.
- Observer mode could be used for streaming/casting matches.
- The hidden ships/skins/portraits suggest cut content that may still be fully functional.
- The `CDebugMenu` takes `CUserInput` which means it responds to keyboard/gamepad input -- finding the activation key combo is the next step.
