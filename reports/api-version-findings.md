# API Version & Endpoint Deep Dive Findings

**Date:** 2026-04-03  
**Source:** Binary analysis of NeedleCommon_Steam_Release.dll and GameComponentsNeedle_Steam_Release.dll  
**Binary path:** `DepotDownloaderMod/build_output/depots/366401/1234898/Bin64/`

---

## TASK 1: API Version String

### CONFIRMED: `needle_serviceApiVersion` default = `"v1"`

**Evidence:** Binary dump of NeedleCommon_Steam_Release.dll at offset 0x6000:
```
needle_publicServiceUrlOverride | v1 | needle_serviceApiVersion | https://deadstar.rel.armature.com/
```

The string `v1` is located immediately before `needle_serviceApiVersion` in the .rdata string table. In the BPE engine's config var registration pattern, the default value precedes the variable name.

### URL Construction Format

Two format strings confirmed at file offset 0x60C0:
```
%s%sapi/public/%s/%s%s    (public endpoints)
%s%sapi/private/%s/%s%s   (private/server endpoints)
```

The arguments are:
1. `%s` = base URL (e.g., `https://deadstar.rel.armature.com/`)
2. `%s` = empty or override prefix
3. `%s` = API version (`v1`)
4. `%s` = endpoint path (e.g., `authenticate`)
5. `%s` = query string suffix (e.g., `?key=value`)

**Full public URL pattern:** `https://deadstar.rel.armature.com/api/public/v1/{path}`  
**Full private URL pattern:** `https://deadstar.rel.armature.com/api/private/v1/{path}`

### Config Variables for URL Override
- `needle_publicServiceUrlOverride` - overrides the base URL for public API
- `needle_privateServiceUrlOverride` - overrides the base URL for private API
- Default base URL: `https://deadstar.rel.armature.com/`

---

## TASK 2: WebServiceInterfaceVersion

### CONFIRMED: WebServiceInterfaceVersion = `3`

**Evidence:** Disassembly of `AddWebServiceInterfaceVersionParam` in NeedleCommon at RVA 0x45B0:
```asm
45BA: LEA rax, [rip+0x3287]     ; "WebServiceInterfaceVersion" (RVA 0x7848)
45C1: MOV rbx, rcx              ; save request params ptr
45C4: LEA rdx, [rip+0x3831]     ; "%d" format string (RVA 0x7DFC)
45CF: XOR eax, eax              ; eax = 0
45D1: LEA rcx, [rsp+40]
45D6: LEA r8d, [rax+3]          ; r8d = 0 + 3 = 3  <-- THE VERSION VALUE
45DA: MOV [rsp+28], 0x1A        ; string length = 26 ("WebServiceInterfaceVersion")
```

The function:
1. Loads the parameter name "WebServiceInterfaceVersion"
2. Formats the integer `3` using `%d`
3. Adds it as an HTTP request parameter

**Every API request includes:** `WebServiceInterfaceVersion=3`

---

## TASK 3: All needle_* Config Variables (483 found in GameComponents)

### Critical Server/Network Variables
| Variable | Context |
|----------|---------|
| `needle_serviceApiVersion` | API version (default: `v1`) |
| `needle_publicServiceUrlOverride` | Override public API base URL |
| `needle_privateServiceUrlOverride` | Override private API base URL |
| `needle_publicip` | Server's public IP |
| `needle_UpdateFrequencyLowSeconds` | Low-priority server update interval |
| `needle_UpdateFrequencyHighSeconds` | High-priority server update interval |
| `needle_requestUpdateBase` | Base request update interval |
| `needle_requestUpdateIncreaseRate` | Rate increase for request polling |
| `needle_requestUpdateMax` | Max request update interval |
| `needle_squadPollBase` | Squad polling base interval |
| `needle_squadPollIncreaseRate` | Squad poll rate increase |
| `needle_squadPollMax` | Max squad poll interval |
| `needle_RegionLookupUrl` | Region lookup service URL |
| `needle_ServerName` | Server display name |
| `needle_MatchSize` | Match size setting |
| `needle_MatchType` | Match type setting |
| `needle_useMatchmaker` | Enable matchmaker |
| `needle_release` | Release flag |
| `needle_publishMatchStats` | Publish match statistics |
| `needle_unhealthyServerKickTime` | Unhealthy server kick timeout |
| `needle_unhealthyServerKillTimeAfterKickTime` | Kill timeout after kick |
| `needle_ResetServerOnNoConnections` | Reset server when empty |

### Match/Game Variables
| Variable | Context |
|----------|---------|
| `needle_MatchAutoStart` | Auto-start match |
| `needle_MatchBalanceTime` | Team balance time |
| `needle_MatchCountdownTime` | Countdown duration |
| `needle_MatchStartCountdown` | Start countdown |
| `needle_MatchMinPlayersPerTeamSmall` | Min players (small) |
| `needle_MatchMinPlayersPerTeamMedium` | Min players (medium) |
| `needle_MatchMinPlayersPerTeamLarge` | Min players (large) |
| `needle_MatchMaxLevelDifference` | Max level difference |
| `needle_MatchMaxPlayersDifference` | Max player count difference |
| `needle_MatchReadyTime` | Ready phase time |
| `needle_MatchFinishedRestartTime` | Restart time after match end |
| `needle_MatchTicketsNeededForCapitalShip` | Tickets for capital ship |
| `needle_MatchTimeBeforeRequestingCapitalShip` | Time before capital ship request |
| `needle_ConquestTicketRateMultiplier` | Ticket drain rate |
| `needle_ConquestTicketsStartBase` | Base starting tickets |
| `needle_ConquestTicketsStartPerSector` | Tickets per sector |
| `needle_ReconTicketsStartSmall` | Recon tickets (small match) |
| `needle_ReconTicketsStartMedium` | Recon tickets (medium match) |
| `needle_ReconTicketsStartLarge` | Recon tickets (large match) |
| `needle_UseTickets` | Enable ticket system |
| `needle_EnableTeamShuffle` | Enable team shuffling |

### Single Player / Debug Variables
| Variable | Context |
|----------|---------|
| `needle_IsSinglePlayer` | Single player mode flag |
| `needle_GodMode` | God mode |
| `needle_AiGodMode` | AI god mode |
| `needle_SkipToLobby` | Skip to lobby screen |
| `needle_SkipToMain` | Skip to main menu |
| `needle_StartRegion` | Starting region ID |
| `needle_CurrentRegionCode` | Current region code |

### Matchmaking Location Variables
| Variable | Context |
|----------|---------|
| `matchmaking_allow_crossplay` | Cross-platform play |
| `matchmaking_location_useast` | US East region |
| `matchmaking_location_uswest` | US West region |
| `matchmaking_location_europe` | Europe region |
| `matchmaking_location_asia` | Asia region |
| `matchmaking_location_oceania` | Oceania region |
| `matchmaking_location_southamerica` | South America region |

Full list: 483 `needle_*` variables found in GameComponentsNeedle_Steam_Release.dll + 3 in NeedleCommon.

---

## TASK 4: API Endpoint Paths

### Confirmed Service Classes and Their Roles

From source file path strings embedded in the binary:

| Source File | Service | Transport |
|-------------|---------|-----------|
| `Services\CNeedleAccountService.cpp` | Authentication | **Public** |
| `Services\CNeedleClientAccountDataService.cpp` | Account data (read/write) | **Public** |
| `Services\CNeedleClientLeaderboardsService.cpp` | Leaderboards | **Public** |
| `Services\CNeedleClientMessagesService.cpp` | Message of the Day | **Public** |
| `Services\CNeedleClientReportingService.cpp` | Bug/abuse reporting | **Public** |
| `Services\CNeedleClientServiceParent.cpp` | Base class (shared params) | N/A |
| `Services\CNeedleServerAccountDataService.cpp` | Server-side account data push | **Private** |
| `Services\CNeedleServerReservationService.cpp` | Server reservations | **Private** |
| `Services\CNeedleTicketValidator.cpp` | Ticket auth validation | **Private** |

### Call Site Analysis

28 total calls to URL construction functions found:
- **16 calls** to `GetPublicServicesUrlForPath` (client-facing)
- **12 calls** to `GetPrivateServicesUrlForPath` (server-facing, requires client cert)

### IMPORTANT: Paths Are Runtime-Constructed shared_string Objects

The endpoint path strings are NOT stored as literal string constants. They are `shared_string` global variables in the `.data` section that get initialized by C++ static constructors at program startup. This means the actual path values cannot be directly extracted from static string analysis.

**However**, based on the service class naming convention and the BPE engine pattern, the paths are almost certainly derived from the service names. The most likely mapping:

| Service | Likely Public Path | Likely Private Path | Evidence |
|---------|-------------------|---------------------|----------|
| CNeedleAccountService | `authenticate` | - | Auth flow strings, parameter names |
| CNeedleClientAccountDataService | `account_data` or `refresh_account_data` | - | RefreshAccountData, PushAccountDataChanges |
| CNeedleClientLeaderboardsService | `leaderboard` or `leaderboards` | - | LeaderboardType, TableOffset, RowCount params |
| CNeedleClientMessagesService | `messages` or `motd` | - | MessageType, DesiredLocale params |
| CNeedleClientReportingService | `reporting` or `report` | - | ReportParams, Body, Logs, SystemSpecs |
| CNeedleServerAccountDataService | - | `account_data` or `push_account_data` | Server push of account/rewards |
| CNeedleServerReservationService | - | `reservation` or `reservations` | ReservationId, Players, MatchSize |
| CNeedleTicketValidator | - | `ticket_auth` or `authenticate_ticket` | Ticket validation for connections |

Additional public endpoints observed from matchmaker class:
- `GameObjects\NeedleNetwork\CComponentNeedleNetworkClientMatchMaker.cpp` - has 3 calls to `GetPublicServicesUrlForPath`

### Matchmaker-specific Additional Paths (likely):
| Service | Likely Path | Evidence |
|---------|-------------|----------|
| Matchmaker search | `matchmaker` or `match_search` | CComponentNeedleNetworkClientMatchMaker |
| Capital ship data client | `capital_ship_data` | CNeedleClientCapitalShipDataService |
| Capital ship match status | `capital_ship_match_status` | ShowClientCapitalShipMatchStatusRequestResponse |
| Start run (contracts) | `start_run` | ShowStartRunRequest, StartRunParams |
| Delete contract | `delete_contract` | DeleteContractParams |

---

## TASK 5: Auth Request/Response Format

### Authentication Flow (from string analysis)

**Login states** (in order):
1. `"not authenticated"`
2. `"authenticating - looking up default region"`
3. `"authenticating - generate auth"`
4. `"authenticating - get session"`
5. `"authenticated"`

### Auth Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `PlatformCode` | string | Platform identifier (e.g., "Steam") |
| `PlatformAuth` | string | Steam authentication ticket (hex-encoded) |
| `ClientVersion` | string | Game build version |
| `Region` | int | Region code (uses `%i` format) |
| `EnvironmentId` | string | Environment identifier |
| `Locale` | string | Client locale |
| `WebServiceInterfaceVersion` | int | Always `3` |

### Auth Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `SessionId` | string | Session token for subsequent requests |
| (JSON body) | object | Full account data (parsed as JSON) |

### Auth Error Codes

| Error Code | When |
|-----------|------|
| `HTTP_AUTH_REQUEST_FAILED` | HTTP request failed |
| `ACCOUNT_SERVER_REQUEST_FAILED` | Server returned error |
| `ACCOUNT_PARSE_ERROR` | JSON parse failure |
| `ACCOUNT_SERVICE_JSON_PARSE_ERROR` | JSON structure invalid |
| `ACCOUNT_SERVICE_NO_GAME_MGR` | No game manager available |

### Shared Request Parameters (CNeedleClientServiceParent)

All client service requests go through `AddSharedParamsAndStartRequest` which adds:
- `SessionId` - from auth response
- `WebServiceInterfaceVersion` = `3`
- Possibly other shared params

If no auth manager is available, error code `NO_AUTH_MANAGER` is returned.

---

## TASK 5b: Server-Side Request Formats

### Server Reservation Service Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ReservationId` | string | Unique reservation ID |
| `RequestId` | string | Request identifier |
| `Players` | array | Player list |
| `PlayerCount` | int | Number of players |
| `RequestType` | string | Type of reservation request |
| `PartyId` | string | Party identifier |
| `ServerName` | string | Server display name |
| `PlayerLevels` | array | Player level data |
| `MatchSize` | int | Match size |
| `ProcessId` | string | Server process ID |
| `PublicIp` | string | Server public IP |
| `ServerPort` | int | Server port |
| `ScavengerCount` | int | Scavenger team count |
| `DrifterCount` | int | Drifter team count |
| `IsInLobby` | bool | Whether in lobby phase |
| `WantsCapitalShip` | bool | Capital ship requested |
| `CapitalShipCount` | int | Number of capital ships |
| `CompactReservations` | ? | Compact reservation format |

### Server Account Data Push Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `AccountAndPlayerDataCollection` | object | Full account + player data |
| `PlayerRewardsCollection` | object | Rewards earned |
| `FameTotal` | int | Total fame earned |
| `FameGuardians` | int | Fame from guardian kills |
| `FameUpgrades` | int | Fame from upgrades |
| `FameActions` | int | Fame from actions |
| `FamePlayers` | int | Fame from player kills |
| `FameCapitalActions` | int | Fame from capital ship |
| `PlayerDataCollection` | object | Player data to push |
| `RollEndOfRunRewards` | ? | End-of-run reward calculation |

### Ticket Validation (Connection Authentication)

Response fields:
| Field | Type | Description |
|-------|------|-------------|
| `OpaquePlatformId` | string | Platform-specific player ID |
| `DisplayName` | string | Player display name |

Error conditions:
- `TicketAuthIncompatibleVersion` - Client build mismatch
- Build comparison: `Incompatible build: %.*s, Expected: %.*s`

### Leaderboard Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ShipFilter` / `ShipFilterType` | int | Filter by ship type |
| `LeaderboardType` | string | Career, Conquest, or Tribe |
| `TableOffset` | int | Pagination offset |
| `RowCount` | int | Rows per page |
| `TimeFrameType` | string | Time frame filter |
| `OrderByColumnIndex` | int | Sort column |

Leaderboard time format strings: `LEADERBOARD_HOURS`, `LEADERBOARD_DAYS`, `LEADERBOARD_WEEKS`, `LEADERBOARD_MILLIONS`, `LEADERBOARD_THOUSANDS`, `LEADERBOARD_MINUTES`

### Messages (MOTD) Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `MessageType` | string | Message type (e.g., "MOTD") |
| `DesiredLocale` | string | Localization locale |
| `System` | string | System identifier |

### Reporting Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ReportType` | string | Type of report |
| `Body` | string | Report text |
| `Screenshot` | binary? | Screenshot data |
| `Platform` | string | Platform identifier |
| `Logs` | string | Game logs |
| `SystemSpecs` | string | System specifications |

### Account Data Service Sub-Operations

| Operation | Parameters | Description |
|-----------|-----------|-------------|
| Ship Augmentation | `AugmentId_*`, `ShipSystem` | Augment a ship system |
| Reconstruct Augment | `TypeId`, `SourceId`, `ConsumedPopulation`, `TypeBasedId`, `ExtraAugmentId` | Reconstruct/reroll augment |
| Rewards Request | (from PlayerRewardsCollection) | Claim rewards |
| Trophy Data | (trophy-related) | Get trophy progress |
| DLC Refresh | (DLC-related) | Refresh DLC ownership |
| Delete Contract | `DeleteContractParams` | Delete a contract |
| Start Run | `StartRunParams` | Start a contract run |

---

## Summary of Critical Values for First Test

| Setting | Value | Confidence |
|---------|-------|------------|
| Base URL | `https://deadstar.rel.armature.com/` | CONFIRMED |
| API Version | `v1` | CONFIRMED |
| Public URL Format | `{base}api/public/v1/{path}` | CONFIRMED |
| Private URL Format | `{base}api/private/v1/{path}` | CONFIRMED |
| WebServiceInterfaceVersion | `3` | CONFIRMED (disassembly proof) |
| Auth path | `authenticate` (inferred) | HIGH CONFIDENCE |
| Auth params | PlatformCode, PlatformAuth, ClientVersion, Region, EnvironmentId, Locale | CONFIRMED |
| Auth response | JSON with SessionId field | CONFIRMED |
| Session param | All subsequent requests include SessionId | CONFIRMED |

### What We Still Don't Know
1. **Exact endpoint path strings** - These are `shared_string` objects initialized at runtime, not string literals. Would need dynamic analysis (debugger/network capture) to confirm exact paths.
2. **needle_* config var default VALUES** - We have all 483+ variable names but most default values are set in code (not as adjacent strings). The `v1` default for `needle_serviceApiVersion` was an exception because it was stored as a string literal nearby.
3. **Exact JSON structure** of auth responses and account data format.
4. **Private API certificate/key format** - The private endpoints require mutual TLS with client certificates (the binary contains certificate PEM data for `deadstar.rel.armature.com`).

### SSL Certificate Found
The binary contains an embedded SSL certificate for `deadstar.rel.armature.com`:
- Issuer: Armature, Austin, Texas, US
- Valid: 2015-09-04 to 2018-06-24
- Used for: Public API HTTPS verification
- Private API also uses client certificates (GetPrivateServicesClientCertificate, GetPrivateServicesClientKey)
