# AWS Metadata & DebugIsFake Analysis

## Executive Summary

The Dead Star server was built to run on AWS EC2 instances. At startup it queries the EC2 instance metadata service (169.254.169.254) for public IP, instance type, and instance ID. A `DebugIsFake()` bypass exists in NeedleCommon but its trigger mechanism is unclear from strings alone. The most promising override path is the **`needle_publicip`** config var, which can supply the public IP directly and likely skip the metadata lookup.

---

## 1. AWS Metadata Usage (NeedleCommon_Steam_Release.dll)

### Namespace: `NNeedleAmazonMetadata`

All AWS metadata logic lives in `NNeedleCommon_Steam_Release.dll` under the `NNeedleAmazonMetadata` namespace.

**Functions found:**
| Mangled Symbol | Decoded Purpose |
|---|---|
| `NNeedleAmazonMetadata::SMetaData::SMetaData()` | Metadata struct constructor |
| `NNeedleAmazonMetadata::RequestMetadata(CHttpManager&)` | Initiates HTTP GET to metadata endpoint |
| `NNeedleAmazonMetadata::HasMetadata()` | Returns whether metadata was successfully retrieved |
| `NNeedleAmazonMetadata::GetMetadata()` | Returns the SMetaData struct |
| `NNeedleAmazonMetadata::IsRequested()` | Whether a metadata request is in flight |
| `NNeedleAmazonMetadata::UpdateReturnComplete()` | Polls for completion of the async HTTP request |
| `NNeedleAmazonMetadata::GetError()` | Returns SRichError on failure |
| `NNeedleAmazonMetadata::DebugIsFake()` | **The debug bypass function** |

**Metadata endpoint and paths:**
```
http://169.254.169.254/2014-11-05/
  meta-data/public-ipv4
  meta-data/instance-id
  meta-data/instance-type
```

The server fetches three things from EC2 metadata:
1. **public-ipv4** — the server's public IP address for client connections
2. **instance-id** — used to identify this server instance in the backend (e.g., `i-0abc123def`)
3. **instance-type** — used for capacity/cost tracking (e.g., `c5.xlarge`)

**No AWS metadata references exist in any other DLL** — Engine, GameComponents, GameCore, Opcode, and DeadStar.exe are all clean. This is fully contained in NeedleCommon.

---

## 2. DebugIsFake() — The Development Bypass

### What we know:
- **Full symbol:** `?DebugIsFake@NNeedleAmazonMetadata@@YA_NXZ`
- **Decoded:** `bool NNeedleAmazonMetadata::DebugIsFake(void)`
- **Location:** `NeedleCommon_Steam_Release.dll`
- **Returns:** `bool` — likely returns `true` when the server should use fake/stubbed metadata

### How to trigger it:
From strings analysis alone, there is **no obvious command-line flag or config var** named "DebugIsFake", "fake", or "mock" in NeedleCommon. The function is a static free function (not a method), suggesting it may:

1. Check a compile-time `#define` (would be baked into the Release build — likely returns `false` in this shipping binary)
2. Check an internal boolean that gets set by another system
3. Check a config var whose name doesn't contain "fake" or "debug"

**Key observation:** The string `PASS=%d;DEBUG=%d` appears in GameComponentsNeedle, suggesting the engine has a debug level system. The DebugIsFake function may check if DEBUG > 0.

### Related debug strings in GameComponentsNeedle:
- `needle_DebugFakePreviousMatchData` — a config var that fakes match data (shows the pattern: `needle_Debug*Fake*`)
- `needle_DebugStressTest` — stress test mode
- `needle_DebugStressTestDisableTickets` — disables ticket validation in stress test
- `needle_DebugStressTestServices` — fakes backend services in stress test
- `FakeListenForSinglePlayer` — method on CServerNetworkScene for single-player mode
- `DEBUG: Players Can Use All Ships` / `DEBUG: Players Can Use All Skins` — debug menu items

**Likely scenario:** In the release build, `DebugIsFake()` returns `false`. It was a development-only toggle, possibly controlled by a build configuration or developer environment variable.

---

## 3. What Happens When Metadata Fails

### Error strings found:
```
Amazon metadata lookup failure.
METADATA_LOOKUP_FAILURE
METADATA_FAILED_TO_LAUNCH
```

### Error handling flow:
1. `RequestMetadata()` starts an async HTTP request to 169.254.169.254
2. `UpdateReturnComplete()` is called each tick to poll for completion
3. On failure, `GetError()` returns an `SRichError` with the failure type
4. Two failure modes exist:
   - **`METADATA_LOOKUP_FAILURE`** — the HTTP request returned an error or timed out
   - **`METADATA_FAILED_TO_LAUNCH`** — the HTTP request couldn't even be started

### What happens next:
The server uses `SServerInstance` (from `NNeedleInstanceWrangler`) to register itself with the backend. Without metadata, the server likely either:
- **Crashes/asserts** — the assertion `!gPublicIpAddress.GetString().empty()` in GameComponentsNeedle confirms the server REQUIRES a non-empty public IP
- **Refuses to register** — `IsValidServerInstance()` would return false if fields are empty
- **Enters unhealthy state** — `~UNHEALTHY_SERVER_DESCRIPTION~`, `needle_unhealthyServerKickTime`, `needle_unhealthyServerKillTimeAfterKickTime` suggest a health monitoring system

**The assertion `!gPublicIpAddress.GetString().empty()` is the critical failure point.** If the public IP is not set (from metadata or override), the server will assert-crash.

---

## 4. needle_publicip and IP Override System

### Config vars for IP/network:
| Config Var | Location | Purpose |
|---|---|---|
| `needle_publicip` | GameComponentsNeedle | **Override for the server's public IP address** |
| `network_ServerAddress` | GameComponentsNeedle, NeedleCommon | Server address for client connections |
| `network_ServerListenPort` | GameComponentsNeedle | Port to listen on |
| `needle_ServerName` | GameComponentsNeedle | Server display name |

### Server registration fields (JSON):
From GameComponentsNeedle strings, the server instance JSON contains:
```
ServerIpAddress
ServerPort
ServerVersion
ServerName
PublicIp
MatchType
Region
```

### IP flow:
1. `NNeedleAmazonMetadata::RequestMetadata()` fetches `meta-data/public-ipv4` from EC2
2. Result stored in `SMetaData` struct
3. Value propagated to `gPublicIpAddress` global
4. **`needle_publicip`** config var can override this value
5. `gPublicIpAddress` used in `CNeedleServerReservationService` to register with backend
6. Registration sends `NeedleGameServerUpdate` to backend via `GetPrivateServicesUrlForPath()`

### The override pattern:
The existence of `needle_publicip` as a separate config var strongly suggests:
- If `needle_publicip` is set, the server uses that value directly
- If not set, it falls back to the EC2 metadata lookup
- The assertion `!gPublicIpAddress.GetString().empty()` fires only if BOTH paths fail

---

## 5. Server Startup Sequence

### Backend service infrastructure:
The server communicates with Armature's backend at `https://deadstar.rel.armature.com/` (now defunct).

**Service URL system:**
| Config Var | Purpose |
|---|---|
| `needle_publicServiceUrlOverride` | Override public-facing API URL |
| `needle_privateServiceUrlOverride` | Override private/internal API URL |
| `needle_serviceApiVersion` | API version string |

**Private services use mTLS:**
```
GetPrivateServicesCACertificate()
GetPrivateServicesClientCertificate()
GetPrivateServicesClientKey()
```

**Backend services in GameComponentsNeedle:**
| Service | Source File | Purpose |
|---|---|---|
| `CNeedleServerReservationService` | Services\CNeedleServerReservationService.cpp | Server heartbeat and player reservation |
| `CNeedleServerAccountDataService` | Services\CNeedleServerAccountDataService.cpp | Player account/progression data |
| `CNeedleTicketValidator` | Services\CNeedleTicketValidator.cpp | Steam ticket authentication |
| `CNeedleClientAccountDataService` | Services\CNeedleClientAccountDataService.cpp | Client-side account data |
| `CNeedleClientLeaderboardsService` | Services\CNeedleClientLeaderboardsService.cpp | Leaderboards |
| `CNeedleClientMessagesService` | Services\CNeedleClientMessagesService.cpp | In-game messaging |
| `CNeedleClientReportingService` | Services\CNeedleClientReportingService.cpp | Player reporting |

### Server flow:
1. Engine initializes (Engine_Steam_Release.dll)
2. `NNeedleAmazonMetadata::RequestMetadata()` called — OR `needle_publicip` checked first
3. Metadata response populates `gPublicIpAddress` 
4. `CServerNetworkScene::Listen()` opens the game port (`network_ServerListenPort`)
5. `CNeedleServerReservationService` sends `NeedleGameServerUpdate` to backend with:
   - ServerIpAddress, ServerPort, ServerVersion, ServerName, MatchType, Region
6. Backend registers the server for matchmaking
7. `CNeedleServerReservationService` heartbeats periodically
8. Matchmaker sends reservations to the server
9. Players connect with Steam tickets, validated by `CNeedleTicketValidator`

---

## 6. Additional Discovery: Region System

```
needle_CurrentRegionCode
needle_RegionLookupUrl
needle_StartRegion
region.deadstarservices.com
```

The server also had region awareness via `region.deadstarservices.com` — another defunct service that needs replacement.

---

## 7. Recommended Strategy for Running Outside AWS

### Tier 1: Minimum Viable (Config Var Override)
Set these config vars to bypass AWS metadata entirely:
```
needle_publicip = "<your-server-public-ip>"
network_ServerListenPort = <port>
needle_ServerName = "Revival Server"
```

Config vars use the `CScriptVar` system. They can likely be set via:
- Command-line arguments (engine uses `GetCommandLineA`)
- A `.cfg` config file
- The engine console

This should satisfy the `!gPublicIpAddress.GetString().empty()` assertion and prevent the metadata lookup from being fatal.

### Tier 2: Fake Metadata Service (If Tier 1 insufficient)
If the server still calls `RequestMetadata()` regardless of `needle_publicip`, run a lightweight HTTP server on `169.254.169.254:80`:
```
GET /2014-11-05/meta-data/public-ipv4  → "1.2.3.4"
GET /2014-11-05/meta-data/instance-id   → "i-deadstar0001"
GET /2014-11-05/meta-data/instance-type  → "c5.xlarge"
```
This can be done with a simple Python/Go HTTP server bound to a loopback alias.

### Tier 3: Backend Service Replacement (Required for multiplayer)
Override the backend URLs:
```
needle_privateServiceUrlOverride = "https://your-server:port"
needle_publicServiceUrlOverride = "https://your-server:port"
```

The replacement backend must implement:
1. **NeedleGameServerUpdate** — accept server registration heartbeats
2. **Matchmaking** — handle `StartMatchmaking_*` requests and return server address + reservations
3. **Account Data** — player progression/loadouts
4. **Ticket Validation** — verify Steam tickets (or stub for testing)

### Tier 4: Binary Patching (If DebugIsFake needed)
If `DebugIsFake()` always returns `false` in the release build:
- Locate the function in the DLL (search for the mangled name in exports)
- Patch the function body to `mov al, 1; ret` (return true)
- This would make the entire metadata system think it's in dev/fake mode

### Priority Order:
1. **Try `needle_publicip` first** — lowest risk, most likely to work
2. **Add fake metadata endpoint** — simple fallback
3. **Build replacement backend** — required anyway for multiplayer
4. **Binary patch** — last resort only if config overrides don't prevent the metadata call
