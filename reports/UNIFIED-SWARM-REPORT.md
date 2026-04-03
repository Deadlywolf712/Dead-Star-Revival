# Dead Star Revival — Unified Swarm Report

**Date:** 2026-04-03
**Swarm Size:** 8 agents
**Agents:** Binary Analyst, Protocol Engineer, API Mapper, Asset Engineer, Auth Specialist, Game Logic Analyst, Server Builder, Integration Tester

---

## Executive Summary

An 8-agent reverse engineering swarm analyzed the Dead Star game binaries (AppID 366400, built July 19, 2016). All major subsystems have been mapped. The path to multiplayer revival is clear, with specific blockers identified and solutions proposed.

**Bottom line:** We can revive multiplayer by (1) building a fake REST backend, (2) redirecting the client/server via config vars, (3) using Goldberg Steam emulator, and (4) compiling the custom server launcher.

---

## 1. Architecture Overview

### Binary Layout
| Binary | Size | Role |
|--------|------|------|
| DeadStar.exe | 23KB | Stub launcher (calls client entry only) |
| GameCore_Steam_Release.dll | 7.3MB | Engine core, networking, both entry points |
| GameComponentsNeedle_Steam_Release.dll | 3.7MB | Game logic, services, 483 config vars |
| Engine_Steam_Release.dll | 5.7MB | HTTP/curl, OpenSSL, sockets, Steam, archives |
| NeedleCommon_Steam_Release.dll | 41KB | API URLs, SSL certs, instance wrangler |
| Renderer_Steam_Release.dll | 698KB | DirectX 11 renderer |
| Opcode_Steam_Release.dll | 447KB | Collision/physics (OPCODE library) |
| steam_api64.dll | 208KB | Steamworks SDK |

- **Compiler:** MSVC 11 (Visual Studio 2012)
- **Runtime:** VC++ 2012 Redistributable + DirectX June 2010
- **Build path:** `E:\rel\Needle_Release\`
- **Build version:** REL-147994

### Entry Points [CONFIRMED by 3 agents]
| Entry | Mangled Name | Ordinal | Signature |
|-------|-------------|---------|-----------|
| Server | `?bpeWin32Server_GameCoreMain@@YAHPEAUHINSTANCE__@@HPEAPEBD@Z` | See note | `int (HINSTANCE*, int argc, const char** argv)` |
| Client | `?bpeWin32_GameCoreMain@@YAHPEAUHINSTANCE__@@0PEADH@Z` | See note | `int (HINSTANCE*, HINSTANCE*, char*, int)` |

> **Ordinal discrepancy:** re-binary and re-tester report server=7500, re-server reports server=7501. This is likely a base-0 vs base-1 numbering difference. The launcher uses GetProcAddress by name, not ordinal, so this doesn't affect functionality.

### Two-Tier Networking
1. **HTTP REST API** — Client ↔ Backend ↔ Server (auth, matchmaking, reservations, account data)
2. **Custom UDP** — Client ↔ Server (gameplay, delta-compressed bit streams)

---

## 2. ARMA v2 Archive Format [CRACKED]

**File:** `GameData/gamedata.ara` (3.2GB)

### Header (32 bytes)
| Offset | Size | Value | Description |
|--------|------|-------|-------------|
| 0x00 | 4 | `ARMA` | Magic bytes |
| 0x04 | 2 | 0x0002 | Version |
| 0x06 | 2 | 0x696E | Unknown |
| 0x08 | 4 | 9,500 | File count |
| 0x0C | 4 | 0x2000 | Hash bucket data offset |
| 0x10 | 4 | 0x20174 | File entry table offset |
| 0x14 | 4 | 0x4E7B0 | File data offset |

### Key Facts
- **9,500 files**, **11,986 paths** (platform variants)
- **No compression** — all files stored raw
- **Hash lookup:** FNV-1a of uppercase path, seed 0x811C9DC5
- **File entry:** 20 bytes each (uint64 offset + uint32 compressed_size + uint32 uncompressed_size + uint32 flags)
- Asset types: .ctxr (textures), .cmdl (models), .cskn (skinned meshes), .cfon (fonts), .fx (shaders), .csif (data), .sgpr (scenes)

### Extracted Config Files

**$/commandlineargs.txt:**
```
-vf $/GameScriptVars.txt -d $/needle_win.bpdeps -i $/needle/loaders/startup.sgpr -l $/needle/ui/loadingscreen/scripts/initial_loading_screen.sgpr
```

**$/gamescriptvars.txt:**
```
r_renderer="needle";
renderConsoleOutput=0;
renderConsoleMessages=0;
needle_useMatchmaker=true;
needle_DemoMode=0;
needle_EnableClientReadyMatchStartClient=false;
needle_EnableClientReadyMatchStartServer=false;
capitalShipEnable=true;
```

> **Critical discovery:** The startup world file is `$/needle/loaders/startup.sgpr` — read from inside the archive. The server doesn't need extracted .sgpr files; the engine's archive system resolves `$/` paths internally.

---

## 3. Authentication System

### Auth Flow [CONFIRMED]
```
1. Client: SteamAPI_Init() + GeneratePlatformSpecificAuth() → Steam ticket
2. Client → Backend: POST /api/public/{version}/authenticate
   Request: { steam_ticket, platform_env, BuildVersion, WebServiceInterfaceVersion }
   Response: { SessionId, account_data, session_data }
3. Client stores SessionId as Bearer token: auth=Bearer {SessionId}
4. All subsequent API calls include: ?auth=Bearer {SessionId}
5. On game server connect: client sends CConnectionTicket (contains reservation ID, account data, build version)
6. Server → Backend: POST /api/private/{version}/authenticate-ticket (validates via mTLS)
7. Server checks: build version match, valid reservation, account data size
```

### Auth State Machine [CONFIRMED]
```
not authenticated → generate auth → get session → lookup region → authenticated
```
Logged as: `CNeedleAccountService auth status changed. [%s]->[%s]`

### SSL/Certificate Infrastructure [CONFIRMED]
- OpenSSL 1.0.2 (Jan 2015) statically linked in Engine DLL
- Self-signed cert: CN=deadstar.rel.armature.com, O=Armature, Austin TX, RSA 2048-bit
- **Expired June 2018**
- mTLS for private API: separate CA cert + client cert + client key
- `DisableSSLPeerVerification()` exists but is per-request only (no global toggle)

### 12 Ticket Auth Error Codes [CONFIRMED]
```
TICKET_AUTH_BAD_ACCOUNT_SIZE    TICKET_AUTH_CANT_PARSE
TICKET_AUTH_DUPLICATE_PLAYER    TICKET_AUTH_INCOMPATIBLE_VERSION
TICKET_AUTH_JSON_DECODE_ERRORS  TICKET_AUTH_JSON_PARSE_ERROR
TICKET_AUTH_NO_GAME_MGR         TICKET_AUTH_NO_RESERVATION
TICKET_AUTH_REQUEST_FAILED      TICKET_AUTH_RESERVATION_INVALID
TICKET_CONNECTIONS_DISALLOWED   TICKET_REVOKED
```

### Auth Bypass Strategy
1. **Redirect API:** Set `needle_publicServiceUrlOverride` and `needle_privateServiceUrlOverride` to point to our fake backend
2. **Fake backend:** Accept any Steam ticket, return valid SessionId + stub account data
3. **Ticket validation:** Always return success on private API authenticate-ticket endpoint
4. **Build version:** Return `REL-147994` to match the client
5. **DNS redirect:** Point `deadstar.rel.armature.com` and `region.deadstarservices.com` to our server
6. **Steam:** Use Goldberg emulator or `steam_appid.txt` with `366400`
7. **INetTicketValidator:** Clean interface — can be replaced if binary patching is viable

---

## 4. REST API — 22 Endpoints Mapped

### Public API (Client → Backend) — 16 Endpoints

| # | Service | Method | Path (inferred) | Priority |
|---|---------|--------|-----------------|----------|
| 1 | Auth | POST | /authenticate | CRITICAL |
| 2 | Account Data | GET | /accountdata | CRITICAL |
| 3 | Matchmake Start | POST | /matchmake | HIGH |
| 4 | Matchmake Progress | GET | /matchmake/progress | HIGH |
| 5 | Leaderboards | GET | /leaderboards | LOW (stub) |
| 6 | Leaderboards Local | GET | /leaderboards/local | LOW (stub) |
| 7 | Messages/MOTD | GET | /messages | LOW (stub) |
| 8 | Report Player | POST | /report | LOW (stub) |
| 9 | Capital Ship Status | GET | /capitalship/status | MEDIUM |
| 10 | Start Run | POST | /capitalship/run | MEDIUM |
| 11 | Delete Contract | DELETE | /contract | MEDIUM |
| 12 | Augment Ship | POST | /augment | MEDIUM |
| 13 | Reconstruct Augment | POST | /reconstruct | MEDIUM |
| 14 | Rewards | GET | /rewards | LOW (stub) |
| 15 | Trophies | GET | /trophies | LOW (stub) |
| 16 | DLC Refresh | GET | /dlc | LOW (stub) |

### Private API (Server → Backend, mTLS) — 6 Endpoints

| # | Service | Method | Path (inferred) | Priority |
|---|---------|--------|-----------------|----------|
| 1 | Reservations | POST | /reservations | CRITICAL |
| 2 | Authenticate Ticket | POST | /authenticate-ticket | CRITICAL |
| 3 | Push Account Data | POST | /accountdata | HIGH |
| 4 | Push Rewards | POST | /rewards | LOW (stub) |
| 5 | Capital Ship Push | POST | /capitalship/status | MEDIUM |
| 6 | Server Status | POST | /server/status | HIGH |

### URL Construction [CONFIRMED]
```
Public:  {baseUrl}api/public/{apiVersion}/{path}?auth=Bearer {token}&WebServiceInterfaceVersion={ver}
Private: {baseUrl}api/private/{apiVersion}/{path}?WebServiceInterfaceVersion={ver}
```

> **Note:** Auth token is passed as a query parameter (`?auth=Bearer {token}`), NOT as an Authorization header.

### Key JSON Schemas

**SServerInstance (server registration):**
```json
{
  "ApiVersion": 1,
  "ServerName": "string",
  "BuildVersion": "REL-147994",
  "MatchType": 0,
  "MatchSize": 1,
  "Port": 27015,
  "ProcessId": 1234,
  "PublicIp": "1.2.3.4"
}
```

**CCoreAccountData (partial — confirmed fields):**
```json
{
  "AccountId": 12345,
  "SessionId": "uuid-string",
  "CurrentPortraitId": 0,
  "PortraitIds": [0, 1, 2],
  "IsDevAccount": false,
  "Fame": 0, "FameTotal": 0, "FameActions": 0, "FamePlayers": 0,
  "FameGuardians": 0, "FameUpgrades": 0, "FameMatch": 0,
  "FameFromActions": 0, "FameFromPlayers": 0, "FameFromGuardians": 0,
  "FameFromUpgrades": 0, "FameCategoryLimits": [],
  "FameCapitalActions": 0, "fameRatio": 0.0,
  "isDLC": false,
  "loadouts": [
    {
      "shipType": 0, "ShipType": 0,
      "SkinId": 0, "AugmentId": 0, "AugmentRank": 0,
      "augmentLevel": 0, "augmentType": 0, "augmentRace": "string",
      "augmentRank_Core": 0, "augmentRank_Ship": 0,
      "augmentRank_Slot1": 0, "augmentRank_Slot2": 0,
      "augmentRank_Slot3": 0, "augmentRank_Slot4": 0
    }
  ]
}
```

**Matchmaking Request:**
```json
{
  "Mode": "string",
  "RequestType": 0,
  "Type": 0,
  "Size": 0,
  "Contract": 0,
  "Party": "string",
  "Count": 1,
  "Crossplay": 0,
  "RegionBitDefault": 0,
  "RegionBitsCustom": 0
}
```

---

## 5. UDP Game Protocol

### Connection Handshake (7 steps) [CONFIRMED]
```
1. Client → Server: ClientConnectTicket (CConnectionTicket with JSON payload)
2. Server: CNeedleConnectionAuthenticator validates ticket
   - Checks build version (REL-147994)
   - Checks reservation exists and is valid
   - Calls backend private API to validate
3. Server → Client: ServerConnectTicketAck (success/fail + error code)
4. Client → Server: ClientMtuDiscovery
5. Server → Client: ServerMtuHandshake / ServerMtuDiscovery
6. MTU test segment exchange
7. OnNetConnection — connection established
```

### Packet Types [CONFIRMED]
| Type | Contents |
|------|----------|
| UserInfo | Player ID (uint8) + CConnectionTicket |
| TransportPacket | Game state (NNetTypes::STransportPacket) |
| ControllerPacket | Player input (CUserInput) |

Each frame carries dual uint16 sequence numbers (base + current).

### Compression [CORRECTED]
- **Snappy** (NOT zlib as initially assumed)
- Three modes: CM_GLOBAL, CM_LOCAL_2, CM_LOCAL_4
- Performance counters track compression/decompression time and byte ratios

### Delta Compression [CONFIRMED]
- `NDeltaCompression::CSchema` defines field layouts
- `CNetDeltaBase<16>` — 16-state sliding window
- `CNetDeltaOutgoing::GenerateDelta()` on server
- `CNetDeltaIncoming::ApplyDelta()` on client
- Resync on window overrun: "Server delta-base outran client window, resyncing.."

### Channel System [CONFIRMED]
- `CNetChannelManager` manages indexed channels
- Reliable vs unreliable separation via dual sequence numbers
- `NET_CHANNEL_ALLOCATION_FAILED` on exhaustion

### Network Constants
| Constant | Value/Type |
|----------|------------|
| Player IDs | uint8 (CStrongId<uint8>) |
| Max players | ~20 (10v10) |
| Delta window | 16 states |
| Port config | `network_ServerListenPort` (uint16) |
| Idle timeout | `needle_IdleTimeoutTime` |
| Ping threshold | `needle_PingTooHighThreshold` |
| Throttle | `network_ThrottleLimit/Step/Threshold` |

### 20 Transport Error Codes + 8 Application Error Codes + 12 Ticket Auth Codes
All catalogued in [protocol-analysis.md](protocol-analysis.md).

---

## 6. Game Logic

### 8 Game Modes [CONFIRMED]
| Mode | Teams | Type | Status |
|------|-------|------|--------|
| Conquest | Hunter vs Needle | 5v5 / 10v10, ticket drain + base capture | Active |
| Recon | Hunter vs Needle | 5v5 / 10v10, tickets | Active |
| Hunt | Drifters vs Scavengers | 5v5 / 10v10, NPC events | Active |
| NeedleEscape | Co-op vs OldEmpire | PvE, capital ship escort | Active |
| Freeplay | N/A | Free roam, no matchmaking | Active |
| Tutorial | N/A | 3 stages | Active |
| NeedleCrisis | ? | Cut content — enum only | Skeleton |
| NeedleDiscovery | ? | Cut content — enum only | Skeleton |
| NeedleExploration | ? | Cut content — enum only | Skeleton |

### Match Lifecycle
```
Matchmaking → Lobby (region voting) → Auto-Start/Balance → Loading →
Galaxy Creation → Playing → Match End → After Action → Restart
```
Controller: `CComponentNeedleGameControllerDefault`

### Ships (12 types)
- 3 classes: Scout, Raider, Frigate
- 4 specialists each: Combat, Mining, Production, Research
- 3 loadout slots, 5 system slots (core + 4), 5 rank levels
- Augment system with 8+ modifier types

### Galaxy System
- Hexagonal sector grid (6 connections at clock positions 2/4/6/8/10/12)
- 5 nebula types with gameplay effects: Cloak, Corrosive, EMP, Fiery, Icy

### 6 Matchmaking Regions
useast, uswest, europe, asia, oceania, southamerica

---

## 7. Server Configuration

### Minimal Config for Revival (gamescriptvars.txt)
```ini
needle_useMatchmaker=false;
needle_IsSinglePlayer=false;
needle_ServerDrawMainView=false;
needle_ServerName="Dead Star Revival";
needle_MatchType=0;
needle_MatchSize=1;
network_ServerListenPort=27015;
network_ServerAddress="0.0.0.0";
needle_ResetServerOnNoConnections=true;
needle_publishMatchStats=false;
needle_publicServiceUrlOverride="http://localhost:8080";
needle_privateServiceUrlOverride="http://localhost:8080";
```

### 483 needle_* Variables + 73 Other Variables
Full lists in [configs/needle_variables_all.txt](../configs/needle_variables_all.txt) and [configs/other_variables.txt](../configs/other_variables.txt).

---

## 8. Cross-Reference: Discrepancies & Corrections

| Topic | Discrepancy | Resolution |
|-------|-------------|------------|
| Server ordinal | re-binary/re-tester say 7500, re-server says 7501 | Base-0 vs base-1 numbering. Launcher uses name lookup, not ordinal. **Non-issue.** |
| Compression | Previously assumed zlib | re-protocol confirmed **Snappy**. Zlib references in Engine DLL are for other purposes (HTTP content encoding). |
| KeyboardControlDefaults.txt | Expected in archive | re-assets confirmed **NOT in archive**. DLL handles absence gracefully. |
| gamescriptvars.txt size | Expected comprehensive | Only 8 overrides; the 483 vars are **hardcoded in DLL** with defaults. |
| D3D11 headless | Can server run headless? | Renderer DLL is hard-linked. D3D11 device created even with ServerDrawMainView=false. Need GPU, virtual adapter, or Mesa software renderer. |
| AWS metadata | Server expects EC2 | `DebugIsFake()` function exists. Non-AWS environments may need metadata stub or the debug path. |

**Zero contradictions** between agents on confirmed findings.

---

## 9. Revival Roadmap

### Phase 1: Minimum Viable Server (Critical Path)
- [ ] Build fake REST backend with 4 critical endpoints:
  - POST /authenticate (return SessionId + stub CCoreAccountData)
  - POST /authenticate-ticket (always return success)
  - POST /reservations (accept and track reservations)
  - POST /server/status (accept heartbeats)
- [ ] Compile DeadStarServer.exe launcher
- [ ] Create `steam_appid.txt` with `366400`
- [ ] Set up Goldberg Steam emulator (or have Steam + game ownership)
- [ ] Write override gamescriptvars.txt with `needle_useMatchmaker=false`
- [ ] Solve D3D11 requirement (virtual display adapter or Mesa)
- [ ] Stub AWS EC2 metadata endpoint (or confirm DebugIsFake works)
- [ ] Test: client connects to self-hosted dedicated server

### Phase 2: Playable Multiplayer
- [ ] Implement matchmaking endpoints (match players to servers)
- [ ] Implement account data persistence (save player progress)
- [ ] Build ARMA v2 unpacker for asset extraction/modding
- [ ] Test all game modes (Conquest, Recon, Hunt, NeedleEscape)
- [ ] Implement leaderboard, messages, reporting stubs

### Phase 3: Full Revival
- [ ] LAN mode activation (CLanServiceAdvertiser/CLanServiceBrowser)
- [ ] Listen server mode (host+play — easier than dedicated)
- [ ] Cross-play infrastructure
- [ ] Cut content investigation (NeedleCrisis, NeedleDiscovery, NeedleExploration)
- [ ] Full asset unpacker for modding community

---

## 10. Files Generated by This Swarm

### Reports (Revival Assets/reports/)
| File | Agent | Size |
|------|-------|------|
| binary-analysis.md | re-binary | Full DLL structure, 30K+ exports, 452 vtables |
| protocol-analysis.md | re-protocol | UDP protocol, handshake, delta compression |
| api-mapping.md | re-api | 22 endpoints, JSON schemas |
| arma-format.md | re-assets | ARMA v2 format specification |
| auth-analysis.md | re-auth | Auth flow, SSL, bypass strategy |
| gamelogic-analysis.md | re-gamelogic | 8 modes, 12 ships, 380+ config vars |
| server-analysis.md | re-server | Server launcher, config, dependencies |
| integration-test.md | re-tester | Validation: 9 confirmed, 0 contradictions |
| **UNIFIED-SWARM-REPORT.md** | orchestrator | This file |

### Configs (Revival Assets/configs/)
| File | Contents |
|------|----------|
| commandlineargs.txt | Extracted from gamedata.ara |
| gamescriptvars.txt | Extracted from gamedata.ara |
| needle_variables_all.txt | 483 needle_* config vars |
| other_variables.txt | 73 non-needle vars (hud_*, r_*, matchmaking_*) |
| deadstar-public-services.pem | Extracted SSL certificate |

### Code (Revival Assets/server/)
| File | Contents |
|------|----------|
| DeadStarServer.c | Custom server launcher (LoadLibrary + GetProcAddress) |

### Assets (Revival Assets/assets/)
| File | Contents |
|------|----------|
| all_file_paths.txt | 11,986 file paths from gamedata.ara |
| file_entries.txt | 9,500 file entries with offsets/sizes |
| file_types.txt | Magic byte distribution |
