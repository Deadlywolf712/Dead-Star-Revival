# Dead Star -- Cut Content Archaeological Report

Generated: 2026-04-03
Source: Binary string analysis of `GameComponentsNeedle_Steam_Release.dll`, `NeedleCommon_Steam_Release.dll`, and cross-referenced asset paths from `_sped_paths.txt`.

---

## 1. CUT GAME MODES

Dead Star shipped with **Conquest** (10v10 sector control), **Recon** (smaller variant), and **Needle Escape** (capital ship endgame run). The binaries contain evidence of **seven additional mode entries** beyond what shipped.

### 1a. Needle Crisis -- PARTIALLY IMPLEMENTED

**DLL Evidence:**
- `MatchType_NeedleCrisis`
- `OnMatchType_NeedleCrisis`
- `~LOADING_MATCH_NEEDLE_CRISIS~`
- `LOADING_NEEDLE_CRISIS_TIP_` (loading screen tips were written)

**Asset Evidence:**
- `region_needle_crisis_4_twobottom_01.cgpr`
- `region_needle_crisis_4_twobottom_02.cgpr`
- `region_needle_crisis_4_twotop_01.cgpr`
- `region_needle_crisis_4_twotop_02.cgpr`
- `region_needle_crisis_5_cross.cgpr`

**Rating: PARTIALLY IMPLEMENTED** -- Has matchtype enum, event handler (`OnMatchType_`), loading screen tips, AND five map layouts. This mode was playable at some point. The map layouts suggest 4-5 sector maps with asymmetric designs (two-bottom, two-top, cross). No dedicated lobby state exists (unlike NeedleEscape which has `LobbyState_NeedleEscape_Game`), suggesting it was cut before the final lobby system was built.

### 1b. Needle Discovery -- PARTIALLY IMPLEMENTED

**DLL Evidence:**
- `MatchType_NeedleDiscovery`
- `OnMatchType_NeedleDiscovery`
- `~LOADING_MATCH_NEEDLE_DISCOVERY~`
- `LOADING_NEEDLE_DISCOVERY_TIP_`

**Asset Evidence:**
- `region_needle_discovery_4_diamond.cgpr`
- `region_needle_discovery_4_unbalanced_01.cgpr` through `_04.cgpr`

**Rating: PARTIALLY IMPLEMENTED** -- Same level of integration as Crisis. Five map layouts. The "unbalanced" layout names suggest asymmetric map designs where teams had different starting positions, possibly a mode where one team defends and the other explores/discovers.

### 1c. Needle Exploration -- PARTIALLY IMPLEMENTED

**DLL Evidence:**
- `MatchType_NeedleExploration`
- `OnMatchType_NeedleExploration`
- `~LOADING_MATCH_NEEDLE_EXPLORATION~`
- `LOADING_NEEDLE_EXPLORATION_TIP_`

**Asset Evidence:**
- `region_needle_exploration_4_diamond_01.cgpr`, `_02.cgpr`
- `region_needle_exploration_4_triangle_01.cgpr`, `_02.cgpr`
- `region_needle_exploration_4_twobottom_01.cgpr`
- `region_needle_exploration_4_twotop_01.cgpr`
- `region_needle_exploration_4_unbalanced_01.cgpr`, `_02.cgpr`

**Rating: PARTIALLY IMPLEMENTED** -- The most map layouts of any cut mode (8 layouts). Triangle, diamond, twobottom/twotop, and unbalanced. This was the most developed of the three cut Needle modes.

### 1d. Freeplay -- CONFIRMED CUT (Late-Stage)

**DLL Evidence:**
- `MatchType_Freeplay`
- `OnMatchType_Freeplay`
- `SetEntryPoint_FreePlayMenu`
- `Triggered_FreePlayMenu`
- `~LOADING_MATCH_FREEPLAY~`
- `LOADING_FREEPLAY_TIP_`

**Asset Evidence (extensive):**
- `freeplay_lobbymenu.cgpr` (dedicated lobby menu script)
- `freeplay_bkgr.ctxr`
- `freeplay_menusquare_neutral.ctxr`, `freeplay_menusquare_selected.ctxr`
- 29 background icons: `icon_freeplay_background_01.ctxr` through `_29.ctxr`
- Asteroid, nebula, outpost, and upgrade selection icons
- `region_freeplay_3_circle.cgpr` (map layout)

**Rating: CONFIRMED CUT** -- This had its own entry point in the main menu system, its own lobby menu, its own map layout, and an extensive icon set suggesting players could customize match parameters (background, asteroids, nebula, outpost types, upgrades). This was essentially a custom/sandbox mode that was very close to shipping. The 29 background options and multiple customization categories suggest a map editor or custom game creator.

### 1e. Hunt -- CONFIRMED SHIPPED (but evidence of larger plans)

- `MatchType_Hunt`
- `StartMatchmaking_Hunt_Large`, `StartMatchmaking_Hunt_Small`
- `Guardian Hunter` role
- `~XP_GUARDIANHUNTER~`

**Rating: SHIPPED** -- But the Large/Small matchmaking options and Guardian Hunter XP suggest it may have been planned as a more prominent mode.

### 1f. Needle (base mode) -- ENUM ONLY

- `MatchType_Needle`

**Rating: ENUM ONLY** -- Appears to be the base/parent enum value. No `OnMatchType_Needle` handler. Possibly the original umbrella mode name before the Conquest/Recon split.

### Summary: All Match Types in Enum Order

| Match Type | Status |
|---|---|
| MatchType_Needle | Enum only (parent) |
| MatchType_Conquest | **SHIPPED** |
| MatchType_Recon | **SHIPPED** |
| MatchType_Hunt | **SHIPPED** |
| MatchType_NeedleEscape | **SHIPPED** (capital ship run) |
| MatchType_NeedleCrisis | **CUT** -- 5 maps, loading tips |
| MatchType_NeedleDiscovery | **CUT** -- 5 maps, loading tips |
| MatchType_NeedleExploration | **CUT** -- 8 maps, loading tips |
| MatchType_Freeplay | **CUT** -- Full menu, 29 bg options |
| MatchType_Tutorial | **SHIPPED** |

---

## 2. CUT RACES (FACTIONS)

Dead Star shipped with 5 playable races (A through E). The binaries contain references to **8 races total** plus test assets.

### Shipped Races (A-E)

Each has full ship assets (Scout, Raider, Frigate), skins, portraits (male/female, basic/elite), augments:
- **Race A** -- Full ship roster, 2M/2F portraits + elite variants
- **Race B** -- Full ship roster, 2M/2F portraits + elite variants
- **Race C** -- Full ship roster, 2M/2F portraits + elite variants
- **Race D** -- Full ship roster, 2M/2F portraits + elite variants
- **Race E** -- Full ship roster, 2M/2F portraits + elite variants

### Cut Races -- ENUM ONLY

- **Race F** (`racef`, `~AUGMENT_ORIGIN_RACEF~`)
- **Race G** (`raceg`, `~AUGMENT_ORIGIN_RACEG~`)
- **Race H** (`raceh`, `~AUGMENT_ORIGIN_RACEH~`)

**Rating: ENUM ONLY** -- These exist in the augment origin enum (meaning augments were planned to be faction-specific for 8 races) but no ship models, portrait assets, or gameplay code exists for races F-H. They were planned but never entered production.

### Special/Crossover Races

- **Ratchet** (`raceratchet`) -- `portrait_ratchet_00.ctxr`, `portrait_ratchet_01.ctxr`
  - **Rating: PARTIALLY IMPLEMENTED** -- Two portrait assets exist. This is a Ratchet & Clank crossover (PS4 exclusive content). Portraits only, no ship.
  
- **S'jet** (`racesjet`) -- `portrait_sjet_f_00.ctxr`
  - **Rating: PARTIALLY IMPLEMENTED** -- One portrait asset. This is a Homeworld crossover reference (S'jet is a prominent Homeworld family). Armature Studio was connected to Gearbox who owned Homeworld IP at the time.

- **Armature Bug** (`racearmaturebug`) -- `portrait_armaturebug_main.ctxr`, `portrait_armaturebug_linesscrolling.ctxr`, `portrait_armaturebug_mask.ctxr`
  - **Rating: PARTIALLY IMPLEMENTED** -- Three texture assets for an animated portrait. Developer studio self-reference, likely a dev-team-only cosmetic.

### Test/Dummy Race

- **Dummy Race** (`dummyrace/dummycategory`) -- Full collision, geometry, debris, skin, UI, and localization assets
  - **Rating: DEVELOPMENT TOOL** -- A template/test ship with complete assets used for development. Has its own `_dummyskin` material.

---

## 3. CUT SHIPS & SHIP TYPES

### Ship Classes (Shipped)

The code references 4 ship functional types:
- `ShipType_Combat`
- `ShipType_Mining`  
- `ShipType_Production`
- `ShipType_Research`

Each race has 3 hull classes: **Scout**, **Raider**, **Frigate** (5 races x 3 = 15 playable ships).

### AI Combat Ships

- `ships/aicombat/frigate/`, `ships/aicombat/raider/`, `ships/aicombat/scout/`
- **Rating: SHIPPED** -- NPC enemy ships (pirates, guardians). Full models and skins.

### Three Loadout Slots

- `Slot_1_ShipType`, `Slot_2_ShipType`, `Slot_3_ShipType`
- Players could bring 3 ships per match. This shipped.

### Hidden Ships Debug

- `needle_ShowHiddenShips` -- Debug cvar to show ships not normally visible in menus
- **Rating: CONFIRMED CUT** -- Implies some ships were in the data but hidden from players.

---

## 4. CUT WEAPONS & DEVICES

### Weapon Types Found in Assets

From ship attachment assets:
- **Pod Cannon** (`weapon_racec_podcannon`) -- Race C specific weapon
- **Mine** (`payload_raced_mine`, `payload_raced_mine_alert`) -- Race D deployable mine

### Turret Types (Outpost Defenses)

Medium turrets:
- Beam MkI, EMP MkI, Energy Pellet MkI, Gatling Gun, ISBM MkI

Small turrets:
- Beam MkI, Blast Cannon MkI, Bullet MkI, Missile MkI

**Note:** The "MkI" suffix on all turrets suggests **MkII/MkIII upgrade tiers** were planned but only MkI was implemented.

### Deprecated Fire Control

- `DEPRECATED: CComponentNeedleFireControlAlternating should not be used anymore.`
- **Rating: CONFIRMED CUT** -- An alternating fire control system existed and was deprecated in favor of `FireControlSimple`.

---

## 5. PS4 / CROSS-PLATFORM -- CONFIRMED CUT (Deep Integration)

### DLL Evidence (GameComponents)

- `ControllerType_PS4`
- `needle_PS4CachedSystemSafeFrameRatio`
- `PS4_ICON`, `%PS4_ICON%`
- `_ps4` platform tag
- `AllowCrossplay`, `matchmaking_allow_crossplay`
- `Crossplay:%d` in matchmaking debug strings
- `SOpaquePlatformId` -- Full platform-agnostic ID system
- `AS_Online_GetPlatformSpecificAuth` -- Platform-specific authentication
- `AS_Online_GetPlatformSpecificEnvironment`

### DLL Evidence (NeedleCommon)

- `_ps4` -- Platform identifier in the common library

### Cross-Platform Architecture

The platform abstraction is deep:
- `SOpaquePlatformId` with constructor, copy, equality operators
- `IsPlatformIdEmpty()`, `GetOpaquePlatformId()`
- Party system uses platform IDs: `IsPlayerInParty(SOpaquePlatformId)`, `KickPlayer(SOpaquePlatformId)`, `SendInvite(SOpaquePlatformId)`, `TransferRoomOwnershipTo(SOpaquePlatformId)`
- `GetPlatformSpecificAuth`, `GetPlatformSpecificEnvironment`
- Crossplay flag in matchmaking: `Mode:%s, ReqType:%d, Type:%d, Size:%d, Contract:%llu, Party:%s, Count:%d, Crossplay:%d region(Default:%d, Custom:%d)`

**Rating: CONFIRMED CUT (Deep)** -- This is not just flags. The entire networking/party/matchmaking system was built with cross-platform support. Platform IDs are abstracted at the lowest level. The PS4 controller type, safe frame ratio, and PS4 icon suggest the PS4 version was in active development. Crossplay was a matchmaking parameter, not just a concept. Dead Star did launch on PS4, so this code was used -- but the Steam build retains all the PS4 cross-platform code paths.

---

## 6. DEMO/FREEPLAY MODE -- CONFIRMED CUT

### DLL Evidence

- `Freeplay` -- Distinct from the matchtype, also appears as a standalone concept
- `Restricted`, `Triggered_Restricted`
- `ShipLocked`, `SkinLocked`, `PortraitLocked`
- `Locked`, `Unlocked` state system
- `LaunchBlocked`, `LaunchUnblocked`
- `CaptureBlocked`

### What it Restricted

The locking system is granular:
- **Ships** could be locked (`ShipLocked`)
- **Skins** could be locked (`SkinLocked`)
- **Portraits** could be locked (`PortraitLocked`)
- **Launch** could be blocked (`LaunchBlocked`)
- **Capture** could be blocked (`CaptureBlocked`)

There's also a "Restricted" trigger state (`Triggered_Restricted`) suggesting a mode where certain features were disabled.

**Rating: CONFIRMED CUT** -- The locking infrastructure exists and is hooked into the UI. This could have been used for a demo/trial mode or free-to-play restrictions. Given that Dead Star was a paid game ($19.99), this was likely planned for a F2P conversion that never happened, or a limited demo.

---

## 7. CUT UI SCREENS & MENUS

### Entry Points (Main Menu Flow)

```
SetEntryPoint_LegalScreen
SetEntryPoint_TitleScreen
SetEntryPoint_MainMenu
SetEntryPoint_TutorialMenu
SetEntryPoint_FreePlayMenu      <-- CUT
SetEntryPoint_MatchmakingLobby
SetEntryPoint_NeedleLobby
SetEntryPoint_GameLobby
```

The Freeplay menu was a top-level entry point alongside Tutorial and Matchmaking. It would have appeared as a main menu option.

### Lobby States

```
LobbyState_Game
LobbyState_Matchmaking
LobbyState_NeedleEscape_Game
LobbyState_NeedleEscape_Matchmaking
```

NeedleEscape has its own lobby flow (separate from standard matchmaking), suggesting it was a distinct experience -- possibly an in-match event rather than a queued mode.

### Freeplay Lobby Menu

The `freeplay_lobbymenu.cgpr` script and extensive icon set reveal a customization screen with:
- **29 backgrounds** to choose from
- **3 asteroid types** 
- **5 nebula types** (cloak, corrosive, EMP, fiery, frozen)
- **5 outpost configurations**
- **4 upgrade presets** + full upgrade option
- **Region/background selection**

This was essentially a **custom match creator** with visual map customization.

### After Action Menu

- `afteractionmenu.cgpr` -- Post-match results screen (shipped)
- References to fame/XP displays, trophy progress

### Structure Upgrade Menu

Images exist for upgrades that may not have all shipped:
- `structure_image_combatbeam.ctxr`
- `structure_image_combatbullet.ctxr`  
- `structure_image_combatemp.ctxr`
- `structure_image_combatmissile.ctxr`
- `structure_image_construction.ctxr`
- `structure_image_mining.ctxr`
- `structure_image_needlefront/left/middle/right.ctxr`
- `structure_image_research.ctxr`
- `structure_image_sensor.ctxr`

---

## 8. COSMETICS & UNLOCKS

### Skin System

- 3 skin tiers: `~SKIN_TYPE_BASIC~`, `~SKIN_TYPE_ELITE~`, `~SKIN_TYPE_PATTERN~`
- `needle_ShowHiddenSkins` -- Debug flag to reveal hidden skins
- `needle_PlayersCanUseAllSkinsForTesting` -- Dev testing flag
- `FocusedSkinCanBePurchased` / `FocusedSkinCanNotBePurchased` -- Skins had purchase states
- Only 1 skin icon exists in assets: `skin_icon_0001.ctxr`

**Rating: PARTIALLY IMPLEMENTED** -- The skin purchasing system and three tiers exist in code. "Pattern" skins (recolors?) are referenced but unclear if they all shipped. The single skin icon suggests the system was early.

### Portrait System

- Portraits span IDs 0-64 (with 51 missing -- portrait_51_package.cgpr does not exist)
- Each race has male/female variants with basic and elite tiers
- `needle_ShowHiddenPortraits` -- Hidden portraits exist
- `OnBasicPortrait` / `OnElitePortrait` -- Two portrait quality tiers
- **Ratchet portraits** (2) and **S'jet portrait** (1) are crossover exclusives
- **Armature Bug portrait** -- Developer cosmetic with animated scrolling lines effect

**Rating: PARTIALLY IMPLEMENTED** -- 64 portrait package slots with some hidden. The gap at ID 51 may be intentional (removed content) or a numbering quirk.

### DLC System

- `CCPLdrNeedlePackageDlcMasterList` -- Full DLC master list system
- `CPOLdrNeedleDlcMasterListEntry` -- Individual DLC entries
- `FocusedShipCanBePurchased` / `FocusedPortraitCanBePurchased` / `FocusedSkinCanBePurchased`
- `OpenStore` -- Links to `http://store.steampowered.com/app/%u`
- `STORE_PURCHASE_REFRESH_GRIDS`
- `isDLC` flag on items
- `StoreHandler` component

**Rating: CONFIRMED CUT** -- A full in-game store was implemented that could link to Steam store pages for DLC purchases. Ships, portraits, and skins all had purchase/DLC flags. No DLC was ever released for Dead Star.

---

## 9. PROGRESSION & TROPHIES

### Augment System (Shipped but with cut content)

- Augment types: Amplifier, Creation, Damage, Data, Defense, Electronics, Empty, Energy, Logic, Propulsion, Universal
- Under-the-hood modifiers: Angular Velocity, Cooldown, Damage Input/Output, Health, Linear Velocity, Repair, Sensor Strength, Speed
- **8 race origins** for augments (only 5 races shipped)
- Augment reconstruction system with critical/miraculous success tiers

### Trophy/Achievement System

```
needle_TrophyBaseCapturesForControlFreak
needle_TrophyDecisiveVictoriesForSoulEater
needle_TrophyFlightTimeForCertifiedPilot
needle_TrophyKillStreakForEnFuego
needle_TrophyKillStreakForUntouchable
needle_TrophyOreSpentForClaimJumper
needle_TrophyPlayerAssistsForAccomplice
needle_TrophyPlayerKillsForBloodGod
needle_TrophyPlayerKillsForReaper
needle_TrophyShipPlayerKills
needle_TrophyVictoriesForBiggestFish
```

**Rating: SHIPPED** -- These correspond to PS4 trophies / Steam achievements.

---

## 10. OBSERVER / SPECTATOR MODE -- PARTIALLY IMPLEMENTED

- `Enable Observer Mode`
- `needle_EnableObserverMode`
- `needle_EnableDebugObserver`
- `needle_ObserverModeSkipAI`
- `needle_ObserverModeTeam`
- `Are Observers Omniscient` / `needle_AreObserversOmniscient`
- `^Observing Team: Hunter`, `^Observing Team: Old Empire`
- `Client Replay` / `needle_ClientReplayMode`

**Rating: PARTIALLY IMPLEMENTED** -- A spectator/observer system exists with team selection, omniscient mode toggle, AI skip, and even a client replay mode. The `^` prefix on some strings suggests debug console output. This was likely a dev tool that was partially exposed or planned for release.

---

## 11. VOICE CHAT -- SHIPPED (Steam Voice)

- Uses Steam's built-in voice API (`GetAvailableVoice`, `GetVoice`, `DecompressVoice`)
- `needle_VoiceChatPushToTalkMode` -- Push-to-talk option
- `needle_VoiceChatLoopback` -- Dev testing
- `needle_VoiceChatSpeakerVolume` -- Volume control
- `MuteAllButFriends` -- Social feature
- No Vivox or third-party voice SDK detected

**Rating: SHIPPED** -- Built on Steam's voice API.

---

## 12. PLAYER COMMS SYSTEM -- SHIPPED

Quick communication wheel with:
- Attack Here, Defend Here, Enemy Spotted, Follow Me, Need Repair, Yes, No, Sorry, Thanks

All have both HUD icons and map icons.

---

## 13. TEST/DEBUG REGIONS

Hidden in the assets are developer test maps:

- `region_test_ai.cgpr` -- AI behavior testing
- `region_test_art.cgpr` -- Art review
- `region_test_barriers.cgpr` -- Collision/barrier testing
- `region_test_empty.cgpr` -- Empty sandbox
- `region_test_gameplay.cgpr` -- General gameplay testing
- `region_test_mega_asteroid.cgpr` -- Large asteroid testing
- `region_test_ncpships.cgpr` -- NPC ship testing
- `region_test_particles.cgpr` -- Particle effect testing
- `region_test_structures.cgpr` -- Structure/outpost testing
- `region_test_three_team.cgpr` -- **THREE TEAM MODE TESTING**
- `region_test_vidcap.cgpr` -- Video capture / trailer recording
- `region_capitalship_vidcap.cgpr` -- Capital ship video capture (attributed to dev "berenger")

**Rating: DEVELOPMENT TOOLS** -- These shipped in the asset files but aren't accessible normally.

### Notable: Three Team Mode

`region_test_three_team.cgpr` -- Evidence that a **3-team game mode** was tested. Dead Star shipped as 2-team (Drifters vs Scavengers) with Old Empire as an AI third faction. A true 3-team PvP mode was explored. The yellow team UI assets (`team_bar_highlight_yellow.ctxr`, `team_yellow_bg.ctxr`) alongside blue, red, and green support this.

**Rating: PARTIALLY IMPLEMENTED** -- Test map exists, team color UI assets exist for 4 colors (blue/red/green/yellow). A 3 or 4 team mode was prototyped.

---

## 14. REGION EVENTS (Some Cut)

Region events found in assets:

| Event | Assets |
|---|---|
| Comet Ice | `regionevent_cometice.ctxr` |
| Comet Storm | `regionevent_cometstorm.ctxr` |
| Comet Molten | Map scripts reference it |
| Comet Plasma | Map scripts reference it |
| Energy Surge | `regionevent_energysurge.ctxr` |
| Guardians | `regionevent_guardians.ctxr` |
| Max Augments | `regionevent_maxaugments.ctxr` |
| Plasma Storm | `regionevent_plasmastorm.ctxr` |
| Pirates | `_event_pirates` in map scripts |
| Misc_0 | Generic events in scripts |

---

## 15. VERSION / BUILD REFERENCES

- `BuildVersion` -- Build version string
- `ClientVersion` / `ServerVersion` -- Client-server version matching
- `AddWebServiceInterfaceVersionParam` -- API versioning
- `buildversion.txt` exists in named assets

No changelog or patch note strings found in the binary. Version tracking was programmatic only.

---

## SUMMARY TABLE

| Category | Finding | Rating |
|---|---|---|
| **Needle Crisis** | 5 map layouts, loading tips, event handler | PARTIALLY IMPLEMENTED |
| **Needle Discovery** | 5 map layouts, loading tips, event handler | PARTIALLY IMPLEMENTED |
| **Needle Exploration** | 8 map layouts, loading tips, event handler | PARTIALLY IMPLEMENTED |
| **Freeplay Mode** | Full menu, 29 backgrounds, map customizer | CONFIRMED CUT |
| **Race F, G, H** | Augment origin enums only | ENUM ONLY |
| **Ratchet Crossover** | 2 portrait textures | PARTIALLY IMPLEMENTED |
| **S'jet Crossover** | 1 portrait texture | PARTIALLY IMPLEMENTED |
| **Armature Bug Portrait** | 3 animated portrait textures | PARTIALLY IMPLEMENTED |
| **PS4 Cross-Platform** | Deep platform abstraction, crossplay flag | CONFIRMED CUT (in Steam build) |
| **Demo/Restrictions** | Ship/skin/portrait locking, launch blocking | CONFIRMED CUT |
| **DLC Store** | Full master list, Steam store links | CONFIRMED CUT |
| **Observer/Spectator** | Mode toggle, team selection, omniscient, replay | PARTIALLY IMPLEMENTED |
| **3-Team Mode** | Test map, 4 team color UI assets | PARTIALLY IMPLEMENTED |
| **Hidden Skins** | Debug flags to show hidden content | CONFIRMED CUT |
| **Hidden Ships** | Debug flags to show hidden content | CONFIRMED CUT |
| **Hidden Portraits** | Debug flags to show hidden content | CONFIRMED CUT |
| **Turret MkII/III** | All turrets suffixed MkI only | ENUM ONLY |
| **Alternating Fire** | Deprecated fire control component | CONFIRMED CUT |
| **Dummy Race Ship** | Full test ship with all asset types | DEVELOPMENT TOOL |
| **12 Test Regions** | AI, art, gameplay, 3-team, vidcap maps | DEVELOPMENT TOOL |

---

## KEY TAKEAWAYS

1. **Freeplay was the biggest cut.** It had its own main menu entry, a full custom match setup screen with 29 backgrounds and extensive customization. This was essentially a private/custom match creator that was very close to completion.

2. **Three Needle sub-modes died together.** Crisis, Discovery, and Exploration all had the same level of integration (enum + event handler + loading tips + multiple map layouts). They were likely different sector configurations for the Needle/capital ship endgame. Exploration was the most developed with 8 map variants.

3. **Eight races were planned, five shipped.** The augment system was designed for 8 factions. Races F-H never entered art production.

4. **The DLC/store system was built but never used.** Ships, skins, and portraits all had purchase flags. The Steam store integration was coded. No DLC was ever released before delisting.

5. **PS4 cross-play was deeply integrated.** The entire party/matchmaking system was built platform-agnostic. Cross-play was a matchmaking parameter. The Steam binary carries all the PS4 code paths.

6. **A 3 or 4 team PvP mode was prototyped.** Team color assets exist for 4 teams, and a dedicated 3-team test region was built.

7. **Observer/spectator with replay was in development.** Omniscient observation, team selection, and client replay functionality exist in the code.
