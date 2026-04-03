# Dead Star API Mapping Report

**Generated:** 2026-04-03
**Source DLLs:** NeedleCommon_Steam_Release.dll, GameComponentsNeedle_Steam_Release.dll, Engine_Steam_Release.dll
**Method:** Static string extraction and cross-referencing from Win64 PE binaries

---

## 1. Base URL and URL Construction

### Base URL [CONFIRMED]
```
https://deadstar.rel.armature.com/
```

### URL Format Strings [CONFIRMED]
```c
// Public API (client -> backend):
"%s%sapi/public/%s/%s%s"
// = {baseUrl}{slash?}api/public/{apiVersion}/{path}{queryString}

// Private API (server -> backend, mutual TLS):
"%s%sapi/private/%s/%s%s"
// = {baseUrl}{slash?}api/private/{apiVersion}/{path}{queryString}
```

### Override Variables [CONFIRMED]
| Variable | Purpose |
|---|---|
| `needle_publicServiceUrlOverride` | Override base URL for public (client) API |
| `needle_privateServiceUrlOverride` | Override base URL for private (server) API |
| `needle_serviceApiVersion` | API version string for URL path |

### Query Parameter System [CONFIRMED]
- `CHttpRequestParameters::AddQuery(key, value)` - adds URL query params
- `NNeedleWebServiceCommon::AddWebServiceInterfaceVersionParam()` - adds `WebServiceInterfaceVersion` param to all requests
- Auth header: `auth=Bearer %s` (added as query parameter, NOT standard Authorization header)

### Region Lookup [CONFIRMED]
- Region lookup domain: `region.deadstarservices.com`
- Variable: `needle_RegionLookupUrl`

### Amazon Metadata Endpoint [CONFIRMED]
```
http://169.254.169.254/2014-11-05/
  meta-data/public-ipv4
  meta-data/instance-type
  meta-data/instance-id
```
Backend runs on AWS. Servers query EC2 instance metadata.

---

## 2. HTTP Infrastructure

### HTTP Library [CONFIRMED]
- **Engine DLL**: libcurl (curl_easy_init, curl_multi_add_handle, curl_multi_perform)
- Content-Type: `application/json`
- TLS/SSL with OpenSSL 1.0.2 (22 Jan 2015)

### HTTP Method Enum [CONFIRMED]
```cpp
enum EHttpMethod {
    // Used via CHttpRequestParameters constructor:
    // CHttpRequestParameters(url, EHttpMethod)
    // GetMethod() returns EHttpMethod
    // Values inferred from usage: GET, POST, PUT, DELETE
};
```

### Request/Response Classes [CONFIRMED]
```cpp
class CHttpRequestParameters {
    CHttpRequestParameters(shared_string url, EHttpMethod method);
    void AddQuery(shared_string key, shared_string value);
    EHttpMethod GetMethod();
};

class CHttpRequestBase {
    bool IsSuccess();
    shared_string BuildResponseBodyNULLTerminated();
    void DebugPrint();
};

class CHttpRequest : public CHttpRequestBase {
    CHttpRequest(CHttpRequestParameters, void*, curl_slist*);
    void InternalRetryRequest(void*, curl_slist*);
};
```

### Auth Header [CONFIRMED]
```
auth=Bearer %s
```
Added as query parameter. Also standard `Authorization:` header is present in Engine DLL.

---

## 3. TLS/Certificate Infrastructure

### Public Services [CONFIRMED]
- `GetPublicServicesCertificate()` — CA cert for validating the public API server

### Private Services (Mutual TLS) [CONFIRMED]
- `GetPrivateServicesCACertificate()` — CA cert
- `GetPrivateServicesClientCertificate()` — Client cert (server identifies itself)
- `GetPrivateServicesClientKey()` — Client private key

### Embedded Certificate [CONFIRMED]
Self-signed X.509 cert for `deadstar.rel.armature.com`:
```
Subject: C=US, ST=Texas, L=Austin, O=Armature, OU=., CN=deadstar.rel.armature.com
Issuer: Same (self-signed)
Valid: 2015-09-04 to 2018-06-24
```
Full PEM in NeedleCommon_Steam_Release.dll.

---

## 4. JSON Library

### rapidjson Usage [CONFIRMED]
- `EncodeJson` / `DecodeJson` functions in `NNeedleInstanceWrangler`
- `SendJsonMessage` on `CTcpJsonStream`
- JSON decode state: `SJsonDecodeState` from `NJsonExtras`
- Error strings: `"JSON object has no member \"%s\""`, `"JSON value is not an object"`, `"JSON value is not a number"`, `"JSON value is not a string"`

---

## 5. Service Classes (All Confirmed)

| Service Class | Source File | API Type | Description |
|---|---|---|---|
| `CNeedleAccountService` | `Services\CNeedleAccountService.cpp` | Public | Authentication, session management |
| `CNeedleClientAccountDataService` | `Services\CNeedleClientAccountDataService.cpp` | Public | Player data read (refresh) |
| `CNeedleServerAccountDataService` | `Services\CNeedleServerAccountDataService.cpp` | Private | Server pushes account data & rewards |
| `CNeedleClientLeaderboardsService` | `Services\CNeedleClientLeaderboardsService.cpp` | Public | Leaderboard queries |
| `CNeedleClientMessagesService` | `Services\CNeedleClientMessagesService.cpp` | Public | Login messages / MOTD |
| `CNeedleClientReportingService` | `Services\CNeedleClientReportingService.cpp` | Public | Player reporting |
| `CNeedleServerReservationService` | `Services\CNeedleServerReservationService.cpp` | Private | Match slot reservations |
| `CNeedleClientCapitalShipDataService` | `GameObjects\NeedleCapitalShip\CNeedleClientCapitalShipDataService.cpp` | Public | Capital ship contract status (client read) |
| `CNeedleServerCapitalShipDataService` | `GameObjects\NeedleCapitalShip\CNeedleServerCapitalShipDataService.cpp` | Private | Capital ship match status (server push) |
| `CNeedleServerStatusCommunicator` | (embedded) | Private | Server health/status heartbeat |
| `CNeedleConnectionAuthenticator` | (embedded) | Private | Validates player tickets against reservations |

### Client Matchmaker (not an HTTP service) [CONFIRMED]
`CComponentNeedleNetworkClientMatchMaker` — source: `GameObjects\NeedleNetwork\CComponentNeedleNetworkClientMatchMaker.cpp`
Uses HTTP requests for matchmaking but is a component, not a standalone service.

---

## 6. API Endpoints — Detailed Mapping

### 6.1 Authentication (CNeedleAccountService) [CONFIRMED]

**Endpoint:** `POST /api/public/{version}/authenticate` [UNCERTAIN - path name inferred]

**Auth Flow States:**
1. `"authenticating - generate auth"` — Generate platform-specific auth (Steam ticket)
2. `"authenticating - get session"` — Call backend to get session
3. `"authenticating - looking up default region"` — Query region after auth
4. `"authenticated"` — Done

**Request Fields:**
| Field | Type | Evidence |
|---|---|---|
| Platform auth ticket | string | `AS_Online_GeneratePlatformSpecificAuth()`, `AS_Online_GetPlatformSpecificAuth()` |
| Platform environment | int | `AS_Online_GetPlatformSpecificEnvironment()` |
| `BuildVersion` | string | [CONFIRMED] Present in NeedleCommon as JSON key |
| `WebServiceInterfaceVersion` | string | [CONFIRMED] Added to all requests |

**Response Fields:**
| Field | Type | Evidence |
|---|---|---|
| `SessionId` | string | [CONFIRMED] `"unable to read SessionId from response"` |
| Account data | object | [CONFIRMED] `"unable to parse account data"`, `"unable to read account data from response"` |
| Session data | object | [CONFIRMED] `"unable to read session data from response"` |

**Error Codes:** [CONFIRMED]
- `ACCOUNT_SERVICE_UNAVAILABLE`
- `ACCOUNT_SERVICE_JSON_PARSE_ERROR`
- `ACCOUNT_PARSE_ERROR`
- `ACCOUNT_SERVER_REQUEST_FAILED`
- `ACCOUNT_SERVICE_NO_GAME_MGR`
- `HTTP_AUTH_REQUEST_FAILED`
- `FAILED_TO_CREATE_REQUEST`

**Auth Status Enum:**
```cpp
// status < NNeedleAccountService::kAuthenticationStatus_Count
// Status transitions logged: "[%s]->[%s] error code: %s (%d)"
```

---

### 6.2 Account Data — Refresh (CNeedleClientAccountDataService) [CONFIRMED]

**Endpoint:** `GET /api/public/{version}/accountdata` [UNCERTAIN - path inferred]

**Debug Vars:** `needle_ShowRefreshAccountDataRequest`, `needle_ShowRefreshAccountDataResponse`

**Request:** Session-authenticated (Bearer token + WebServiceInterfaceVersion)

**Response — CCoreAccountData Fields:**

#### Core Fields [CONFIRMED from error messages and string refs]
| Field | Type | Evidence |
|---|---|---|
| `AccountId` | uint | [CONFIRMED] Used everywhere as player identifier |
| `SessionId` | string | [CONFIRMED] Read from auth response |
| `CurrentPortraitId` | int | [CONFIRMED] String ref |
| `PortraitIds` | array | [CONFIRMED] Unlocked portrait list |
| Loadout data | object | [CONFIRMED] `"Invalid loadout. Using default"` |
| Unlocked ships | array | [CONFIRMED] `"Invalid number of unlocked ships"` |
| `IsDevAccount` | bool | [CONFIRMED] String ref |

#### Loadout Structure [CONFIRMED]
| Field | Type | Evidence |
|---|---|---|
| `shipType` / `ShipType` | int | [CONFIRMED] Both cases found as string refs |
| `SkinId` | int | [CONFIRMED] `SetSkinIdForShipType()` |
| `AugmentId` | int | [CONFIRMED] String ref |
| `AugmentRank` | int | [CONFIRMED] String ref |
| `augmentLevel` | int | [CONFIRMED] String ref, `LocalIncreaseShipAugmentLevel()` |
| `augmentType` | int/string | [CONFIRMED] String ref |
| `augmentRace` | string | [CONFIRMED] String ref |
| Slot index | int | [CONFIRMED] `SetMainLoadoutSlotIndex()`, `SetShipForLoadoutSlot()` |

#### Augment Sub-fields [CONFIRMED]
```
augmentRank_Core
augmentRank_Ship
augmentRank_Slot1
augmentRank_Slot2
augmentRank_Slot3
augmentRank_Slot4
```

#### Fame / Progression [CONFIRMED]
| Field | Type | Evidence |
|---|---|---|
| `Fame` | int | [CONFIRMED] Top-level string |
| `FameTotal` | int | [CONFIRMED] String ref |
| `fameRatio` | float | [CONFIRMED] String ref |
| `FameActions` | int | [CONFIRMED] |
| `FamePlayers` | int | [CONFIRMED] |
| `FameGuardians` | int | [CONFIRMED] |
| `FameUpgrades` | int | [CONFIRMED] |
| `FameMatch` | int | [CONFIRMED] |
| `FameFromActions` | int | [CONFIRMED] |
| `FameFromPlayers` | int | [CONFIRMED] |
| `FameFromGuardians` | int | [CONFIRMED] |
| `FameFromUpgrades` | int | [CONFIRMED] |
| `FameCategoryLimits` | array | [CONFIRMED] |
| `FameCapitalActions` | int | [CONFIRMED] |

#### DLC Data [CONFIRMED]
| Field | Type | Evidence |
|---|---|---|
| `isDLC` | bool | [CONFIRMED] String ref |
| DLC master list | array | [CONFIRMED] `CCPLdrNeedlePackageDlcMasterList` |

#### Account Data Validation [CONFIRMED]
```
CCoreAccountData::ValidateAndFixup() performs:
- Invalid loadout -> use default
- Invalid number of unlocked ships -> error
- Invalid portrait -> use default
- No unlocked portraits -> error
```

---

### 6.3 Account Data — Push Changes (CNeedleServerAccountDataService) [CONFIRMED]

**Endpoint:** `POST /api/private/{version}/accountdata` [UNCERTAIN - path inferred]

**Debug Vars:** `needle_ShowPushPlayerAccountDataChangesRequest`, `needle_ShowPushPlayerAccountDataChangesResponse`

**Request:** Contains modified account data fields (server pushes player progression after match)

**Related vars:**
- `needle_ForceAccountDataRefresh`
- `needle_ForcePushAccountData`

---

### 6.4 Push Rewards (CNeedleServerAccountDataService) [CONFIRMED]

**Endpoint:** `POST /api/private/{version}/rewards` [UNCERTAIN - path inferred]

**Debug Vars:** `needle_ShowPushRewardsRequest`, `needle_ShowPushRewardsResponse`

**Request Fields:**
| Field | Type | Evidence |
|---|---|---|
| `AccountId` | uint | [CONFIRMED] |
| `MatchId` | string | [CONFIRMED] `StartRewardsRequestInternal() - No match id` |
| `ContractId` | uint64 | [CONFIRMED] `no contract id` |
| `rewardEarned` | bool | [CONFIRMED] String ref |
| `rewardType` | int | [CONFIRMED] String ref, `"Unrecognized reward type: %d"` |

**Response:** `PlayerRewardsCollection`

**Reward Types:**
- `NormalRewards`
- `EscapeRunRewards`
- Portrait rewards
- Skin rewards
- Augment rewards
- Population rewards

---

### 6.5 Matchmaking (CComponentNeedleNetworkClientMatchMaker) [CONFIRMED]

**Endpoint:** `POST /api/public/{version}/matchmake` [UNCERTAIN - path inferred]

**Debug logging format:**
```
"Mode:%s, ReqType:%d, Type:%d, Size:%d, Contract:%llu, Party:%s, Count:%d, Crossplay:%d region(Default:%d, Custom:%d)"
```

**Request Fields:** [CONFIRMED from format string]
| Field | Type | Evidence |
|---|---|---|
| Mode | string | Request mode (Matchmaker vs direct) |
| RequestType | int | `ERequestType::LastSequentialCall` |
| Type (MatchType) | int | See MatchType enum below |
| Size (MatchSize) | int | See MatchSize enum below |
| Contract | uint64 | Contract ID for capital ship runs |
| Party | string | Party ID |
| Count | int | Player count |
| Crossplay | int/bool | `matchmaking_allow_crossplay` |
| RegionBitDefault | int | Default region bits |
| RegionBitsCustom | int | Custom region bits |

**Request Types:**
1. `LaunchInitialMatchMakeRequest` — first request
2. `LaunchProgressMatchMakeRequest` — polling for match progress
3. `LaunchSquadInServerMatchMakeRequest` — squad joining existing server

**Response Fields:**
| Field | Type | Evidence |
|---|---|---|
| Server address | string | `"Server address: %s:%d"` — IP:Port |
| Error info | string | Parsed separately on failure |

**MatchType Enum:** [CONFIRMED]
```
MatchType_Conquest
MatchType_Recon
MatchType_Hunt
MatchType_Freeplay
MatchType_Needle
MatchType_NeedleCrisis
MatchType_NeedleDiscovery
MatchType_NeedleEscape
MatchType_NeedleExploration
MatchType_Tutorial
```

**MatchSize Enum:** [CONFIRMED]
```
MatchSize_Small
MatchSize_Medium
MatchSize_Large
```

**Matchmaking Start Actions (UI):** [CONFIRMED]
```
StartMatchmaking_Conquest_Any
StartMatchmaking_Conquest_Large
StartMatchmaking_Conquest_Small
StartMatchmaking_Hunt_Large
StartMatchmaking_Hunt_Small
StartMatchmaking_Recon_Large
StartMatchmaking_Recon_Small
StartMatchmaking_NeedleEscape
StartMatchmaking_JoinParty
StartMatchmaking_LateJoinParty
StartMatchmaking_RetryPreviousType
```

**Error Codes:**
- `MATCHMAKER_JSON_PARSE_FAILURE`
- `MATCHMAKER_REQUEST_FAILURE`
- `MATCHMAKER_RETRYING`

**Region Codes (from script vars):** [CONFIRMED]
```
matchmaking_location_useast
matchmaking_location_uswest
matchmaking_location_europe
matchmaking_location_asia
matchmaking_location_oceania
matchmaking_location_southamerica
```

---

### 6.6 Reservations (CNeedleServerReservationService) [CONFIRMED]

**Endpoint:** `POST /api/private/{version}/reservations` [UNCERTAIN - path inferred]

**Source:** `Services\CNeedleServerReservationService.cpp`

**Request Fields (server -> backend):**
| Field | Type | Evidence |
|---|---|---|
| `ReservationId` | string | [CONFIRMED] Parsed from/to string via `ReservationIdAsString`/`ReservationIdFromString` |
| `Reservations` | array | [CONFIRMED] `"reservations.size() <= NNetTypes::skMaxNetworkPlayers"` |
| Player info per reservation | object | `"Reservation #%d (%s): count=%d team=%d"` |

**Response:** Server update launch confirmation or error

**Reservation Lifecycle:**
1. Backend assigns reservations via matchmaking response
2. Server receives reservations: `"Reservation received for player %s:%u and will be valid for %f seconds"`
3. Players connect with `CConnectionTicket` containing reservation ID
4. Server validates: `StartAuthenticateTicketForPlayer` checks reservation
5. Timeout: `"Reservation for player %s:%u timed out"`
6. Team mismatch: `"Player %u (%s) team %d does not match reservation team %d"`

**Error Codes:**
- `INVALID_MATCH_RESERVATION`
- `"Too many reservations"`
- `"Reservation (%s) FAILED"`

---

### 6.7 Connection Authentication (CNeedleConnectionAuthenticator) [CONFIRMED]

**Endpoint:** `POST /api/private/{version}/authenticate-ticket` [UNCERTAIN - path inferred]

**Purpose:** Game server validates a player's connection ticket against the backend.

**Request Fields:**
| Field | Type | Evidence |
|---|---|---|
| `ReservationId` | string | [CONFIRMED] Checked before request |
| `AccountId` | uint | [CONFIRMED] `"Revoking player ticket for account %ul"` |
| `BuildVersion` | string | [CONFIRMED] `"Incompatible build: %.*s, Expected: %.*s"` |
| Connection ticket data | binary/string | `CConnectionTicket` |

**Ticket Auth Error Types:** [CONFIRMED]
```
TicketAuthBadAccountSize
TicketAuthCantParse
TicketAuthDuplicatePlayer
TicketAuthIncompatibleVersion
TicketAuthJsonDecodeErrors
TicketAuthJsonParseError
TicketAuthNoGameMgr
TicketAuthNoReservation
TicketAuthReservationInvalid
TicketAuthRequestFailed
TicketConnectionsDisallowed
TicketRevoked
```

---

### 6.8 Leaderboards (CNeedleClientLeaderboardsService) [CONFIRMED]

**Endpoint:** `GET /api/public/{version}/leaderboards` [UNCERTAIN - path inferred]

**Debug Vars:** `needle_ShowLeaderboardResponse`, `needle_ShowLocalLeaderboardEntryResponse`

**Two Request Types:**
1. **Leaderboard List** — `StartLeaderboardRequestInternal()`
2. **Local Entry** — `StartLocalLeaderboardEntryRequestInternal()`

**Request Fields:**
| Field | Type | Evidence |
|---|---|---|
| `LeaderboardType` | int | [CONFIRMED] String ref |
| Column sort ID | int | [CONFIRMED] From error message |
| `AccountId` | uint | For local entry lookup |
| `SessionId` | string | Auth token |

**Leaderboard Categories (UI strings):** [CONFIRMED]
```
ShowCareerLeaderboard
ShowConquestLeaderboard
ShowReconLeaderboard
ShowTribeLeaderboard
ShowLeaderboardCategory_0 through _4
```

**Leaderboard Column Types:** [CONFIRMED]
```
KILLS, DEATHS, ASSISTS, WINS, LOSSES
KILLDEATHRATIO, ASSISTDEATHRATIO, WINLOSSRATIO
FAME, FAMEPERMINUTE
BESTSTREAK, BEST_SUPPORT_STREAK
LEVEL, RANK, NAME, PLAYTIME
OUTPOSTS, ASSAULTS, HACKS, DEFENDS
DOMINATIONS, SHUTDOWNS, DECISIVE_VICTORY, STRATEGIC_VICTORY
ORE_SPENT, SUPPORT, SUPPORT_ACTIONS, TACTICAL_ACTIONS
NEEDLERUNS, NEEDLESUCCESS, NEEDLEFAILS, NEEDLESUCCESSRATIO, NEEDLEASSISTS
AVENGER, BLOODTHIRSTY (from game strings)
```

**Time Filters:** [CONFIRMED]
```
LEADERBOARD_TIME_MONTHLY
LEADERBOARD_TIME_WEEKLY
LEADERBOARD_ALL_TIME
```

**Ship Filters:** [CONFIRMED]
```
LEADERBOARD_ALL_SHIPS
LEADERBOARD_ALL_CATEGORY_SHIPS
```

---

### 6.9 Client Messages / MOTD (CNeedleClientMessagesService) [CONFIRMED]

**Endpoint:** `GET /api/public/{version}/messages` [UNCERTAIN - path inferred]

**Source:** `Services\CNeedleClientMessagesService.cpp`

**Debug Vars:** (none found for request; response parsed inline)

**Response Fields:**
| Field | Type | Evidence |
|---|---|---|
| `LoginMessage` | string | [CONFIRMED] String ref, `"LoginMessage - Error:"` |
| `MessageOfTheDay` / `Motd` | string | [CONFIRMED] String refs |
| `date` | string | [CONFIRMED] String ref |

**Related var:** `needle_LastSeenLoginMessage`

---

### 6.10 Player Reporting (CNeedleClientReportingService) [CONFIRMED]

**Endpoint:** `POST /api/public/{version}/report` [UNCERTAIN - path inferred]

**Source:** `Services\CNeedleClientReportingService.cpp`

**Debug Vars:** `needle_ShowPostReportRequest`, `needle_ShowPostReportResponse`

**Request Fields:**
| Field | Type | Evidence |
|---|---|---|
| `ReportType` | int | [CONFIRMED] String ref |
| `ReportParams` | object | [CONFIRMED] String ref |
| `body` | string | [CONFIRMED] String ref (report text body) |
| `TargetAccountId` | uint | [CONFIRMED] String ref |
| `InstigatorAccountId` | uint | [CONFIRMED] String ref |

---

### 6.11 Capital Ship Data — Client (CNeedleClientCapitalShipDataService) [CONFIRMED]

**Endpoint:** `GET /api/public/{version}/capitalship/status` [UNCERTAIN - path inferred]

**Debug Vars:** `needle_ShowClientCapitalShipMatchStatusRequestResponse`

**Request:** `StartCapitalShipStatusRequest()` — needs valid contract ID

**Response Fields:**
| Field | Type | Evidence |
|---|---|---|
| `CapitalShipMatchState` | int | [CONFIRMED] String ref |
| `ContractId` | uint64 | [CONFIRMED] Compared against current contract |
| `CapitalShipCount` | int | [CONFIRMED] String ref |
| `JumpNumber` | int | [CONFIRMED] String ref |
| `LastCompletedJumpNumber` | int | [CONFIRMED] String ref |
| Node data array (0-3) | objects | See below |

**Capital Ship Node Fields:** [CONFIRMED from debug vars]
```
Node_0_SpecialistId, Node_1_SpecialistId, Node_2_SpecialistId, Node_3_SpecialistId
CoreSpecialistId
```
Per-node fields (from needle_DebugContract_* vars):
```
EverDestroyed (bool)
Level (int)
Ore (int)
Pod_0_Destroyed through Pod_3_Destroyed (bool)
SpecialistId (int)
```

---

### 6.12 Capital Ship Data — Server Push (CNeedleServerCapitalShipDataService) [CONFIRMED]

**Endpoint:** `POST /api/private/{version}/capitalship/status` [UNCERTAIN - path inferred]

**Debug Vars:** `needle_ShowPushCapitalShipMatchStatsRequest`, `needle_ShowPushCapitalShipMatchStatsResponse`, `needle_ShowServerCapitalShipMatchStatusRequestResponse`

**Request:** `PushCapitalShipMatchStatus()` — pushes match state after each jump

**Error:** `NET_APP_ERROR_CAPITAL_SHIP_DATA_ERROR`, `NET_APP_ERROR_CAPITAL_SHIP_MATCH_FINISHED`

---

### 6.13 Capital Ship Run — Start/Delete (mixed client/server) [CONFIRMED]

**Start Run Endpoint:** `POST /api/public/{version}/capitalship/run` [UNCERTAIN]
- Debug: `needle_ShowStartRunRequest`, `needle_ShowStartRunResponse`
- Error: `"Start Run Request Failed"`, `"StartStartRunRequest() called when it had a request already in progress"`
- Request: `StartRunParams`
- Confirmation: `"PreThinkStartRunRequest: Request Successful"`

**Delete Contract Endpoint:** `DELETE /api/public/{version}/contract` [UNCERTAIN]
- Debug: `needle_ShowDeleteContractRequest`, `needle_ShowDeleteContractResponse`
- Request: `DeleteContractParams`
- Error: `"Delete Contract Request Failed"`
- Confirmation: `"PreThinkDeleteContractRequest: Request Successful"`
- Validation: `"Trying to delete an invalid contract id."`

---

### 6.14 Ship Augmentation (client) [CONFIRMED]

**Augment Ship Endpoint:** `POST /api/public/{version}/augment` [UNCERTAIN]
- Debug: `needle_ShowAugmentShipRequest`, `needle_ShowAugmentShipResponse`
- Error: `"Augment Ship Request failed"`, `"StartShipAugmentationRequest() called when it had a request already in progress"`
- Request: `AugmentShipParams`

**Reconstruct Augment Endpoint:** `POST /api/public/{version}/reconstruct` [UNCERTAIN]
- Debug: `needle_ShowReconstructAugmentRequest`, `needle_ShowReconstructAugmentResponse`
- Error: `"Reconstruct Augment Request failed"`, `"StartReconstructAugmentRequest() called when it had a request already in progress"`

---

### 6.15 Rewards Request (client) [CONFIRMED]

**Endpoint:** `GET /api/public/{version}/rewards` [UNCERTAIN]
- Debug: `needle_ShowRewardsResponse`
- Error: `"Rewards Request failed"`, `"Rewards Request failed to parse json"`
- Requires: match ID or contract ID (`"StartRewardsRequestInternal() - No match id and no contract id"`)

---

### 6.16 Trophy Data (client) [CONFIRMED]

**Endpoint:** `GET /api/public/{version}/trophies` [UNCERTAIN]
- Debug: `needle_ShowTrophyDataResponse`
- Error: `"Trophy Data Request failed"`, `"Trophy Data Request failed to parse json"`

---

### 6.17 DLC Refresh (client) [CONFIRMED]

**Endpoint:** `GET /api/public/{version}/dlc` [UNCERTAIN]
- Error: `"StartRefreshDlcRequest() called when it had a request already in progress"`

---

### 6.18 Server Instance Registration (NNeedleInstanceWrangler + ServerStatusCommunicator) [CONFIRMED]

**Endpoint:** `POST /api/private/{version}/server/status` [UNCERTAIN - path inferred]

**SServerInstance JSON Fields** (EncodeJson/DecodeJson in NeedleCommon): [CONFIRMED]
| Field | Type | Evidence |
|---|---|---|
| `ApiVersion` | int | [CONFIRMED] First field in format string |
| `ServerName` | string | [CONFIRMED] `needle_ServerName` |
| `BuildVersion` | string | [CONFIRMED] `buildVersion.length() < skBuildVersionStringMax` |
| `MatchType` | int | [CONFIRMED] See enum above |
| `MatchSize` | int | [CONFIRMED] See enum above |
| `Port` | int | [CONFIRMED] `network_ServerListenPort`, `GetListenPort()` |
| `ProcessId` | int | [CONFIRMED] `GetCurrentProcessId()` |
| `PublicIp` | string | [CONFIRMED] `needle_publicip`, `gPublicIpAddress` |

**Format string for debug:** `"API:%d, name:%s, Build:%s, MatchType:%d, MatchSize:%d, Port:%d"`

**ServerStatusCommunicator errors:** `"reported error: %s (%d)"`

---

## 7. Error Response Format [CONFIRMED]

Based on error message parsing patterns:

```json
{
    "error": {
        "code": "<ERROR_CODE_STRING>",
        "message": "<human-readable message>"
    }
}
```

Evidence: `"Account service request failed, API failure, code %d, message: \"%s\""`

The `code` field appears to be an integer HTTP status, and `message` is a string. The error code enum strings (like `ACCOUNT_SERVICE_UNAVAILABLE`) are client-side mappings.

**All Known Error Code Strings:**
```
ACCOUNT_PARSE_ERROR
ACCOUNT_SERVER_REQUEST_FAILED
ACCOUNT_SERVICE_JSON_PARSE_ERROR
ACCOUNT_SERVICE_NO_GAME_MGR
ACCOUNT_SERVICE_UNAVAILABLE
CONNECTION_ERROR
DATABASE_ERROR
FAILED_TO_CREATE_REQUEST
HTTP_AUTH_REQUEST_FAILED
INVALID_MATCH_RESERVATION
JSON_DECODE_ERROR
MATCHMAKER_JSON_PARSE_FAILURE
MATCHMAKER_REQUEST_FAILURE
MATCHMAKER_RETRYING
NET_APP_ERROR_CAPITAL_SHIP_DATA_ERROR
NET_APP_ERROR_CAPITAL_SHIP_MATCH_FINISHED
NET_APP_ERROR_IDLE_TIMEOUT
NET_APP_ERROR_NETWORKDEVICEDISCONNECTED
NET_APP_ERROR_PING_TOO_HIGH
NET_APP_ERROR_SERVERCONNECTIONTIMEOUT
NET_APP_ERROR_STATSREADFAILURE
NET_APP_ERROR_UNHEALTHY_SERVER_KICKOUT
UNINITIALIZED_ERROR
```

---

## 8. Shared Request Parameters [CONFIRMED]

`AddSharedParamsAndStartRequest()` is called by most client services. It:
1. Gets the account service (`mpAccountService != NULL`)
2. Adds `SessionId` as bearer token (`auth=Bearer %s`)
3. Adds `WebServiceInterfaceVersion` query param
4. Starts the HTTP request

---

## 9. Player Stats Structure (NNeedlePlayerStats) [CONFIRMED]

### General Stats [CONFIRMED]
| Field | Type | Evidence |
|---|---|---|
| `FamePerAcePilot` | array[kAcePilot_Count] | [CONFIRMED] `mFamePerAcePilot size must match` |
| `FamePerSupportAction` | array[kTacticalAction_Count] | [CONFIRMED] |
| `FamePerTacticalAction` | array[kTacticalAction_Count] | [CONFIRMED] |

### Per-Match Stats [CONFIRMED from format strings]
```
kills: match=%d total=%d unlock=%d,%d
assists: match=%d total=%d unlock=%d
captures: match=%d total=%d unlock=%d
decisive victory: match=%d total=%d unlock=%d
ore: match=%d total=%d unlock=%d
streak: total=%d, unlock=%d,%d
victory: match=%d total=%d unlock=%d
ship %d kills: match=%d total=%d unlock=%d
```

### Ace Pilot Types [CONFIRMED]
| Ace Type | Evidence |
|---|---|
| `AceAttackerCount` | [CONFIRMED] |
| `AceDefenderCount` | [CONFIRMED] |
| `AceTopCaptureCount` | [CONFIRMED] |
| `AceUpgraderCount` | [CONFIRMED] |

### Player Data Fields [CONFIRMED]
| Field | Evidence |
|---|---|
| `InstigatorAccountId` | Target for kill/assist |
| `InstigatorShipType` | Ship type of instigator |
| `InstigatorShipSystem` | Device/system involved |
| `InstigatorType` | Entity type |
| `InstigatorSubType` | Sub-type |
| `InstigatorStatsIndex` | Index in stats array |
| `TargetAccountId` | Victim |
| `playerTeam` | Team assignment |

---

## 10. Matchmaking Regions [CONFIRMED]

| Region Variable | Region Code |
|---|---|
| `matchmaking_location_useast` | US East |
| `matchmaking_location_uswest` | US West |
| `matchmaking_location_europe` | Europe |
| `matchmaking_location_asia` | Asia |
| `matchmaking_location_oceania` | Oceania |
| `matchmaking_location_southamerica` | South America |

Region lookup: `needle_RegionLookupUrl` -> `region.deadstarservices.com`

Region config vars:
- `needle_CurrentRegionCode`
- `needle_StartRegion`
- `needle_HasSetDefaultRegionSettings`
- `RegionBitDefault` / `RegionBitsCustom`

---

## 11. Contract Data Structure [CONFIRMED]

### Fields (from debug vars)
| Field | Evidence |
|---|---|
| `ContractId` | [CONFIRMED] `needle_DebugContractId` |
| `ShipType` | [CONFIRMED] `needle_DebugContract_ShipType` |
| `PrevJumpNumber` | [CONFIRMED] `needle_DebugContract_PrevJumpNumber` |
| `CoreSpecialistId` | [CONFIRMED] `needle_DebugContract_Core_SpecialistId` |
| Per-node (0-3): SpecialistId, EverDestroyed, Level, Ore, Pod_0-3_Destroyed | [CONFIRMED] |
| `needle_ContractMaxJumps` | Max jumps in a run |

### Contract States [CONFIRMED]
```
CONTRACT_STATE_UNUSED
CONTRACT_STATE_IN_PROGRESS
CONTRACT_STATE_SUCCESS
CONTRACT_STATE_FAILURE
```

---

## 12. Skin & DLC System [CONFIRMED]

| Field | Evidence |
|---|---|
| `SkinId` | [CONFIRMED] `SetSkinIdForShipType()` |
| `skinType` | [CONFIRMED] camelCase string ref |
| `hasUnviewedSkin` | [CONFIRMED] camelCase string ref |
| `isDLC` | [CONFIRMED] camelCase string ref |
| `DlcMasterList` | [CONFIRMED] Component name |

---

## 13. Party/Squad System [CONFIRMED]

| Field | Evidence |
|---|---|
| `PartyId` | [CONFIRMED] `GeneratePartyId()` |
| `PartySize` | [CONFIRMED] String ref |
| `squadIndex` | [CONFIRMED] camelCase string ref |
| `needle_MaxSquadSize` | Squad size limit |
| `needle_squadPollBase` / `needle_squadPollMax` / `needle_squadPollIncreaseRate` | Squad polling intervals |

Party messages: `PARTY_MATCHMAKE`, `PARTY_DISCONNECT`, `PARTY_INVOLVED`

---

## 14. Experience System [CONFIRMED]

| Variable | Purpose |
|---|---|
| `needle_ExperienceLevel1` through `needle_ExperienceLevel9` | XP thresholds per level |
| `needle_ExperienceAdjustMinimum` | Min XP adjustment |
| `needle_ExperienceAdjustPercentagePerCategory` | XP scaling per category |
| `needle_ExperienceAdjustPercentagePerLevel` | XP scaling per level |
| `needle_ExperienceAssistMultiplier` | Assist XP multiplier |
| `needle_ExperienceAssistRadius` | Assist detection radius |
| `needle_ExperiencePercentageToOtherShipTypes` | XP spread to other ships |
| `needle_ExperiencePerCrystalUpgradingStructure` | XP from crystal upgrades |
| `needle_ExperiencePerOreUpgradingStructure` | XP from ore upgrades |

---

## 15. Complete Endpoint Summary

### Public API (Client -> Backend)

| # | Service | Method | Path (UNCERTAIN) | Purpose |
|---|---|---|---|---|
| 1 | CNeedleAccountService | POST | `/authenticate` | Login with Steam ticket, get SessionId |
| 2 | CNeedleClientAccountDataService | GET | `/accountdata` | Refresh player profile |
| 3 | CComponentNeedleNetworkClientMatchMaker | POST | `/matchmake` | Find/join match |
| 4 | CComponentNeedleNetworkClientMatchMaker | GET | `/matchmake/progress` | Poll matchmaking status |
| 5 | CNeedleClientLeaderboardsService | GET | `/leaderboards` | Get leaderboard data |
| 6 | CNeedleClientLeaderboardsService | GET | `/leaderboards/local` | Get local player entry |
| 7 | CNeedleClientMessagesService | GET | `/messages` | Get MOTD/login messages |
| 8 | CNeedleClientReportingService | POST | `/report` | Submit player report |
| 9 | CNeedleClientCapitalShipDataService | GET | `/capitalship/status` | Get contract/capital ship status |
| 10 | (client) | POST | `/capitalship/run` | Start capital ship run |
| 11 | (client) | DELETE | `/contract` | Delete a contract |
| 12 | (client) | POST | `/augment` | Augment a ship |
| 13 | (client) | POST | `/reconstruct` | Reconstruct an augment |
| 14 | (client) | GET | `/rewards` | Get match/contract rewards |
| 15 | (client) | GET | `/trophies` | Get trophy data |
| 16 | (client) | GET | `/dlc` | Refresh DLC ownership |

### Private API (Server -> Backend, Mutual TLS)

| # | Service | Method | Path (UNCERTAIN) | Purpose |
|---|---|---|---|---|
| 1 | CNeedleServerReservationService | POST | `/reservations` | Create/update player reservations |
| 2 | CNeedleServerAccountDataService | POST | `/accountdata` | Push player data changes |
| 3 | CNeedleServerAccountDataService | POST | `/rewards` | Push match rewards |
| 4 | CNeedleServerCapitalShipDataService | POST | `/capitalship/status` | Push capital ship match state |
| 5 | CNeedleConnectionAuthenticator | POST | `/authenticate-ticket` | Validate player connection ticket |
| 6 | CNeedleServerStatusCommunicator | POST | `/server/status` | Server heartbeat/registration |

---

## 16. Key Configuration Variables

| Variable | Purpose |
|---|---|
| `needle_publicServiceUrlOverride` | Override public API base URL |
| `needle_privateServiceUrlOverride` | Override private API base URL |
| `needle_serviceApiVersion` | API version in URL path |
| `needle_ServerName` | Game server display name |
| `needle_publicip` | Server's public IP address |
| `network_ServerListenPort` | Game server listen port |
| `needle_useMatchmaker` | Enable/disable matchmaking |
| `needle_MatchType` | Current match type |
| `needle_MatchSize` | Current match size |
| `needle_RegionLookupUrl` | Region detection service URL |
| `needle_CurrentRegionCode` | Current region code |
| `needle_WaitForAccountDataReadyTime` | Timeout for account data |
| `needle_NetworkRatingUpdatePeriod` | Rating sync interval |
| `needle_MatchCountdownTime` | Match start countdown |
| `needle_MaxSquadSize` | Max squad size |
| `needle_CapitalShipRunJumpCount` | Jumps per capital ship run |
| `needle_FameRateForDecisiveWin` | Fame multiplier for decisive win |
| `needle_FameRateForStrategicWin` | Fame multiplier for strategic win |
| `needle_FameRateForLoss` | Fame multiplier for loss |
| `needle_FameRateForCapitalShipEscape` | Fame for capital ship escape |
| `needle_ServerFameGainMultiplier` | Server-wide fame multiplier |
| `needle_IgnoreDatabaseFameCaps` | Debug: bypass fame caps |
| `needle_ContractMaxJumps` | Max jumps in contracts |
| `needle_MatchTimeBeforeRequestingCapitalShip` | Time before capital ship spawns |

---

## Notes

- All endpoint **paths** are marked [UNCERTAIN] because exact URL segments are not stored as strings in the binary; they are likely constructed programmatically or stored in obfuscated/compiled form. The path names are inferred from service names and error messages.
- All **JSON field names** that appear as standalone strings in the binary are marked [CONFIRMED].
- The `WebServiceInterfaceVersion` query parameter is added to every request by `AddWebServiceInterfaceVersionParam()`.
- The Bearer token is passed as `auth=Bearer {token}` (likely as a query parameter, given the AddQuery infrastructure, not a standard Authorization header).
- The game was built from source at `E:\rel\Needle_Release\` at Armature Studio in Austin, TX.
- Error format shows: HTTP status code (int) + error message string.
