# Dead Star Server Analysis Report

Generated: 2026-04-03
Analyst: Server Builder Agent

---

## 1. Bin64 File Catalog

| File | Size | Description |
|------|------|-------------|
| DeadStar.exe | 23,040 bytes | Client launcher stub (imports GameCore) |
| GameCore_Steam_Release.dll | 7,276,544 bytes | Core engine + server entry point |
| GameComponentsNeedle_Steam_Release.dll | 3,650,560 bytes | Game logic, matchmaking, config vars |
| Engine_Steam_Release.dll | 5,696,000 bytes | HTTP, networking, sockets, audio, input |
| Renderer_Steam_Release.dll | 698,368 bytes | DirectX 11 renderer |
| NeedleCommon_Steam_Release.dll | 41,472 bytes | Web service URLs, instance wrangler, certs |
| Opcode_Steam_Release.dll | 447,488 bytes | Collision/physics (OPCODE library) |
| steam_api64.dll | 208,296 bytes | Steamworks SDK |

**Build date**: Tue Jul 19 12:36:43 2016 (GameCore), Tue Jul 19 12:37:48 2016 (DeadStar.exe)
**Compiler**: MSVC 11 (Visual Studio 2012) - links MSVCR110.dll / MSVCP110.dll
**Architecture**: x86-64 (PE32+), Windows GUI subsystem
**Build path**: `E:\rel\Needle_Release\`

---

## 2. Server Entry Point

### [CONFIRMED] Export Name
```
?bpeWin32Server_GameCoreMain@@YAHPEAUHINSTANCE__@@HPEAPEBD@Z
```

### [CONFIRMED] Demangled Signature
```cpp
int __cdecl bpeWin32Server_GameCoreMain(HINSTANCE__*, int, const char**)
```

### [CONFIRMED] Export Location
- **DLL**: GameCore_Steam_Release.dll
- **Export ordinal**: 7501 (base 1 = ordinal 7501)
- **Note**: Ordinal 7501 is `bpeWin32Server_GameCoreMain`, ordinal 7502 is `bpeWin32_GameCoreMain` (client)

### [CONFIRMED] Client Entry Point (for comparison)
```
?bpeWin32_GameCoreMain@@YAHPEAUHINSTANCE__@@0PEADH@Z
```
Demangled: `int bpeWin32_GameCoreMain(HINSTANCE*, HINSTANCE*, char*, int)`
- This is a standard WinMain-style signature (hInstance, hPrevInstance, lpCmdLine, nCmdShow)
- The SERVER version takes `(HINSTANCE*, int argc, const char** argv)` - a main()-style signature

---

## 3. Command-Line Arguments

### [CONFIRMED] World File: `-i <path>`
The game expects a world file via the `-i` flag:
```
The game has neither a command line world file (-i <blah>) nor an overridden world file (startupScripting="<blah>")!
```

The world file must be a `.sgpr` (Script Game Package Resource) file:
```
Invalid filepath passed for loading of scripting (either command line argument or loadScripting lua var). Must be .sgpr file.
```

### [CONFIRMED] Additional Flags
| Flag | Purpose |
|------|---------|
| `-i <file.sgpr>` | World/level script package file |
| `-debuggfx` | Enable graphics debugging |
| `-telemetry` | Enable RAD Telemetry profiling |

### [CONFIRMED] Config File Mechanism
The engine reads additional args from `$/commandlineargs.txt` (where `$` = game root):
```
Reading command line arguments from commandlineargs.txt...
```

And loads script variables from `$/gamescriptvars.txt`:
```
%S. Proceeding in case there is a valid override in GameScriptVars.txt.
```

The `startupScripting` variable in GameScriptVars.txt can override the `-i` world file:
```
Overridden startup scripting: %s
```

### [CONFIRMED] Config Format
Lines in gamescriptvars.txt appear to use semicolon-terminated assignments:
```
-- %S;
```
The `--` prefix is used for logging parsed entries.

---

## 4. DLL Dependency Chain

### Full Dependency Tree for Server Operation

```
DeadStarServer.exe (custom launcher)
  +-- GameCore_Steam_Release.dll (server entry)
  |     +-- Engine_Steam_Release.dll
  |     |     +-- steam_api64.dll
  |     |     +-- Opcode_Steam_Release.dll
  |     |     |     +-- MSVCR110.dll
  |     |     |     +-- KERNEL32.dll
  |     |     +-- XINPUT1_3.dll
  |     |     +-- DNSAPI.dll
  |     |     +-- WININET.dll
  |     |     +-- IPHLPAPI.DLL
  |     |     +-- WS2_32.dll
  |     |     +-- KERNEL32.dll
  |     |     +-- USER32.dll
  |     |     +-- ADVAPI32.dll
  |     |     +-- SHELL32.dll
  |     |     +-- MSVCP110.dll
  |     |     +-- MSVCR110.dll
  |     |     +-- RPCRT4.dll
  |     |     +-- SETUPAPI.dll
  |     |     +-- WINMM.dll
  |     |     +-- ole32.dll
  |     |     +-- HID.DLL
  |     +-- NeedleCommon_Steam_Release.dll
  |     |     +-- steam_api64.dll
  |     |     +-- dbghelp.dll
  |     |     +-- Engine_Steam_Release.dll
  |     |     +-- KERNEL32.dll
  |     |     +-- USER32.dll
  |     |     +-- SHELL32.dll
  |     |     +-- MSVCP110.dll
  |     |     +-- MSVCR110.dll
  |     |     +-- Secur32.dll
  |     +-- Renderer_Steam_Release.dll
  |     |     +-- Engine_Steam_Release.dll
  |     |     +-- KERNEL32.dll
  |     |     +-- USER32.dll
  |     |     +-- MSVCP110.dll
  |     |     +-- MSVCR110.dll
  |     |     +-- dxgi.dll
  |     |     +-- d3d11.dll
  |     |     +-- d3dx11_43.dll
  |     |     +-- D3DCOMPILER_43.dll
  |     +-- WS2_32.dll
  |     +-- KERNEL32.dll
  |     +-- USER32.dll
  |     +-- steam_api64.dll
  |     +-- MSVCP110.dll
  |     +-- MSVCR110.dll
  |     +-- dxgi.dll
  +-- GameComponentsNeedle_Steam_Release.dll (loaded by GameCore)
        +-- GameCore_Steam_Release.dll
        +-- Engine_Steam_Release.dll
        +-- Renderer_Steam_Release.dll
        +-- steam_api64.dll
        +-- NeedleCommon_Steam_Release.dll
        +-- KERNEL32.dll
        +-- USER32.dll
        +-- MSVCP110.dll
        +-- MSVCR110.dll
```

### [CONFIRMED] Required Game DLLs (must be co-located)
1. GameCore_Steam_Release.dll
2. Engine_Steam_Release.dll
3. GameComponentsNeedle_Steam_Release.dll
4. NeedleCommon_Steam_Release.dll
5. Renderer_Steam_Release.dll
6. Opcode_Steam_Release.dll
7. steam_api64.dll

### [CONFIRMED] Required System DLLs (Windows)
- MSVCR110.dll, MSVCP110.dll (Visual C++ 2012 Redistributable)
- d3d11.dll, dxgi.dll, d3dx11_43.dll, D3DCOMPILER_43.dll (DirectX 11)
- XINPUT1_3.dll (gamepad input)
- WS2_32.dll, DNSAPI.dll, WININET.dll, IPHLPAPI.DLL (networking)
- Standard Windows: KERNEL32, USER32, ADVAPI32, SHELL32, RPCRT4, SETUPAPI, WINMM, ole32, HID, Secur32, dbghelp

### [UNCERTAIN] Third-Party DLLs (may be loaded at runtime)
- Telemetry64.dll (RAD Telemetry - optional profiling, searched at runtime)

---

## 5. Headless Mode / ServerDrawMainView

### [CONFIRMED] Config Variable
```
needle_ServerDrawMainView
```
Found in GameComponentsNeedle_Steam_Release.dll as a registered config variable.

### [UNCERTAIN] Headless Behavior
The server entry point (`bpeWin32Server_GameCoreMain`) likely still initializes the renderer since:
- GameCore directly imports Renderer_Steam_Release.dll
- Renderer_Steam_Release.dll imports d3d11.dll, dxgi.dll, d3dx11_43.dll, D3DCOMPILER_43.dll

Setting `needle_ServerDrawMainView` to `false`/`0` likely prevents the main render loop from drawing but does NOT eliminate the D3D11 initialization. The server **will need a GPU or virtual display adapter** unless:
1. The renderer initialization can be stubbed out
2. A headless D3D11 driver (like Mesa3D's software renderer) is provided

### [CONFIRMED] Renderer Factory Pattern
```
GameRendererFactory
Unknown renderer %s - using default
```
The `CGameManager` constructor takes a `unique_ptr<IGameRenderer>`, and there is a factory function `GameRendererFactory`. The string "Unknown renderer %s - using default" suggests there may be a way to specify a renderer type. This is a potential hook for a null/headless renderer.

---

## 6. Steam Dependency

### [CONFIRMED] Steam is Required
Multiple DLLs import `steam_api64.dll`:
- GameCore_Steam_Release.dll
- Engine_Steam_Release.dll
- GameComponentsNeedle_Steam_Release.dll
- NeedleCommon_Steam_Release.dll

### [CONFIRMED] Steam API Functions Used (by GameCore)
```
SteamAPI_Init
SteamAPI_Shutdown
SteamAPI_RunCallbacks
SteamAPI_RegisterCallback
SteamAPI_UnregisterCallback
SteamAPI_RestartAppIfNecessary
SteamUser
SteamUserStats
SteamUtils
```

### [CONFIRMED] Fatal on Steam Failure
```
SteamAPI_Init() failed
Steam must be running to play this game. SteamAPI_Init() failed.
```

### [UNCERTAIN] Server vs Client Steam Usage
The server does NOT appear to use the SteamGameServer API (no `SteamGameServer_Init`, `SteamGameServer_RunCallbacks` exports imported). This means:
- The server uses the same Steam client APIs as the game client
- It likely needs Steam running with a valid account that owns AppID 366400
- **OR** a `steam_appid.txt` file containing `366400` in the working directory

### Workaround Options
1. **steam_appid.txt**: Place a file containing `366400` in the Bin64 directory to bypass `SteamAPI_RestartAppIfNecessary`
2. **Stub steam_api64.dll**: Create a replacement DLL that returns success for all calls
3. **Goldberg Emulator**: Drop-in replacement for steam_api64.dll that emulates Steam offline

---

## 7. Build Instructions for Server Launcher

### Architecture
The server launcher is a minimal Windows x64 executable that:
1. Loads GameCore_Steam_Release.dll
2. Gets the address of `bpeWin32Server_GameCoreMain`
3. Calls it with (hInstance, argc, argv)

### Cross-Compile with MinGW (Linux to Windows)
```bash
x86_64-w64-mingw32-gcc -o DeadStarServer.exe DeadStarServer.c \
    -mwindows -mconsole \
    -L/path/to/Bin64 -lGameCore_Steam_Release \
    -Wl,--enable-auto-import
```

### Compile with MSVC (Windows)
```cmd
cl /Fe:DeadStarServer.exe DeadStarServer.c /link /SUBSYSTEM:CONSOLE user32.lib
```

### Compile with MinGW (Standalone, no import lib needed)
```bash
x86_64-w64-mingw32-gcc -o DeadStarServer.exe DeadStarServer.c -mconsole
```
Since we use runtime `LoadLibrary`/`GetProcAddress`, no import library is needed.

---

## 8. Minimal Server Configuration

### Required Config Variables

| Variable | Source DLL | Type | Purpose |
|----------|-----------|------|---------|
| `network_ServerListenPort` | GameComponentsNeedle | int | UDP port for game traffic |
| `network_ServerAddress` | GameComponentsNeedle | string | Server bind address |
| `needle_ServerName` | GameComponentsNeedle | string | Display name for the server |
| `needle_useMatchmaker` | GameComponentsNeedle | bool | Whether to use matchmaker (set false) |
| `needle_MatchType` | GameComponentsNeedle | enum | Conquest/Recon/Hunt/Freeplay/etc. |
| `needle_MatchSize` | GameComponentsNeedle | enum | Small/Medium/Large |
| `needle_ServerDrawMainView` | GameComponentsNeedle | bool | Render the game view (false for headless) |
| `needle_ResetServerOnNoConnections` | GameComponentsNeedle | bool | Auto-reset on empty server |
| `needle_IsSinglePlayer` | GameComponentsNeedle | bool | Must be false for multiplayer |

### Important Optional Variables

| Variable | Purpose |
|----------|---------|
| `needle_ServerBroadcast` | Server broadcast message |
| `needle_ServerOptions` | Server option flags |
| `needle_publicip` | Public IP override |
| `needle_IdleTimeoutTime` | Kick idle players after N seconds |
| `needle_IdleTimeoutTimeWarning` | Warning before idle kick |
| `needle_PingTooHighThreshold` | Max ping before kick |
| `needle_PingTooHighDropTime` | Time over threshold before kick |
| `needle_unhealthyServerKickTime` | Kick time for unhealthy server |
| `needle_unhealthyServerKillTimeAfterKickTime` | Kill time after kick |
| `needle_MatchAutoStart` | Auto-start match |
| `needle_MatchCountdownTime` | Pre-match countdown |
| `needle_MatchBalanceTime` | Team balance timer |
| `needle_EnableTeamShuffle` | Enable team shuffling |
| `needle_AllowPlayerTeamChange` | Allow team switching |
| `needle_privateServiceUrlOverride` | Override private API URL |
| `needle_publicServiceUrlOverride` | Override public API URL |
| `needle_serviceApiVersion` | API version string |
| `needle_RegionLookupUrl` | Region lookup URL |
| `needle_publishMatchStats` | Publish stats to backend |
| `AllowServerRestart` | Allow server restart on match end |
| `serverUpdateHz` | Server tick rate |
| `needle_StartRegion` | Starting region code |

### Match Types (needle_MatchType values)
From `MatchType_*` strings:
- `Conquest` - Control point capture mode
- `Recon` - Recon mode with tickets
- `Hunt` - Hunter vs hunted
- `Freeplay` - Free play mode
- `Needle` - Base Needle mode
- `NeedleCrisis` - Crisis variant
- `NeedleDiscovery` - Discovery variant
- `NeedleEscape` - Escape variant
- `NeedleExploration` - Exploration variant
- `Tutorial` - Tutorial mode

### Match Sizes (needle_MatchSize values)
- `Small`
- `Medium`
- `Large`

### Matchmaking Regions
- `useast`
- `uswest`
- `europe`
- `asia`
- `oceania`
- `southamerica`

---

## 9. Backend Service Architecture

### [CONFIRMED] API Base URLs
| URL | Purpose |
|-----|---------|
| `https://deadstar.rel.armature.com/` | Public API base (Armature Studio backend) |
| `region.deadstarservices.com` | Region lookup DNS |
| `http://169.254.169.254/2014-11-05/` | AWS EC2 metadata endpoint |

### [CONFIRMED] AWS Metadata Usage
The server queries AWS EC2 instance metadata:
- `meta-data/instance-id`
- `meta-data/instance-type`
- `meta-data/public-ipv4`

This confirms original servers ran on AWS EC2.

### [CONFIRMED] Service Architecture (NNeedleWebServiceCommon)
The game has two service tiers:
1. **Public services**: Uses `GetPublicServicesUrlForPath()` and `GetPublicServicesCertificate()`
2. **Private services**: Uses `GetPrivateServicesUrlForPath()` with client cert auth (`GetPrivateServicesClientCertificate()`, `GetPrivateServicesClientKey()`, `GetPrivateServicesCACertificate()`)

Override variables:
- `needle_publicServiceUrlOverride` - Override public API base URL
- `needle_privateServiceUrlOverride` - Override private API base URL

### [CONFIRMED] Server-Side Services
| Service | Source File | Purpose |
|---------|------------|---------|
| CNeedleServerReservationService | Services\CNeedleServerReservationService.cpp | Server registration/heartbeat |
| CNeedleServerAccountDataService | Services\CNeedleServerAccountDataService.cpp | Player account data sync |
| CNeedleServerCapitalShipDataService | GameObjects\NeedleCapitalShip\ | Capital ship match stats |
| CNeedleServerStatusCommunicator | (runtime) | Server health/status reporting |
| NeedleGameServerUpdate | (runtime) | Server state updates to backend |

### [CONFIRMED] Client-Side Matchmaking
| Component | Purpose |
|-----------|---------|
| CComponentNeedleNetworkClientMatchMaker | Client matchmaking requests |
| NNeedleMatchMaker | Matchmaking protocol handler |
| NNeedleInstanceWrangler | Server instance JSON encode/decode |

### [CONFIRMED] Matchmaking Protocol
The matchmaker is HTTP-based with JSON responses:
```
Matchmaker: StartRequest - Starting matchmake with parameters: %s.
Matchmaker: GetProgressRequest - Starting LaunchProgressMatchMakeRequest with parameters: %s.
Matchmaker: Request complete. Server address: %s:%d.
Matchmaker: StartRequest - Attempting direct connection to %s.
```

Flow:
1. Client sends initial matchmake request (HTTP POST)
2. Client polls progress (HTTP GET/POST)
3. Server responds with `address:port` when match found
4. Client connects directly to game server

### [CONFIRMED] Google Analytics
```
https://www.google-analytics.com/collect
&aid=com.armature.deadStar&av=WIN-
```
The game reports analytics to Google Analytics with app ID `com.armature.deadStar`.

---

## 10. Network Protocol

### [CONFIRMED] Transport
- **Protocol**: UDP (via WS2_32.dll Winsock)
- **Port log**: `CNetConnectionManager: Listening on port %d`
- **Port type**: unsigned short (`USHORT` / `WORD` - from `GetListenPort` returning `G` = unsigned short)
- **Bind retry**: `Bind to local port %hu failed, trying next`

### [CONFIRMED] MTU Discovery
```
ServerMtuDiscovery
ServerMtuHandshake
netServerMaxMtuTestSegmentPackets
netServerMtuTest
```

### [CONFIRMED] Connection Handshake
```
ServerConnectInitAck
ServerConnectTicketAck
```
The connection uses a ticket-based validation (`INetTicketValidator`, `CConnectionTicket`).

### [CONFIRMED] Network Architecture
- `CServerNetworkScene` - Server-side network scene manager
- `CClientNetworkScene` - Client-side network scene manager
- Delta compression: `Server delta-base outran client window, resyncing..`
- Listen server support: `FakeListenForSinglePlayer`, `CreateOrGetExistingListenServerConnectionIfListening`

---

## 11. Game Data

### [CONFIRMED] Asset Archive
All game data is packed in `GameData/gamedata.ara` (Armature Resource Archive).
No loose `.sgpr` files exist; they are contained within the archive.

### [CONFIRMED] Config Files (expected in game root `$/`)
- `commandlineargs.txt` - Additional command-line arguments
- `gamescriptvars.txt` - Script variable overrides (key="value"; format)
- `KeyboardControlDefaults.txt` - Input bindings
- `GameSettings.json` - Game settings

---

## 12. Critical Findings for Server Revival

### Immediate Blockers
1. **No loose .sgpr files**: The world/level files are inside `gamedata.ara`. The server needs either:
   - The `-i` flag pointing to an extracted .sgpr file
   - A `startupScripting` override in `gamescriptvars.txt`
   - An understanding of how the server discovers world files internally

2. **Steam requirement**: All major DLLs import `steam_api64.dll`. Need either:
   - Steam running with game ownership
   - `steam_appid.txt` with `366400`
   - Goldberg Steam emulator

3. **Renderer requirement**: The DLL chain includes D3D11. Need either:
   - A GPU/virtual display
   - Setting `needle_ServerDrawMainView=false` (may reduce but not eliminate D3D requirement)
   - A headless D3D11 solution

4. **Dead backend**: `https://deadstar.rel.armature.com/` is likely down. Must:
   - Override with `needle_publicServiceUrlOverride` and `needle_privateServiceUrlOverride`
   - Build replacement API server
   - Set `needle_useMatchmaker=false` for direct connect

### Recommended Startup Configuration

**gamescriptvars.txt:**
```
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

**steam_appid.txt:**
```
366400
```

**commandlineargs.txt:**
```
-i $/GameData/needle_server.sgpr
```
[UNCERTAIN] The exact .sgpr filename for server startup is unknown.

---

## 13. DeadStarServer.c Launcher

The launcher source file did not exist at `DeadStarServer.c`. A complete launcher has been written to `/home/john-tran/Desktop/Dead Star Revival/Revival Assets/server/DeadStarServer.c`.

### Launcher Design
- Runtime loads GameCore_Steam_Release.dll via `LoadLibraryA`
- Resolves `bpeWin32Server_GameCoreMain` by mangled name
- Passes (hInstance, argc, argv) to the server entry
- Creates `steam_appid.txt` if not present
- Supports all command-line passthrough
- Console mode for log output
